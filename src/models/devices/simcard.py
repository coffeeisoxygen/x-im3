from .base import Device


class SimCard(Device):
    """Representasi SIM card fisik"""

    def __init__(self, iccid, msisdn=None, signal=0):
        self.iccid = iccid
        self.msisdn = msisdn or "Unknown"
        self.signal = signal
        self.port_device = None
        self.carrier = None
        self.last_updated = None

    def get_identifier(self):
        return self.iccid

    def is_connected(self):
        return self.port_device is not None

    def get_short_id(self):
        """Mendapatkan versi pendek dari ICCID"""
        if len(self.iccid) > 8:
            return f"{self.iccid[:4]}...{self.iccid[-4:]}"
        return self.iccid

    def __repr__(self):
        port_info = f" on {self.port_device}" if self.port_device else ""
        return f"ICCID: {self.get_short_id()}, MSISDN: {self.msisdn}, Signal: {self.signal}{port_info}"
