import requests
import os
import time
import logging
import json
import random
from forall import *
from baseClass import base
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class TelegramBotAutomation(base):
    def boost(self):
        try:
            boostBut = self.wait_for_element(By.CSS_SELECTOR,
                                            "#root > div.h-screen.bg-gradient-to-b.from-\[\#F7FFEB\].via-\[\#E4FFBE\].to-\[\#79B22A\].fixed.z-0.left-0.right-0.bottom-0.top-0.dark\:bg-none.dark\:bg-\[\#030C02\].max-w-md.mx-auto > div.fixed.left-0.right-0.bottom-0.z-40 > div > div > div:nth-child(2) > div > div:nth-child(3) > div"
                                            )
            boostBut.click()
            logging.info(f"Account {self.serial_number}: clicked boost")
            self.sleep(7, 9)
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant boost, {str(e)}")
    
    def tree(self):
        try:
            treeBut = self.wait_for_element(By.XPATH,
                                            '/html/body/div[1]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]'
                                            )
            
            self.driver.execute_script("arguments[0].click();", treeBut)
            logging.info(f"Account {self.serial_number}: clicked tree")
            self.sleep(7, 9)
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant click tree, {str(e)}")
    
    def upgrade(self):
        try:
            upgBut = self.wait_for_element(By.XPATH,
                                           '/html/body/div[1]/div[2]/div[1]/div[1]/div[7]/div[2]/div/button'
                                           )
            self.driver.execute_script("arguments[0].click();", upgBut)
            logging.info(f"Account {self.serial_number}: upgraded")
            self.sleep(7, 9)
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant upgrade, {str(e)}")

    
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
            remove_key_lines('locked_accounts.txt', 'WEEDUPG')

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
                    lock_account(accounts[i - 1], 'WEEDUPG')
                    bot = TelegramBotAutomation(accounts[i - 1])
                    bot.scrshot = 0  # 0 for no screenshots
                    try:
                        delete_oldScreens()
                        bot.navigate_to_bot()
                        bot.send_message("https://t.me/seeedgoidacoin")
                        bot.click_link('t.me/seed_coin_bot/app?startapp')
                        time.sleep(5)
                        bot.boost()
                        bot.tree()
                        bot.upgrade()
                        bot.tree()
                        bot.upgrade()

                        logging.info(f"Account {accounts[i - 1]}: Processing completed successfully.")
                        success = True
                    except Exception as e:
                        logging.warning(f"Account {accounts[i - 1]}: Error occurred on attempt {retry_count + 1}: {e}")
                        retry_count += 1
                    finally:
                        logging.info("-------------END-----------")
                        bot.browser_manager.close_browser()
                        logging.info("-------------END-----------")
                        unlock_account(accounts[i - 1], "WEEDUPG")
                        sleep_time = random.randrange(5, 15)
                        logging.info(f"Sleeping for {sleep_time} seconds.")
                        time.sleep(sleep_time)

                    if retry_count >= 3:
                        logging.warning(f"Account {accounts[i - 1]}: Failed after 3 attempts.")

            if not success:
                logging.warning(f"Account {accounts[i - 1]}: Moving to next account after 3 failed attempts.")

        logging.info("All accounts processed. Waiting 24 hours before restarting.")

        for hour in range(24):
            logging.info(f"Waiting... {24 - hour} hours left till restart.")
            time.sleep(60 * 60)

        logging.info("Shuffling accounts for the next cycle.")


if __name__ == "__main__":
    process_accounts()