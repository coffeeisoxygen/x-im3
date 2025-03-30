import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import serial

from src.services.port_service import PortService
from src.services.sim_service import SimService  # Asumsi akan dibuat
from src.utils.logging import get_logger

logger = get_logger("models.modemmanager")


class ModemManager:
    """
    Class utama untuk mengorkestrasi semua komponen aplikasi.
    Menggunakan Service Pattern untuk manajemen komponen.
    """

    def __init__(self, config_file="modem_config.json", max_workers=10):
        """Inisialisasi ModemManager dengan services yang diperlukan"""
        logger.info("Inisialisasi ModemManager")

        # Inisialisasi services
        self.port_service = PortService(config_file=config_file)
        self.sim_service = SimService()  # Perlu dibuat

        # Setup threading components
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.command_queue = queue.Queue()
        self.response_callbacks = {}
        self.lock = threading.Lock()

        # Start command processing thread
        self.running = True
        self.command_thread = threading.Thread(target=self._process_command_queue)
        self.command_thread.daemon = True
        self.command_thread.start()

    def _process_command_queue(self):
        """Process commands from queue in background"""
        while self.running:
            try:
                # Get command with 1 second timeout
                command_data = self.command_queue.get(timeout=1)
                if command_data:
                    port_device, command, callback, timeout = command_data
                    try:
                        result = self._execute_at_command(port_device, command, timeout)
                        if callback:
                            callback(result)
                    except Exception as e:
                        logger.error(f"Error executing command: {str(e)}")
                    finally:
                        self.command_queue.task_done()
            except queue.Empty:
                pass  # Just continue if queue is empty

    def _execute_at_command(self, port_device, command, timeout):
        """Execute AT command directly"""
        # This is the actual implementation that runs in a worker thread
        return self.send_at_command(port_device, command, timeout)

    def send_at_command_async(self, port_device, command, callback=None, timeout=1):
        """
        Send AT command asynchronously

        Args:
            port_device: Port to use
            command: AT command to send
            callback: Function to call with response
            timeout: Response timeout in seconds
        """
        self.command_queue.put((port_device, command, callback, timeout))

    def detect_all_devices(self):
        """Deteksi semua perangkat secara paralel"""
        logger.info("Mendeteksi semua perangkat")

        # Deteksi port terlebih dahulu (sudah paralel di PortService)
        self.port_service.detect_ports(max_workers=8)

        # Kemudian deteksi SIM card pada port yang terdeteksi
        available_ports = self.port_service.get_available_ports()
        sim_count = self.sim_service.detect_simcards_from_ports(available_ports)

        return {
            "ports": {
                "all": self.port_service.get_all_ports(),
                "connected": self.port_service.get_connected_ports(),
                "disconnected": [
                    p for p in self.port_service.get_all_ports() if not p.is_connected()
                ],
            },
            "sim_cards": {
                "count": sim_count,
                "all": self.sim_service.get_all_simcards(),
            },
        }

    def send_at_command(self, port_device, command, timeout=1):
        """
        Kirim AT command ke port tertentu

        Args:
            port_device: Port untuk digunakan (contoh: COM6)
            command: AT command yang akan dikirim
            timeout: Waktu tunggu respons dalam detik

        Returns:
            Respons dari modem atau None jika gagal
        """
        if port_device not in self.port_service.ports:
            logger.warning(f"Port {port_device} tidak ditemukan")
            return None

        port = self.port_service.ports[port_device]
        if port.status != "connected" or not port.enabled:
            logger.warning(f"Port {port_device} tidak terhubung atau tidak diaktifkan")
            return None

        try:
            logger.debug(f"Mengirim command '{command}' ke {port_device}")
            ser = serial.Serial(port_device, 115200, timeout=timeout)
            time.sleep(0.5)

            # Reset buffer
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            # Tambahkan AT di depan command jika tidak ada
            if not command.upper().startswith("AT"):
                command = "AT" + command

            # Pastikan command diakhiri dengan \r\n
            if not command.endswith("\r\n"):
                command += "\r\n"

            # Kirim command
            ser.write(command.encode())
            time.sleep(timeout)
            response = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")

            ser.close()
            logger.debug(f"Respons dari {port_device}: {response}")
            return response
        except Exception as e:
            logger.error(f"Error saat mengirim command ke {port_device}: {str(e)}")
            return None

    def send_at_command_to_all(self, command, timeout=1):
        """
        Kirim AT command ke semua port yang terhubung dan diaktifkan

        Args:
            command: AT command yang akan dikirim
            timeout: Waktu tunggu respons dalam detik

        Returns:
            Dict dengan port device sebagai key dan respons sebagai value
        """
        logger.info(f"Mengirim command '{command}' ke semua port aktif")
        available_ports = self.port_service.get_available_ports()
        results = {}

        for port in available_ports:
            result = self.send_at_command(port.device, command, timeout)
            results[port.device] = result

        return results

    def broadcast_command(self, command, callback=None, timeout=1):
        """
        Kirim AT command ke semua port tersedia secara paralel

        Args:
            command: AT command to send
            callback: Function to call with each response
            timeout: Timeout in seconds

        Returns:
            Future object that will contain results dict when done
        """
        available_ports = self.port_service.get_available_ports()
        results = {}

        def process_port(port):
            result = self.send_at_command(port.device, command, timeout)
            with self.lock:
                results[port.device] = result
            if callback:
                callback(port.device, result)

        # Submit all tasks
        futures = [self.executor.submit(process_port, port) for port in available_ports]

        # Return future that represents completion of all tasks
        return results, futures

    def dial_ussd(self, port_device, ussd_code, timeout=10):
        """
        Dial USSD code pada port tertentu

        Args:
            port_device: Port untuk digunakan
            ussd_code: Kode USSD (contoh: *123#)
            timeout: Waktu tunggu respons dalam detik

        Returns:
            Respons dari modem atau None jika gagal
        """
        logger.info(f"Dialing USSD code {ussd_code} pada port {port_device}")

        # Format AT command untuk USSD
        ussd_command = f'AT+CUSD=1,"{ussd_code}",15'

        response = self.send_at_command(port_device, ussd_command, timeout)

        # Tunggu respons USSD (biasanya dikirim sebagai notifikasi tidak diminta)
        if response and "OK" in response:
            try:
                ser = serial.Serial(port_device, 115200, timeout=timeout)
                time.sleep(2)  # Berikan waktu lebih lama untuk respons USSD

                ussd_response = ser.read(ser.in_waiting).decode(
                    "utf-8", errors="ignore"
                )
                ser.close()

                if "+CUSD:" in ussd_response:
                    logger.debug(f"USSD response: {ussd_response}")
                    return ussd_response
                else:
                    logger.warning(
                        f"Tidak ada respons USSD dalam waktu {timeout} detik"
                    )
            except Exception as e:
                logger.error(f"Error saat membaca respons USSD: {str(e)}")

        return response

    def dial_ussd_to_all(self, ussd_code, timeout=10):
        """
        Dial USSD code pada semua port yang terhubung dan diaktifkan

        Args:
            ussd_code: Kode USSD (contoh: *123#)
            timeout: Waktu tunggu respons dalam detik

        Returns:
            Dict dengan port device sebagai key dan respons sebagai value
        """
        logger.info(f"Dialing USSD code {ussd_code} ke semua port aktif")
        available_ports = self.port_service.get_available_ports()
        results = {}

        for port in available_ports:
            result = self.dial_ussd(port.device, ussd_code, timeout)
            results[port.device] = result

        return results

    def enable_port(self, device_id):
        """Aktifkan port tertentu"""
        return self.port_service.enable_port(device_id)

    def disable_port(self, device_id):
        """Nonaktifkan port tertentu"""
        return self.port_service.disable_port(device_id)

    def get_sim_info(self, iccid):
        """Dapatkan informasi SIM card berdasarkan ICCID"""
        return self.sim_service.get_simcard_info(iccid)

    def get_port_status(self):
        """Dapatkan status semua port"""
        ports = self.port_service.get_all_ports()
        return {
            port.device_id: {"enabled": port.enabled, "status": port.status}
            for port in ports
        }

    def get_single_port_status(self, port_device):
        """Dapatkan status port tertentu"""
        port = self.port_service.get_port(port_device)
        if port:
            return {"enabled": port.enabled, "status": port.status}
        else:
            logger.warning(f"Port {port_device} tidak ditemukan")
            return None

    def check_balance(self, port_device, ussd_code="*123#", timeout=10):
        """
        Cek pulsa pada port tertentu dengan kode USSD umum

        Args:
            port_device: Port untuk digunakan
            ussd_code: Kode USSD untuk cek pulsa (default: *123#)
            timeout: Waktu tunggu respons dalam detik

        Returns:
            Respons dari modem atau None jika gagal
        """
        logger.info(f"Memeriksa pulsa pada port {port_device} dengan kode {ussd_code}")
        return self.dial_ussd(port_device, ussd_code, timeout)

    def send_sms(self, port_device, phone_number, message, timeout=5):
        """
        Kirim SMS dari port tertentu

        Args:
            port_device: Port untuk digunakan
            phone_number: Nomor telepon tujuan
            message: Isi pesan
            timeout: Waktu tunggu respons dalam detik

        Returns:
            True jika berhasil, False jika gagal
        """
        logger.info(f"Mengirim SMS ke {phone_number} dari port {port_device}")

        try:
            # Atur mode teks
            text_mode = self.send_at_command(port_device, "AT+CMGF=1", timeout)
            if not text_mode or "OK" not in text_mode:
                logger.error(f"Gagal mengatur text mode pada port {port_device}")
                return False

            # Atur nomor tujuan
            ser = serial.Serial(port_device, 115200, timeout=timeout)
            time.sleep(0.5)

            ser.write(f'AT+CMGS="{phone_number}"\r'.encode())
            time.sleep(1)

            # Kirim pesan dan Ctrl+Z (26 in ASCII)
            ser.write(f"{message}{chr(26)}".encode())
            time.sleep(5)  # Berikan waktu lebih lama untuk pengiriman SMS

            response = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            ser.close()

            if "+CMGS:" in response:
                logger.debug(f"SMS berhasil dikirim: {response}")
                return True
            else:
                logger.warning(f"SMS gagal dikirim: {response}")
                return False

        except Exception as e:
            logger.error(f"Error saat mengirim SMS: {str(e)}")
            return False

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.running = False
        if hasattr(self, "command_thread") and self.command_thread.is_alive():
            self.command_thread.join(2.0)  # Wait up to 2 seconds
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)
