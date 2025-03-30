import json
import re

from src.controllers.port_controller import PortController
from src.utils.logging import get_logger

logger = get_logger("ATCommand")


class ATCommand:
    """Kelas untuk mengirim perintah AT dan menangani respons"""

    def __init__(self, connection):
        self.connection = connection
        self.patterns = self._load_patterns()

    def _load_patterns(self, config_file="at_patterns.json"):
        """Memuat pola respons dari file konfigurasi"""
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Gagal memuat pola AT: {e}")
            return {}

    def send(self, command):
        """Mengirim perintah AT dan mengembalikan respons"""
        try:
            response = PortController.send_command(self.connection, command)
            return response.strip() if response else None
        except Exception as e:
            logger.error(f"Error saat mengirim AT command: {e}")
            return None

    def parse_response(self, response, pattern_name):
        """Memparsing respons berdasarkan pola"""
        if pattern_name not in self.patterns:
            logger.error(f"Pola '{pattern_name}' tidak ditemukan di konfigurasi")
            return None

        pattern = self.patterns[pattern_name]
        match = re.search(pattern, response)
        return match.group(1) if match else None
