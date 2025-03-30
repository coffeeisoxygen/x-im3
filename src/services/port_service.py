import threading
from concurrent.futures import ThreadPoolExecutor

from src.controllers.port_controller import PortController
from src.models.devices.port import SerialPort
from src.utils.logging import get_logger

logger = get_logger("services.port")


class PortService:
    """Service untuk deteksi dan manajemen port"""

    def __init__(self, config_file="modem_config.json"):
        self.ports = {}
        self.filters = ["USB Serial", "Modem", "GSM", "WWAN", "HUAWEI", "ZTE", "Sierra"]
        self.config_file = config_file
        self.port_controller = PortController()

    def detect_ports(self, max_workers=10):
        """Mendeteksi port dengan filter dan verifikasi"""
        logger.info("Memulai deteksi port...")

        # Filter awal
        potential_ports = self._filter_ports()
        logger.info(f"Ditemukan {len(potential_ports)} port potensial")

        # Verifikasi koneksi dengan multithreading
        results = {}
        lock = threading.Lock()

        def verify_port(port_info):
            device_id = port_info.device
            name = port_info.description

            # Buat port device
            port = SerialPort(device_id, name, status="unknown")

            # Verifikasi koneksi
            connection = self.port_controller.open_connection(device_id)
            if connection:
                # Coba AT command dasar
                response = self.port_controller.send_command(connection, "AT")
                if response and "OK" in response:
                    port.set_status("connected")
                else:
                    port.set_status("disconnected")

                self.port_controller.close_connection(connection)
            else:
                port.set_status("disconnected")

            # Thread-safe update results
            with lock:
                results[device_id] = port

        # Proses verifikasi paralel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(verify_port, potential_ports)

        # Update ports
        self.ports = results

        connected_count = sum(1 for p in self.ports.values() if p.is_connected())
        logger.info(
            f"Deteksi selesai. {connected_count}/{len(self.ports)} port terhubung"
        )

        return self.ports

    def _filter_ports(self):
        """Filter port berdasarkan deskripsi"""
        all_ports = self.port_controller.list_system_ports()
        filtered = []

        for port in all_ports:
            # Skip port yang jelas bukan modem
            excluded = ["Bluetooth", "Printer", "Mouse", "Keyboard"]
            if any(ex.lower() in port.description.lower() for ex in excluded):
                continue

            # Filter berdasarkan deskripsi
            if any(f.lower() in port.description.lower() for f in self.filters):
                filtered.append(port)

        return filtered

    def get_port(self, device_id):
        """Mendapatkan port berdasarkan ID"""
        return self.ports.get(device_id)

    def get_all_ports(self):
        """Mendapatkan semua port"""
        return list(self.ports.values())

    def get_connected_ports(self):
        """Mendapatkan port yang terhubung"""
        return [p for p in self.ports.values() if p.is_connected()]

    def get_available_ports(self):
        """Mendapatkan port yang tersedia untuk digunakan"""
        return [p for p in self.ports.values() if p.is_available()]

    def enable_port(self, device_id):
        """Mengaktifkan port"""
        if device_id in self.ports:
            self.ports[device_id].enabled = True
            logger.info(f"Port {device_id} diaktifkan")
            return True
        return False

    def disable_port(self, device_id):
        """Menonaktifkan port"""
        if device_id in self.ports:
            self.ports[device_id].enabled = False
            logger.info(f"Port {device_id} dinonaktifkan")
            return True
        return False

    def refresh_port(self, device_id):
        """Refresh status koneksi single port"""
        if device_id not in self.ports:
            return False

        port = self.ports[device_id]
        connection = self.port_controller.open_connection(device_id)
        if connection:
            response = self.port_controller.send_command(connection, "AT")
            port.set_status("connected" if response and "OK" in response else "disconnected")
            self.port_controller.close_connection(connection)
        else:
            port.set_status("disconnected")

        return port.is_connected()

    def enable_multiple_ports(self, device_ids):
        """Mengaktifkan beberapa port sekaligus"""
        results = {}
        for device_id in device_ids:
            results[device_id] = self.enable_port(device_id)
        return results

    def disable_multiple_ports(self, device_ids):
        """Menonaktifkan beberapa port sekaligus"""
        results = {}
        for device_id in device_ids:
            results[device_id] = self.disable_port(device_id)
        return results
