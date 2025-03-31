import time

import uiautomator2 as u2


def launch_indosat_care():
    # Hubungkan ke device
    d = u2.connect()
    print("Terhubung ke device")

    # Pastikan layar menyala dan perangkat terbuka
    d.screen_on()

    # Coba membuka kunci jika terkunci
    if not d.info.get("screenOn"):
        d.unlock()
        time.sleep(1)

    # Kembali ke home screen (pastikan kita dalam keadaan bersih)
    for _ in range(3):  # Tekan home beberapa kali untuk memastikan
        d.press("home")
        time.sleep(0.5)

    # Tutup Indosat Care jika sudah berjalan (untuk memastikan fresh start)
    d.app_stop("com.pure.indosat.care")
    time.sleep(1)

    # Buka aplikasi Indosat Care
    print("Membuka aplikasi Indosat Care...")
    d.app_start("com.pure.indosat.care")

    # Tunggu splash screen (waktu lebih lama)
    print("Menunggu splash screen...")
    time.sleep(5)  # Tunggu lebih lama untuk splash screen

    # Verifikasi apakah aplikasi terbuka dengan benar
    current_app = d.app_current()
    if current_app["package"] == "com.pure.indosat.care":
        print("Indosat Care berhasil dibuka")

        # Tunggu hingga layar login muncul
        print("Menunggu layar login muncul...")
        login_wait_success = False

        # Tunggu hingga 15 detik untuk layar login
        for _ in range(15):
            if d(text="LOGIN / REGISTER").exists(timeout=1):
                login_wait_success = True
                print("Layar login terdeteksi")
                break
            time.sleep(1)
            print("Masih menunggu layar login...")

        if not login_wait_success:
            print("Timeout menunggu layar login, ambil screenshot...")
            d.screenshot("error_splash_screen.png")

        return d
    else:
        print(f"Gagal membuka Indosat Care, saat ini di: {current_app['package']}")
        # Coba sekali lagi
        d.app_start("com.pure.indosat.care")
        time.sleep(5)  # Tunggu lebih lama
        return d


def is_continue_successful(d):
    """Fungsi sederhana untuk cek apakah continue berhasil"""
    # Cek indikator layar selanjutnya (OTP atau verifikasi)
    if d(text="OTP").exists(timeout=2) or d(text="Verification").exists(timeout=2):
        print("Layar verifikasi terdeteksi - Continue berhasil!")
        return True

    # Jika masih di layar input nomor, berarti gagal
    if d(resourceId="com.pure.indosat.care:id/tilMobileNumber").exists(timeout=1):
        print("Masih di layar input nomor - Continue gagal")
        return False

    # Jika UI berubah tapi tidak dikenali dengan jelas
    print("UI berubah, kemungkinan continue berhasil")
    return True


