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

    def __init__(self):
        self.serial_number = 206 #аккаунт в адс
        self.driver = None

    def check_browser_status(self):
        try:
            response = requests.get(
                'http://local.adspower.net:50325/api/v1/browser/active',
                params={'serial_number': self.serial_number}
            )
            data = response.json()
            if data['code'] == 0 and data['data']['status'] == 'Active':
                logging.info(f"{self.serial_number}: Browser is already active.")
                return True
            else:
                return False
        except Exception as e:
            logging.exception(f"{self.serial_number}: Exception in checking browser status: {str(e)}")
            return False

    def start_browser(self):
        try:
            if self.check_browser_status():
                logging.info(f"{self.serial_number}: Browser already open. Closing the existing browser.")
                self.close_browser()
                time.sleep(20)

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
                chrome_options.add_argument("--remote-debugging-port=9222")  # Важно для взаимодействия
                service = Service(executable_path=webdriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.set_window_size(600, 900)
                logging.info(f"{self.serial_number}: Browser started successfully.")
                return True
            else:
                logging.warning(f"{self.serial_number}: Failed to start the browser. Error: {data['msg']}")
                return False
        except Exception as e:
            logging.exception(f"{self.serial_number}: Exception in starting browser: {str(e)}")
            return False

    def close_browser(self):
        try:
            if self.driver:
                try:
                    self.driver.close()
                    self.driver.quit()
                    self.driver = None
                    logging.info(f"{self.serial_number}: Browser closed successfully.")
                except WebDriverException as e:
                    logging.info(f"{self.serial_number}: exception, Browser should be closed now")
        except Exception as e:
            logging.exception(
                f"{self.serial_number}: General Exception occurred when trying to close the browser: {str(e)}")
        finally:
            try:
                response = requests.get(
                    'http://local.adspower.net:50325/api/v1/browser/stop',
                    params={'serial_number': self.serial_number}
                )
                data = response.json()
                if data['code'] == 0:
                    logging.info(f"{self.serial_number}: Browser closed successfully.")
                else:
                    logging.info(f"{self.serial_number}: exception, Browser should be closed now")
            except Exception as e:
                logging.exception(
                    f"{self.serial_number}: Exception occurred when trying to close the browser: {str(e)}")



class Automation():
    def __init__(self):
        self.browser_manager = BrowserManager()
        logging.info(f"Initializing automation")
        self.browser_manager.start_browser()
        self.driver = self.browser_manager.driver

    def __del__(self):
        self.browser_manager.close_browser()
        logging.info("Object deleted")
        time.sleep(20)

    def wait_for_element(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def wait_for_elements(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_all_elements_located((by, value))
        )

    def switch_to_iframe(self):
        self.driver.switch_to.default_content()
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            self.driver.switch_to.frame(iframes[0])
            return True
        return False

    def sleep(self, a, b):
        sleep_time = random.randrange(a, b)
        logging.info(f"{sleep_time}sec sleep...")
        time.sleep(sleep_time)

    def addon(self, password):
        try:
            all_windows = self.driver.window_handles
            self.driver.switch_to.window(all_windows[-1])
            confirm = self.wait_for_element(By.XPATH,
                                            '/html/body/div[2]/div/div/div/div/div[3]/form/div[4]/button[2]'
                                            )
            confirm.click()
            self.sleep(1,3)
            success = True
        except Exception as e:
            success = False
            logging.info("error in confirming.")
        try:
            check = self.wait_for_element(By.XPATH, 
                                        '/html/body/div[2]/div/div/div/div/div[3]/form/div[1]/h2'
                                        )
            if check.text == "Недостаточно средств":
                logging.info("no money bro")
                succes = False
        except Exception as e:
            success = True

        if success:
            try:
                passwordInput = self.wait_for_element(By.XPATH,
                                                      '/html/body/div[2]/div[2]/div/div/div/div[3]/form/div[1]/div/input'
                                                      )
                passwordInput.send_keys(password + Keys.ENTER)
                logging.info(f"input ok: {password}")
                self.sleep(1,2)
                success = True
            except Exception as e:
                success = False
                logging.info("error in confirming.")

        
        if success:
            try:
                tabs = self.driver.window_handles
                logging.info(f"Found {len(tabs)} tabs")

                for tab in tabs:
                    try:
                        self.driver.switch_to.window(tab)
                        
                        current_url = self.driver.current_url
                        logging.info(f"Tab {tab} has URL {current_url}")
                        
                        if "fragment.com/stars" in current_url:
                            main_tab = tab
                            logging.info(f"Found Fragment tab: {tab}")
                            break
                    except Exception as e:
                        logging.warning(f"Error '{str(e)}' on tab {tab}")

            except Exception as e:
                logging.error(f"Error '{str(e)}' while handling tabs")
        return success

    
    def Fragment1(self, recepient_tg, howmanystars):
        success = False
        try:
            self.driver.get("https://fragment.com/stars")
            self.driver.switch_to.default_content()
            logging.info(f"openned fragment.")
            self.sleep(2,3)
            success = True
        except Exception as e:
            logging.info(f"cant open fragment")
            self.browser_manager.close_browser()
        
        if success:
            try:
                recepient = self.wait_for_element(By.XPATH,
                                                  '/html[1]/body[1]/div[2]/main[1]/form[1]/div[1]/div[2]/input[1]'
                                                  )
                recepient.send_keys(recepient_tg)
                logging.info(f"input {recepient_tg} ok")
                self.sleep(2,3)
                success = True
            except Exception as e:
                success = False
                logging.info("cant input tg id")
        
        if success:
            try:
                howmanyInput = self.wait_for_element(By.XPATH,
                                                     '/html[1]/body[1]/div[2]/main[1]/form[1]/div[2]/div[1]/input[1]'
                                                     )
                howmanyInput.send_keys(howmanystars)
                logging.info(f"input {howmanystars} ok")
                self.sleep(2,3)
                success = True
            except Exception as e:
                success = False
                logging.info(f"cant input stars")
        
        if success:
            try:
                buy = self.wait_for_element(By.XPATH,
                                            '/html/body/div[2]/main/div/button'
                                            )
                self.driver.execute_script("arguments[0].scrollIntoView();", buy)
                buy.click()
                logging.info(f"clicked buy")
                self.sleep(2,3)
                success = True
            except Exception as e:
                success = False
                logging.info(f"cant buy")

        if success:
            try:
                Galochka = self.wait_for_element(By.XPATH,
                                            '/html/body/div[2]/div/div/div/section/form/label'
                                            )
                Galochka.click()
                logging.info(f"clicked Galochka")
                self.sleep(2,3)
                success = True
            except Exception as e:
                success = False
                logging.info(f"cant click Galochka")
        
        if success:
            try:
                confirm = self.wait_for_element(By.XPATH,
                                                '/html/body/div[2]/div/div/div/section/form/div/button'
                                                )
                confirm.click()
                logging.info(f"confirmed")

                self.sleep(2,3)
                success = True
            except Exception as e:
                success = False
                logging.info(f"cant confirm")

    def wait(self):
        i = 0
        self.sleep(30, 35)
        while i < 3:
            i+=1
            

            try:
                buymore = self.wait_for_element(By.CSS_SELECTOR,
                                      '#aj_content > main > section.tm-main-intro-buttons > a'
                                      )
                buymore.click()
                logging.info(f"clicked buy more")
                return True
            except Exception as e:
                self.sleep(5, 10)
        return False

def read_accounts_from_file():
    with open('accounts_stars.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]

def run():
    bot = Automation()
    deleted = False
    accounts = read_accounts_from_file()
    for account in accounts:
        retry = 0
        success = False
        while retry < 3 and not success:
            try:
                if deleted:
                    bot = Automation()
                bot.Fragment1(account, 250) #кол-во звезд
                if not bot.addon("10011983"): #пароль
                    del bot
                    deleted = True
            except Exception as e:
                logging.warning("error")
                if not deleted:
                    del bot
                    deleted = True
            finally:
                logging.info("----end----")
                if not deleted:
                    if not bot.wait():
                        del bot
                        deleted = True
                    else:
                        success = True
            retry += 1
    del bot

if __name__ == "__main__":
    run()