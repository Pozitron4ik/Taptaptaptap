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
        link = self.wait_for_element(By.CSS_SELECTOR, "a[href*='https://t.me/PAWSOG_bot/PAWS?startapp']")
        link.click()

        # После последней обновы 31.08.24 закомментил
        # launch_click = self.wait_for_element(By.XPATH, "//body/div[@class='popup popup-peer popup-confirmation active']/div[@class='popup-container z-depth-1']/div[@class='popup-buttons']/button[1]/div[1]")
        # launch_click.click()
        logging.info(f"Account {self.serial_number}: PAWS STARTED")
        sleep_time = random.randrange(5, 8)
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

    def switch_tabs(self, main_tab_url, target_url):
        """
        Переключение между вкладками:
        - Закрываем только ненужные вкладки (например, с URL ненужного контекста).
        - Возвращаемся к вкладке с `target_url`.
        """
        try:
            tabs = self.driver.window_handles
            logging.info(f"Account {self.serial_number}: {len(tabs)} tabs open.")

            main_tab = None
            target_tab = None

            for tab in tabs:
                try:
                    self.driver.switch_to.window(tab)
                    current_url = self.driver.current_url
                    logging.info(f"Account {self.serial_number}: Tab {tab} has URL {current_url}")

                    # Определяем основную вкладку
                    if current_url == main_tab_url:
                        main_tab = tab
                        logging.info(f"Account {self.serial_number}: Found main tab: {tab}")
                    # Определяем целевую вкладку
                    elif current_url == target_url:
                        target_tab = tab
                        logging.info(f"Account {self.serial_number}: Found target tab: {tab}")
                    # Закрываем ненужные вкладки
                    elif "x.com" in current_url:  # Условие для ненужных вкладок
                        self.driver.close()
                        logging.info(f"Account {self.serial_number}: Closed tab with URL {current_url}")
                except Exception as e:
                    logging.info(f"Account {self.serial_number}: Error '{str(e)}' on tab {tab}")

            # Переключаемся на целевую вкладку, если она найдена
            if target_tab:
                self.driver.switch_to.window(target_tab)
                logging.info(f"Account {self.serial_number}: Switched to target tab: {target_tab}")
            # Если целевая вкладка не найдена, возвращаемся на основную
            elif main_tab:
                self.driver.switch_to.window(main_tab)
                logging.info(f"Account {self.serial_number}: Switched back to main tab: {main_tab}")
            else:
                logging.error(f"Account {self.serial_number}: Target tab not found.")

            self.switch_to_iframe()  # Возврат в iframe, если требуется
        except Exception as e:
            logging.error(f"Account {self.serial_number}: Error in switch_tabs: {e}")

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

    def earn(self):
        try:
            butEarn = self.wait_for_element(By.XPATH,
                                             '/html[1]/body[1]/div[1]/div[1]/div[1]/div[5]/div[3]/div[5]'
                                             )
            butEarn.click()
            self.sleep(3, 4)
            logging.info(f"Account {self.serial_number}: clicked Earn")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e)}")

    def limited_questX(self):
        try:
            butQuest1 = self.wait_for_element(By.XPATH,
                                              '/html/body/div/div/div/div[5]/div[2]/div[4]/div/div[3]/div[2]/div[2]')
            butQuest1.click()
            logging.info(f"Account {self.serial_number}: Clicked Heart button.")
            self.sleep(2, 4)

            # Переключаем вкладку
            self.switch_tabs(self.main_tab_url, "https://web.telegram.org/k/#@pawslovedengi")
            self.sleep(3, 6)

            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                logging.info(f"Account {self.serial_number}: Screenshot saved.")
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: Error in mysteryquest1: {e}")


    def Claim_limited_questX(self):
        try:
            butClaim = self.wait_for_element(By.XPATH,
                                            '/html[1]/body[1]/div[1]/div[1]/div[1]/div[5]/div[2]/div[4]/div[1]/div[3]/div[1]/div[2]/div[1]'
                                            )
            butClaim.click()
            self.sleep(2, 4)
            logging.info(f"Account {self.serial_number}: clicked Claim")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e)}")

    def limited_quest2(self):
        try:
            butQuest2 = self.wait_for_element(By.XPATH,
                                              '/html[1]/body[1]/div[1]/div[1]/div[1]/div[5]/div[2]/div[4]/div[1]/div[3]/div[2]/div[2]/div[1]')
            butQuest2.click()
            logging.info(f"Account {self.serial_number}: Clicked Heart button.")
            self.sleep(2, 4)

            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                logging.info(f"Account {self.serial_number}: Screenshot saved.")
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: Error in mysteryquest1: {e}")

    def Claim_limited_quest2(self):
        try:
            butClaim2 = self.wait_for_element(By.XPATH,
                                            '/html[1]/body[1]/div[1]/div[1]/div[1]/div[5]/div[2]/div[4]/div[1]/div[3]/div[2]/div[2]/div[1]'
                                            )
            butClaim2.click()
            logging.info(f"Account {self.serial_number}: clicked Claim")
            self.sleep(3, 5)
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e)}")

    def check_and_click_buttons(self):

        try:
            self.sleep(3, 5)
            # Проверяем наличие первой кнопки
            first_button_xpath = '/html[1]/body[1]/div[1]/div[1]/div[1]/div[2]/div[5]'
            first_buttons = self.driver.find_elements(By.XPATH, first_button_xpath)
            if first_buttons:
                first_button = first_buttons[0]
                self.driver.execute_script("arguments[0].scrollIntoView();", first_button)
                first_button.click()
                logging.info(f"Account {self.serial_number}: Let's start clicked.")
                self.sleep(8, 11)
                second_button_xpath = '/html[1]/body[1]/div[1]/div[1]/div[1]/div[4]/div[4]'
                second_buttons = self.driver.find_elements(By.XPATH, second_button_xpath)
                if second_buttons:
                    second_button = second_buttons[0]
                    self.driver.execute_script("arguments[0].scrollIntoView();", second_button)
                    second_button.click()
                    logging.info(f"Account {self.serial_number}: Gotcha is clicked .")
                else:
                    logging.info(f"Account {self.serial_number}: Gotcha is not found.")
            else:
                logging.info(f"Account {self.serial_number}: Let's start is not found.")
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Ошибка в check_and_click_buttons: {str(e)}")

    def click_combination(self, combination):
        try:
            # Инициализируем список кнопок
            buttons = []
            for k in range(1, 6):  # k от 1 до 5
                try:
                    button = self.wait_for_element(
                        By.XPATH,
                        f'/html[1]/body[1]/div[1]/div[1]/div[1]/div[5]/div[3]/div[{k}]'
                    )
                    buttons.append(button)
                except Exception as e:
                    logging.info(f"Account {self.serial_number}: Не удалось найти кнопку {k}: {str(e)}")
                    return False

            # Нажимаем кнопки в заданной комбинации
            for pos in combination:
                try:
                    btn = buttons[pos - 1]  # Индексация списка начинается с 0
                    self.driver.execute_script("arguments[0].scrollIntoView();", btn)
                    btn.click()
                    logging.info(f"Account {self.serial_number}: Clicked button on position {pos}")
                    self.sleep(1, 3)
                except Exception as e:
                    logging.info(f"Account {self.serial_number}: Error in clicked {pos}: {str(e)}")
                    return False

            # Добавляем явный возврат True после успешного выполнения
            return True

        except Exception as e:
            logging.info(f"Account {self.serial_number}: Complex Error in click_combination: {str(e)}")
            return False

    def Claim_all_limited_quest(self):

        try:
            button_xpaths = []
            N = 1
            while True:
                xpath = f'/html/body/div/div/div/div[5]/div[2]/div[4]/div/div[3]/div[{N}]/div[2]'
                try:
                    self.driver.find_element(By.XPATH, xpath)
                    button_xpaths.append(xpath)
                    logging.info(f"Account {self.serial_number}: Кнопка {N} найдена и добавлена в список.")
                    N += 1
                except NoSuchElementException:
                    logging.info(f"Account {self.serial_number}: Больше нет кнопок после N={N - 1}.")
                    break

            if not button_xpaths:
                logging.info(f"Account {self.serial_number}: Кнопки для нажатия не найдены.")
                return

            for idx, xpath in enumerate(button_xpaths):
                try:
                    button = self.wait_for_element(By.XPATH, xpath)
                    self.driver.execute_script("arguments[0].scrollIntoView();", button)
                    button.click()
                    logging.info(f"Account {self.serial_number}: Нажата кнопка {idx + 1} в первом круге.")
                    # self.switch_tabs(self.main_tab_url, "https://web.telegram.org/k/#@pawsupfam")
                    # self.sleep(3, 6)
                    self.sleep(2, 3)
                except Exception as e:
                    logging.warning(
                        f"Account {self.serial_number}: Не удалось нажать кнопку {idx + 1} в первом круге: {e}")

            # for idx, xpath in enumerate(button_xpaths):
            #     try:
            #         button = self.wait_for_element(By.XPATH, xpath)
            #         self.driver.execute_script("arguments[0].scrollIntoView();", button)
            #         button.click()
            #         logging.info(f"Account {self.serial_number}: Нажата кнопка {idx + 1} во втором круге.")
            #         self.sleep(2, 3)
            #     except Exception as e:
            #         logging.warning(
            #             f"Account {self.serial_number}: Не удалось нажать кнопку {idx + 1} во втором круге: {e}")

            logging.info(f"Account {self.serial_number}: Функция Claim_all_limited_quest завершена.")

        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Произошла ошибка в Claim_all_limited_quest: {e}")


    def Claim_Phone(self):
        try:
            self.sleep(3, 4)
            butClaim3 = self.wait_for_element(By.CSS_SELECTOR,
                                            '#next-app > div.main-page-con > div.main-content-container.is-show > div.main-content-wrapper > div.quests-tab-con.is-show > div > div.section-items-con.quests > div:nth-child(3) > div.points > div.start-btn.claim'
                                            )
            butClaim3.click()
            logging.info(f"Account {self.serial_number}: clicked Claim")
            self.sleep(2, 3)
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e)}")



