import time

import uiautomator2 as u2


def connect_to_device():
    """Connect to the device and ensure the screen is on."""
    d = u2.connect()
    print("Terhubung ke device")
    d.screen_on()
    if not d.info.get("screenOn"):
        d.unlock()
        time.sleep(1)
    return d


def reset_to_home_screen(d):
    """Ensure the device is on the home screen."""
    for _ in range(3):
        d.press("home")
        time.sleep(0.5)


def stop_and_start_app(d, package_name):
    """Stop the app if running and start it fresh."""
    d.app_stop(package_name)
    time.sleep(1)
    d.app_start(package_name)
    time.sleep(5)  # Wait for splash screen


def wait_for_login_screen(d):
    """Wait for the login screen to appear."""
    print("Menunggu layar login muncul...")
    for _ in range(15):
        if d(text="LOGIN / REGISTER").exists(timeout=1):
            print("Layar login terdeteksi")
            return True
        time.sleep(1)
        print("Masih menunggu layar login...")
    print("Timeout menunggu layar login, ambil screenshot...")
    d.screenshot("error_splash_screen.png")
    return False


def launch_indosat_care():
    """Launch the Indosat Care app and ensure it is ready."""
    d = connect_to_device()
    reset_to_home_screen(d)
    stop_and_start_app(d, "com.pure.indosat.care")

    current_app = d.app_current()
    if current_app["package"] == "com.pure.indosat.care":
        print("Indosat Care berhasil dibuka")
        if wait_for_login_screen(d):
            return d
    else:
        print(f"Gagal membuka Indosat Care, saat ini di: {current_app['package']}")
        stop_and_start_app(d, "com.pure.indosat.care")
    return d


def is_continue_successful(d):
    """Check if the continue action was successful."""
    if d(text="OTP").exists(timeout=2) or d(text="Verification").exists(timeout=2):
        print("Layar verifikasi terdeteksi - Continue berhasil!")
        return True
    if d(resourceId="com.pure.indosat.care:id/tilMobileNumber").exists(timeout=1):
        print("Masih di layar input nomor - Continue gagal")
        return False
    print("UI berubah, kemungkinan continue berhasil")
    return True


def input_phone_number(d, nomor):
    """Input the phone number into the login field."""
    input_field = d(className="android.widget.EditText")
    if input_field.exists(timeout=2):
        input_field.set_text(nomor)
        print(f"Nomor {nomor} diinput")
        time.sleep(1)
        input_field.clear_text()
        time.sleep(0.5)
        nomor_minus_one = nomor[:-1]
        input_field.set_text(nomor_minus_one)
        time.sleep(1)
        print(f"Input nomor tanpa digit terakhir: {nomor_minus_one}")
        last_digit = nomor[-1]
        input_field.set_text(nomor_minus_one + last_digit)
        time.sleep(1)
        print(f"Menambahkan digit terakhir: {last_digit}")
        d.press("enter")
        time.sleep(1)
        d.press("back")
        time.sleep(1.5)
        d.screenshot("after_keyboard_dismissed.png")
        return True
    print("Field EditText tidak ditemukan")
    d.screenshot("edittext_not_found.png")
    return False


def handle_login(d):
    """Handle the login process."""
    try:
        if d(text="LOGIN / REGISTER").exists(timeout=5):
            d(text="LOGIN / REGISTER").click()
            time.sleep(2)
            if d(text="Continue with Google").exists(timeout=2):
                d.press("back")
                time.sleep(1)
            d.screenshot("login_page.png")

        if d(resourceId="com.pure.indosat.care:id/tilMobileNumber").exists(timeout=5):
            if input_phone_number(d, "85714471111"):
                continue_btn = d(resourceId="com.pure.indosat.care:id/btnContinue")
                if continue_btn.exists() and continue_btn.info.get("enabled", False):
                    continue_btn.click()
                    time.sleep(3)
                    d.screenshot("after_continue_click.png")
                    return is_continue_successful(d)
                else:
                    print("Tombol Continue tidak aktif")
                    d.screenshot("continue_disabled.png")
        else:
            print("Field input nomor tidak ditemukan")
            d.screenshot("input_field_not_found.png")
    except Exception as e:
        print(f"Error saat login: {e}")
        d.screenshot("login_error.png")
    return False


def navigate_to_topup_game(d):
    """Navigate to the Top Up Game menu."""
    try:
        if d(resourceId="com.pure.indosat.care:id/navigation_buy").exists(timeout=5):
            d(resourceId="com.pure.indosat.care:id/navigation_buy").click()
            time.sleep(3)
            d.screenshot("buy_tab_clicked.png")
        else:
            print("Tab Buy tidak ditemukan")
            return False

        if d(
            resourceId="com.pure.indosat.care:id/tvTabText", text="Top Up Game!"
        ).exists(timeout=2):
            x, y = d(
                resourceId="com.pure.indosat.care:id/tvTabText", text="Top Up Game!"
            ).center()
            d.click(x, y)
            time.sleep(2)
            d.screenshot("topup_game_clicked.png")
            return True

        print("Tab Top Up Game tidak langsung terlihat, mencoba scroll...")
        scroll_container = d(className="android.widget.HorizontalScrollView")
        if scroll_container.exists():
            for i in range(4):
                d.swipe(0.8, 0.25, 0.2, 0.25)
                time.sleep(1.5)
                d.screenshot(f"scroll_{i + 1}.png")
                if d(
                    resourceId="com.pure.indosat.care:id/tvTabText", text="Top Up Game!"
                ).exists(timeout=1):
                    x, y = d(
                        resourceId="com.pure.indosat.care:id/tvTabText",
                        text="Top Up Game!",
                    ).center()
                    d.click(x, y)
                    time.sleep(2)
                    d.screenshot("topup_game_clicked_after_scroll.png")
                    return True
        else:
            print("Tidak dapat menemukan container scroll horizontal")
    except Exception as e:
        print(f"Error saat navigasi ke Top Up Game: {e}")
        d.screenshot("navigation_error.png")
    return False


