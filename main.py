import sys
import pickle
import io
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import psutil

# Установка кодировки для вывода в консоль
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Функция для полной остановки всех процессов ChromeDriver
def kill_chrome_driver_processes():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'chromedriver' or 'chrome' in proc.info['name'].lower():
            proc.kill()

# Настройки для headless-режима (заебали чета менять)
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

# Функция для загрузки куки
def load_cookies(driver, path):
    try:
        with open(path, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print(f"Cookies loaded from {path}.", flush=True)
    except FileNotFoundError:
        print(f"File {path} not found, continuing without loading cookies.", flush=True)

# Список файлов с куками - вписиывваете сами
cookie_files = ['cookies.pkl', 'cookies1.pkl', 'cookies2.pkl']
cookie_index = 0  # Индекс для текущего файла куки

# Проверка на наличие карты и клик по карте
def check_for_card(driver, timeout):
    start_time = time.time()  # Замер времени начала поиска карты
    end_time = start_time + timeout
    card_found = False

    while time.time() < end_time:
        print("Checking for card...", flush=True)  # Сообщение о проверке
        try:
            # Переключаемся на основной контент
            driver.switch_to.default_content()  
            
            # Проверка на наличие элемента
            card_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.card-notification[data-card-name]'))
            )
            # Если элемент найден, измеряем время и выводим сообщение
            time_taken = time.time() - start_time
            print(f"\033[92mCard found! Time taken: {time_taken:.2f} seconds.\033[0m", flush=True)  # Зеленый цвет
            card_found = True

            # Клик по карте через JavaScript
            driver.execute_script("arguments[0].click();", card_div)
            print(f"\033[92mCard clicked.\033[0m", flush=True)

            break  # Выходим из цикла

        except Exception as e:
            print("Card not found or not yet available, retrying...", flush=True)
            time.sleep(10)  # Ждем 10 секунд перед повторной проверкой

    if not card_found:
        time_taken = time.time() - start_time  # Замер времени, даже если карта не найдена
        print(f"\033[91mCard not found within the time limit. Total time spent: {time_taken:.2f} seconds.\033[0m", flush=True)  # Красный цвет
    return card_found

# Запуск бесконечного цикла для выполнения задачи
while True:
    # Полный перезапуск ChromeDriver
    kill_chrome_driver_processes()

    # Создаем новый экземпляр Service и инициализируем драйвер. Ставим свое расположение хромдрайвера
    service = Service(executable_path=r'/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get("https://animestars.org/aniserials/video/drama/1108-korzinka-fruktov-final.html")

    # Загрузка куки из текущего файла
    load_cookies(driver, cookie_files[cookie_index])

    # Обновление страницы с загруженными куками
    driver.refresh()

    try:
        # Ожидание появления iframe и переключение на него
        print("Waiting for iframe to be available...", flush=True)
        WebDriverWait(driver, 80).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe[src*="kodik.info"]'))
        )
        print("Switched to iframe.", flush=True)

        # Переменная для отслеживания наличия кнопки play
        play_button_visible = True

        while play_button_visible:
            try:
                # Поиск кнопки Play по XPath
                play_button = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[4]/a'))
                )
                print("Play button found.", flush=True)

                # Проверяем, виден ли элемент
                if driver.execute_script("return arguments[0].offsetParent !== null;", play_button):
                    # Нажимаем на кнопку через JavaScript
                    driver.execute_script("arguments[0].click();", play_button)
                    print("Click performed on the Play button.", flush=True)

                    # Ожидание появления карточки в течение 600 секунд
                    card_found = check_for_card(driver, 600)

                    # Перезагрузка страницы
                    print("Reloading page...", flush=True)
                    driver.refresh()  # Перезагрузка страницы
                    print("Page reloaded successfully.", flush=True)
                    time.sleep(10)  # Ждем 10 секунд перед новым запуском
                    break  # Выходим из внутреннего цикла

                else:
                    play_button_visible = False
                    print("Play button is no longer visible. Stopping clicks.", flush=True)

            except Exception as e:
                # Обрабатываем исключение stale element или отсутствие элемента
                if "stale element reference" in str(e):
                    print("Stale element reference. Play button may have changed or been removed.", flush=True)
                elif "no such element" in str(e):
                    print("Play button not found. Waiting for the next iteration.", flush=True)
                    play_button_visible = False
                else:
                    print("An error occurred while trying to find/click the button:", str(e), flush=True)

                # Останавливаем дальнейшие попытки
                play_button_visible = False

        # Переходим в режим ожидания перед перезапуском
        print("Waiting for 10 seconds before restarting with new cookies.", flush=True)
        time.sleep(10)  # Ждем 10 секунд

    except Exception as e:
        print("An error occurred:", str(e), flush=True)

    finally:
        # Закрытие браузера и полная остановка службы
        driver.quit()
        service.stop()
        print("Restarting in 1 seconds.", flush=True)

    # Переключаем на следующий файл куки
    cookie_index = (cookie_index + 1) % len(cookie_files)

    time.sleep(1)