def read_accounts_from_file():
    with open('accounts_paws.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]


def write_accounts_to_file(accounts):
    with open('accounts_paws.txt', 'w') as file:
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
            remove_key_lines('locked_accounts.txt', 'PAWS')

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
                    lock_account(accounts[i - 1], 'PAWS')
                    bot = TelegramBotAutomation(accounts[i - 1])
                    bot.scrshot = 0  # 0 for no screenshots
                    try:
                        delete_oldScreens()
                        bot.navigate_to_bot()
                        bot.send_message("https://t.me/lapkerydengidao")
                        bot.click_link()
                        bot.check_and_click_buttons()
                        bot.earn()
                        bot.Claim_all_limited_quest()
                        # bot.limited_questX()
                       #bot.limited_quest2()
                       #bot.Claim_limited_questX()
                       #bot.Claim_limited_quest2()
                        # combination = [2, 1, 2, 3, 5]  # комбинация
                        # if bot.click_combination(combination):
                        #     logging.info(f"Account {accounts[i - 1]}: Combination clicked successfully.")
                        # else:
                        #     logging.info(f"Account {accounts[i - 1]}: Error in clicking combination.")

                        # bot.Claim_Phone()
                        logging.info(f"Account {accounts[i - 1]}: Processing completed successfully.")
                        success = True
                    except Exception as e:
                        logging.warning(f"Account {accounts[i - 1]}: Error occurred on attempt {retry_count + 1}: {e}")
                        retry_count += 1
                    finally:
                        logging.info("-------------END-----------")
                        bot.browser_manager.close_browser()
                        logging.info("-------------END-----------")
                        unlock_account(accounts[i - 1], "PAWS")
                        sleep_time = random.randrange(4, 6)
                        logging.info(f"Sleeping for {sleep_time} seconds.")
                        time.sleep(sleep_time)

                    if retry_count >= 3:
                        logging.warning(f"Account {accounts[i - 1]}: Failed after 3 attempts.")

            if not success:
                logging.warning(f"Account {accounts[i - 1]}: Moving to next account after 3 failed attempts.")

        logging.info("All accounts processed. Waiting 1 hour before restarting.")

        for hour in range(1):
            logging.info(f"Waiting... {1 - hour} hour left till restart.")
            time.sleep(60 * 60)

        logging.info("Shuffling accounts for the next cycle.")


if __name__ == "__main__":
    process_accounts()