def handle_login(d):
    """Fungsi untuk menangani proses login dengan nomor telepon"""
    try:
        # Klik pada tombol login/register jika ada
        print("Mencari tombol LOGIN / REGISTER...")
        if d(text="LOGIN / REGISTER").exists(timeout=5):
            print("Tombol LOGIN / REGISTER ditemukan, mengklik...")
            d(text="LOGIN / REGISTER").click()
            time.sleep(2)

            # Tangani popup Google jika muncul
            if d(text="Continue with Google").exists(timeout=2):
                print("Popup Google terdeteksi, menutup...")
                d.press("back")
                time.sleep(1)

            # Screenshot untuk memastikan halaman input nomor
            d.screenshot("login_page.png")

        # Fokus pada input nomor
        print("Mencari field input nomor...")
        if d(resourceId="com.pure.indosat.care:id/tilMobileNumber").exists(timeout=5):
            print("Field input nomor ditemukan")

            # Klik pada field nomor
            d(resourceId="com.pure.indosat.care:id/tilMobileNumber").click()
            time.sleep(1)

            # Cari input field
            input_field = d(className="android.widget.EditText")

            if input_field.exists(timeout=2):
                # Input nomor
                nomor = "85714471111"
                input_field.set_text(nomor)
                print(f"Nomor {nomor} diinput")
                time.sleep(1)

                # STRATEGI: Hapus karakter terakhir lalu input kembali
                input_field.clear_text()  # Hapus semua dulu
                time.sleep(0.5)

                # Input nomor kecuali digit terakhir
                nomor_minus_one = nomor[:-1]
                input_field.set_text(nomor_minus_one)
                time.sleep(1)
                print(f"Input nomor tanpa digit terakhir: {nomor_minus_one}")

                # Tambahkan digit terakhir
                last_digit = nomor[-1]
                input_field.set_text(nomor_minus_one + last_digit)
                time.sleep(1)
                print(f"Menambahkan digit terakhir: {last_digit}")

                # Tekan enter untuk konfirmasi input
                d.press("enter")
                time.sleep(1)

                # PERBAIKAN: Tutup keyboard dengan tombol back
                print("Menutup keyboard dengan tombol back...")
                d.press("back")
                time.sleep(1.5)  # Waktu lebih lama untuk memastikan keyboard hilang

                # Screenshot setelah input lengkap dan keyboard hilang
                d.screenshot("after_keyboard_dismissed.png")

                # Coba klik tombol continue
                continue_btn = d(resourceId="com.pure.indosat.care:id/btnContinue")
                if continue_btn.exists():
                    is_enabled = continue_btn.info.get("enabled", False)
                    print(f"Tombol Continue ditemukan, status enabled: {is_enabled}")

                    if is_enabled:
                        print("Tombol Continue aktif, mengklik...")
                        continue_btn.click()
                        time.sleep(3)
                        d.screenshot("after_continue_click.png")
                        return is_continue_successful(d)
                    else:
                        print("Tombol Continue tidak aktif, mencoba sekali lagi...")
                        # Coba refresh UI dengan tap dan back
                        input_field.click()
                        time.sleep(0.5)
                        d.press("back")
                        time.sleep(1)

                        # Cek lagi setelah refresh
                        if continue_btn.exists() and continue_btn.info.get(
                            "enabled", False
                        ):
                            print("Tombol Continue sekarang aktif!")
                            continue_btn.click()
                            time.sleep(3)
                            d.screenshot("after_continue_click_retry.png")
                            return is_continue_successful(d)
                        else:
                            print(
                                "Tombol Continue masih tidak aktif setelah refresh UI"
                            )
                            d.screenshot("continue_disabled.png")
                else:
                    print("Tombol Continue tidak ditemukan")
                    d.screenshot("continue_not_found.png")
            else:
                print("Field EditText tidak ditemukan")
                d.screenshot("edittext_not_found.png")
        else:
            print("Field input nomor tidak ditemukan")
            d.screenshot("input_field_not_found.png")

    except Exception as e:
        print(f"Error saat login: {e}")
        d.screenshot("login_error.png")

    return False


