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

debug = True

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
            # Сохраняем текущий URL основной вкладки
            self.main_tab_url = self.driver.current_url
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
        link = self.wait_for_element(By.CSS_SELECTOR, "a[href*='https://t.me/TVerse?startapp=galaxy-0001d27add0002dfcc1f0000a93a7a']")
        link.click()

        logging.info(f"Account {self.serial_number}: TINY STARTED")
        sleep_time = random.randrange(4, 8)
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

    def click_launch_button(self):
        logging.info(f"Account {self.serial_number}: Trying to click Launch button.")
        launch_button = self.wait_for_element(
            By.XPATH,
            "//body/div[@class='popup popup-peer popup-confirmation active']/div[@class='popup-container z-depth-1']/div[@class='popup-buttons']/button[1]/div[1]"
        )
        launch_button.click()
        logging.info(f"Account {self.serial_number}: Clicked Launch button.")
        self.sleep(2, 4)

    def click_begin_your_own_journey_button(self):
        logging.info(f"Account {self.serial_number}: Trying to click 'Begin your own journey' button.")
        begin_journey_button = self.wait_for_element(
            By.XPATH,
            "/html[1]/body[1]/div[2]/div[1]/div[1]/div[4]/a[1]"
        )

        button_text = begin_journey_button.text.strip()
        logging.info(f"Account {self.serial_number}: Found button with text: '{button_text}'")
        self.sleep(2, 5)

        if button_text == "Begin your own journey":
            begin_journey_button.click()
            self.sleep(2, 5)
            logging.info(f"Account {self.serial_number}: Clicked 'Begin your own journey' button.")
        else:
            logging.info(
                f"Account {self.serial_number}: Button text '{button_text}' does not match 'Begin your own journey', skipping click.")

    def click_begin_button(self):
        logging.info(f"Account {self.serial_number}: Trying to click 'Begin' button.")
        begin_button = self.wait_for_element(
            By.XPATH,
            "/html[1]/body[1]/div[2]/div[3]/div[2]/div[1]/div[1]/div[4]/button[1]"
        )

        button_text = begin_button.text.strip()
        self.sleep(1, 3)

        if button_text == "Begin":
            begin_button.click()
            logging.info(f"Account {self.serial_number}: Clicked 'Begin' button.")
            self.sleep(2, 4)
        else:
            logging.info(
                f"Account {self.serial_number}: Button text '{button_text}' does not match 'Begin', skipping click.")

    def first_try(self):
        # Шаг 1: Launch Button
        try:
            self.click_launch_button()
        except TimeoutException:
            logging.info(f"Account {self.serial_number}: Launch button not found due to timeout.")
        except NoSuchElementException:
            logging.info(f"Account {self.serial_number}: Launch button not found.")
        except WebDriverException as e:
            logging.info(f"Account {self.serial_number}: WebDriverException while clicking Launch button: {e}")
        except Exception as e:
            logging.info(f"Account {self.serial_number}: Unexpected error while clicking Launch button: {e}")

        # Шаг 2: Begin your own journey
        try:
            self.click_begin_your_own_journey_button()
        except TimeoutException:
            logging.info(f"Account {self.serial_number}: 'Begin your own journey' button not found due to timeout.")
        except NoSuchElementException:
            logging.info(f"Account {self.serial_number}: 'Begin your own journey' button not found.")
        except WebDriverException as e:
            logging.info(
                f"Account {self.serial_number}: WebDriverException while clicking 'Begin your own journey': {e}")
        except Exception as e:
            logging.info(f"Account {self.serial_number}: Unexpected error while clicking 'Begin your own journey': {e}")

        # Шаг 3: Begin Button
        try:
            self.click_begin_button()
        except TimeoutException:
            logging.info(f"Account {self.serial_number}: 'Begin' button not found due to timeout.")
        except NoSuchElementException:
            logging.info(f"Account {self.serial_number}: 'Begin' button not found.")
        except WebDriverException as e:
            logging.info(f"Account {self.serial_number}: WebDriverException while clicking 'Begin': {e}")
        except Exception as e:
            logging.info(f"Account {self.serial_number}: Unexpected error while clicking 'Begin': {e}")

    def click_home(self):
        try:
            # Ищем SVG path внутри кнопки Home
            home_path = self.wait_for_element(
                By.XPATH,
                "/html[1]/body[1]/div[2]/div[1]/div[1]/div[3]/a[1]/*[name()='svg'][1]/*[name()='path'][1]"
            )

            # Получаем атрибут d из path
            path_d = home_path.get_attribute("d")
            logging.info(f"Account {self.serial_number}: Home path 'd' attribute = {path_d}")

            expected_d = "M4 7L10 2L16 7V16H4V7Z"
            if path_d == expected_d:
                # Если атрибут совпадает с ожидаемым, кликаем по кнопке Home
                home_button = self.wait_for_element(
                    By.XPATH,
                    "/html[1]/body[1]/div[2]/div[1]/div[1]/div[3]/a[1]"
                )
                home_button.click()
                logging.info(f"Account {self.serial_number}: Clicked Home button.")
                self.sleep(2, 4)
            else:
                # Если атрибут не совпадает, пропускаем клик
                logging.info(f"Account {self.serial_number}: Home icon does not match expected shape, skipping click.")

        except TimeoutException:
            logging.info(f"Account {self.serial_number}: Home button not found, skipping.")
        except NoSuchElementException:
            logging.info(f"Account {self.serial_number}: Home button not found, skipping.")
        except Exception as e:
            logging.info(f"Account {self.serial_number}: Error in click_home: {e}")

    def add_stars(self):
        try:
            # Кликаем по кнопке "add stars"
            add_stars_button = self.wait_for_element(
                By.XPATH,
                "/html[1]/body[1]/div[2]/div[1]/div[1]/div[4]/a[1]"
            )
            add_stars_button.click()
            logging.info(f"Account {self.serial_number}: click add stars")
            self.sleep(2, 4)

            # Пытаемся найти stars_icon
            try:
                star_icon = self.wait_for_element(
                    By.XPATH,
                    "/html/body/div[2]/div[3]/div[2]/div/div[1]/div[2]/label[2]/b[2]/span[3]/*[name()='svg'][1]/*[name()='path'][1]"
                )
                # Проверяем атрибут d
                path_d = star_icon.get_attribute("d")
                expected_d = "M6.17983 9.72194L3.47933 11.3763C3.19853 11.5483 2.83144 11.4601 2.65942 11.1793C2.57541 11.0422 2.55036 10.8769 2.58996 10.721L3.008 9.07562C3.1589 8.48166 3.56535 7.98515 4.11781 7.71991L7.06392 6.30543C7.20127 6.23949 7.25915 6.07468 7.19321 5.93734C7.1398 5.82611 7.01903 5.76386 6.89746 5.78491L3.61806 6.35266C2.95143 6.46807 2.26781 6.28398 1.74928 5.84944L0.713291 4.98125C0.460898 4.76974 0.427757 4.39367 0.63927 4.14127C0.742143 4.01852 0.890075 3.94231 1.04975 3.92981L4.215 3.6821C4.43862 3.6646 4.6335 3.52309 4.71934 3.31586L5.94044 0.368212C6.06647 0.0639811 6.41526 -0.0804784 6.7195 0.0455524C6.86558 0.106068 6.98164 0.222131 7.04215 0.368212L8.26325 3.31586C8.34909 3.52309 8.54397 3.6646 8.76759 3.6821L11.9502 3.93117C12.2785 3.95687 12.5238 4.24383 12.4982 4.57213C12.4858 4.73006 12.4111 4.87658 12.2905 4.97936L9.86327 7.04866C9.6924 7.19433 9.61785 7.42365 9.6704 7.64195L10.4166 10.7419C10.4937 11.0621 10.2966 11.3841 9.97647 11.4611C9.82263 11.4982 9.66038 11.4725 9.52545 11.3899L6.80277 9.72194C6.61163 9.60485 6.37097 9.60485 6.17983 9.72194Z"

                if path_d == expected_d:
                    logging.info(
                        f"Account {self.serial_number}: stars_icon found and matches expected shape, nothing more to do.")
                    self.sleep(2, 4)
                    return
                else:
                    logging.info(
                        f"Account {self.serial_number}: stars_icon found but does not match expected shape, proceeding to create stars.")
            except (TimeoutException, NoSuchElementException):
                logging.info(f"Account {self.serial_number}: stars_icon not found, proceeding to create stars.")

            # Если дошли сюда, значит либо иконка не найдена, либо не соответствует ожидаемой
            self.sleep(3, 5)
            create_stars_button = self.wait_for_element(
                By.XPATH,
                "/html[1]/body[1]/div[2]/div[3]/div[2]/div[1]/div[1]/div[3]/button[1]"
            )
            create_stars_button.click()
            logging.info(f"Account {self.serial_number}: create_stars button clicked.")
            self.sleep(3, 5)

        except Exception as e:
            logging.info(f"Account {self.serial_number}: Error in add_stars: {e}")

    def check_claim_stardust_and_add_stars(self):
        stage = 0
        try:
            # Считываем текст звёздной пыли/кнопки
            howMany_StarDust_text = self.wait_for_element(
                By.XPATH,
                '/html/body/div[2]/div[1]/div/div[4]/a[2]/span'
            ).text.strip()

            # Проверяем, является ли текст числом с процентов
            if howMany_StarDust_text.endswith('%'):
                # Преобразуем значение к целому числу, удаляя символ '%'
                howMany_StarDust = int(howMany_StarDust_text.replace('%', ''))
                logging.info(f"Account {self.serial_number}: Current stardust level: {howMany_StarDust}%")

                if howMany_StarDust >= 0:
                    # Уровень пыли >= 20%, кликаем по claim без проверки текста
                    claim_button = self.wait_for_element(
                        By.XPATH,
                        '/html[1]/body[1]/div[2]/div[1]/div[1]/div[4]/a[2]'
                    )
                    claim_button.click()
                    logging.info(f"Account {self.serial_number}: Claimed stardust at {howMany_StarDust}%")
                    self.sleep(2, 5)

                    if self.scrshot:
                        self.driver.save_screenshot(f'screen{self.scrshot}.png')
                        logging.info(f"Account {self.serial_number}: Screenshot saved.")
                        self.scrshot += 1

                    stage += 1
                    self.add_stars()
                else:
                    # Если меньше 20%
                    logging.info(
                        f"Account {self.serial_number}: Stardust only {howMany_StarDust}%, skipping claim and add_stars.")
                    self.sleep(3, 5)
            else:
                # Если текст не заканчивается на '%', проверяем что там
                if howMany_StarDust_text == "Collect stardust":
                    # Если текст "Collect stardust" - кликаем
                    claim_button = self.wait_for_element(
                        By.XPATH,
                        '/html[1]/body[1]/div[2]/div[1]/div[1]/div[4]/a[2]'
                    )
                    claim_button.click()
                    logging.info(f"Account {self.serial_number}: Claimed stardust because text was 'Collect stardust'")
                    self.sleep(2, 5)

                    if self.scrshot:
                        self.driver.save_screenshot(f'screen{self.scrshot}.png')
                        logging.info(f"Account {self.serial_number}: Screenshot saved.")
                        self.scrshot += 1

                    stage += 1
                    self.add_stars()
                else:
                    # Если текст и не '%', и не 'Collect stardust', то просто логируем
                    logging.info(
                        f"Account {self.serial_number}: Unrecognized stardust text '{howMany_StarDust_text}', skipping claim and add_stars.")
                    self.sleep(2, 4)

        except Exception as e:
            logging.info(f"Account {self.serial_number}: Error while checking stardust: {e}")




