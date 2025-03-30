class SerialPort:
    def __init__(self, device, name, status, enabled=True):
        self.device = device  # COM6
        self.name = name  # Deskripsi port
        self.status = status  # connected/disconnected
        self.enabled = enabled  # Apakah port diaktifkan oleh pengguna
        self.last_used = None  # Kapan terakhir digunakan
        self.simcard = None  # Informasi SIM card

    def __repr__(self):
        status_text = f"{self.status}"
        if not self.enabled:
            status_text += " (disabled)"

        sim_info = ""
        if self.simcard:
            sim_info = f" - SIM: {self.simcard['iccid'][-4:]}"

        return f"{self.device} ({self.name}) - {status_text}{sim_info}"
