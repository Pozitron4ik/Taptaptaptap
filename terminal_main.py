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

logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

debug = True


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

    def navigate_to_bot(self, message):
        try:
            self.driver.get('https://web.telegram.org/a/')
            logging.info(f"Account {self.serial_number}: Navigated to Telegram web.")
            chat_input_area = self.wait_for_element(By.XPATH,
                                                    # '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/input[1]'
                                                    '//*[@id="telegram-search-input"]'
                                                    )
            chat_input_area.click()
            chat_input_area.send_keys(message)

            time.sleep(1)
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1

            search_area = self.wait_for_element(By.XPATH,
                                                #   '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/ul[1]/a[1]/div[1]'
                                                '//*[@id="LeftColumn-main"]/div[2]/div[2]/div/div[2]/div/div[2]/div/div'
                                                )
            search_area.click()

            logging.info(f"Account {self.serial_number}: bot searched.")

            time.sleep(2)

            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1


        except Exception as e:
            logging.exception(f"Account {self.serial_number}: Exception in navigating to Telegram bot: {str(e)}")
            self.browser_manager.close_browser()

    def start_game(self):
        try:
            play = self.wait_for_element(By.XPATH,
                                         '//*[@id="MiddleColumn"]/div[3]/div[2]/div/div[2]/div[1]/div[2]/div/button[1]'
                                         )
            play.click()

            logging.info(f"Account {self.serial_number}: clicked play.")
            self.sleep(7, 15)

            self.switch_to_iframe()

            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1

        except Exception as e:
            logging.exception(f"Account {self.serial_number}: {str(e)}")
            self.browser_manager.close_browser()

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

    def moneyButton(self):
        try:
            i = 0
            while i < 3:
                button1 = self.wait_for_element(By.XPATH,
                                                '/html/body/div[1]/div/main/div/div[2]/button'
                                                )
                self.driver.execute_script("arguments[0].scrollIntoView();", button1)
                button1.click()
                time.sleep(2)
                if self.scrshot:
                    self.driver.save_screenshot(f'screen{self.scrshot}.png')
                    self.scrshot += 1
                logging.exception(f"Account {self.serial_number}: clicked continue")
                i += 1
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: {str(e)}")

    def code(self, sequence):
        success = False
        if len(sequence) != 6:
            logging.exception(f"Account {self.serial_number}: sequence length must be 6")
            return
        try:
            input = self.wait_for_element(By.XPATH,
                                          '/html/body/div[1]/div/main/main/section[1]/div/div[1]/input'
                                          )
            input.send_keys(sequence)
            logging.info(f"Account {self.serial_number}: input ok")
            success = True
            self.sleep(3, 5)
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant input, {str(e)}")

        if success:
            try:
                verify = self.wait_for_element(By.XPATH,
                                               '/html/body/div[1]/div/main/main/section[1]/div/div[2]/div/button'
                                               # "#main > div > main > main > section:nth-child(1) > div > div.flex.overflow-hidden.text-black > div > button"
                                               )
                verify.click()
                logging.info(f"Account {self.serial_number}: verified ok")
                self.sleep(2, 4)
            except Exception as e:
                logging.info(f"Account {self.serial_number}: cant verify, {str(e)}")

    def dontlose(self):
        try:
            take = self.wait_for_element(By.XPATH,
                                         '/html/body/div[6]/div[3]/div/a'
                                         # "#radix-\:r6\: > div.relative.overflow-auto.pb-32 > div > a"
                                         )
            take.click()
            logging.info(f"Account {self.serial_number}: took 4000 trmnl")
            self.sleep(3, 5)
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: cant take 4000 trmnl, {str(e)}")

    def push(self):
        try:
            pushBut = self.wait_for_element(By.XPATH,
                                            '/html/body/div[1]/div/footer/div[2]/div[3]/a/div'
                                            )
            pushBut.click()
            logging.info(f"Account {self.serial_number}: push")
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: cant push, {str(e)}")

    def claim(self):
        try:
            mainBut = self.wait_for_element(By.CSS_SELECTOR,
                                            "#main > div > main > main > section.flex.grow.flex-col.items-center.justify-center.gap-y-2xl > div.flex.h-\[14\.6875rem\].items-center.justify-center > button"
                                            )
            self.driver.execute_script("arguments[0].scrollIntoView();", mainBut)
            self.driver.execute_script("arguments[0].click();", mainBut)
            logging.info(f"Account {self.serial_number}: claimed")
            self.sleep(5, 7)
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: cant claim, {str(e)}")

    def tap(self):
        self.sleep(5, 10)
        actions = ActionChains(self.driver)
        actions.move_by_offset(175, 505).click().perform()
        logging.info(f"Account {self.serial_number}: tapped")
        self.sleep(5, 6)
        if self.scrshot:
            self.driver.save_screenshot(f'screen{self.scrshot}.png')
            self.scrshot += 1

    def wait_for_element(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def wait_for_elements(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_all_elements_located((by, value))
        )


def read_accounts_from_file():
    with open('accounts_terminal.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]


def write_accounts_to_file(accounts):
    with open('accounts_terminal.txt', 'w') as file:
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
            remove_key_lines('locked_accounts.txt', 'TERMINAL')

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
                    lock_account(accounts[i - 1], 'TERMINAL')
                    bot = TelegramBotAutomation(accounts[i - 1])
                    bot.scrshot = 0  # 0 for no screenshots
                    try:
                        # delete_oldScreens()
                        bot.navigate_to_bot("@terminalgame_bot")
                        bot.start_game()
                        # bot.moneyButton()
                        bot.dontlose()
                        bot.code("123456")
                        bot.push()
                        bot.claim()

                        logging.info(f"Account {accounts[i - 1]}: Processing completed successfully.")
                        success = True
                    except Exception as e:
                        logging.warning(f"Account {accounts[i - 1]}: Error occurred on attempt {retry_count + 1}: {e}")
                        retry_count += 1
                    finally:

                        logging.info("-------------END-----------")
                        bot.browser_manager.close_browser()
                        logging.info("-------------END-----------")
                        sleep_time = random.randrange(5, 15)
                        unlock_account(accounts[i - 1], "TERMINAL")
                        logging.info(f"Sleeping for {sleep_time} seconds.")
                        time.sleep(sleep_time)

                    if retry_count >= 3:
                        logging.warning(f"Account {accounts[i - 1]}: Failed after 3 attempts.")
                        remove_key_lines('locked_accounts.txt', 'TERMINAL')

            if not success:
                logging.warning(f"Account {accounts[i - 1]}: Moving to next account after 3 failed attempts.")

        logging.info("All accounts processed. Waiting 6 hours before restarting.")

        for hour in range(12):
            logging.info(f"Waiting... {12 - hour} hours left till restart.")
            time.sleep(60 * 60)

        logging.info("Shuffling accounts for the next cycle.")


if __name__ == "__main__":
    process_accounts()