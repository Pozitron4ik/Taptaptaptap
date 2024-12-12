import requests
import os
import time
import logging
import json
import random
from forall import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

debug = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')


class BrowserManager:

    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.driver = None

    def check_browser_status(self):
        try:
            response = requests.get(
                'http://local.adspower.net:50325/api/v1/browser/active',
                params={'serial_number': self.serial_number}
            )
            data = response.json()
            if data['code'] == 0 and data['data']['status'] == 'Active':
                logging.info(f"Account {self.serial_number}: Browser is already active.")
                return True
            else:
                return False
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in checking browser status: {str(e)}")
            return False

    def start_browser(self):
        try:
            if self.check_browser_status():
                logging.info(f"Account {self.serial_number}: Browser already open. Closing the existing browser.")
                self.close_browser()
                time.sleep(5)

            script_dir = os.path.dirname(os.path.abspath(__file__))
            requestly_extension_path = os.path.join(script_dir, 'blum_unlocker_extension')

            if debug:
                launch_args = json.dumps([f"--load-extension={requestly_extension_path}"])
                headless_param = "0"
            else:
                launch_args = json.dumps(["--headless=new", f"--load-extension={requestly_extension_path}"])
                headless_param = "1"

            request_url = (
                f'http://local.adspower.net:50325/api/v1/browser/start?'
                f'serial_number={self.serial_number}&ip_tab=1&headless={headless_param}&launch_args={launch_args}'
            )

            response = requests.get(request_url)
            data = response.json()
            if data['code'] == 0:
                selenium_address = data['data']['ws']['selenium']
                webdriver_path = data['data']['webdriver']
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", selenium_address)

                service = Service(executable_path=webdriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_window_size(600, 900)
                logging.info(f"Account {self.serial_number}: Browser started successfully.")
                return True
            else:
                logging.warning(f"Account {self.serial_number}: Failed to start the browser. Error: {data['msg']}")
                return False
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in starting browser: {str(e)}")
            return False

    def close_browser(self):
        try:
            if self.driver:
                try:
                    self.driver.close()
                    self.driver.quit()
                    self.driver = None
                    logging.info(f"Account {self.serial_number}: Browser closed successfully.")
                except WebDriverException as e:
                    logging.info(f"Account {self.serial_number}: exception, Browser should be closed now")
        except Exception as e:
            logging.exception(
                f"Account {self.serial_number}: General Exception occurred when trying to close the browser: {str(e)}")
        finally:
            try:
                response = requests.get(
                    'http://local.adspower.net:50325/api/v1/browser/stop',
                    params={'serial_number': self.serial_number}
                )
                data = response.json()
                if data['code'] == 0:
                    logging.info(f"Account {self.serial_number}: Browser closed successfully.")
                else:
                    logging.info(f"Account {self.serial_number}: exception, Browser should be closed now")
            except Exception as e:
                logging.exception(
                    f"Account {self.serial_number}: Exception occurred when trying to close the browser: {str(e)}")


class TelegramBotAutomation:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.browser_manager = BrowserManager(serial_number)
        logging.info(f"Initializing automation for account {serial_number}")
        self.browser_manager.start_browser()
        self.driver = self.browser_manager.driver

    def sleep(self, a, b):
        sleep_time = random.randrange(a, b)
        logging.info(f"Account {self.serial_number}: {sleep_time}sec sleep...")
        time.sleep(sleep_time)

    def navigate_to_bot(self):
        try:
            self.driver.get('https://web.telegram.org/k/')
            logging.info(f"Account {self.serial_number}: Navigated to Telegram web.")
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in navigating to Telegram bot: {str(e)}")
            self.browser_manager.close_browser()

    def send_message(self, message):
        chat_input_area = self.wait_for_element(By.XPATH,
                                                '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/input[1]')
        chat_input_area.click()
        chat_input_area.send_keys(message)

        search_area = self.wait_for_element(By.XPATH,
                                            '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/ul[1]/a[1]/div[1]')
        search_area.click()
        logging.info(f"Account {self.serial_number}: Group searched.")
        self.sleep(2, 3)

    def click_link(self):
        link = self.wait_for_element(By.CSS_SELECTOR, "a[href*='t.me/seed_coin_bot/app?startapp']")
        link.click()

        # После последней обновы 31.08.24 закомментил
        # launch_click = self.wait_for_element(By.XPATH, "//body/div[@class='popup popup-peer popup-confirmation active']/div[@class='popup-container z-depth-1']/div[@class='popup-buttons']/button[1]/div[1]")
        # launch_click.click()
        logging.info(f"Account {self.serial_number}: SEED STARTED")
        sleep_time = random.randrange(4, 6)
        logging.info(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        if not self.switch_to_iframe():
            logging.info(f"Account {self.serial_number}: No iframes found")
            return

    def switch_to_iframe(self):
        self.driver.switch_to.default_content()
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            self.driver.switch_to.frame(iframes[0])
            return True
        return False

    def switch_tabs(self):
        try:
            # Логирование начала процесса переключения
            logging.info("Начинаем переключение вкладок.")

            # Получаем список открытых вкладок
            tabs = self.driver.window_handles
            logging.info(f"Открыто {len(tabs)} вкладок.")

            # Определяем текущую вкладку
            current_tab = self.driver.current_window_handle
            current_index = tabs.index(current_tab)

            # Рассчитываем индекс следующей вкладки
            next_index = (current_index + 1) % len(tabs)
            logging.info(f"Переключаемся с вкладки {current_index} на {next_index}.")

            # Переключаемся на следующую вкладку
            self.driver.switch_to.window(tabs[next_index])

            # Ждём некоторое время, чтобы вкладка могла полностью загрузиться
            time.sleep(1)

            # Делаем скриншот, если включена опция
            if self.scrshot:
                screenshot_name = f'screen{self.scrshot}.png'
                self.driver.save_screenshot(screenshot_name)
                logging.info(f"Сохранен скриншот: {screenshot_name}")
                self.scrshot += 1

            # Ждём перед переключением обратно
            self.sleep(3, 7)

            # Возвращаемся на исходную вкладку
            logging.info("Переключаемся обратно на исходную вкладку.")
            self.driver.switch_to.window(tabs[current_index])

            # Переходим в iframe, если это нужно
            logging.info("Переключаемся на iframe.")
            self.switch_to_iframe()

        except Exception as e:
            # Логируем любые возникшие ошибки
            logging.error(f"Ошибка в аккаунте {self.serial_number}: {e}")

    def back(self):
        self.driver.switch_to.default_content()
        self.wait_for_element(By.XPATH,
                              '/html/body/div[6]/div/div[1]/button[1]'
                              ).click()
        time.sleep(2)
        if self.scrshot:
            self.driver.save_screenshot(f'screen{self.scrshot}.png')
            self.scrshot += 1
        self.switch_to_iframe()

    def wait_for_element(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def wait_for_elements(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_all_elements_located((by, value))
        )

    def checkNews(self):
        try:
            news = self.wait_for_element(By.XPATH,
                                         '/html[1]/body[1]/div[1]/div[2]/div[1]/div[2]/div[4]/div[1]/div[1]/div[1]/div[1]/div[2]'
                                         )
            self.driver.execute_script("arguments[0].scrollIntoView();", news)
            news.click()
            self.sleep(1, 3)
            logging.info(f"Account {self.serial_number}: checked news")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e)}")


    def click_until_no_button(self):
            """
            Нажимает на первую кнопку, затем, если появляется вторая кнопка, нажимает на неё.
            Повторяет процесс, пока вторая кнопка не перестанет появляться.
            """
            try:
                first_button_xpath = '/html[1]/body[1]/div[1]/div[2]/div[1]/div[2]/div[3]/div[1]/img[1]'
                second_button_xpath = '/html[1]/body[1]/div[1]/div[2]/div[1]/div[3]/div[1]/div[1]/div[1]/button[1]'

                while True:
                    # Нажимаем на первую кнопку
                    try:
                        first_button = self.wait_for_element(By.XPATH, first_button_xpath, timeout=5)
                        self.driver.execute_script("arguments[0].scrollIntoView();", first_button)
                        first_button.click()
                        logging.info(f"Account {self.serial_number}: Нажата первая кнопка.")
                        self.sleep(1, 2)
                    except TimeoutException:
                        logging.info(f"Account {self.serial_number}: Первая кнопка не найдена. Завершаем цикл.")
                        break  # Если первая кнопка не найдена, выходим из цикла

                    # Проверяем наличие второй кнопки
                    try:
                        second_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, second_button_xpath))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView();", second_button)
                        second_button.click()
                        logging.info(f"Account {self.serial_number}: Нажата вторая кнопка.")
                        self.sleep(1, 2)
                    except TimeoutException:
                        logging.info(f"Account {self.serial_number}: Вторая кнопка не появилась. Завершаем цикл.")
                        break  # Если второй кнопки нет, выходим из цикла

            except Exception as e:
                logging.exception(f"Account {self.serial_number}: Ошибка в click_until_no_button: {str(e)}")

    def claim(self):
        try:
            butClaim = self.wait_for_element(By.XPATH,
                                             '/html[1]/body[1]/div[1]/div[2]/div[1]/div[2]/div[4]/div[1]/div[1]/div[1]/div[1]/div[2]'
                                             )
            butClaim.click()
            self.sleep(1, 3)
            logging.info(f"Account {self.serial_number}: clicked claim")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e)}")

    def earn(self):
        try:

            but = self.wait_for_element(By.CSS_SELECTOR,
                                        # '/html/body/div[1]/div[2]/div[2]/div/div/div[2]/div/div[2]/div[2]/div'
                                       # "#root > div.h-screen.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].fixed.z-0.left-0.right-0.bottom-0.top-0.dark\:bg-none.dark\:bg-\[\#030C02\].max-w-md.mx-auto > div.fixed.left-0.right-0.bottom-0.z-40 > div > div > div:nth-child(2) > div > div:nth-child(2) > div > div"
                                        "body > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2)"
                                        )
            #  but.click()
            self.driver.execute_script("arguments[0].click();", but)
            self.sleep(1, 4)
            logging.info(f"Account {self.serial_number}: clicked earn")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e)}")

    def reboot(self):
        logging.info(f"Account {self.serial_number}: rebooting...")
        try:
            self.driver.switch_to.default_content()
            menu = self.wait_for_element(By.XPATH,
                                         '/html/body/div[6]/div/div[1]/div[1]/div/div[2]/button[1]/span[1]'
                                         )
            menu.click()
            self.driver.switch_to.default_content()
            time.sleep(4)
            reload = self.wait_for_element(By.XPATH,
                                           # #page-chats > div.btn-menu.contextmenu.bottom-center.active.was-open > div:nth-child(2)
                                           '/html/body/div[1]/div[3]/div[2]'
                                           )
            reload.click()
            self.sleep(4, 6)
            self.switch_to_iframe()
        except Exception as e:
            logging.info(f"Account {self.serial_number}: error rebooting")

    def daily(self):
        stage = 0
        try:
            bonus = self.wait_for_element(By.CSS_SELECTOR,
                                          # '#root > div.h-screen.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].fixed.z-0.left-0.right-0.bottom-0.top-0.dark\:bg-none.dark\:bg-\[\#030C02\].max-w-md.mx-auto > div:nth-child(1) > div.pt-5.px-4.pb-\[60px\].relative.z-40.h-screen.bg-\[\#FFFFFF\] > div.mt-3.overflow-auto.max-h-\[calc\(100\%-100px\)\] > div:nth-child(2) > div.z-10.relative.cursor-pointer.grid.grid-cols-12.gap-3.bg-white.rounded-xl.p-3.w-full.border-\[1px\].border-\[\#F3F3F3\].border-solid > div.col-span-4.flex.items-center.justify-end'
                                          #     '#root > div.h-screen.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].fixed.z-0.left-0.right-0.bottom-0.top-0.dark\:bg-none.dark\:bg-\[\#030C02\].max-w-md.mx-auto > div:nth-child(1) > div.pt-5.px-4.pb-\[60px\].relative.z-40.h-screen.bg-\[\#FFFFFF\] > div.mt-3.overflow-auto.max-h-\[calc\(100\%-100px\)\] > div.mb-3.rounded-2xl > div.z-10.relative.cursor-pointer.grid.grid-cols-12.gap-3.bg-white.rounded-xl.p-3.w-full.border-\[1px\].border-\[\#F3F3F3\].border-solid > div.col-span-4.flex.items-center.justify-end > button'
                                          # '#root > div.h-screen.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].fixed.z-0.left-0.right-0.bottom-0.top-0.dark\:bg-none.dark\:bg-\[\#030C02\].max-w-md.mx-auto > div:nth-child(1) > div.pt-5.px-4.pb-\[60px\].relative.z-40.h-screen.bg-\[\#FFFFFF\] > div.mt-3.overflow-auto.max-h-\[calc\(100\%-100px\)\] > div.mb-3.rounded-2xl > div.z-10.relative.cursor-pointer.grid.grid-cols-12.gap-3.bg-white.rounded-xl.p-3.w-full.border-\[1px\].border-\[\#F3F3F3\].border-solid > div.col-span-4.flex.items-center.justify-end'
                                          "div[class='col-span-4 flex items-center justify-end'] button[class='bg-[#61A700] w-[80px] rounded-[38px] py-2 px-[22px] capitalize text-[#fff] text-sm font-semibold flex items-center justify-center']"
                                          )
            self.driver.execute_script("arguments[0].click();", bonus)

            # bonus.click()
            self.sleep(1, 4)
            logging.info(f"Account {self.serial_number}: clicked start")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
            stage += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e), stage}")

        if stage:
            i = 1
            buts = [0, 0, 0, 0, 0, 0, 0]
            flags = [0, 0, 0, 0, 0, 0, 0]
            try:
                while i < 8:
                    buts[i - 1] = self.wait_for_element(By.XPATH,
                                                        f'/html/body/div[1]/div[2]/div/div[1]/div[3]/button[{i}]'
                                                        )
                    self.driver.execute_script("arguments[0].scrollIntoView();", buts[i - 1])
                    logging.info(f"Account {self.serial_number}: initialized day {i}")
                    try:
                        if self.wait_for_element(By.XPATH,
                                                 f'/html/body/div[1]/div[2]/div/div[1]/div[3]/button[{i}]/div[1]/img'
                                                 ):
                            flags[i - 1] = 1
                            logging.info(f"Account {self.serial_number}: day {i} is not present")
                    except Exception as e:
                        logging.info(f"Account {self.serial_number}: day {i} is good")

                    i += 1
                stage += 1

                logging.info(f"Account {self.serial_number}: good days are 0: {flags}")

            except Exception as e:
                logging.info(f"Account {self.serial_number}: {str(e), stage}")

            if stage > 1:
                i = 1
                try:
                    while i < 8:
                        if flags[i - 1] != 1:
                            buts[i - 1].click()
                            logging.info(f"Account {self.serial_number}: clicked day {i}")
                            self.sleep(1, 3)
                        i += 1
                    stage += 1
                    self.sleep(1, 3)

                except Exception as e:
                    logging.info(f"Account {self.serial_number}: {str(e), stage}")

            if stage > 2:
                try:
                    claimTicket = self.wait_for_element(By.XPATH,
                                                        '/html/body/div[1]/div[2]/div/div[1]/div[2]/button'
                                                        )
                    self.driver.execute_script("arguments[0].scrollIntoView();", claimTicket)
                    claimTicket.click()
                    self.sleep(1, 3)
                    logging.info(f"Account {self.serial_number}: claimed")
                    if self.scrshot:
                        self.driver.save_screenshot(f'screen{self.scrshot}.png')
                        self.scrshot += 1
                except Exception as e:
                    logging.info(f"Account {self.serial_number}: {str(e), stage}")

    def click_until_no_button(self):
            """
            Нажимает на первую кнопку, затем, если появляется вторая кнопка, нажимает на неё.
            Повторяет процесс, пока вторая кнопка не перестанет появляться.
            """
            try:
                first_button_xpath = '/html[1]/body[1]/div[1]/div[2]/div[1]/div[2]/div[3]/div[1]/img[1]'
                second_button_xpath = '/html[1]/body[1]/div[1]/div[2]/div[1]/div[3]/div[1]/div[1]/div[1]/button[1]'

                while True:
                    # Нажимаем на первую кнопку
                    try:
                        first_button = self.wait_for_element(By.XPATH, first_button_xpath, timeout=5)
                        self.driver.execute_script("arguments[0].scrollIntoView();", first_button)
                        first_button.click()
                        self.sleep(3, 5)
                        logging.info(f"Account {self.serial_number}: Нажата первая кнопка.")
                    except TimeoutException:
                        logging.info(f"Account {self.serial_number}: Первая кнопка не найдена. Завершаем цикл.")
                        break  # Если первая кнопка не найдена, выходим из цикла

                    # Проверяем наличие второй кнопки
                    try:
                        second_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, second_button_xpath))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView();", second_button)
                        second_button.click()
                        self.sleep(15, 20)
                        logging.info(f"Account {self.serial_number}: Нажата вторая кнопка.")
                    except TimeoutException:
                        logging.info(f"Account {self.serial_number}: Вторая кнопка не появилась. Завершаем цикл.")
                        break  # Если второй кнопки нет, выходим из цикла

            except Exception as e:
                logging.exception(f"Account {self.serial_number}: Ошибка в click_until_no_button: {str(e)}")

    def worm(self):
        stage = 0
        success = True
        try:
            cherv = self.wait_for_element(By.CSS_SELECTOR,
                                          #  '#root > div.h-screen.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].fixed.z-0.left-0.right-0.bottom-0.top-0.dark\:bg-none.dark\:bg-\[\#030C02\].max-w-md.mx-auto > div:nth-child(1) > div.h-screen.overflow-hidden.flex.flex-col.flex-1.px-4.relative.z-60.dark\:bg-transparent.dark\:bg-gradient-to-b.from-transparent.via-transparent.to-transparent.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].pb-\[110px\] > div.flex.flex-1.relative.justify-center.bg-no-repeat.bg-contain.bg-center.z-10.w-\[114\%\].-ml-\[7\%\].-mb-\[5\%\] > div.relative.w-\[35\%\].h-\[40\%\].z-10.top-\[55\%\].-right-0.-translate-y-\[50\%\].-translate-x-\[20\%\] > div > img'
                                          # '#root > div.h-screen.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].fixed.z-0.left-0.right-0.bottom-0.top-0.dark\:bg-none.dark\:bg-\[\#030C02\].max-w-md.mx-auto > div:nth-child(1) > div.h-screen.overflow-hidden.flex.flex-col.flex-1.px-4.relative.z-60.dark\:bg-transparent.dark\:bg-gradient-to-b.from-transparent.via-transparent.to-transparent.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].pb-\[110px\] > div.flex.flex-1.relative.justify-center.bg-no-repeat.bg-contain.bg-center.z-10.w-\[114\%\].-ml-\[7\%\].-mb-\[5\%\] > div > div:nth-child(2) > img'
                                          "#root > div.h-screen.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].fixed.z-0.left-0.right-0.bottom-0.top-0.dark\:bg-none.dark\:bg-\[\#030C02\].max-w-md.mx-auto > div:nth-child(1) > div.h-screen.overflow-hidden.flex.flex-col.flex-1.px-4.relative.z-60.dark\:bg-transparent.dark\:bg-gradient-to-b.from-transparent.via-transparent.to-transparent.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].pb-\[110px\] > div.flex.flex-1.relative.justify-center.bg-no-repeat.bg-contain.bg-center.z-10.w-\[114\%\].-ml-\[7\%\].-mb-\[5\%\] > div > div > img"
                                          )

            self.driver.execute_script("arguments[0].click();", cherv)
            self.sleep(1, 3)
            logging.info(f"Account {self.serial_number}: catching chervyachok...")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1

        except Exception as e:
            success = False
            logging.info(f"Account {self.serial_number}: no worm")

        try:
            understand = self.wait_for_element(By.XPATH,
                                               '/html/body/div[3]/div[3]/div[3]/button'
                                               )
            understand.click()
            logging.info(f"Account {self.serial_number}: clicked i understand")
            success = False
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant click i understand")

        if success:
            logging.info(f"Account {self.serial_number}: червь пойман")
            try:
                yep = self.wait_for_element(By.XPATH,
                                            '/html/body/div[3]/div[3]/div[2]/button'
                                            )
                yep.click()
                logging.info(f"Account {self.serial_number}: yep")
            except Exception as e:
                logging.info(f"Account {self.serial_number}: no yep")
        else:
            logging.info(f"Account {self.serial_number}: червь не пойман")

    def egg(self):
        stage = 0
        try:
            yaytso = self.wait_for_element(By.XPATH,
                                           '/html/body/div[1]/div[2]/div[1]/div[2]/div[3]/div[2]/img'
                                           )
            yaytso.click()
            logging.info(f"Account {self.serial_number}: got egg")

            self.sleep(1, 3)
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
            self.back()
            self.back()

        except Exception as e:
            logging.info(f"Account {self.serial_number}: no egg")
        # self.reboot()


