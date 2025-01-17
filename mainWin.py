import sys
import io
import time
import os
from datetime import datetime, timedelta
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import psutil
import pytz

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Можете поменять колво
PROXY_CONFIGS = [
    {
        "host": "ip",
        "port": "port",
        "username": "user",
        "password": "pass"
    },
    {
        "host": "ip",
        "port": "port",
        "username": "user",
        "password": "pass"
    },
    {
        "host": "ip",
        "port": "port",
        "username": "user",
        "password": "pass"
    },
    {
        "host": "ip",
        "port": "port",
        "username": "user",
        "password": "pass"
    },
]

# Можете убрать прокси2 прокси3 и тд, также можно добавлять к прокси еще аккаунты
ACCOUNTS = {
    "proxy1": [
        {"username": "ВАШ_ЛОГИН", "password": "ВАШ_ПАРОЛЬ", "cards": 25},
        {"username": "ВАШ_ЛОГИН", "password": "ВАШ_ПАРОЛЬ", "cards": 25},
    ],
    "proxy2": [
        {"username": "ВАШ_ЛОГИН", "password": "ВАШ_ПАРОЛЬ", "cards": 25},
    ],
    "proxy3": [
        {"username": "ВАШ_ЛОГИН", "password": "ВАШ_ПАРОЛЬ", "cards": 25},
    ],
    "proxy4": [
        {"username": "ВАШ_ЛОГИН", "password": "ВАШ_ПАРОЛЬ", "cards": 25},
    ]
}

def create_screenshot_directory():
    directory = "failed_attempts_screenshots"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def kill_chrome_driver_processes():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'chromedriver' or 'chrome' in proc.info['name'].lower():
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass

def create_proxy_extension(proxy_config):
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
            }
        };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (proxy_config["host"], proxy_config["port"], 
           proxy_config["username"], proxy_config["password"])

    path = os.path.dirname(os.path.abspath(__file__))
    proxy_extension_path = os.path.join(path, f'proxy_auth_extension_{proxy_config["host"]}')
    
    if not os.path.exists(proxy_extension_path):
        os.makedirs(proxy_extension_path)
    
    with open(os.path.join(proxy_extension_path, "manifest.json"), 'w') as f:
        f.write(manifest_json)
    
    with open(os.path.join(proxy_extension_path, "background.js"), 'w') as f:
        f.write(background_js)
    
    return proxy_extension_path

def is_logged_in(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".user-menu"))
        )
        return True
    except:
        return False

def login(driver, username, password):
    try:
        driver.get("https://animestars.org")
        print(f"Попытка входа для пользователя {username}...", flush=True)
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.header__btn.btn.js-show-login"))
            )
            driver.execute_script("arguments[0].click();", login_button)
            print("Кнопка входа нажата.", flush=True)
        except Exception as e:
            print(f"Ошибка при нажатии кнопки входа: {str(e)}", flush=True)
            return False
        
        try:
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='login_name']"))
            )
            username_field.clear()
            username_field.send_keys(username)
            print("Логин введен.", flush=True)
            
            password_field = driver.find_element(By.XPATH, "//input[@name='login_password']")
            password_field.clear()
            password_field.send_keys(password)
            print("Пароль введен.", flush=True)
        except Exception as e:
            print(f"Ошибка при вводе учетных данных: {str(e)}", flush=True)
            return False

        try:
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@onclick='submit();']"))
            )
            driver.execute_script("arguments[0].click();", submit_button)
            print("Кнопка отправки формы нажата.", flush=True)
        except Exception as e:
            print(f"Ошибка при отправке формы: {str(e)}", flush=True)
            return False

        driver.refresh()
        print("Страница обновлена после отправки формы.", flush=True)
        return True
        
    except Exception as e:
        print(f"Неожиданная ошибка при входе в систему для пользователя {username}: {str(e)}", flush=True)
        return False


def check_for_card(driver, timeout):
    start_time = time.time()
    end_time = start_time + timeout
    card_found = False

    while time.time() < end_time:
        print("Проверка наличия карты...", flush=True)
        try:
            driver.switch_to.default_content()
            time.sleep(2)
            card_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-notification[data-card-name]'))
            )
            time_taken = time.time() - start_time
            print(f"\033[92mКарта найдена! Затраченное время: {time_taken:.2f} секунд.\033[0m", flush=True)
            card_found = True

            time.sleep(5)
            driver.execute_script("arguments[0].click();", card_div)
            print(f"\033[92mКарта кликнута.\033[0m", flush=True)
            break

        except Exception as e:
            print("Карта не найдена или еще не доступна, повторная попытка...", flush=True)
            time.sleep(10)

    if not card_found:
        time_taken = time.time() - start_time
        print(f"\033[91mКарта не найдена в течение заданного времени. Общее затраченное время: {time_taken:.2f} секунд.\033[0m", flush=True)
        
        screenshot_dir = create_screenshot_directory()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshot_dir, f"failed_attempt_{timestamp}.png")
        try:
            driver.save_screenshot(screenshot_path)
            print(f"Скриншот сохранен: {screenshot_path}", flush=True)
        except Exception as e:
            print(f"Ошибка при сохранении скриншота: {str(e)}", flush=True)

    return card_found