def navigate_to_garena_shell(d):
    """Menavigasi ke Garena Shell setelah berada di halaman Top Up Game."""
    try:
        print("Mencari kategori Reseller di halaman Top Up Game...")

        # Screenshot awal untuk debugging
        d.screenshot("top_up_game_initial.png")

        # 1. Scroll ke bawah untuk menemukan kategori tabs
        found_categories = False
        for i in range(3):  # Scroll maksimal 3 kali ke bawah
            # Cek apakah kategori-kategori sudah terlihat
            categories = ["Best Seller", "Top Up Langsung", "Kode Voucher", "Reseller"]
            for category in categories:
                if d(text=category).exists(timeout=1):
                    found_categories = True
                    print(f"Kategori '{category}' terdeteksi")
                    break

            if found_categories:
                break

            # Belum terlihat, scroll ke bawah
            print(f"Scroll vertikal ke-{i + 1}")
            d.swipe(0.5, 0.8, 0.5, 0.3)  # Scroll dari bawah ke atas
            time.sleep(1.5)

        if not found_categories:
            print("Tidak bisa menemukan kategori setelah beberapa kali scroll")
            d.screenshot("categories_not_found.png")
            return False

        # 2. Klik tab Reseller
        print("Mencari tab Reseller...")
        reseller_tab = d(text="Reseller")
        if reseller_tab.exists(timeout=2):
            print("Tab Reseller ditemukan, mengklik...")

            # Karena TextView mungkin tidak clickable, gunakan koordinat dari center()
            x, y = reseller_tab.center()
            d.click(x, y)
            time.sleep(2)
            d.screenshot("reseller_tab_clicked.png")
        else:
            print("Tab Reseller tidak ditemukan")
            d.screenshot("reseller_tab_not_found.png")
            return False

        # 3. Cari Garena Shell
        print("Mencari Garena Shell...")

        # Coba cari langsung
        garena_found = False

        # Cari dengan berbagai kemungkinan text
        garena_options = ["Garena Shell", " Garena Shell ", "Garena"]
        for text_option in garena_options:
            if d(text=text_option).exists(timeout=2):
                print(f"Garena Shell ditemukan dengan text: '{text_option}'")
                garena_element = d(text=text_option)
                garena_found = True
                break

        # Atau cari dengan resource ID
        if not garena_found and d(
            resourceId="com.pure.indosat.care:id/tvTitle", textContains="Garena"
        ).exists(timeout=2):
            print("Garena Shell ditemukan dengan resourceId dan text partial")
            garena_element = d(
                resourceId="com.pure.indosat.care:id/tvTitle", textContains="Garena"
            )
            garena_found = True

        # Jika masih tidak ditemukan, coba scroll lagi
        if not garena_found:
            print("Garena Shell tidak langsung terlihat, mencoba scroll...")
            for i in range(3):  # Scroll maksimal 3 kali
                d.swipe(0.5, 0.8, 0.5, 0.3)  # Scroll dari bawah ke atas
                time.sleep(1.5)

                # Cek lagi setelah scroll
                for text_option in garena_options:
                    if d(text=text_option).exists(timeout=2):
                        print(
                            f"Garena Shell ditemukan setelah scroll dengan text: '{text_option}'"
                        )
                        garena_element = d(text=text_option)
                        garena_found = True
                        break

                if garena_found:
                    break

        # Klik Garena Shell jika ditemukan
        if garena_found:
            # Jika elemen tidak clickable, gunakan koordinat
            if not garena_element.info.get("clickable", False):
                x, y = garena_element.center()
                d.click(x, y)
            else:
                garena_element.click()

            print("Berhasil mengklik Garena Shell")
            time.sleep(2)
            d.screenshot("garena_shell_clicked.png")
            return True
        else:
            print("Garena Shell tidak ditemukan")
            d.screenshot("garena_shell_not_found.png")
            return False

    except Exception as e:
        print(f"Error saat navigasi ke Garena Shell: {e}")
        d.screenshot("garena_navigation_error.png")
        return False


def main():
    """Main function to execute the automation."""
    print("Memulai otomasi Indosat Care...")
    d = launch_indosat_care()

    if d(text="LOGIN / REGISTER").exists(timeout=5):
        print("Halaman login terdeteksi")
        if handle_login(d):
            print("Login berhasil!")
            if navigate_to_topup_game(d):
                print("Navigasi ke Top Up Game berhasil!")

                # Tambahkan navigasi ke Garena Shell
                if navigate_to_garena_shell(d):
                    print("Navigasi ke Garena Shell berhasil!")
                    # Di sini bisa dilanjutkan dengan pemilihan denominasi atau langkah berikutnya
                else:
                    print("Navigasi ke Garena Shell gagal")
            else:
                print("Navigasi ke Top Up Game gagal")
        else:
            print("Login gagal")
    elif d(resourceId="com.pure.indosat.care:id/ivMenu").exists(timeout=3):
        print("Sudah di halaman utama")
        d.screenshot("main_screen.png")

        # Jika sudah di halaman utama, coba langsung navigasi
        if navigate_to_topup_game(d):
            print("Navigasi ke Top Up Game berhasil!")
            if navigate_to_garena_shell(d):
                print("Navigasi ke Garena Shell berhasil!")
            else:
                print("Navigasi ke Garena Shell gagal")
    else:
        print("Status aplikasi tidak dikenali")
        d.screenshot("unknown_state.png")
    print("Otomasi selesai")


if __name__ == "__main__":
    main()