def read_accounts_from_file():
    with open('accounts_tinyVerse.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]


def write_accounts_to_file(accounts):
    with open('accounts_tinyVerse.txt', 'w') as file:
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
            remove_key_lines('locked_accounts.txt', 'TINY')

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


            else:

                while retry_count < 3 and not success:
                    lock_account(accounts[i - 1], 'TINY')
                    bot = TelegramBotAutomation(accounts[i - 1])
                    bot.scrshot = 0  # 0 for no screenshots
                    try:
                        delete_oldScreens()
                        bot.navigate_to_bot()
                        bot.send_message("https://t.me/malenkaygalaktikadao")
                        bot.click_link()
                        bot.first_try()
                        bot.click_home()
                        bot.check_claim_stardust_and_add_stars()
                        logging.info(f"Account {accounts[i - 1]}: Processing completed successfully.")
                        success = True
                    except Exception as e:
                        logging.warning(f"Account {accounts[i - 1]}: Error occurred on attempt {retry_count + 1}: {e}")
                        retry_count += 1
                    finally:
                        logging.info("-------------END-----------")
                        bot.browser_manager.close_browser()
                        logging.info("-------------END-----------")
                        unlock_account(accounts[i - 1], "TINY")
                        sleep_time = random.randrange(4, 6)
                        logging.info(f"Sleeping for {sleep_time} seconds.")
                        time.sleep(sleep_time)

                    if retry_count >= 3:
                        logging.warning(f"Account {accounts[i - 1]}: Failed after 3 attempts.")

            if not success:
                logging.warning(f"Account {accounts[i - 1]}: Moving to next account after 3 failed attempts.")

        logging.info("All accounts processed. Waiting 1 hour before restarting.")

        for hour in range(4):
            logging.info(f"Waiting... {4 - hour} hour left till restart.")
            time.sleep(60 * 60)

        logging.info("Shuffling accounts for the next cycle.")


if __name__ == "__main__":
    process_accounts()