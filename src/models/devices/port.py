from .base import PortDevice


class SerialPort(PortDevice):
    """Representasi port serial fisik"""

    def __init__(self, device_id, name=None):
        super().__init__(device_id, name)
        self.connection_params = {"baudrate": 115200, "timeout": 1}
        self.simcard_id = None

    def set_active(self, active):
        """Mengaktifkan atau menonaktifkan port"""
        self.active = active
        self.mark_activity()

    def set_status(self, status):
        """Mengubah status koneksi (connected, disconnected, unknown)"""
        self.status = status
        self.mark_activity()

    def is_available(self):
        """Memeriksa apakah port tersedia untuk digunakan"""
        return self.is_connected() and self.active

    def __repr__(self):
        status_text = self.status.capitalize()
        active_text = "Active" if self.active else "Inactive"
        return f"{self.device_id} ({self.name}) - {status_text}, {active_text}"
