from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from app.apis.predict.download_watcher import downloaded_file
from app.apis.predict.predict_names import filename_to_predictname

from datetime import datetime
import time
from os import remove
import os 


from typing import Callable, Any
import functools

from app.apis.predict.predict_user import User, UserList
from zipfile import ZipFile

from io import StringIO
import pandas as pd
import requests
import hashlib
from app.apis.s3.s3manager import S3Manager

import pymongo
client = pymongo.MongoClient('172.17.0.1:27017')

__signin_btn = "/html/body/div[1]/div/div[2]/div/div/div[1]/form/div[3]/button"
__signedin_lbl = "/html/body/div[1]/div/div[1]/div[2]/ul/li[1]/span/a" 
def login(user:User, driver:webdriver) -> Any:
    try:
        driver.save_screenshot(f'antes de loguearse.png')
        wait = WebDriverWait(driver, 15)
        # driver.close()
        driver.get(user.url)
        print(user.url)
        print(driver.current_url)
        time.sleep(3)
        driver.save_screenshot(f'login_page_x.png')
        
        signin_button = wait.until(EC.element_to_be_clickable((By.XPATH, __signin_btn)))
        driver.save_screenshot(f'login_page.png')

        input_email = driver.find_element("name", "email")
        input_password = driver.find_element("name", "password")

        input_email.send_keys(user.user) #Email
        input_password.send_keys(user.password) #password
        driver.save_screenshot('password.png')

        signin_button.click()

        signedin = wait.until(EC.presence_of_element_located((By.XPATH, __signedin_lbl)))
        driver.save_screenshot('logueado.png')
        print(driver.current_url)
        print(signedin.text)

        if(signedin.text != "Predict"):
            driver.quit()
            raise Exception("cant login")

        return driver
    except Exception as ex:
        driver.quit()
        raise Exception(ex)



__upload_btn = "//input[@type='file']"
__uploader = "//span[@class='ant-typography file-uploader__auxtext']"
def analyze_file(user:User , driver: webdriver , image: str) -> webdriver:

    wait = WebDriverWait(driver, 10)
    wait_upload = WebDriverWait(driver, 80)

    url = driver.current_url
    # if(url != f"{user.url}?formated=true"):
    if(user.url not in driver.current_url):
        #lugar incorrecto para subir un archivo
        print(f"se va a loguear {user.user}")
        driver = login(user=user, driver=driver)


    print(f'se va a analyzar el archivo {image}') 
    uploadButton = wait.until(EC.presence_of_element_located(("xpath", __upload_btn)))
    driver.execute_script("arguments[0].removeAttribute('style')", uploadButton)
    print(f'/code/{image}')
    time.sleep(1)
    uploadButton.send_keys(f'/code/{image}') #esta es una path local.
    wait.until(EC.presence_of_element_located(("xpath", __uploader)))

    wait_upload.until_not(EC.presence_of_element_located(("xpath", __uploader)))

    return driver


__menu_dropdown = "//div[@class='ant-dropdown-trigger actions-menu item-actions__actions-menu']"
__download_item = "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light menu-contents']/li[3]"
__download_raw = "//ul[@class='ant-dropdown-menu ant-dropdown-menu-sub ant-dropdown-menu-vertical']/li[1]"
def download_file(user:User, driver:webdriver, stimulus:str) -> webdriver:
    print(f"se inicio la descarga de: {stimulus}")
    try:
        if(driver.current_url != f"{user.url}?predictionType=formatted"):
            login(user=user, driver=driver)

        wait = WebDriverWait(driver, 10)
        predict_name = filename_to_predictname(stimulus)
        element_to_download = find_stimulu(user=user, driver=driver, stimulus=predict_name)

        activate_menu = ActionChains(driver).move_to_element(element_to_download)
        activate_menu.perform()

        driver.save_screenshot("elemento_activado.png")
        open_menu = wait.until(EC.presence_of_element_located(("xpath", __menu_dropdown)))
        open_menu.click()

        download_menu = wait.until(EC.presence_of_element_located(("xpath", __download_item)))
        activate_download_options = ActionChains(driver).move_to_element(download_menu)
        activate_download_options.perform()

        time.sleep(1)
        download_raw = wait.until(EC.presence_of_element_located(("xpath", __download_raw)))
        driver.save_screenshot("download_raw.png")
        download_raw.click()

        wait_download = downloaded_file(f"{stimulus}_results.zip")
        # with ZipFile(f"{stimulus}_results.zip") as z_file:
        #     print(z_file.filename)
        #     print(z_file.filelist)

        driver.quit()
        return driver
        # raise Exception("cant find element")
    except Exception as ex:
        driver.quit()
        raise Exception(ex)

