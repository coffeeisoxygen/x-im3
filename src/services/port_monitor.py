import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class PortMonitor:
    """Kelas untuk memonitor status port serial secara periodik"""

    def __init__(self, port_service, config=None):
        """
        Inisialisasi monitor port

        Args:
            port_service: Instance PortService yang digunakan
            config: Konfigurasi monitor (dict)
        """
        self.port_service = port_service
        self.config = config or {}
        self.interval = self.config.get("port_monitor_interval", 2)
        self.running = False
        self.monitor_thread = None
        self.output_handlers = []
        logger.info("PortMonitor initialized")

    def add_output_handler(self, handler):
        """
        Menambahkan handler untuk output monitoring

        Args:
            handler: Fungsi yang menerima status monitoring
        """
        if callable(handler):
            self.output_handlers.append(handler)
            return True
        return False

    def remove_output_handler(self, handler):
        """Menghapus handler dari daftar"""
        if handler in self.output_handlers:
            self.output_handlers.remove(handler)
            return True
        return False

    def start(self):
        """Memulai monitor dalam thread terpisah"""
        if self.running:
            logger.warning("Monitor already running")
            return False

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Port monitoring started")
        return True

    def stop(self):
        """Menghentikan monitor"""
        if not self.running:
            return False

        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        logger.info("Port monitoring stopped")
        return True

    def _monitor_loop(self):
        """Loop monitor utama yang berjalan di thread terpisah"""
        logger.debug("Monitor thread started")

        while self.running:
            try:
                # PERBAIKAN: Refresh semua port terlebih dahulu
                # untuk mendeteksi status koneksi secara real-time
                for device_id in self.port_service.list_all_ports():
                    self.port_service.refresh_port(device_id)

                # Dapatkan status port aktif setelah refresh
                active_ports = self.port_service.list_active_ports()

                # Buat data status dengan timestamp
                status_data = {"timestamp": datetime.now(), "ports": active_ports}

                # Kirim ke semua handler
                for handler in self.output_handlers:
                    try:
                        handler(status_data)
                    except Exception as e:
                        logger.error(f"Error in output handler: {e}")

                # Tunggu interval berikutnya
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Tunggu lebih lama jika ada error

        logger.debug("Monitor thread stopped")

    def get_current_status(self):
        """Mendapatkan status terakhir (non-blocking)"""
        active_ports = self.port_service.list_active_ports()
        return {"timestamp": datetime.now(), "ports": active_ports}