def read_accounts_from_file():
    with open('accounts_seed.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]


def write_accounts_to_file(accounts):
    with open('accounts_seed.txt', 'w') as file:
        for account in accounts:
            file.write(f"{account}\n")


def process_accounts():
    last_processed_account = None

    while True:

        accounts = read_accounts_from_file()
        random.shuffle(accounts)
        write_accounts_to_file(accounts)
        i = 0
        while i < len(accounts):
            remove_empty_lines('locked_accounts.txt')
            remove_key_lines('locked_accounts.txt', 'WEED')

            retry_count = 0
            i += 1
            success = False
            if is_account_locked(accounts[i - 1]):
                if i == len(accounts):
                    retry_count = 3
                else:
                    accounts.append(accounts[i - 1])
                    accounts.pop(i - 1)
                    print(accounts)
                    i -= 1
                # здесь выход в новую итерацию цикла со следующего элемента

            else:

                while retry_count < 3 and not success:
                    lock_account(accounts[i - 1], 'WEED')
                    bot = TelegramBotAutomation(accounts[i - 1])
                    bot.scrshot = 0  # 0 for no screenshots
                    try:
                        delete_oldScreens()
                        bot.navigate_to_bot()
                        bot.send_message("https://t.me/seeedgoidacoin")
                        bot.click_link()
                        time.sleep(1)
                        bot.click_until_no_button()
                        bot.checkNews()
                        bot.worm()

                        bot.claim()
                        bot.earn()
                        bot.daily()


                        logging.info(f"Account {accounts[i - 1]}: Processing completed successfully.")
                        success = True
                    except Exception as e:
                        logging.warning(f"Account {accounts[i - 1]}: Error occurred on attempt {retry_count + 1}: {e}")
                        retry_count += 1
                    finally:
                        logging.info("-------------END-----------")
                        bot.browser_manager.close_browser()
                        logging.info("-------------END-----------")
                        unlock_account(accounts[i - 1], "WEED")
                        sleep_time = random.randrange(5, 15)
                        logging.info(f"Sleeping for {sleep_time} seconds.")
                        time.sleep(sleep_time)

                    if retry_count >= 3:
                        logging.warning(f"Account {accounts[i - 1]}: Failed after 3 attempts.")

            if not success:
                logging.warning(f"Account {accounts[i - 1]}: Moving to next account after 3 failed attempts.")

        logging.info("All accounts processed. Waiting 2 hours before restarting.")

        for hour in range(2):
            logging.info(f"Waiting... {2 - hour} hours left till restart.")
            time.sleep(60 * 60)

        logging.info("Shuffling accounts for the next cycle.")


if __name__ == "__main__":
    process_accounts()