from datetime import datetime

from src.utils.atcommand import ATCommand
from src.utils.logging import get_logger

logger = get_logger("SimCard")


class SimCard:
    """Kelas untuk menangani data SIM Card"""

    def __init__(self, port_connection):
        self.iccid = None
        self.msisdn = None
        self.balance = None
        self.active_until = None
        self.last_update = None
        self.at = ATCommand(port_connection)

    def check_iccid(self):
        """Mengambil ICCID dari perintah AT"""
        response = self.at.send("AT+ICCID")
        if response:
            self.iccid = self.at.parse_response(response, "iccid")
            self.last_update = datetime.now()
            logger.info(f"ICCID diperbarui: {self.iccid}")
        return self.iccid

    def check_info(self):
        """Mengambil info MSISDN, Balance, dan Status Aktif"""
        response = self.at.send("ATD*185#")
        if response:
            self.msisdn = self.at.parse_response(response, "msisdn")
            self.balance = self.at.parse_response(response, "balance")
            self.active_until = self.at.parse_response(response, "active_until")
            self.last_update = datetime.now()
            logger.info(
                f"Info SIM diperbarui: MSISDN={self.msisdn}, Balance={self.balance}, Active={self.active_until}"
            )

        return {
            "msisdn": self.msisdn,
            "balance": self.balance,
            "active_until": self.active_until,
        }