class AccountManager:
    def __init__(self, proxy_config, accounts):
        self.proxy_config = proxy_config
        self.accounts = accounts
        self.current_index = 0
        self.active_accounts = list(range(len(accounts)))
        self.checks_per_account = {account["username"]: 0 for account in accounts}

    def get_next_account(self):
        if not self.active_accounts:
            return None
        
        account_index = self.active_accounts[self.current_index % len(self.active_accounts)]
        self.current_index += 1
        return self.accounts[account_index]

    def update_account_status(self, username, cards_found):
        self.checks_per_account[username] += cards_found
        if self.checks_per_account[username] >= next(account["cards"] 
            for account in self.accounts if account["username"] == username):
            self.active_accounts = [i for i in self.active_accounts 
                if self.accounts[i]["username"] != username]
            return True
        return False

def restart_at_midnight(account_managers):
    moscow_tz = pytz.timezone('Europe/Moscow')
    while True:
        current_time = datetime.now(moscow_tz)
        next_restart = current_time.replace(hour=23, minute=59, second=50, microsecond=0)
        if next_restart <= current_time:
            next_restart += timedelta(days=1)

        time_until_restart = (next_restart - current_time).total_seconds()
        time.sleep(time_until_restart)

        print("Выполняется полный перезапуск в 00:00 МСК...", flush=True)
        kill_chrome_driver_processes()
        for manager in account_managers:
            manager.current_index = 0
            manager.active_accounts = list(range(len(manager.accounts)))
            manager.checks_per_account = {account["username"]: 0 for account in manager.accounts}
        os.execv(sys.executable, [sys.executable] + sys.argv)

def process_account_group(account_manager):
    chrome_options = Options()
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
    chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--disable-webrtc")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-logging-redirect")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option("prefs", {
        "webrtc.ip_handling_policy": "disable_non_proxied_udp",
        "webrtc.multiple_routes_enabled": False,
        "webrtc.nonproxied_udp_enabled": False
    })

    proxy_extension_path = create_proxy_extension(account_manager.proxy_config)
    chrome_options.add_argument(f'--load-extension={proxy_extension_path}')

    while True:
        account = account_manager.get_next_account()
        if not account:
            print(f"Акки хуяки наверное умерли {account_manager.proxy_config['host']}", flush=True)
            break

        driver = None
        try:
            chromedriver_path = os.path.join(os.path.dirname(__file__), 'chromedriver-win64', 'chromedriver.exe')
            service = ChromeService(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            if not login(driver, account["username"], account["password"]):
                print(f"Ошибка входа в аккаунт {account['username']}. Пропускаем.", flush=True)
                continue

            driver.get("https://animestars.org/aniserials/video/drama/749-korzinka-fruktov-2-sezon.html")
            driver.execute_script("window.scrollBy(0, 1190);")
            
            WebDriverWait(driver, 80).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe[src*="kodik.info"]'))
            )

            play_button_visible = True
            while play_button_visible:
                try:
                    play_button = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[4]/a'))
                    )

                    if driver.execute_script("return arguments[0].offsetParent !== null;", play_button):
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", play_button)
                        
                        card_found = check_for_card(driver, 1600)
                        if card_found:
                            if account_manager.update_account_status(account["username"], 1):
                                print(f"Аккаунт {account['username']} достиг лимита карт", flush=True)
                                break
                            print(f"Карта не найдена для {account['username']}", flush=True)

                        driver.refresh()
                        time.sleep(10)
                        break
                    else:
                        play_button_visible = False
                        print("Кнопка воспроизведения больше не видна. Не кликаем.", flush=True)

                except Exception as e:
                    if "Все плохо, пишите разрабу." in str(e):
                        print("кнопка пропала.", flush=True)
                    elif "no such element" in str(e):
                        print("Кнопка не найдена.", flush=True)
                    else:
                        print(f"Ошибка обработки кнопки: {str(e)}", flush=True)
                    play_button_visible = False

        except Exception as e:
            print(f"Ошибка с аккаунтом {account['username']}: {str(e)}", flush=True)
        finally:
            if driver:
                driver.quit()
            time.sleep(5)

def main():
    account_managers = []
    for i, proxy_config in enumerate(PROXY_CONFIGS):
        proxy_accounts = ACCOUNTS[f"proxy{i+1}"]
        account_managers.append(AccountManager(proxy_config, proxy_accounts))
    
    restart_thread = Thread(target=restart_at_midnight, args=(account_managers,), daemon=True)
    restart_thread.start()
    
    print("Начинаем вход в группы аккаунтов с прокси", flush=True)
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_account_group, account_managers)

    print("Все группы аккаунтов завершили обработку.", flush=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCкрипт прекращен пользователем.", flush=True)
        kill_chrome_driver_processes()
        sys.exit(0)
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}", flush=True)
        kill_chrome_driver_processes()
        sys.exit(1)
