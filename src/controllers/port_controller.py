import logging
import time

import serial
import serial.tools.list_ports

from src.utils.config import load_config

logger = logging.getLogger(__name__)


class PortController:
    """Controller untuk operasi port serial"""

    def __init__(self, config_file="config.json"):
        self.config = load_config(config_file)
        logger.debug(
            f"PortController initialized with baudrate: {self.config['baudrate']}"
        )

    def list_system_ports(self):
        """List semua port yang tersedia pada sistem"""
        return list(serial.tools.list_ports.comports())

    def open_connection(self, device_id):
        """Membuka koneksi ke port serial"""
        try:
            connection = serial.Serial(
                device_id,
                baudrate=self.config["baudrate"],
                timeout=self.config["timeout"],
            )
            time.sleep(0.5)  # Waktu inisialisasi
            logger.debug(f"Opened connection to {device_id}")
            return connection
        except Exception as e:
            logger.error(f"Failed to open connection to {device_id}: {str(e)}")
            return None

    def send_command(self, connection, command):
        """Mengirim perintah AT ke port"""
        try:
            if not connection or connection.closed:
                logger.error("Cannot send command: connection closed or invalid")
                return None

            # Reset buffer
            connection.reset_input_buffer()
            connection.reset_output_buffer()

            # Format command
            if not command.upper().startswith("AT"):
                command = "AT" + command
            if not command.endswith("\r\n"):
                command += "\r\n"

            # Send and read response
            connection.write(command.encode())
            time.sleep(self.config["timeout"])
            response = connection.read(connection.in_waiting).decode(
                "utf-8", errors="ignore"
            )

            logger.debug(f"Command: {command.strip()}, Response: {response.strip()}")
            return response
        except Exception as e:
            logger.error(f"Error sending command: {str(e)}")
            return None

    def close_connection(self, connection):
        """Menutup koneksi serial"""
        try:
            if connection and not connection.closed:
                connection.close()
                return True
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")
        return False
