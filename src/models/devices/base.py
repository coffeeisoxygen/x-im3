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
        self.status = "unknown"  # unknown, connected, disconnected
        self.active = False  # Flag apakah port diaktifkan oleh user
        self.last_activity = None

    def get_identifier(self):
        """Implementasi method dari base class"""
        return self.device_id

    def is_connected(self):
        """Implementasi method dari base class"""
        return self.status == "connected"

    def is_active(self):
        """Memeriksa apakah port diaktifkan oleh user"""
        return self.active

    def mark_activity(self):
        """Catat aktivitas terbaru"""
        self.last_activity = datetime.now()

    def __repr__(self):
        return f"{self.device_id} ({self.name}) - Status: {self.status}, Active: {self.active}"
