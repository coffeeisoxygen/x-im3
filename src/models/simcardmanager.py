import threading
from concurrent.futures import ThreadPoolExecutor

from src.utils.logging import get_logger

from .simcard import SimCard

# Create logger for this module
logger = get_logger("models.simcardmanager")


class SimCardManager:
    def __init__(self):
        self.simcards = {}

    def update_from_portmanager(self, port_manager, max_workers=8):
        """Update SIM cards dari port manager secara paralel"""
        logger.info("Memperbarui database SIM card...")

        # Deteksi SIM cards dari semua port secara paralel
        available_ports = port_manager.get_available_ports()
        updated_count = 0
        lock = threading.Lock()

        def process_port(port):
            nonlocal updated_count
            sim_info = port_manager.detect_simcard(port.device)
            if sim_info and "iccid" in sim_info:
                iccid = sim_info["iccid"]
                msisdn = sim_info["msisdn"] or "Unknown"
                signal = sim_info["signal"] or 0

                with lock:
                    # Perbarui atau tambahkan SIM card dengan thread-safe approach
                    if iccid in self.simcards:
                        self.simcards[iccid].msisdn = msisdn
                        self.simcards[iccid].signal = signal
                        self.simcards[iccid].port_device = port.device
                    else:
                        sim = SimCard(iccid, msisdn, signal)
                        sim.port_device = port.device
                        self.simcards[iccid] = sim

                    updated_count += 1

        # Gunakan thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(process_port, available_ports)

        logger.info(f"Database SIM card diperbarui. {updated_count} SIM card aktif")
        return updated_count

    def add_simcard(self, iccid, msisdn, signal):
        sim = SimCard(iccid, msisdn, signal)
        self.simcards[iccid] = sim

    def get_simcard_info(self, iccid):
        return self.simcards.get(iccid)

    def list_simcards(self):
        return list(self.simcards.values())
