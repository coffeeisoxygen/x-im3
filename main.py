import logging
import threading
import time

from src.services.port_service import PortService
from src.utils.config import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)

logger = logging.getLogger(__name__)


def monitor_ports(port_service):
    """Loop untuk memonitor status port secara periodik"""
    try:
        while True:
            active_ports = port_service.list_active_ports()
            print("\n=== Status Port Aktif ===")
            if not active_ports:
                print("Tidak ada port aktif")
            else:
                for device_id, port in active_ports.items():
                    status = "Terhubung" if port.is_connected() else "Terputus"
                    print(f"{device_id} - {port.name} - {status}")
            print("=========================")
            time.sleep(2)
    except Exception as e:
        logger.error(f"Error in port monitoring: {str(e)}")


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
        print(f"\nDitemukan {len(detected_ports)} port:")

        if detected_ports:
            for device_id, port in detected_ports.items():
                print(f"- {port}")
        else:
            print("Tidak ada port terdeteksi")

        # Auto-activate all connected ports
        for device_id, port in port_service.list_connected_ports().items():
            port_service.enable_port(device_id)
            print(f"Port {device_id} diaktifkan otomatis")

        # Start port monitoring thread
        port_service.start_monitoring()

        # Display monitoring information in separate thread
        monitor_thread = threading.Thread(target=monitor_ports, args=(port_service,))
        monitor_thread.daemon = True
        monitor_thread.start()

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
                all_ports = port_service.list_all_ports()
                print("\nSemua port:")
                for device_id, port in all_ports.items():
                    print(f"- {port}")
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
        port_service.stop_monitoring()
        logger.info("Application shutdown")
        print("Program berakhir.")


if __name__ == "__main__":
    main()
