from src.utils.logging import get_logger

from .simcard import SimCard

# Create logger for this module
logger = get_logger("models.simcardmanager")


class SimCardManager:
    def __init__(self):
        self.simcards = {}

    def update_from_portmanager(self, port_manager):
        """Update SIM cards dari port manager"""
        logger.info("Memperbarui database SIM card...")

        # Deteksi SIM cards dari semua port
        available_ports = port_manager.get_available_ports()
        updated_count = 0

        for port in available_ports:
            sim_info = port_manager.detect_simcard(port.device)
            if sim_info and "iccid" in sim_info:
                iccid = sim_info["iccid"]
                msisdn = sim_info["msisdn"] or "Unknown"
                signal = sim_info["signal"] or 0

                # Perbarui atau tambahkan SIM card
                if iccid in self.simcards:
                    self.simcards[iccid].msisdn = msisdn
                    self.simcards[iccid].signal = signal
                    self.simcards[iccid].port_device = port.device
                else:
                    sim = SimCard(iccid, msisdn, signal)
                    sim.port_device = port.device
                    self.simcards[iccid] = sim

                updated_count += 1

        logger.info(f"Database SIM card diperbarui. {updated_count} SIM card aktif")
        return updated_count

    def add_simcard(self, iccid, msisdn, signal):
        sim = SimCard(iccid, msisdn, signal)
        self.simcards[iccid] = sim

    def get_simcard_info(self, iccid):
        return self.simcards.get(iccid)

    def list_simcards(self):
        return list(self.simcards.values())
