import time

import serial
import serial.tools.list_ports

from src.utils.logging import get_logger

logger = get_logger("controllers.port")


class PortController:
    """Controller untuk operasi tingkat rendah pada port serial"""

    @staticmethod
    def list_system_ports():
        """Mendapatkan semua port yang tersedia pada sistem"""
        return list(serial.tools.list_ports.comports())

    @staticmethod
    def open_connection(port_device, baudrate=115200, timeout=1):
        """Membuka koneksi ke port serial"""
        try:
            connection = serial.Serial(port_device, baudrate, timeout=timeout)
            time.sleep(0.5)  # Berikan waktu untuk inisialisasi
            return connection
        except Exception as e:
            logger.error(f"Gagal membuka koneksi ke {port_device}: {str(e)}")
            return None

    @staticmethod
    def send_command(connection, command, timeout=1):
        """Mengirim perintah ke koneksi yang sudah terbuka"""
        try:
            if not connection or connection.closed:
                logger.error("Koneksi tidak valid")
                return None

            # Reset buffer
            connection.reset_input_buffer()
            connection.reset_output_buffer()

            # Format AT command
            if not command.upper().startswith("AT"):
                command = "AT" + command

            if not command.endswith("\r\n"):
                command += "\r\n"

            # Kirim command
            connection.write(command.encode())
            time.sleep(timeout)

            # Baca respons
            response = connection.read(connection.in_waiting).decode(
                "utf-8", errors="ignore"
            )
            return response
        except Exception as e:
            logger.error(f"Error saat mengirim command: {str(e)}")
            return None

    @staticmethod
    def close_connection(connection):
        """Menutup koneksi serial"""
        try:
            if connection and not connection.closed:
                connection.close()
                return True
        except Exception as e:
            logger.error(f"Error saat menutup koneksi: {str(e)}")
        return False
