import sys
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

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
    
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
        next_restart = current_time.replace(hour=23, minute=59, second=50, microsecond=0)
        if next_restart <= current_time:
            next_restart += timedelta(days=1)

        time_until_restart = (next_restart - current_time).total_seconds()

        time.sleep(time_until_restart)

        print("Выполняется полный перезапуск в 00:00 МСК...", flush=True)
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

accounts = [
    {"username": "ВАШ_ЛОГИН", "password": "ВАШ_ПАРОЛЬ", "cards": 25},
]

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
        
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".user-menu"))
            )
            print(f"Успешный вход в систему для пользователя {username}.", flush=True)
            return True
        except Exception as e:
            print(f"Ошибка при проверке успешного входа: {str(e)}", flush=True)
            return False
        
    except Exception as e:
        print(f"Неожиданная ошибка при входе в систему для пользователя {username}: {str(e)}", flush=True)
        return False

def is_logged_in(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".user-menu"))
        )
        return True
    except:
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
    return card_found

def main():
    account_index = 0
    checks_per_account = {account["username"]: 0 for account in accounts}
    all_cards_found = False

    restart_thread = Thread(target=restart_at_midnight, daemon=True)
    restart_thread.start()

    while True:
        current_account = accounts[account_index]
        if checks_per_account[current_account["username"]] >= current_account["cards"]:
            account_index = (account_index + 1) % len(accounts)
            if all(checks >= account["cards"] for account, checks in zip(accounts, checks_per_account.values())):
                if not all_cards_found:
                    print("Все аккаунты достигли своего лимита. Ожидание сброса...", flush=True)
                    all_cards_found = True
                time.sleep(60)
                continue
        else:
            all_cards_found = False

        kill_chrome_driver_processes()

        service = ChromeService(executable_path=r'/usr/local/bin/chromedriver')
        driver = None
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.get("https://animestars.org")
            if not is_logged_in(driver):
                if not login(driver, current_account["username"], current_account["password"]):
                    print(f"Не удалось войти в систему для аккаунта {current_account['username']}. Пропуск текущей итерации.", flush=True)
                    continue
            else:
                print(f"Уже выполнен вход для аккаунта {current_account['username']}.", flush=True)

            driver.get("https://animestars.org/aniserials/video/josei/921-paradajz-kiss.html")

            driver.execute_script("window.scrollBy(0, 1190);")
            print("Страница прокручена до плеера", flush=True)

            print("Ожидание доступности iframe...", flush=True)
            WebDriverWait(driver, 80).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe[src*="kodik.info"]'))
            )
            print("Переключено на iframe.", flush=True)

            play_button_visible = True

            while play_button_visible:
                try:
                    play_button = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[4]/a'))
                    )
                    print("Кнопка воспроизведения найдена.", flush=True)

                    if driver.execute_script("return arguments[0].offsetParent !== null;", play_button):
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", play_button)
                        print("Выполнен клик по кнопке воспроизведения.", flush=True)

                        card_found = check_for_card(driver, 1600)

                        if card_found:
                            checks_per_account[current_account["username"]] += 1
                            print(f"Карты найдены для {current_account['username']}: {checks_per_account[current_account['username']]}/{current_account['cards']}", flush=True)
                        else:
                            print(f"Карта не найдена для {current_account['username']}. Счетчик не увеличен.", flush=True)

                        print("Перезагрузка страницы...", flush=True)
                        driver.refresh()
                        print("Страница успешно перезагружена.", flush=True)
                        time.sleep(10)
                        break

                    else:
                        play_button_visible = False
                        print("Кнопка воспроизведения больше не видна. Остановка кликов.", flush=True)

                except Exception as e:
                    if "stale element reference" in str(e):
                        print("Устаревшая ссылка на элемент. Кнопка воспроизведения могла измениться или быть удалена.", flush=True)
                    elif "no such element" in str(e):
                        print("Кнопка воспроизведения не найдена. Ожидание следующей итерации.", flush=True)
                    else:
                        print("Произошла ошибка при попытке найти/кликнуть кнопку:", str(e), flush=True)
                    play_button_visible = False

        except Exception as e:
            print("Произошла ошибка:", str(e), flush=True)

        finally:
            if driver:
                driver.quit()
            print("Перезапуск через 5 секунд.", flush=True)
            time.sleep(5)

        account_index = (account_index + 1) % len(accounts)

if __name__ == "__main__":
    main()
