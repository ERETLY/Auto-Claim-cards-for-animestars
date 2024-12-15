import sys
import pickle
import io
import time
import os
from datetime import datetime, timedelta
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import psutil
import pytz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def kill_chrome_driver_processes():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'chromedriver' or 'chrome' in proc.info['name'].lower():
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass

def restart_at_midnight():
    moscow_tz = pytz.timezone('Europe/Moscow')
    while True:
        current_time = datetime.now(moscow_tz)

        next_restart = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        if next_restart <= current_time:
            next_restart += timedelta(days=1)

        time_until_restart = (next_restart - current_time).total_seconds()

        if time_until_restart < 0:
            print("Calculated negative sleep time, skipping to next iteration.", flush=True)
            continue

        try:
            time.sleep(time_until_restart)
        except ValueError as e:
            print(f"Error in sleep: {e}", flush=True)
            continue

        print("Restarting script at 00:00 MSK...", flush=True)
        kill_chrome_driver_processes()
        os.execv(sys.executable, ['python'] + sys.argv)

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
chrome_options.add_argument("--enable-webgl")
chrome_options.add_argument("--use-gl=swiftshader")
chrome_options.add_argument("--enable-webgl2-compute-context")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36")
chrome_options.add_argument("--ignore-gpu-blacklist")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--allow-running-insecure-content")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--mute-audio")

def load_cookies(driver, path):
    try:
        with open(path, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print(f"Cookies loaded from {path}.", flush=True)
    except FileNotFoundError:
        print(f"File {path} not found, continuing without loading cookies.", flush=True)

cookie_files = ['cookies.pkl', 'cookies1.pkl', 'cookies2.pkl']
Cards_for_cookies = [25, 23, 23]

def check_for_card(driver, timeout):
    start_time = time.time()
    end_time = start_time + timeout
    card_found = False

    while time.time() < end_time:
        print("Checking for card...", flush=True)
        try:
            driver.switch_to.default_content()
            time.sleep(2)
            card_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-notification[data-card-name]'))
            )
            time_taken = time.time() - start_time
            print(f"\033[92mCard found! Time taken: {time_taken:.2f} seconds.\033[0m", flush=True)
            card_found = True

            time.sleep(5)
            driver.execute_script("arguments[0].click();", card_div)
            print(f"\033[92mCard clicked.\033[0m", flush=True)

            break

        except Exception as e:
            print("Card not found or not yet available, retrying...", flush=True)
            time.sleep(10)

    if not card_found:
        time_taken = time.time() - start_time
        print(f"\033[91mCard not found within the time limit. Total time spent: {time_taken:.2f} seconds.\033[0m", flush=True)
    return card_found

def main():
    cookie_index = 0
    checks_per_cookie = {file: 0 for file in cookie_files}

    restart_thread = Thread(target=restart_at_midnight, daemon=True)
    restart_thread.start()

    while True:
        if checks_per_cookie[cookie_files[cookie_index]] >= Cards_for_cookies[cookie_index]:
            cookie_index = (cookie_index + 1) % len(cookie_files)
            if all(checks >= Cards_for_cookies[i] for i, checks in enumerate(checks_per_cookie.values())):
                time.sleep(60)
                continue

        kill_chrome_driver_processes()

        service = ChromeService(executable_path=r'/usr/local/bin/chromedriver')
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("https://animestars.org/aniserials/video/josei/921-paradajz-kiss.html")

            load_cookies(driver, cookie_files[cookie_index])

            driver.refresh()

            driver.execute_script("window.scrollBy(0, 1190);")
            print("Scrolled page to player", flush=True)

            print("Waiting for iframe to be available...", flush=True)
            WebDriverWait(driver, 80).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe[src*="kodik.info"]'))
            )
            print("Switched to iframe.", flush=True)

            play_button_visible = True

            while play_button_visible:
                try:
                    play_button = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[4]/a'))
                    )
                    print("Play button found.", flush=True)

                    if driver.execute_script("return arguments[0].offsetParent !== null;", play_button):
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", play_button)
                        print("Click performed on the Play button.", flush=True)

                        card_found = check_for_card(driver, 1600)

                        if card_found:
                            checks_per_cookie[cookie_files[cookie_index]] += 1
                            print(f"Cards found for {cookie_files[cookie_index]}: {checks_per_cookie[cookie_files[cookie_index]]}/{Cards_for_cookies[cookie_index]}", flush=True)
                        else:
                            print(f"No card found for {cookie_files[cookie_index]}. Counter not incremented.", flush=True)

                        print("Reloading page...", flush=True)
                        driver.refresh()
                        print("Page reloaded successfully.", flush=True)
                        time.sleep(10)
                        break

                    else:
                        play_button_visible = False
                        print("Play button is no longer visible. Stopping clicks.", flush=True)

                except Exception as e:
                    if "stale element reference" in str(e):
                        print("Stale element reference. Play button may have changed or been removed.", flush=True)
                    elif "no such element" in str(e):
                        print("Play button not found. Waiting for the next iteration.", flush=True)
                    else:
                        print("An error occurred while trying to find/click the button:", str(e), flush=True)
                    play_button_visible = False

        except Exception as e:
            print("An error occurred:", str(e), flush=True)

        finally:
            if driver:
                driver.quit()
            print("Restarting in 1 second.", flush=True)

        cookie_index = (cookie_index + 1) % len(cookie_files)

        time.sleep(1)

if __name__ == "__main__":
    main()