def navigate_to_topup_game(d):
    """Navigasi ke menu Top Up Game dengan resource ID yang tepat"""
    try:
        # 1. Klik tab Buy terlebih dahulu
        print("Mencari dan mengklik tab Buy...")
        if d(resourceId="com.pure.indosat.care:id/navigation_buy").exists(timeout=5):
            d(resourceId="com.pure.indosat.care:id/navigation_buy").click()
            time.sleep(3)
            d.screenshot("buy_tab_clicked.png")
        else:
            print("Tab Buy tidak ditemukan")
            return False

        # 2. Mencari tab "Top Up Game!" dengan resource ID yang tepat
        print("Mencari tab Top Up Game...")

        # Cek apakah tab sudah terlihat
        if d(
            resourceId="com.pure.indosat.care:id/tvTabText", text="Top Up Game!"
        ).exists(timeout=2):
            print("Tab Top Up Game! ditemukan")

            # PENTING: TextView sendiri tidak clickable, kita perlu menemukan parent yang clickable
            # Strategi 1: Klik pada area TextView
            x, y = d(
                resourceId="com.pure.indosat.care:id/tvTabText", text="Top Up Game!"
            ).center()
            d.click(x, y)
            print(f"Mengklik pada koordinat tab: ({x}, {y})")
            time.sleep(2)
            d.screenshot("topup_game_clicked.png")
            return True

        # Tab tidak langsung terlihat, perlu scroll
        print("Tab Top Up Game tidak langsung terlihat, mencoba scroll...")

        # Cari semua tab untuk navigasi
        all_tabs = d(resourceId="com.pure.indosat.care:id/tvTabText")
        if all_tabs.count > 0:
            print(f"Ditemukan {all_tabs.count} tab, memeriksa satu per satu")

            # Periksa teks dari tab yang terlihat
            tab_texts = []
            for i in range(all_tabs.count):
                tab_text = all_tabs[i].info.get("text", "")
                tab_texts.append(tab_text)
                print(f"Tab {i + 1}: {tab_text}")

            print(f"Tab terlihat: {tab_texts}")

            # Jika "Top Up Game!" tidak ada dalam tab yang terlihat, scroll horizontal
            if "Top Up Game!" not in tab_texts:
                print(
                    "Tab Top Up Game! tidak ada dalam tab yang terlihat, perlu scroll"
                )

                # Temukan ScrollView horizontal
                scroll_container = d(className="android.widget.HorizontalScrollView")
                if scroll_container.exists():
                    # Scroll beberapa kali ke kanan sampai menemukan Top Up Game
                    for i in range(4):
                        print(f"Scroll horizontal ke-{i + 1}")

                        # Scroll dari kanan ke kiri (karena tab ada di sebelah kanan)
                        d.swipe(0.8, 0.25, 0.2, 0.25)
                        time.sleep(1.5)
                        d.screenshot(f"scroll_{i + 1}.png")

                        # Cek apakah tab sudah terlihat
                        if d(
                            resourceId="com.pure.indosat.care:id/tvTabText",
                            text="Top Up Game!",
                        ).exists(timeout=1):
                            print("Tab Top Up Game! ditemukan setelah scroll")
                            x, y = d(
                                resourceId="com.pure.indosat.care:id/tvTabText",
                                text="Top Up Game!",
                            ).center()
                            d.click(x, y)
                            print(f"Mengklik pada koordinat tab: ({x}, {y})")
                            time.sleep(2)
                            d.screenshot("topup_game_clicked_after_scroll.png")
                            return True
                else:
                    print("Tidak dapat menemukan container scroll horizontal")
        else:
            print("Tidak dapat menemukan tab dengan resource ID tvTabText")

        return False

    except Exception as e:
        print(f"Error saat navigasi ke Top Up Game: {e}")
        d.screenshot("navigation_error.png")
        return False


# Jalankan fungsi
if __name__ == "__main__":
    print("Memulai otomasi Indosat Care...")
    d = launch_indosat_care()

    # Deteksi state dan handle
    if d(text="LOGIN / REGISTER").exists(timeout=5):
        print("Halaman login terdeteksi")
        success = handle_login(d)
        if success:
            print("Login berhasil!")

            # Navigasi ke Top Up Game
            topup_success = navigate_to_topup_game(d)
            if topup_success:
                print("Navigasi ke Top Up Game berhasil!")
                # Selanjutnya bisa dilanjutkan dengan memilih Garen
            else:
                print("Navigasi ke Top Up Game gagal")
        else:
            print("Login gagal")
    elif d(resourceId="com.pure.indosat.care:id/ivMenu").exists(timeout=3):
        print("Sudah di halaman utama")
        d.screenshot("main_screen.png")
    else:
        print("Status aplikasi tidak dikenali")
        d.screenshot("unknown_state.png")

    print("Otomasi selesai")