def analyze_download_file(user:User, driver:webdriver, stimulus:str) -> webdriver:
    print(f"se inicio la descarga de: {stimulus}")
    try:
        # if(driver.current_url != f"{user.url}?predictionType=formatted"):
        if(user.url not in driver.current_url):
            login(user=user, driver=driver)

        wait = WebDriverWait(driver, 10)
        predict_name = filename_to_predictname(stimulus)
        element_to_download = find_stimulu(user=user, driver=driver, stimulus=predict_name)

        activate_menu = ActionChains(driver).move_to_element(element_to_download)
        activate_menu.perform()

        driver.save_screenshot("elemento_activado.png")
        open_menu = wait.until(EC.presence_of_element_located(("xpath", __menu_dropdown)))
        open_menu.click()

        download_menu = wait.until(EC.presence_of_element_located(("xpath", __download_item)))
        activate_download_options = ActionChains(driver).move_to_element(download_menu)
        activate_download_options.perform()

        time.sleep(1)
        download_raw = wait.until(EC.presence_of_element_located(("xpath", __download_raw)))
        driver.save_screenshot("download_raw.png")
        download_raw.click()

        wait_download = downloaded_file(f"{stimulus}_results.zip")

        # driver.quit()
        return driver
        # raise Exception("cant find element")
    except Exception as ex:
        driver.quit()
        raise Exception(ex)

__folder_loaded = "/html/body/div[1]/div/div[2]/div[1]/div/div[3]/div/div/div/div[1]/div/a/div"
__stimulu_span = ".//strong/span[@class='highlighted-text']"
def find_stimulu(user:User, driver:webdriver, stimulus:str) -> WebElement:
    try:
        print(f"va a buscar el elemento: {stimulus}")
        if(driver.current_url != f"{user.url}?predictionType=formatted"):
            driver = login(user=user, driver=driver)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located(("xpath", __folder_loaded)))
        links_elements = driver.find_elements('tag name', 'a')
        driver.save_screenshot('huecada.png')
        time.sleep(5)

        links_elements = filter(lambda l: l.get_attribute("href") != None, links_elements)
        links_elements = filter(lambda l: '/predict/media' in l.get_attribute("href"), links_elements)

        for element in links_elements:
            # print(element)
            href = element.get_attribute("href")
            span = element.find_element('xpath', __stimulu_span)
            driver.save_screenshot('elemento.png')

            if(span.text == stimulus):
                print("si se encontro")
                return element

        print("no se encontro el puto elemento")
        driver.quit()
        raise Exception("cant find element")
    except Exception as ex:
        driver.quit()
        raise Exception(ex)


def generate_dataset(collection: str, driver: webdriver):
    try:
        predict_mongo = client.get_database('analyzer').get_collection('predict')

        s3m = S3Manager()
        s3_objects = s3m.s3_list_files(collection)
        print(len(s3_objects))

        for obj in s3_objects:
            print("nueva imagen de s3")
            image_url = f"https://geotec-dev.s3.amazonaws.com/{obj.key}"
            image_request = requests.get(image_url)
            nombrecin = obj.key.split('/')[-1]

            hash = hashlib.sha256(image_request.content).hexdigest()
            print(hash)

            existe = predict_mongo.find_one({"image_hash": hash})
            if not existe:
                objeto = {"image_hash": hash
                            , "image_url": image_url }

                #procesamiento de la imagen propio de predict

                with open(nombrecin, 'wb') as f:
                    f.write(image_request.content)
                
                user:User = UserList().get_user(1)

                # login(user=user, driver=driver)
                print("se va a iniciar un nuevo analisis en predict")
                result_analyze = analyze_file(user=user, driver=driver, image=nombrecin)
                stimulus_name = nombrecin.split('.')[0]
                result_download = analyze_download_file(user=user, driver=driver, stimulus=stimulus_name)

                with ZipFile(f"{stimulus_name}_results.zip") as z_file:
                    for z in z_file.filelist:
                        z_content = z_file.read(z)
                        if z.filename.endswith('.csv'):
                            # print(zzz[:100])
                            df = pd.read_csv(StringIO(z_content.decode('utf-8')))
                            metrics = df.to_dict(orient='records')
                            if 'AOI name' in metrics[0]:
                                objeto.update({'aois': metrics})
                            else:
                                objeto.update(metrics[0])
                        else:
                            print(f'se subira al s3 {z.filename.split("/")[1]}')
                            print('===================================================')
                            s3m.s3_save_object(collection=collection, api='predict', name=stimulus_name 
                                                ,filename=z.filename.split('/')[1], file=z_content)
                            print(z.filename)
                            print('===================================================')


                print("mierda")
                print(f'deberia estar en: {driver.current_url}')
                print('===================================================')
                os.remove(nombrecin)
                os.remove(f"{stimulus_name}_results.zip")
                # driver.quit()

                predict_mongo.insert_one(objeto)
                time.sleep(3)
                driver.save_screenshot("despuesdesubir.png")

                # s3m.s3_save_object(collection=collection, api='predict', name=nombrecin, file=open('huecada.png', 'rb'))
                # break

        return {}

    except Exception as ex:
        print(ex)
        raise ex
