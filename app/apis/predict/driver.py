
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import os

def driver_options():
    print(os.getenv('DOWNLOAD_DIR'))
    if('DOWNLOAD_DIR' in os.environ):
        raise Exception("DOWNLOAD_DIR environment var is not set.")

    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_experimental_option('useAutomationExtension', False)

        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument('--disable-dev-shm-usage')

        chrome_prefs = {
                            "profile.default_content_settings.popups": 0
                            ,"download.prompt_for_download" : "false"
                            ,"download.directory_upgrade": "true"
                            ,"download.default_directory" : os.getenv('DOWNLOAD_DIR')
                        }


        chrome_options.experimental_options["prefs"] = chrome_prefs 

        # d = DesiredCapabilities.CHROME
        # d['loggingPrefs'] = { 'browser':'ALL' }

        # driver = webdriver.Chrome(options=chrome_options, desired_capabilities=d)
        # driver = webdriver.Chrome(options=chrome_options)
        # driver.execute_cdp_cmd("Page.setBypassCSP", {"enabled": True})
        # driver.maximize_window()
        return chrome_options

    except Exception as e:
        print(e)
        raise Exception(str(e))





def configure_driver() -> webdriver:
    print(os.getenv('DOWNLOAD_DIR'))
    if('DOWNLOAD_DIR' in os.environ):
        raise Exception("DOWNLOAD_DIR environment var is not set.")

    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_experimental_option('useAutomationExtension', False)

        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument('--disable-dev-shm-usage')

        chrome_prefs = {
                            "profile.default_content_settings.popups": 0
                            ,"download.prompt_for_download" : "false"
                            ,"download.directory_upgrade": "true"
                            ,"download.default_directory" : os.getenv('DOWNLOAD_DIR')
                        }


        chrome_options.experimental_options["prefs"] = chrome_prefs 

        # d = DesiredCapabilities.CHROME
        # d['loggingPrefs'] = { 'browser':'ALL' }

        # driver = webdriver.Chrome(options=chrome_options, desired_capabilities=d)
        # driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd("Page.setBypassCSP", {"enabled": True})
        driver.maximize_window()
        return driver

    except Exception as e:
        print(e)
        raise Exception(str(e))


