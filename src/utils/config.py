import json
import logging
import os

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "baudrate": 115200,
    "timeout": 1,
    "max_workers": 10,
    "port_filters": [
        "USB Serial Device",
        "Modem",
        "GSM",
        "WWAN",
        "HUAWEI",
        "ZTE",
        "Sierra",
    ],
    "excluded_ports": ["Bluetooth", "Printer", "Mouse", "Keyboard"],
    "port_monitor_interval": 2,  # seconds
}


def load_config(config_file="config.json"):
    """Load configuration with fallback to defaults"""
    config = DEFAULT_CONFIG.copy()

    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
                logger.info(f"Loaded configuration from {config_file}")
        else:
            logger.warning(f"Config file {config_file} not found, using defaults")
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}, using defaults")

    return config
