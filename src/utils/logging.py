import logging
import sys
from datetime import datetime
from pathlib import Path

# Buat direktori logs jika belum ada
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Konfigurasi format log default
DEFAULT_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name,
    level=logging.INFO,
    file_logging=True,
    console_logging=True,
    log_format=DEFAULT_FORMAT,
):
    """
    Membuat dan mengonfigurasi logger.

    Args:
        name: Nama logger (biasanya nama modul)
        level: Level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        file_logging: Apakah log disimpan ke file
        console_logging: Apakah log ditampilkan di konsol
        log_format: Format string untuk pesan log

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Hapus handler lama jika ada
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Buat formatter
    formatter = logging.Formatter(log_format, DATE_FORMAT)

    # Console handler
    if console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if file_logging:
        log_filename = (
            f"{datetime.now().strftime('%Y%m%d')}_{name.replace('.', '_')}.log"
        )
        file_handler = logging.FileHandler(logs_dir / log_filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name, level=logging.INFO):
    """
    Mendapatkan logger dengan nama tertentu.

    Args:
        name: Nama logger (biasanya nama modul)
        level: Level logging

    Returns:
        Logger instance
    """
    return setup_logger(name, level)
