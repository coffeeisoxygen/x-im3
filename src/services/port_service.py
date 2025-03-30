import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from src.controllers.port_controller import PortController
from src.models.devices.port import SerialPort
from src.utils.config import load_config

logger = logging.getLogger(__name__)


class PortService:
    """Service untuk deteksi dan manajemen port"""

    def __init__(self, config_file="config.json"):
        self.config = load_config(config_file)
        self.ports = {}  # Dictionary of SerialPort objects
        self.port_controller = PortController(config_file)

        # Thread management
        self.monitor_thread = None
        self.monitoring = False
        self.lock = threading.Lock()

        logger.info("PortService initialized")

    def detect_ports(self):
        """Mendeteksi dan memverifikasi port yang tersedia"""
        logger.info("Starting port detection")
        system_ports = self.port_controller.list_system_ports()
        logger.debug(f"Found {len(system_ports)} system ports")

        # Remember active state of existing ports
        active_states = {}
        for device_id, port in self.ports.items():
            active_states[device_id] = port.active

        # Results container and synchronization
        verified_ports = {}
        lock = threading.Lock()

        def verify_port(port_info):
            device_id = port_info.device
            name = port_info.description

            # Skip excluded ports
            if any(ex.lower() in name.lower() for ex in self.config["excluded_ports"]):
                logger.debug(f"Skipping excluded port: {device_id} - {name}")
                return

            # Only process ports matching our filters, unless filters are empty
            filters = self.config["port_filters"]
            if filters and not any(f.lower() in name.lower() for f in filters):
                logger.debug(f"Port didn't match any filter: {device_id} - {name}")
                return

            # Create port object
            port = SerialPort(device_id, name)

            # Restore active state if port existed before
            if device_id in active_states:
                port.set_active(active_states[device_id])

            # Verify connection
            connection = self.port_controller.open_connection(device_id)
            if connection:
                logger.debug(f"Testing connection to {device_id}")
                response = self.port_controller.send_command(connection, "AT")
                connected = response and "OK" in response
                port.set_status("connected" if connected else "disconnected")
                self.port_controller.close_connection(connection)
            else:
                port.set_status("disconnected")

            # Thread-safe update of results
            with lock:
                verified_ports[device_id] = port
                logger.debug(f"Port {device_id} verified: {port.status}")

        # Use multithreading for parallel detection
        with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            executor.map(verify_port, system_ports)

        # Update ports dictionary
        with self.lock:
            self.ports = verified_ports

        connected_count = sum(1 for p in self.ports.values() if p.is_connected())
        logger.info(
            f"Port detection complete: {connected_count}/{len(self.ports)} connected"
        )

        return self.ports

    def start_monitoring(self):
        """Start background monitoring thread"""
        if self.monitoring:
            logger.warning("Port monitoring already running")
            return False

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_ports)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Port monitoring started")
        return True

    def stop_monitoring(self):
        """Stop background monitoring thread"""
        if not self.monitoring:
            return False

        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        logger.info("Port monitoring stopped")
        return True

    def _monitor_ports(self):
        """Background thread to monitor port status"""
        logger.debug("Port monitor thread started")

        while self.monitoring:
            try:
                logger.debug("Checking port statuses")
                for device_id, port in list(self.ports.items()):
                    connection = self.port_controller.open_connection(device_id)
                    if connection:
                        response = self.port_controller.send_command(connection, "AT")
                        connected = response and "OK" in response
                        with self.lock:
                            port.set_status(
                                "connected" if connected else "disconnected"
                            )
                        self.port_controller.close_connection(connection)
                    else:
                        with self.lock:
                            port.set_status("disconnected")

                # Wait for next check interval
                time.sleep(self.config["port_monitor_interval"])
            except Exception as e:
                logger.error(f"Error in port monitoring: {str(e)}")
                time.sleep(5)  # Wait a bit longer if there was an error

        logger.debug("Port monitor thread stopped")

    def list_all_ports(self):
        """Mendapatkan semua port"""
        with self.lock:
            return self.ports.copy()

    def list_active_ports(self):
        """Mengambil semua port yang aktif"""
        with self.lock:
            return {
                device_id: port for device_id, port in self.ports.items() if port.active
            }

    def list_connected_ports(self):
        """Mengambil semua port yang terhubung"""
        with self.lock:
            return {
                device_id: port
                for device_id, port in self.ports.items()
                if port.is_connected()
            }

    def list_available_ports(self):
        """Mengambil semua port yang tersedia untuk digunakan (terhubung dan aktif)"""
        with self.lock:
            return {
                device_id: port
                for device_id, port in self.ports.items()
                if port.is_connected() and port.active
            }

    def enable_port(self, device_id):
        """Mengaktifkan port tertentu"""
        with self.lock:
            if device_id in self.ports:
                logger.info(f"Enabling port {device_id}")
                self.ports[device_id].set_active(True)
                return True
        return False

    def disable_port(self, device_id):
        """Menonaktifkan port tertentu"""
        with self.lock:
            if device_id in self.ports:
                logger.info(f"Disabling port {device_id}")
                self.ports[device_id].set_active(False)
                return True
        return False

    def enable_all_ports(self):
        """Mengaktifkan semua port"""
        with self.lock:
            for port in self.ports.values():
                port.set_active(True)
        logger.info(f"Enabled all ports ({len(self.ports)})")

    def disable_all_ports(self):
        """Menonaktifkan semua port"""
        with self.lock:
            for port in self.ports.values():
                port.set_active(False)
        logger.info(f"Disabled all ports ({len(self.ports)})")

    def get_port(self, device_id):
        """Mendapatkan port berdasarkan ID"""
        with self.lock:
            return self.ports.get(device_id)

    def refresh_port(self, device_id):
        """Refresh status koneksi port tertentu"""
        port = self.get_port(device_id)
        if not port:
            logger.warning(f"Port {device_id} not found")
            return False

        connection = self.port_controller.open_connection(device_id)
        if connection:
            response = self.port_controller.send_command(connection, "AT")
            with self.lock:
                port.set_status(
                    "connected" if response and "OK" in response else "disconnected"
                )
            self.port_controller.close_connection(connection)
            logger.debug(f"Refreshed port {device_id}: {port.status}")
            return port.is_connected()
        else:
            with self.lock:
                port.set_status("disconnected")
            logger.debug(f"Could not connect to port {device_id}")
            return False

    def get_sorted_ports(self):
        """Mendapatkan semua port diurutkan berdasarkan nama (COM1, COM2, ...)"""
        with self.lock:
            # Konversi port ke list untuk pengurutan
            ports_list = list(self.ports.values())

            # Urutkan berdasarkan nomor COM (COM1, COM2, ...)
            def get_com_number(port):
                # Ekstrak angka dari COM10, COM2, dll.
                try:
                    return int(port.device_id.lower().replace("com", ""))
                except ValueError:
                    return 999  # Nilai tinggi untuk yang non-standard

            return sorted(ports_list, key=get_com_number)

    def get_grouped_ports(self):
        """Mendapatkan port dikelompokkan berdasarkan status koneksi"""
        sorted_ports = self.get_sorted_ports()

        # Kelompokkan berdasarkan status
        connected = [p for p in sorted_ports if p.is_connected()]
        disconnected = [p for p in sorted_ports if not p.is_connected()]

        return {"connected": connected, "disconnected": disconnected}
