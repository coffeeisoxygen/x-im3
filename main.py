import logging

from src.services.port_monitor import PortMonitor
from src.services.port_service import PortService
from src.utils.config import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)

logger = logging.getLogger(__name__)


def console_output_handler(status_data):
    """Handler untuk output monitoring ke konsol"""
    timestamp = status_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    ports = status_data["ports"]

    print(f"\n=== Status Port Aktif ({timestamp}) ===")
    if not ports:
        print("Tidak ada port aktif")
    else:
        # Urutkan port berdasarkan nama
        sorted_ports = sorted(
            ports.values(),
            key=lambda p: int(p.device_id.lower().replace("com", "") or 0),
        )

        # Kelompokkan berdasarkan koneksi
        connected = [p for p in sorted_ports if p.is_connected()]
        disconnected = [p for p in sorted_ports if not p.is_connected()]

        # Tampilkan port terhubung dulu
        if connected:
            print("- Terhubung:")
            for port in connected:
                print(f"  {port.device_id} - {port.name}")

        # Kemudian port terputus
        if disconnected:
            print("- Terputus:")
            for port in disconnected:
                print(f"  {port.device_id} - {port.name}")

    print("======================================")


def main():
    """Fungsi utama program"""
    logger.info("Starting application")

    # Load configuration
    config = load_config()

    # Setup port service
    port_service = PortService()

    try:
        # Deteksi port
        print("Mendeteksi port...")
        detected_ports = port_service.detect_ports()

        # Tampilkan port terdeteksi dengan pengurutan yang lebih baik
        grouped_ports = port_service.get_grouped_ports()

        print(f"\nDitemukan {len(detected_ports)} port:")

        # Tampilkan port terhubung
        if grouped_ports["connected"]:
            print("\n- Terhubung:")
            for port in grouped_ports["connected"]:
                print(f"  {port.device_id} - {port.name} - {port.status}")

        # Tampilkan port terputus
        if grouped_ports["disconnected"]:
            print("\n- Terputus:")
            for port in grouped_ports["disconnected"]:
                print(f"  {port.device_id} - {port.name} - {port.status}")

        if not detected_ports:
            print("Tidak ada port terdeteksi")

        # Auto-activate all connected ports
        for device_id, port in port_service.list_connected_ports().items():
            port_service.enable_port(device_id)
            print(f"Port {device_id} diaktifkan otomatis")

        # Setup dan mulai monitoring
        port_monitor = PortMonitor(port_service, config)
        port_monitor.add_output_handler(console_output_handler)
        port_monitor.start()

        # Command line interface
        print("\nPerintah yang tersedia:")
        print("  list               - Tampilkan semua port")
        print("  enable [port_id]   - Aktifkan port")
        print("  disable [port_id]  - Nonaktifkan port")
        print("  refresh [port_id]  - Perbarui status port")
        print("  enable-all         - Aktifkan semua port")
        print("  disable-all        - Nonaktifkan semua port")
        print("  exit               - Keluar program")

        while True:
            cmd = input("\nCommand: ").strip().lower()

            if cmd == "exit":
                break
            elif cmd == "list":
                # Dapatkan port yang diurutkan
                grouped_ports = port_service.get_grouped_ports()

                print("\nSemua port:")

                # Tampilkan port terhubung
                if grouped_ports["connected"]:
                    print("\n- Terhubung:")
                    for port in grouped_ports["connected"]:
                        active_status = "Aktif" if port.active else "Nonaktif"
                        print(f"  {port.device_id} - {port.name} - {active_status}")

                # Tampilkan port terputus
                if grouped_ports["disconnected"]:
                    print("\n- Terputus:")
                    for port in grouped_ports["disconnected"]:
                        active_status = "Aktif" if port.active else "Nonaktif"
                        print(f"  {port.device_id} - {port.name} - {active_status}")

            elif cmd.startswith("enable "):
                port_id = cmd.split(" ", 1)[1]
                if port_service.enable_port(port_id):
                    print(f"Port {port_id} diaktifkan.")
                else:
                    print(f"Port {port_id} tidak ditemukan.")
            elif cmd.startswith("disable "):
                port_id = cmd.split(" ", 1)[1]
                if port_service.disable_port(port_id):
                    print(f"Port {port_id} dinonaktifkan.")
                else:
                    print(f"Port {port_id} tidak ditemukan.")
            elif cmd.startswith("refresh "):
                port_id = cmd.split(" ", 1)[1]
                if port_service.refresh_port(port_id):
                    print(f"Port {port_id} terhubung.")
                else:
                    print(f"Port {port_id} terputus atau tidak ditemukan.")
            elif cmd == "enable-all":
                port_service.enable_all_ports()
                print("Semua port diaktifkan.")
            elif cmd == "disable-all":
                port_service.disable_all_ports()
                print("Semua port dinonaktifkan.")
            else:
                print("Perintah tidak dikenal.")

    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        # Cleanup
        port_monitor.stop()
        logger.info("Application shutdown")
        print("Program berakhir.")


if __name__ == "__main__":
    main()
