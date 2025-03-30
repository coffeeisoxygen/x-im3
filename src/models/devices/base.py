from abc import ABC, abstractmethod
from datetime import datetime


class Device(ABC):
    """Base class untuk semua perangkat"""

    @abstractmethod
    def get_identifier(self):
        """Mendapatkan identifier unik perangkat"""
        pass

    @abstractmethod
    def is_connected(self):
        """Memeriksa apakah perangkat terhubung"""
        pass


class PortDevice(Device):
    """Base class untuk perangkat port serial"""

    def __init__(self, device_id, name=None):
        self.device_id = device_id
        self.name = name or device_id
        self.status = "unknown"
        self.enabled = True
        self.last_activity = None

    def get_identifier(self):
        return self.device_id

    def is_connected(self):
        return self.status == "connected"

    def mark_activity(self):
        """Catat aktivitas terbaru pada perangkat"""
        self.last_activity = datetime.now()
