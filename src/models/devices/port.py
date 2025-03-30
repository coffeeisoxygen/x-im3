from .base import PortDevice


class SerialPort(PortDevice):
    """Representasi port serial fisik"""

    def __init__(self, device_id, name=None, status="unknown", enabled=True):
        super().__init__(device_id, name)
        self.status = status
        self.enabled = enabled
        self.simcard = None
        self.connection_info = {"baudrate": 115200, "timeout": 1}

    def __repr__(self):
        status_text = self.status
        if not self.enabled:
            status_text += " (disabled)"

        sim_info = ""
        if self.simcard:
            sim_info = f" - SIM: {self.simcard.get_short_id()}"

        return f"{self.device_id} ({self.name}) - {status_text}{sim_info}"

    def set_status(self, status):
        """Update status koneksi port"""
        self.status = status
        self.mark_activity()

    def is_available(self):
        """Memeriksa apakah port tersedia untuk digunakan"""
        return self.is_connected() and self.enabled
