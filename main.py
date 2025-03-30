import logging
import threading
import time

import serial.tools.list_ports

from src.models.modemmanager import ModemManager
from src.utils.logging import setup_logger


def list_all_system_ports():
    """Menampilkan semua port sistem sebagai referensi"""
    ports = serial.tools.list_ports.comports()
    print(f"Ditemukan {len(ports)} port pada sistem:")
    for i, port in enumerate(ports):
        print(f"{i + 1}. {port.device} - {port.description}")
    return ports


def main():
    # Aktifkan logging
    logger = setup_logger("main", level=logging.DEBUG)
    logger.info("Aplikasi dimulai")

    # Tampilkan semua port yang tersedia pada sistem
    print("\n===== SEMUA PORT SISTEM =====")
    list_all_system_ports()

    # Inisialisasi modem manager dan deteksi perangkat
    print("\n===== DETEKSI PERANGKAT =====")
    modem_manager = ModemManager()

    # Show loading indicator
    stop_loading = threading.Event()
    loading_thread = threading.Thread(
        target=show_loading_animation, args=(stop_loading,)
    )
    loading_thread.daemon = True
    loading_thread.start()

    # Run device detection
    start_time = time.time()
    devices = modem_manager.detect_all_devices()
    end_time = time.time()

    # Stop loading animation
    stop_loading.set()
    loading_thread.join()

    print(f"\nDeteksi selesai dalam {end_time - start_time:.2f} detik")

    # Tampilkan hasil deteksi
    connected_ports = devices["ports"]["connected"]
    disconnected_ports = devices["ports"]["disconnected"]
    sim_cards = devices["sim_cards"]["all"]
    sim_count = devices["sim_cards"]["count"]

    # Display connected ports
    if connected_ports:
        print(f"\nModem terhubung ({len(connected_ports)}):")
        for i, port in enumerate(connected_ports):
            print(f"{i + 1}. {port.device} - {port.name} - {port.status}")
    else:
        print("\nTidak ada modem yang terhubung")

    # Display disconnected ports
    if disconnected_ports:
        print(f"\nModem terdeteksi tapi tidak terhubung ({len(disconnected_ports)}):")
        for i, port in enumerate(disconnected_ports):
            print(f"{i + 1}. {port.device} - {port.name} - {port.status}")

    # Display SIM cards
    print("\n===== DETEKSI SIM CARD =====")
    if sim_count == 0:
        print("Tidak ada SIM card terdeteksi pada modem yang terhubung!")
    else:
        print(f"\nSIM card terdeteksi ({sim_count}):")
        display_sim_cards(sim_cards, connected_ports)

    # Port management UI
    display_port_management_ui(modem_manager, connected_ports)

    logger.info("Aplikasi selesai")


def show_loading_animation(stop_event):
    """Show animation while processing"""
    animation = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        print(f"\rDeteksi perangkat... {animation[idx % len(animation)]}", end="")
        idx += 1
        time.sleep(0.1)


def display_sim_cards(sim_cards, connected_ports):
    """Tampilkan informasi SIM card"""
    for i, sim in enumerate(sim_cards):
        # Temukan port yang terkait dengan SIM ini
        port_info = ""
        for port in connected_ports:
            if hasattr(sim, "port_device") and port.device == sim.port_device:
                port_info = f"({port.name})"
                break

        # Format display values
        msisdn_display = (
            sim.msisdn if sim.msisdn != "Unknown" else "Nomor tidak diketahui"
        )
        iccid_display = (
            f"{sim.iccid[:4]}...{sim.iccid[-4:]}" if len(sim.iccid) > 8 else sim.iccid
        )
        signal_display = f"{sim.signal}/31" if isinstance(sim.signal, int) else "?"

        # Print information
        print(f"{i + 1}. Port: {sim.port_device} {port_info}")
        print(f"   ICCID: {iccid_display}")
        print(f"   Nomor: {msisdn_display}")
        print(f"   Sinyal: {signal_display}")


def display_port_management_ui(modem_manager, connected_ports):
    """Tampilkan UI untuk manajemen port"""
    print("\n===== MENGELOLA PORT MODEM =====")
    print("Contoh cara mengaktifkan/menonaktifkan port:")
    print("  modem_manager.enable_port('COM6')")
    print("  modem_manager.disable_port('COM7')")

    if connected_ports:
        try:
            choice = input("\nApakah ingin mengubah status port? (y/n): ")
            if choice.lower() == "y":
                port_to_change = input("Masukkan port (contoh: COM6): ")
                action = input("Aktifkan port ini? (y/n): ")

                if action.lower() == "y":
                    modem_manager.enable_port(port_to_change)
                    print(f"Port {port_to_change} diaktifkan")
                else:
                    modem_manager.disable_port(port_to_change)
                    print(f"Port {port_to_change} dinonaktifkan")

                # Tampilkan status terbaru
                print("\nStatus port setelah perubahan:")
                port_status = modem_manager.get_port_status()
                for device, status in port_status.items():
                    status_text = "Aktif" if status["enabled"] else "Nonaktif"
                    print(f"{device}: {status_text}")
        except KeyboardInterrupt:
            print("\nOperasi dibatalkan oleh pengguna")


if __name__ == "__main__":
    main()
