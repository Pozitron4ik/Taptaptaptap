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
        link = self.wait_for_element(By.CSS_SELECTOR, "a[href*='https://t.me/Tomarket_ai_bot/app?startapp=0000cIsm']")
        link.click()

        # После последней обновы 31.08.24 закомментил
        # launch_click = self.wait_for_element(By.XPATH, "//body/div[@class='popup popup-peer popup-confirmation active']/div[@class='popup-container z-depth-1']/div[@class='popup-buttons']/button[1]/div[1]")
        # launch_click.click()
        logging.info(f"Account {self.serial_number}: TOMAT STARTED")
        self.sleep(4, 8)
        if self.scrshot:
            self.driver.save_screenshot(f'screen{self.scrshot}.png')
            self.scrshot += 1
        if not self.switch_to_iframe():
            logging.info(f"Account {self.serial_number}: No iframes found")
            return

    def clicker(self):
        stage = 0
        try:
            startgame = self.wait_for_element(By.CSS_SELECTOR,
                                              '#root > div > div._home_lw6uc_1 > div._board_pnata_1 > div._boardBtn_pnata_183'
                                              )
            startgame.click()
            logging.info(f"Account {self.serial_number}: started tapalka")
            self.sleep(7, 10)
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
            stage += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: can't start game, {str(e)}")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        if stage:
            try:
                # Wait until the game area is available
                game_area = self.wait_for_element(By.CSS_SELECTOR, 'canvas')

                # Get the size and location of the game area
                game_rect = game_area.rect
                game_x = game_rect['x']
                game_y = game_rect['y']
                game_width = game_rect['width']
                game_height = game_rect['height']

                logging.info(f"Game area size: width={game_width}, height={game_height}, x={game_x}, y={game_y}")

                # Define margins to avoid edges
                margin = 10  # pixels
                x_start = game_x + margin
                y_start = game_y + margin
                x_end = game_x + game_width - margin
                y_end = game_y + game_height - margin

                # Duration of the game in seconds
                duration = 30
                end_time = time.time() + duration
                next_screenshot_time = time.time() + 5  # Time for the next screenshot

                # Move the mouse to the center of the game area at the start
                action = ActionChains(self.driver)
                center_x = game_x + game_width / 2
                center_y = game_y + game_height / 2
                action.move_by_offset(center_x, center_y).perform()

                while time.time() < end_time:
                    # Generate a random number of movements to simulate multiple fingers
                    num_moves = random.randint(6, 10)
                    for _ in range(num_moves):
                        x_offset = random.uniform(x_start, x_end)
                        y_offset = random.uniform(y_start, y_end)

                        # Log the movement
                        logging.info(f"Moving to: x={x_offset}, y={y_offset}")

                        # Move the mouse to the random position within the game area
                        action = ActionChains(self.driver)
                        action.move_by_offset(x_offset - center_x, y_offset - center_y).perform()
                        center_x = x_offset
                        center_y = y_offset

                        # Very short delay to simulate rapid movements
                        time.sleep(random.uniform(0.0001, 0.008))

                    # Check if it's time to take a screenshot
                    if time.time() >= next_screenshot_time:
                        # Switch back to default content to take a screenshot

                        if self.scrshot:
                            self.driver.save_screenshot(f'screen{self.scrshot}.png')
                            self.scrshot += 1
                        next_screenshot_time += 5  # Schedule next screenshot in 5 seconds

                # Take the final screenshot after the game ends

                if self.scrshot:
                    self.driver.save_screenshot(f'screen{self.scrshot}.png')
                    self.scrshot += 1

            except Exception as e:
                logging.info(f"Account {self.serial_number}: error during moving, {str(e)}")
                self.driver.switch_to.default_content()
                if self.scrshot:
                    self.driver.save_screenshot(f'screen{self.scrshot}.png')
                    self.scrshot += 1

    def daily(self):
        try:
            prodoljit = self.wait_for_element(By.CSS_SELECTOR,
                                              # "//span[text()='Продолжить']"
                                              # '#root > div > div > div._main_hyf84_37 > div._phaseTwo_hyf84_162 > div._continueWrap_hyf84_375'
                                              #  '#root > div._layout_o460a_1 > div > div._cta_1id1y_54'
                                              '#root > div._layout_o460a_1.scrollable > div > div._main_842pa_37 > div._phaseTwo_842pa_152 > div._continueWrap_842pa_348 > div'

                                              #   '#root > div._layout_o460a_1.scrollable > div > div._main_842pa_37 > div._phaseTwo_842pa_152 > div._continueWrap_842pa_348 > div'
                                              #   '#root > div > div > div._main_hyf84_37 > div._phaseTwo_hyf84_162 > div._continueWrap_hyf84_375 > div'
                                              )
            prodoljit.click()
            logging.info(f"Account {self.serial_number}: took daily bonus")
            self.sleep(7, 15)
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: no daily bonus")

    def dailyTomat(self):
        stage = 0
        try:

            someArea = self.wait_for_element(By.XPATH,
                                        '/html/body/div[2]/div[2]/div[1]/div[2]'
                                                )
            x = someArea.location['x']
            y = someArea.location['y']
            actions = ActionChains(self.driver)
            actions.move_by_offset(x, y).click().perform()


            self.sleep(1, 2)
            logging.info(f"Account {self.serial_number}: clicked daily tomat")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
            stage += 1

            if stage:
                self.switch_to_iframe()
                claim = self.wait_for_element(By.CSS_SELECTOR,
                                              '#root > div._layout_o460a_1._layoutTabbar_o460a_21 > div._home_lw6uc_1 > div._popup_16kb3_17._popupVisible_16kb3_30._popStyle_1l65e_99 > div > div > div.w-full.px-\[12px\].py-\[8px\].mt-\[16px\].bg-white.border-1.border-solid.border-\[\#E9ECEC\].rounded-\[12px\] > div.flex.items-center.gap-\[8px\].py-\[12px\].border-0.border-solid.border-\[\#E9ECEC\] > button'
                                              )
                claim.click()
                self.sleep(5, 8)
                logging.info(f"Account {self.serial_number}: collected daily tomat")
                if self.scrshot:
                    self.driver.save_screenshot(f'screen{self.scrshot}.png')
                    self.scrshot += 1
                stage += 1

            if stage > 1:
                close = self.wait_for_element(By.CSS_SELECTOR,
                                              '#root > div._layout_o460a_1._layoutTabbar_o460a_21 > div._home_lw6uc_1 > div._popup_16kb3_17._popupVisible_16kb3_30._popStyle_1l65e_99 > i'
                                              )
                close.click()
                self.sleep(1, 2)
                logging.info(f"Account {self.serial_number}: closed dailytomat window")
                if self.scrshot:
                    self.driver.save_screenshot(f'screen{self.scrshot}.png')
                    self.scrshot += 1

        except Exception as e:
            logging.info(f"Account {self.serial_number}: no daily tomat {str(e)}")

    def spin(self):
        try:
            stars = int(self.wait_for_element(By.XPATH,
                                              '/html/body/div[2]/div[2]/div[1]/div[2]/p'
                                              #   '/html/body/div[2]/div[2]/div[1]/div[2]'
                                              # '#root > div > div._home_lw6uc_1 > div._levelWrapper_9q7q5_44 > div > div.pos-relative.z-3._levelBox_9q7q5_55 > p._levelNum_9q7q5_77'
                                              ).text)
            logging.info(f"Account {self.serial_number}: stars: {stars}")
        except Exception as e:
            stars = 0
            logging.info(f"Account {self.serial_number}: fuck")
        stage = 0
        try:
            start = self.wait_for_element(By.CSS_SELECTOR,
                                          #    '#root > div > div._home_lw6uc_1 > div.w-20.h-20.bg-no-repeat.bg-center.bg-contain.fixed.top-\[calc\(50\%-40px-110px\)\].right-3.cursor-pointer'
                                          '#root > div._layout_o460a_1._layoutTabbar_o460a_21 > div._home_lw6uc_1 > div.w-\[59\.5px\].h-\[80\.5px\].fixed.top-\[calc\(50\%-15px\)\].right-\[21px\].cursor-pointer._entry_wzwhq_219'
                                          )
            start.click()
            self.sleep(3, 5)
            logging.info(f"Account {self.serial_number}: krutilka on screen")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
            stage += 1

            counter = 0
            if stage:
                while (stars) and (counter < 1):
                    starSpin = self.wait_for_element(By.CSS_SELECTOR,
                                                     '._button_wzwhq_68._buttonSmall_wzwhq_93._buttonSpin_wzwhq_136._buttonSmallYellow_wzwhq_172'
                                                     )
                    starSpin.click()
                    self.sleep(8, 10)
                    stars -= 1
                    counter += 1
                    logging.info(f"Account {self.serial_number}: spinned, left {stars} spins")

                logging.info(f"Account {self.serial_number}: now free spins...")

                leftSpins = self.wait_for_element(By.XPATH,
                                                  # '#root > div > div > div._gameBoy_1oajv_22 > div > div._button_1oajv_68._buttonSmall_1oajv_93._buttonSpinTg_1oajv_145._buttonSmallBlue_1oajv_176 > div > div'
                                                  # '#root > div._layout_o460a_1.scrollable > div > div._gameBoy_wzwhq_22 > div > div._button_wzwhq_68._buttonSmall_wzwhq_93._buttonSpinTg_wzwhq_145._buttonSmallBlue_wzwhq_176 > div > div'
                                                  # '/html/body/div[2]/div[2]/div/div[3]/div/div[4]/div/div/text()'
                                                  '/html/body/div[2]/div[2]/div/div[3]/div/div[4]/div/div'
                                                  )

                howMany = get_last_char(leftSpins.text)
                logging.info(f"Account {self.serial_number}: left {howMany} free spins")
                howMany = int(howMany)
                while howMany:
                    freeSpin = self.wait_for_element(By.CSS_SELECTOR,
                                                     # '#root > div > div > div._gameBoy_1oajv_22 > div > div._button_1oajv_68._buttonSmall_1oajv_93._buttonSpinTg_1oajv_145._buttonSmallBlue_1oajv_176'
                                                     # '#root > div._layout_o460a_1.scrollable > div > div._gameBoy_wzwhq_22 > div > div._button_wzwhq_68._buttonSmall_wzwhq_93._buttonSpinTg_wzwhq_145._buttonSmallBlue_wzwhq_176'
                                                     '._button_wzwhq_68._buttonSmall_wzwhq_93._buttonSpinTg_wzwhq_145._buttonSmallBlue_wzwhq_176'
                                                     )
                    freeSpin.click()
                    self.sleep(8, 10)
                    howMany -= 1
                    logging.info(f"Account {self.serial_number}: spinned, left {howMany} spins")
                    if self.scrshot:
                        self.driver.save_screenshot(f'screen{self.scrshot}.png')
                        self.scrshot += 1


        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e), stage}")
        finally:
            self.driver.switch_to.default_content()
            if stage:
                self.back()

    def closeShit(self):
        try:
            close = self.wait_for_element(By.XPATH,
                                          '/html/body/div[5]/div[2]'
                                          )
            close.click()
            logging.info(f"Account {self.serial_number}: closed shit")
            self.sleep(2, 5)
        except Exception as e:
            logging.info(f"Account {self.serial_number}: no shit")

    def tomawaits(self):
        try:
            enter = self.wait_for_element(By.XPATH,
                                          '/html/body/div[2]/div[2]/div/div[4]'
                                          )
            enter.click()
            logging.info(f"Account {self.serial_number}: your toma awaits - entered")
            self.sleep(2, 5)
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: no toma yet")

    def farmingStart(self):
        try:
            farmingBut = self.wait_for_element(By.CSS_SELECTOR,
                                               # '//*[@id="root"]/div/div[1]/div[4]'
                                               # '/html/body/div[2]/div[2]/div[1]/div[4]/div[2]'
                                               '#root > div._layout_o460a_1._layoutTabbar_o460a_21 > div._home_lw6uc_1 > div._farmBtnWrapper_sptob_62 > div._farmBtnBox_sptob_69 > div'
                                               )
            farmingBut.click()
            logging.info(f"Account {self.serial_number}: good! farming was activated now or already active")
            self.sleep(4, 6)
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e)}")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1

    def farmingEnd(self):
        try:
            collect = self.wait_for_element(By.XPATH,
                                            '/html[1]/body[1]/div[2]/div[2]/div[1]/div[4]/div[2]/div[1]'
                                            )
            collect.click()
            logging.info(f"Account {self.serial_number}: collected points or still farming")
            self.sleep(6, 8)
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cannot collect points")
            if self.scrshot:
                self.driver.save_screenshot(f'screen{self.scrshot}.png')
                self.scrshot += 1

    def switch_to_iframe(self):
        self.driver.switch_to.default_content()
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            self.driver.switch_to.frame(iframes[0])
            return True
        return False

    def switch_tabs(self, main_tab_url):
        try:
            tabs = self.driver.window_handles
            logging.info(f"Account {self.serial_number}: {len(tabs)} tabs")

            main_tab = None

            for tab in tabs:
                try:
                    self.driver.switch_to.window(tab)
                    current_url = self.driver.current_url
                    logging.info(f"Account {self.serial_number}: Tab {tab} has URL {current_url}")

                    if main_tab_url == current_url:
                        main_tab = tab
                        logging.info(f"Account {self.serial_number}: Found main tab: {tab}")
                    else:
                        self.driver.switch_to.window(tab)
                        self.driver.close()
                        logging.info(f"Account {self.serial_number}: Closed tab")
                        tabs = self.driver.window_handles
                except Exception as e:
                    (f"Account {self.serial_number}: error '{str(e)}' on tab {tab}")

            tabs = self.driver.window_handles

            if main_tab and main_tab in tabs:
                self.driver.switch_to.window(main_tab)
                logging.info(f"Account {self.serial_number}: Switched to main tab {main_tab}")
            else:
                logging.error(f"Account {self.serial_number}: Main tab not found.")

            self.switch_to_iframe()
        except Exception as e:
            logging.error(f"Account {self.serial_number}: error '{str(e)}'")

    def watchYT(self, switch) -> bool:
        success = False
        try:
            current_tab_url = self.driver.current_url
            start = self.wait_for_element(By.XPATH,
                                          #  '/html/body/div[2]/div[2]/div[1]/div[2]/div[7]/div[2]/div[3]/div/div[2]'
                                          '/html/body/div[2]/div[2]/div[1]/div[2]/div[8]/div[2]/div[3]/div/div[2]'
                                          )
            self.driver.execute_script("arguments[0].scrollIntoView();", start)
            start.click()
            self.sleep(3, 5)
            logging.info(f"Account {self.serial_number}: pressed YT")
            success = True
        except Exception as e:
            logging.info(f"Account {self.serial_number}: error '{str(e)}'")
            success = False
        if success:
            if switch != 0:
                self.sleep(10, 15)
                self.switch_tabs(current_tab_url)
        return success

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

    def congratulation(self):
        try:
            cross = self.wait_for_element(By.CSS_SELECTOR,
                                          '#root > div._layout_o460a_1.scrollable > div > div._popup_16kb3_17._popupVisible_16kb3_30 > i'
                                          )
            logging.info(f"Account {self.serial_number}: 'Сongratulations' - going back")
            self.back()
        except Exception as e:
            logging.info(f"Account {self.serial_number}: no congratulation screen")

    def clay(self):
        stage = 0
        try:
            howMany = int(self.wait_for_element(By.XPATH,
                                                '/html/body/div[2]/div[2]/div[1]/div[2]/p'
                                             #   '/html/body/div[2]/div[2]/div[1]/div[2]'
                                                # '#root > div > div._home_lw6uc_1 > div._levelWrapper_9q7q5_44 > div > div.pos-relative.z-3._levelBox_9q7q5_55 > p._levelNum_9q7q5_77'
                                                ).text)
            if howMany:
                clay = self.wait_for_element(By.CSS_SELECTOR,
                                             #'#root > div._layout_o460a_1._layoutTabbar_o460a_21 > div._home_lw6uc_1 > div._levelWrapper_1tlfu_120'
                                             '#root > div._layout_o460a_1._layoutTabbar_o460a_21 > div._home_lw6uc_1 > div._levelWrapper_1ahtf_120'
                                             )
                clay.click()
                logging.info(f"Account {self.serial_number}: clicked clay, left {howMany} stars")
                self.sleep(5, 8)
                if self.scrshot:
                    self.driver.save_screenshot(f'screen{self.scrshot}.png')
                    self.scrshot += 1
                stage += 1

        except Exception as e:
            logging.info(f"Account {self.serial_number}: {str(e), stage}")

        if stage:
            try:
                lvlup = self.wait_for_element(By.CSS_SELECTOR,
                                              '#root > div._layout_o460a_1.scrollable > div > div._fixedBox_79gla_125 > div._btns_79gla_188 > button._btn_79gla_188._upgradeBtn_79gla_216'
                                              )
                lvlup.click()
                logging.info(f"Account {self.serial_number}: lvl upped")
                self.sleep(1, 3)
                if self.scrshot:
                    self.driver.save_screenshot(f'screen{self.scrshot}.png')
                    self.scrshot += 1
                stage += 1
            except Exception as e:
                logging.info(f"Account {self.serial_number}: {str(e), stage}")
        if stage > 1:
            try:
                use = self.wait_for_element(By.CSS_SELECTOR,
                                            # '#root > div > div > div._popup_16kb3_17._popupVisible_16kb3_30 > div > div > button'
                                           # '#root > div._layout_o460a_1.scrollable > div > div._popup_pnpwc_17._popupVisible_pnpwc_30 > div > div > button'
                                            '#root > div._layout_o460a_1.scrollable > div > div._popup_kzeyp_17._popupVisible_kzeyp_30 > div > div > button'
                                            )
                use.click()
                self.sleep(1, 3)
                if self.scrshot:
                    self.driver.save_screenshot(f'screen{self.scrshot}.png')
                    self.scrshot += 1
                stage += 1
            except Exception as e:
                logging.info(f"Account {self.serial_number}: {str(e), stage}")

        if stage > 2:
            self.congratulation()

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

    def tasks(self):
        try:
            tasksBut = self.wait_for_element(By.XPATH,
                                             '/html/body/div[2]/div[2]/div[2]/div[2]'
                                             )
            tasksBut.click()
            logging.info(f"Account {self.serial_number}: openned tasks")
            self.sleep(2, 4)
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant open tasks - {str(e)}")

    def matrix(self, order):
        # передавать 1 или 0 в зависимости от того клейм там или не клейм
        if not self.watchYT(1):
            return

        self.sleep(22, 25)

        self.home()
        self.tasks()

        # если в прошлой был 0 то не выполнять
        self.watchYT(0)

        self.reboot()

        self.home()
        self.tasks()

        buts = [[0, 0, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]]
        stage = 0

        try:

            dailyCombo = self.wait_for_element(By.XPATH,
                                               '/html/body/div[2]/div[2]/div[1]/div[2]/div[2]/div[2]'
                                               )
            dailyCombo.click()
            logging.info(f"Account {self.serial_number}: openned daily combo")
            self.sleep(2, 4)
            stage += 1
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant open daily combo - {str(e), stage}")

        if stage:
            i = 0
            k = 1
            success = True
            while i < 3:
                j = 0
                while j < 4:
                    try:
                        buts[i][j] = self.wait_for_element(By.XPATH,
                                                           f'/html/body/div[2]/div[2]/div/div[3]/div[2]/div[1]/div[{k}]'
                                                           )
                    except Exception as e:
                        sucess = False
                        logging.info(f"Account {self.serial_number}: error '{str(e)}' on element a{i}{j}")
                    j += 1
                    k += 1
                i += 1
            if success:
                stage += 1
                logging.info(f"Account {self.serial_number}: matrix initialized")

        if stage > 1:
            step = 1
            success = True
            while step <= 3:
                found = False
                i = 0
                while i < 3:
                    j = 0
                    while j < 4:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView();", buts[i][j])
                            if step == order[i][j]:
                                buts[i][j].click()
                                logging.info(f"Account {self.serial_number}: pressed {order[i][j]} button")
                                self.sleep(1, 3)
                                step += 1
                                found = True
                                break  # Exit the inner loop
                        except Exception as e:
                            success = False
                            logging.info(f"Account {self.serial_number}: {str(e)} on stage {stage}, element{i}{j}")
                        j += 1
                    if found:
                        break  # Exit the outer loop
                    i += 1
            if success:
                logging.info(f"Account {self.serial_number}: clicked all buttons")
                self.sleep(5, 7)
                stage += 1

        if stage > 2:
            self.back()
            logging.info(f"Account {self.serial_number}: finished daily combo and went back to tasks")

    def home(self):
        try:
            homeBut = self.wait_for_element(By.XPATH,
                                            '/html/body/div[2]/div[2]/div[2]/div[1]'
                                            )
            homeBut.click()
            logging.info(f"Account {self.serial_number}: openned home")
            self.sleep(2, 4)
        except Exception as e:
            logging.info(f"Account {self.serial_number}: cant open home - {str(e)}")

    def check_and_go_back(self):
        try:
            # Устанавливаем тайм-аут ожидания (например, 10 секунд)
            wait = WebDriverWait(self.driver, 4)

            element = wait.until(EC.presence_of_element_located((By.XPATH, "//p[text()='First-time Tomato Booster']")))

            if element:
                self.back()
                logging.info(f"Account {self.serial_number}: closed shit")
        except TimeoutException:
            # Если элемент не найден в течение тайм-аута
            logging.info(f"Account {self.serial_number}: time for shit ran out")
        except Exception as e:
            logging.exception(f"Account {self.serial_number}: no shit")

    def wait_for_element(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def wait_for_elements(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_all_elements_located((by, value))
        )


def read_accounts_from_file():
    with open('accounts_tomat.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]


def write_accounts_to_file(accounts):
    with open('accounts_tomat.txt', 'w') as file:
        for account in accounts:
            file.write(f"{account}\n")


def process_accounts():
    last_processed_account = None

    order = [[0, 2, 3, 0],
             [0, 0, 0, 0],
             [0, 0, 1, 0]]

    while True:

        accounts = read_accounts_from_file()
        random.shuffle(accounts)
        write_accounts_to_file(accounts)
        i = 0
        while i < len(accounts):
            remove_empty_lines('locked_accounts.txt')
            remove_key_lines('locked_accounts.txt', 'TOMAT')

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
                    lock_account(accounts[i - 1], 'TOMAT')
                    bot = TelegramBotAutomation(accounts[i - 1])
                    bot.scrshot = 0  # 0 for no screenshots
                    try:
                        delete_oldScreens()
                        bot.navigate_to_bot()
                        bot.send_message("https://t.me/tomarketkormiplotno")
                        bot.click_link()
                        bot.check_and_go_back()
                        bot.closeShit()
                        bot.daily()
                        bot.check_and_go_back()
                        bot.tomawaits()
                        # bot.clicker()
                        bot.farmingStart()
                        bot.farmingEnd()
                        bot.farmingStart()
                        #bot.dailyTomat()
                        bot.spin()
                        bot.clay()
                       #bot.tasks()
                       #bot.matrix(order)
                       #bot.home()

                        logging.info(f"Account {accounts[i - 1]}: Processing completed successfully.")
                        success = True
                    except Exception as e:
                        logging.warning(f"Account {accounts[i - 1]}: Error occurred on attempt {retry_count + 1}: {e}")
                        retry_count += 1
                    finally:
                        logging.info("-------------END-----------")
                        bot.browser_manager.close_browser()
                        logging.info("-------------END-----------")
                        unlock_account(accounts[i - 1], "TOMAT")
                        sleep_time = random.randrange(5, 15)
                        logging.info(f"Sleeping for {sleep_time} seconds.")
                        time.sleep(sleep_time)

                    if retry_count >= 3:
                        logging.warning(f"Account {accounts[i - 1]}: Failed after 3 attempts.")

            if not success:
                logging.warning(f"Account {accounts[i - 1]}: Moving to next account after 3 failed attempts.")

        logging.info("All accounts processed. Waiting 3 hours before restarting.")

        for hour in range(3):
            logging.info(f"Waiting... {3 - hour} hours left till restart.")
            time.sleep(60 * 60)

        logging.info("Shuffling accounts for the next cycle.")


if __name__ == "__main__":
    process_accounts()