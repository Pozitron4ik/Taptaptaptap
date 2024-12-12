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

debug = False

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
            logging.exception(f"Account {self.serial_number}: General Exception occurred when trying to close the browser: {str(e)}")
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
                logging.exception(f"Account {self.serial_number}: Exception occurred when trying to close the browser: {str(e)}")

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
        chat_input_area = self.wait_for_element(By.XPATH, '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/input[1]')
        chat_input_area.click()
        chat_input_area.send_keys(message)

        search_area = self.wait_for_element(By.XPATH, '/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/ul[1]/a[1]/div[1]')
        search_area.click()
        logging.info(f"Account {self.serial_number}: Group searched.")

    def click_link(self):
        link = self.wait_for_element(By.CSS_SELECTOR, "a[href*='t.me/catsdogs_game_bot/join?startapp=452987344']")
        link.click()
        
        #После последней обновы 31.08.24 закомментил
        #launch_click = self.wait_for_element(By.XPATH, "//body/div[@class='popup popup-peer popup-confirmation active']/div[@class='popup-container z-depth-1']/div[@class='popup-buttons']/button[1]/div[1]")
        #launch_click.click()
        logging.info(f"Account {self.serial_number}: CATDOG STARTED")
        sleep_time = random.randrange(6, 12)
        logging.info(f"Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        if not self.switch_to_iframe():
            logging.info(f"Account {self.serial_number}: No iframes found")
            return

    def firstRun(self):
        stage=0
        try:
            cont = self.wait_for_element(By.XPATH,
                                        '/html/body/div/div[2]/div[2]/div[3]/button'
                                        #'body > div > div.flex.h-svh.w-svw.flex-col.justify-between.p-4 > div.flex.absolute.top-0.right-0.bottom-0.left-0.flex-col.justify-between.py-8.px-4 > div:nth-child(3) > button'
                                        )
            self.driver.execute_script("arguments[0].scrollIntoView();", cont)
            cont.click()
            logging.info(f"Account {self.serial_number}: clicked continue")
            self.sleep(2, 4)
            stage+=1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant click continue, {str(e), stage}")
        
        if stage:
            animals = [0, 0]
            i = 0
            try:
                while i<2:
                    animals[i] = self.wait_for_element(By.XPATH,
                                                    f'/html/body/div/div[2]/div[2]/div[2]/div[{i+1}]'
                                                    )
                    logging.info(f"Account {self.serial_number}: found {animals[i].text}")
                    i+=1
                choice = random.choice(animals)
                self.driver.execute_script("arguments[0].click();", choice)
                logging.info(f"Account {self.serial_number}: clicked {choice.text}")
                self.sleep(2, 4)
                stage+=1
            except Exception as e:
                logging.info(f"Account {self.serial_number}: cant chose,  {str(e), stage}")

        if stage>1:
            try:
                cont = self.wait_for_element(By.XPATH,
                                            '/html/body/div/div[2]/div[2]/div[3]/button'
                                            )
                self.driver.execute_script("arguments[0].scrollIntoView();", cont)
                self.driver.execute_script("arguments[0].click();", cont)
                logging.info(f"Account {self.serial_number}: clicked continue")
                self.sleep(2, 4)
            except Exception as e:
                logging.info(f"Account {self.serial_number}: cant click continue, {str(e), stage}")

    def claim(self):
        try:
            claimBut = self.wait_for_element(By.XPATH,
                                             '/html/body/div[1]/div[2]/div[1]/div/div[2]/button'
                                             )
            claimBut.click()
            logging.info(f"Account {self.serial_number}: claimed")
            self.sleep(2, 4)
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant claim, {str(e)}")

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
    
    def reboot(self):
        logging.info(f"Account {self.serial_number}: rebooting...")
        try:
            self.driver.switch_to.default_content()
            menu = self.wait_for_element(By.XPATH,
                                         '/html/body/div[6]/div/div[1]/div[1]/div/div[2]/button[1]/span[1]'
                                         )
            menu.click()
            self.driver.switch_to.default_content()
            time.sleep(2)
            reload = self.wait_for_element(By.XPATH,
                                           # #page-chats > div.btn-menu.contextmenu.bottom-center.active.was-open > div:nth-child(2)
                                           '/html/body/div[1]/div[3]/div[2]'
                                           )
            reload.click()
            self.sleep(4, 6)
            self.switch_to_iframe()
            self.check_and_go_back()

        except Exception as e:
            logging.info(f"Account {self.serial_number}: error rebooting")
  
    def wait_for_element(self, by, value, timeout=10):
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )

    def wait_for_elements(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_all_elements_located((by, value))
        )

    



def read_accounts_from_file():
    with open('../../farmilki-maiN/farmilki-main/accounts_catdog.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]

def write_accounts_to_file(accounts):
    with open('../../farmilki-maiN/farmilki-main/accounts_catdog.txt', 'w') as file:
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
            remove_key_lines('locked_accounts.txt', 'KOTOPES')
            
            retry_count = 0
            i+=1
            success = False
            if is_account_locked(accounts[i-1]):
                if i == len(accounts):
                    retry_count = 3            
                else:
                    accounts.append(accounts[i-1])
                    accounts.pop(i-1)
                    print(accounts)
                    i-=1
                #здесь выход в новую итерацию цикла со следующего элемента
            
            else:
                
                while retry_count < 3 and not success:
                    lock_account(accounts[i-1], 'KOTOPES' )
                    bot = TelegramBotAutomation(accounts[i-1])
                    bot.scrshot = 0 #0 for no screenshots
                    try:
                        delete_oldScreens()
                        bot.navigate_to_bot()
                        bot.send_message("https://t.me/huihuisdf1488sdfks")
                        bot.click_link()
                        time.sleep(1)
                        bot.firstRun()
                        bot.claim()
                    
                        logging.info(f"Account {accounts[i-1]}: Processing completed successfully.")
                        success = True  
                    except Exception as e:
                        logging.warning(f"Account {accounts[i-1]}: Error occurred on attempt {retry_count + 1}: {e}")
                        retry_count += 1  
                    finally:
                        logging.info("-------------END-----------")
                        bot.browser_manager.close_browser()
                        logging.info("-------------END-----------")
                        unlock_account(accounts[i-1], "KOTOPES")
                        sleep_time = random.randrange(5, 15)
                        logging.info(f"Sleeping for {sleep_time} seconds.")
                        time.sleep(sleep_time)
                    
                    if retry_count >= 3:
                        logging.warning(f"Account {accounts[i-1]}: Failed after 3 attempts.")
                

            if not success:
                logging.warning(f"Account {accounts[i-1]}: Moving to next account after 3 failed attempts.")
                

            

        

        logging.info("All accounts processed. Waiting 4 hours before restarting.")

        for hour in range(4):
            logging.info(f"Waiting... {4 - hour} hours left till restart.")
            time.sleep(60 * 60)  

        
        logging.info("Shuffling accounts for the next cycle.")

if __name__ == "__main__":
    process_accounts()
