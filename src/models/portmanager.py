import json
import os
import time

import serial
import serial.tools.list_ports

from src.utils.logging import get_logger

from .serialport import SerialPort

# Create logger for this module
logger = get_logger("models.portmanager")


class PortManager:
    def __init__(self, filters=None, config_file="modem_config.json"):
        """
        Inisialisasi Port Manager dengan filter opsional.

        Args:
            filters: List string deskripsi untuk filter (default: None)
            config_file: File konfigurasi untuk menyimpan status aktif/nonaktif port
        """
        self.ports = {}
        self.default_filters = [
            "USB Serial",
            "Modem",
            "GSM",
            "WWAN",
            "HUAWEI",
            "ZTE",
            "Sierra",
        ]
        self.custom_filters = filters
        self.config_file = config_file
        self.user_preferences = self._load_preferences()
        logger.info("PortManager initialized")

    def _load_preferences(self):
        """Muat preferensi pengguna dari file konfigurasi"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Gagal memuat preferensi: {str(e)}")
        return {"enabled_ports": [], "disabled_ports": []}

    def _save_preferences(self):
        """Simpan preferensi pengguna ke file konfigurasi"""
        pref = {
            "enabled_ports": [p.device for p in self.ports.values() if p.enabled],
            "disabled_ports": [p.device for p in self.ports.values() if not p.enabled],
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(pref, f, indent=4)
        except Exception as e:
            logger.error(f"Gagal menyimpan preferensi: {str(e)}")

    def detect_ports(self, preserve_preferences=True):
        """
        Mendeteksi port secara lengkap (filter + verifikasi koneksi).

        Args:
            preserve_preferences: Apakah mempertahankan preferensi pengguna (default: True)
        """
        logger.info("Memulai deteksi port...")

        # Simpan status enabled sebelumnya
        previous_enabled_status = {}
        if preserve_preferences:
            for device, port in self.ports.items():
                previous_enabled_status[device] = port.enabled

        # Reset ports dict but keep preferences
        self.ports = {}

        # Langkah 1: Filter awal berdasarkan deskripsi
        potential_ports = self._filter_ports()
        logger.info(
            f"Ditemukan {len(potential_ports)} port potensial setelah filtering"
        )

        # Langkah 2: Verifikasi koneksi dengan AT command
        for port in potential_ports:
            connection_status = self._verify_connection(port.device)

            # Tentukan status enabled berdasarkan preferensi sebelumnya
            enabled = True
            if preserve_preferences and port.device in previous_enabled_status:
                enabled = previous_enabled_status[port.device]
            elif port.device in self.user_preferences["disabled_ports"]:
                enabled = False

            if connection_status:
                self.ports[port.device] = SerialPort(
                    port.device, port.name, "connected", enabled
                )
            else:
                self.ports[port.device] = SerialPort(
                    port.device, port.name, "disconnected", enabled
                )

        logger.info(f"Deteksi selesai. Ditemukan {len(self.ports)} port modem")
        logger.info(
            f"   - {len([p for p in self.ports.values() if p.status == 'connected'])} port terhubung"
        )
        logger.info(
            f"   - {len([p for p in self.ports.values() if p.status == 'disconnected'])} port tidak terhubung"
        )
        logger.info(
            f"   - {len([p for p in self.ports.values() if p.enabled])} port diaktifkan"
        )
        logger.info(
            f"   - {len([p for p in self.ports.values() if not p.enabled])} port dinonaktifkan"
        )

        # Simpan preferensi
        self._save_preferences()

        return self.ports

    def _filter_ports(self):
        """
        Filter port berdasarkan deskripsi.

        Returns:
            list: Port yang lolos filter
        """
        filters = self.custom_filters or self.default_filters
        all_ports = serial.tools.list_ports.comports()
        logger.debug(f"Total port terdeteksi: {len(all_ports)}")

        # Filter port berdasarkan deskripsi
        filtered_ports = []
        excluded = ["Bluetooth", "Printer", "Mouse", "Keyboard"]

        for port in all_ports:
            logger.debug(f"Memeriksa port: {port.device} - {port.description}")

            # Skip port yang jelas bukan modem
            if any(ex.lower() in port.description.lower() for ex in excluded):
                logger.debug(f"Port {port.device} dilewati (kategori excluded)")
                continue

            # Ambil port yang sesuai filter
            if any(f.lower() in port.description.lower() for f in filters):
                logger.debug(f"Port {port.device} lolos filter deskripsi")
                filtered_ports.append(port)
            else:
                logger.debug(f"Port {port.device} tidak lolos filter deskripsi")

        return filtered_ports

    def _verify_connection(self, port_name):
        """
        Verifikasi koneksi dengan port menggunakan AT command.

        Args:
            port_name: Nama port yang akan diverifikasi

        Returns:
            bool: True jika terhubung, False jika tidak
        """
        baud_rates = [115200, 9600, 57600, 38400, 19200]  # Prioritaskan baud yang umum
        at_commands = [b"AT\r\n"]  # Mulai dengan AT command paling dasar

        for baud in baud_rates:
            try:
                logger.debug(f"Mencoba port {port_name} dengan baud rate {baud}")
                ser = serial.Serial(port_name, baud, timeout=1)
                time.sleep(0.5)

                # Reset buffer
                ser.reset_input_buffer()
                ser.reset_output_buffer()

                # Kirim AT command
                ser.write(at_commands[0])
                time.sleep(0.5)
                response = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")

                # Tutup koneksi
                ser.close()

                # Periksa respons
                if "OK" in response:
                    logger.info(f"Port {port_name} terhubung dengan baud {baud}")
                    return True

            except Exception as e:
                logger.debug(
                    f"Gagal koneksi ke {port_name} dengan baud {baud}: {str(e)}"
                )

        logger.debug(f"Port {port_name} tidak merespons AT command")
        return False

    def enable_port(self, device):
        """Aktifkan port untuk digunakan"""
        if device in self.ports:
            self.ports[device].enabled = True
            logger.info(f"Port {device} diaktifkan")
            self._save_preferences()
            return True
        logger.warning(f"Port {device} tidak ditemukan")
        return False

    def disable_port(self, device):
        """Nonaktifkan port"""
        if device in self.ports:
            self.ports[device].enabled = False
            logger.info(f"Port {device} dinonaktifkan")
            self._save_preferences()
            return True
        logger.warning(f"Port {device} tidak ditemukan")
        return False

    def get_available_ports(self):
        """Mendapatkan port yang terhubung dan diaktifkan"""
        available = [
            p for p in self.ports.values() if p.status == "connected" and p.enabled
        ]
        logger.debug(f"Mengembalikan {len(available)} port tersedia")
        return available

    def get_connected_ports(self):
        """Mendapatkan semua port yang terhubung (aktif dan nonaktif)"""
        connected = [p for p in self.ports.values() if p.status == "connected"]
        logger.debug(f"Mengembalikan {len(connected)} port terhubung")
        return connected

    def get_enabled_ports(self):
        """Mendapatkan port yang diaktifkan oleh pengguna"""
        enabled = [p for p in self.ports.values() if p.enabled]
        logger.debug(f"Mengembalikan {len(enabled)} port diaktifkan")
        return enabled

    def get_all_ports(self):
        """Mendapatkan semua port (terhubung dan tidak terhubung)"""
        return list(self.ports.values())

    def detect_simcard(self, port_device):
        """Deteksi informasi SIM card pada port tertentu"""
        if port_device not in self.ports:
            logger.warning(f"Port {port_device} tidak ada")
            return None

        port = self.ports[port_device]
        if port.status != "connected":
            logger.warning(f"Port {port_device} tidak terhubung")
            return None

        logger.info(f"Mendeteksi SIM card pada port {port_device}")

        try:
            # Gunakan baudrate yang sudah diketahui berhasil
            ser = serial.Serial(port_device, 115200, timeout=2)
            time.sleep(0.5)

            # Reset buffer
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            # Deteksi ICCID
            ser.write(b"AT+CCID\r\n")
            time.sleep(0.5)
            response = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            iccid = self._parse_iccid(response)

            # Deteksi nomor telepon (MSISDN)
            ser.write(b"AT+CNUM\r\n")
            time.sleep(0.5)
            response = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            msisdn = self._parse_msisdn(response)

            # Deteksi kekuatan sinyal
            ser.write(b"AT+CSQ\r\n")
            time.sleep(0.5)
            response = ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            signal = self._parse_signal_strength(response)

            ser.close()

            if iccid:
                # Update status port
                port.simcard = {"iccid": iccid, "msisdn": msisdn, "signal": signal}
                logger.info(
                    f"SIM card terdeteksi pada {port_device}: ICCID {iccid}, MSISDN {msisdn}"
                )
                return port.simcard
            else:
                port.simcard = None
                logger.warning(f"Tidak ada SIM card terdeteksi pada {port_device}")
                return None

        except Exception as e:
            logger.error(f"Error saat deteksi SIM card pada {port_device}: {str(e)}")
            return None

    def detect_all_simcards(self):
        """Deteksi SIM card di semua port yang terhubung dan diaktifkan"""
        logger.info("Mendeteksi SIM card di semua port...")

        sim_cards = {}
        available_ports = self.get_available_ports()

        for port in available_ports:
            sim_info = self.detect_simcard(port.device)
            if sim_info and "iccid" in sim_info:
                sim_cards[port.device] = sim_info

        logger.info(f"Deteksi SIM card selesai. Ditemukan {len(sim_cards)} SIM card")
        return sim_cards

    def _parse_iccid(self, response):
        """Parse ICCID dari respons AT+CCID"""
        if not response:
            return None

        # Format respons bervariasi antar modem
        # +CCID: 8962xxxxxxxxxx
        # 8962xxxxxxxxxx
        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()
            if "+CCID:" in line:
                parts = line.split("+CCID:")
                if len(parts) > 1:
                    return parts[1].strip()
            elif line.startswith("8962") or line.startswith(
                "8901"
            ):  # Awalan ICCID umum
                return line.strip()
        return None

    def _parse_msisdn(self, response):
        """Parse MSISDN dari respons AT+CNUM"""
        if not response:
            return None

        # +CNUM: "","08xxxxxxxxx",129
        lines = response.strip().split("\n")
        for line in lines:
            if "+CNUM:" in line:
                parts = line.split(",")
                if len(parts) > 1:
                    number = parts[1].replace('"', "").strip()
                    return number
        return None

    def _parse_signal_strength(self, response):
        """Parse kekuatan sinyal dari respons AT+CSQ"""
        if not response:
            return 0

        # +CSQ: 21,0
        lines = response.strip().split("\n")
        for line in lines:
            if "+CSQ:" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    values = parts[1].strip().split(",")
                    if values:
                        try:
                            signal = int(values[0])
                            return signal
                        except ValueError:
                            pass
        return 0
