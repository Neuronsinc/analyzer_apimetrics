## Api imports
from fastapi import FastAPI, File, UploadFile, Form, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import shutil
import requests
import aiohttp
import asyncio

##Bot imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
import time

#random imports
from random import *
from os import remove
from asgiref import sync
import watchdog.events
import watchdog.observers
import re
import json
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from dotenv import load_dotenv
from pathlib import Path
from distutils.util import strtobool

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

RootPath = os.getenv('ROOT')
Backend = os.getenv('BACKEND')
Headless = os.getenv('HEADLESS')
DownloadDir = strtobool(os.getenv('DOWNLOADDIR'))
UploadNeuronsDir = os.getenv('PATHFORUPLOADNEURONS')
SrcPath = strtobool(os.getenv('SRCPATH'))


userArr = ['erick.moreno@troiatec.com', 'juan.roberto@troiatec.com', 'kevyn.lopez@troiatec.com', 'o.rivera@troiatec.com', 'c.castillo@troiatec.com']
passworsArr = ['Troiatec2023$', 'Troiatec060112#', 'Troiatec2023$', 'Troiatec2023$', 'Troiatec2023$']
folderArr = ['/predict/folder/a6c2b8b8-cded-49a4-b7a2-fd2808f443e5', '/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e', '/predict/folder/b49f8374-4bdf-4511-a6c1-d95e63de0504', '/predict/folder/0e3ed6c1-9976-4502-b693-1b3b3b4b63bd', '/predict/folder/d6148517-eb51-4e68-a8d9-0c6b101e8097']
urlArr = ['https://app.neuronsinc.com/predict/folder/a6c2b8b8-cded-49a4-b7a2-fd2808f443e5', 'https://app.neuronsinc.com/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e', 'https://app.neuronsinc.com/predict/folder/b49f8374-4bdf-4511-a6c1-d95e63de0504' ,'https://app.neuronsinc.com/predict/folder/0e3ed6c1-9976-4502-b693-1b3b3b4b63bd' , 'https://app.neuronsinc.com/predict/folder/d6148517-eb51-4e68-a8d9-0c6b101e8097']

evento = ""
zipName = ''

def AvisoSoporte(tipo, id_folder, fileName, token, mensaje, cuenta, apis):
    data = {"type": tipo, "idF": id_folder, "Emessage": mensaje, "cuenta": cuenta, "apis": apis}
    fo = open(RootPath + fileName, 'rb')
    file = {'File': fo}
    headers = {'Authorization': token}
    r = requests.post(url= Backend + '/BotSupport/new_mail', files=file ,data=data, headers=headers)
    jsonResponse = r.json()
    # Eliminar archivo y zip.
    fo.close()
    remove(fileName)
    return jsonResponse


def GetNumber():
    #x = randint(1, 100)
    #if ((x % 2) == 0):
        #return 0
    return randint(0, 4)

def QuitWatermark(fname, text, nameWithoutExt):
    image = Image.open(fname)
    w, h = image.size

    #Create a mask with the dimensions of the rectangle
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    shape = [(w - 150, h - 50), (w - 10, h - 10)]
    draw.rectangle(shape, fill=255)
    mask.save(nameWithoutExt + "_mask.png")

    #put the mask in the image
    blurred = image.filter(ImageFilter.GaussianBlur(20))
    image.paste(blurred, mask=mask)

    #Add text to image
    font = ImageFont.truetype('Fonts\Montserrat.ttf', 25)
    I1 = ImageDraw.Draw(image)
    I1.text((w - 130, h - 50), text, font=font,fill="Black", align='center', stroke_fill="black", stroke_width=1)

    #Save the new image and delete de mask
    image.save(fname)
    remove(nameWithoutExt + "_mask.png")

async def async_aiohttp_post(url,data, headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as response:
            return await response.json()
           

def ExecuteNeurons(api, getStimulus, idstimulus, token):
    data = {'api': api}
    headers = {'Authorization': token}
    ApiCredentials = requests.post(url= Backend + '/Stimulus/getApiCredentials',data=data, headers=headers)
    ApiC = ApiCredentials.json()
    split_up = os.path.splitext(getStimulus["imageUrl"])

    d = {"file": getStimulus["imageUrl"]
            , "id_folder": getStimulus["id_folder"]
            , "id_stimulus": idstimulus
            , "fileN": getStimulus["title"]  + split_up[1]}

    #BotD = requests.post(url=ApiC["url"], data=d, headers=headers)

    #return BotD.json()
    #asyncio.run(async_aiohttp_post(ApiC["url"], data=d, headers=he))
    return ApiC,d,headers

async def ExecuteAttention(api, getStimulus, idStimulus, token, studySettings, ws, userCreation = None):

    data = {'api': api}
    headers = {'Authorization': token}
    ApiCredentials = requests.post(url= Backend + '/Stimulus/getApiCredentials',data=data, headers=headers)
    ApiC = ApiCredentials.json()
    split_up = os.path.splitext(getStimulus["imageUrl"])

    try:
        today = datetime.now()
        originalName = getStimulus["title"] + split_up[1]
        extension = ''
        tipo = 0
        if (".png" in originalName or ".PNG" in originalName):
            extension = '.png'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpg" in originalName or ".JPG" in originalName):
            extension = '.jpg'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpeg" in originalName or ".JPEG" in originalName):
            extension = '.jpeg'
            originalName = originalName[0: len(originalName) - 5]
        elif (".mp4" in originalName or ".MP4" in originalName):
            extension = '.mp4'
            originalName = originalName[0: len(originalName) - 4]
            tipo = 1

        fileName = "Attention"+str(today.day) + str(today.month) + str(today.year) + "_" +str(today.hour)+str(today.minute)+str(today.second) + (re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))) + extension
        
        img_data = requests.get(getStimulus["imageUrl"]).content
        with open(fileName, 'wb') as f:
            f.write(img_data)
    except Exception:
        return {"message": "Error uploading the file"}
    finally:
        f.close()
    
    data = {'study_name': studySettings["study_name"], 'study_type': studySettings["study_type"], 'content_type': studySettings["content_type"], 'tasks[0]': 'focus', 'tasks[1]': 'clarity_score'}
    fo = open(RootPath + fileName, 'rb')
    file = {'file': fo} # la ruta debe ser cambiada por la ruta del servidor
    headers = {'Api-key': ApiC["clave"]}
    r = requests.post(url=ApiC["url"], files=file ,data=data, headers=headers)
    jsonResponse = r.json()

    fo.close()
    if ("success" in str(jsonResponse)):
        id = (jsonResponse["data"]["study_id"]).strip('\"')
        remove(fileName)
        
        


        t_end = time.time() + (30 * 1)
        finished = False
        while(time.time() < t_end):
            status = requests.get(url= ApiC["url"] + '/' + id + '/status', headers=headers)
            if not(status is None):
                status = status.json()
                if(status["data"]["status"] == "finished"):
                    finished = True
                    break
        
        if(finished):
            size = 0

            mapsArr = ['heatmap', 'focus']

            mapaux = 0

            print(id)

            while(mapaux < len(mapsArr)):
                headers = {'Api-key': ApiC["clave"]}
                map = requests.get(url= ApiC["url"] + '/' + id + '/image?image=' + mapsArr[mapaux], headers=headers)
        
                actualFname = getStimulus["title"] + '_attention_' + mapsArr[mapaux] +'.jpg'

                with open(actualFname, 'wb') as f:
                    f.write(map.content)

                size += os.path.getsize(RootPath + actualFname)

                data = {"idStimulus": idStimulus, "n": "attentionInsights_" + mapsArr[mapaux], "api": 2} if userCreation == None else {"idStimulus": idStimulus, "n": "attentionInsights_" + mapsArr[mapaux], "api": 2, 'userCreation': userCreation}

                fo = open(RootPath + actualFname, 'rb')
                file = {'file': fo} # la ruta debe ser cambiada por la ruta del servidor
                headers = {'Authorization': token}
                r = requests.post(url= Backend + "/Stimulus/SaveAndUploadAStimulusV2", files=file ,data=data, headers=headers)
                jsonResponse = r.json()

                print(jsonResponse)

                if(str(jsonResponse) == "successful"):
                    fo.close()
                    remove(actualFname)

                mapaux = mapaux + 1     

            
        #obtener y guardar los scores

            await ws.send_json({
            "message": f"MapsR"
            })

            headers = {'Api-key': ApiC["clave"]}

            scores = requests.get(url=ApiC["url"] + '/' + id, headers=headers)
            arrScore = scores.json()

            data = {'api': 2}
            headers = {'Authorization': token}

            ApiMetrics = requests.post(url= Backend + "/Stimulus/getApiMetrics",data=data, headers=headers)
            ApiMetrics = json.loads(ApiMetrics.text)
            print(ApiMetrics[0]["id"])
            print(len(ApiMetrics))
            metricsids = []

            apiaux = 0

            while(apiaux < len(ApiMetrics)):
                metricsids.append(ApiMetrics[apiaux]["id"])
                apiaux = apiaux + 1

            
            i = 0
            while(i < len(metricsids)):
                data = {"value": arrScore["data"]["aesthetics"]["clarity_score"], "idMetric": metricsids[i], "idStimulus": idStimulus} if userCreation == None else {"value": arrScore["data"]["aesthetics"]["clarity_score"], "idMetric": metricsids[i], "idStimulus": idStimulus, "userCreation": userCreation}
                headers = {'Authorization': token}
                r = requests.post(url= Backend + "/Stimulus/AddToScore",data=data, headers=headers)
                jsonResponse = r.json()

                if("inserted" not in(jsonResponse)):
                    return "fail"
            
                i = i + 1


            #save size of stimulus
            data = {'idStimulus': idStimulus, 'size': size}
            headers = {'Authorization': token}

            size = requests.post(url=Backend + "/Stimulus/UpdateSize",data=data, headers=headers)
            
            return "Successful"

    else:
        remove(fileName)
        return {"message": f"{jsonResponse}"}
    
    return await "something gone wrong"

async def ExecuteFengGui(api, getStimulus, idStimulus, token, ws, userCreation = None):
    data = {'api': api}
    headers = {'Authorization': token}
    ApiCredentials = requests.post(url=Backend + '/Stimulus/getApiCredentials',data=data, headers=headers)
    ApiC = ApiCredentials.json()
    
    jsonrpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "ImageAttention",
        "params": { "InputImage" : getStimulus['imageUrl'], "viewType" : 0, "ViewDistance" : 1, "analysisOptions" : 0, "outputOptions" : 111
        }
    }
    
    headers = {'Authorization': 'Basic ' + ApiC["clave"]}
    r = requests.post(url=ApiC["url"], json=jsonrpc, headers=headers)
    FengResponse = r.json()

    if ("result" in FengResponse):
        #Guardar mapas
        size = 0

        mapsArr = ['gazeplot', 'aoi']

        mapaux = 0

        id = FengResponse['result']['imageID']
        print(id)
        while(mapaux < len(mapsArr)):
            headers = {'Authorization': 'Basic ' + ApiC["clave"]}
            map = requests.get(url= 'https://service.feng-gui.com/users/erick.moreno.troiatec.com/files/images/' + id.replace(".png", "_" + mapsArr[mapaux] + ".png"), headers=headers)
        
            actualFname = getStimulus["title"] + '_feng_' + mapsArr[mapaux] +'.png'
            print(map)
            with open(actualFname, 'wb') as f:
                f.write(map.content)
            
            QuitWatermark(actualFname, mapsArr[mapaux], getStimulus["title"] + '_feng_' + mapsArr[mapaux])

            size += os.path.getsize(RootPath + actualFname)

            data = {"idStimulus": idStimulus, "n": "fengGui_" + mapsArr[mapaux], "api": 3} if userCreation == None else {"idStimulus": idStimulus, "n": "fengGui" + mapsArr[mapaux], "api": 3, 'userCreation': userCreation}

            fo = open(RootPath + actualFname, 'rb')
            file = {'file': fo} # la ruta debe ser cambiada por la ruta del servidor
            headers = {'Authorization': token}
            r = requests.post(url=Backend + "/Stimulus/SaveAndUploadAStimulusV2", files=file ,data=data, headers=headers)
            jsonResponse = r.json()

            print(jsonResponse)

            if(str(jsonResponse) == "successful"):
                fo.close()
                remove(actualFname)
            mapaux = mapaux + 1
                
        #Guardar los scores
        data = {'api': 3}
        headers = {'Authorization': token}

        ApiMetrics = requests.post(url=Backend + "/Stimulus/getApiMetrics",data=data, headers=headers)
        ApiMetrics = json.loads(ApiMetrics.text)
        print(ApiMetrics[0]["id"])
        print(len(ApiMetrics))
           
            
        i = 0
        while(i < len(ApiMetrics)):
            data = {"value": FengResponse["result"][(ApiMetrics[i]["name"]).lower()], "idMetric": ApiMetrics[i]["id"], "idStimulus": idStimulus} if userCreation == None else { "value": FengResponse["result"][(ApiMetrics[i]["name"]).lower()], "idMetric": ApiMetrics[i]["id"], "idStimulus": idStimulus, "userCreation": userCreation}
            headers = {'Authorization': token}
            r = requests.post(url=Backend + "/Stimulus/AddToScore",data=data, headers=headers)
            jsonResponse = r.json()
            print(jsonResponse)
            if("inserted" not in(jsonResponse)):
                return "fail"
            i = i + 1

            #chequear si hay aois , si sí guardar
        if ("aOIs" in FengResponse['result']):
            aois = FengResponse['result']['aOIs']

            j = 0

            while(j < len(aois)):
                data = {'punctuation': aois[j]['visibilityScore'], 'name': aois[j]['text'], 'idStimulus': idStimulus, 'idApi': 3} if userCreation == None else {'punctuation': aois[j]['visibilityScore'], 'name': aois[j]['text'], 'idStimulus': idStimulus, 'idApi': 3, 'userCreation': userCreation}
                headers = {'Authorization': token}
                r = requests.post(url=Backend + "/Stimulus/InsertAoi",data=data, headers=headers)
                jsonResponse = r.json()

                if("inserted" not in(jsonResponse)):
                    return "fail"
                j = j + 1


        #save size of stimulus
        data = {'idStimulus': idStimulus, 'size': size}
        headers = {'Authorization': token}

        size = requests.post(url=Backend + "/Stimulus/UpdateSize",data=data, headers=headers)
        

        return "Successful"
        
    return await "something gone wrong"



class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        watchdog.events.PatternMatchingEventHandler.__init__(self, patterns=['*.zip'], ignore_directories=True, case_sensitive=False)
    
    def on_created(self, event):
        print("Se creo el archivo", event.src_path)
        return event.src_path
    
    def on_any_event(self, event):
        global evento
        evento = event.src_path
        print("cualquier evento", event.src_path, event.event_type)
        return event.src_path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/test")
def file(primero: str = Form(), file: UploadFile = File(...)):
    return {"message": file}

@app.options("/singleFile")
def singeOptions():
    return {"message": True}

@app.post("/singleFile")
def singleFile(t: Request, id_folder: str = Form(), file: UploadFile = File(...)):
    token = t.headers.get('Authorization')
    try:
        today = datetime.now()
        originalName = file.filename
        extension = ''
        tipo = 0
        if (".png" in originalName or ".PNG" in originalName):
            extension = '.png'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpg" in originalName or ".JPG" in originalName):
            extension = '.jpg'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpeg" in originalName or ".JPEG" in originalName):
            extension = '.jpeg'
            originalName = originalName[0: len(originalName) - 5]
        elif (".mp4" in originalName or ".MP4" in originalName):
            extension = '.mp4'
            originalName = originalName[0: len(originalName) - 4]
            tipo = 1

        fileName = str(today.day) + str(today.month) + str(today.year) + "_" +str(today.hour)+str(today.minute)+str(today.second) + (re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))) + extension
        
        with open(fileName, 'wb') as f:
            shutil.copyfileobj(file.file, f)
    except Exception:
        return {"message": "Error uploading the file"}
    finally:
        file.file.close()

    #userArr = ['erick.moreno@troiatec.com', 'juan.roberto@troiatec.com', 'kevyn.lopez@troiatec.com', 'o.rivera@troiatec.com', 'c.castillo@troiatec.com']
    #passworsArr = ['Troiatec2023$', 'Troiatec060112#', 'Troiatec2023$', 'Troiatec2023$', 'Troiatec2023$']
    #folderArr = ['/predict/folder/a6c2b8b8-cded-49a4-b7a2-fd2808f443e5', '/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e', '/predict/folder/b49f8374-4bdf-4511-a6c1-d95e63de0504', '/predict/folder/0e3ed6c1-9976-4502-b693-1b3b3b4b63bd', '/predict/folder/d6148517-eb51-4e68-a8d9-0c6b101e8097']
    #urlArr = ['https://app.neuronsinc.com/predict/folder/aceacbd2-3c2d-426f-97a0-5411d18920d5', 'https://app.neuronsinc.com/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e']

    random = GetNumber()
    
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    #------------This is for headless mode -------------------
    #chrome_options.add_argument("--headless=new") #<-- para versiones de Chrome >= 109
    #chrome_options.add_argument("--headless=chrome") #<-- para versiones de Chrome >= 96 , <= 108
    chrome_options.add_argument(Headless) #<- actual funcionando en servidor (version 108)
    chrome_options.add_argument("--window-size=1920,1080")
    #---------------------------------------------------------
    
    #-----------This is for download directory----------------
    if (DownloadDir):
        chrome_prefs = {"download.default_directory": r"C:\Users\Dev1\Desktop\ApiBotAnalyzer"}
        chrome_options.experimental_options["prefs"] = chrome_prefs
    #----------------------------------------------------------

    repeatedTimes = 0
    loops = 2

    uploadedF = False
    spanF = False
    finished = False
    spanFounded = False
    file =''
    span = ''

    while (repeatedTimes < loops):
        
        loginFinished = False

        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get('https://app.neuronsinc.com/')
            #driver.get(urlArr[random])
            driver.maximize_window()
            input1 = driver.find_element("name", "email")
            input2 = driver.find_element("name", "password")
            input1.send_keys(userArr[random]) #Email
            input2.send_keys(passworsArr[random]) #password
            button = driver.find_element("xpath", "//button[@class='ant-btn ant-btn-primary login__signin-button__button']")
            button.click()
            loginFinished = True
        except Exception:
            pass

        if not (loginFinished):
            if ((loops - repeatedTimes) == 1):
                driver.quit()
                AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible Iniciar sesión en predict.",  userArr[random], 'Neurons')
                return {"message": f"send alert" }
            else:
                driver.quit()
                repeatedTimes += 1
                continue 
        
        # # GO TO PREDICT PAGE
        delay = 5 #seconds
        predictPage = 0 # times repeated
        predictPageFinished = False
        while (predictPage < 2):
            try:
                #predictButton = WebDriverWait(driver, delay).until(EC.presence_of_element_located(("css selector", "div.dashboard__predict")))
                predictButton = WebDriverWait(driver, delay).until(EC.element_to_be_clickable(("xpath", "//a[@href='"+"/predict"+"']"))) #probar llegar hasta carperta
                print("page ready")
                predictButton.click()
                predictPageFinished = True
                break
            except TimeoutException:
                print("mucho tiempo")
                predictPage = predictPage + 1
                pass

        if not (predictPageFinished):
            if ((loops - repeatedTimes) == 1):
                driver.quit()
                AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible ir a al apartado de predict, es decir al dar click al botón no se logró ir a https://app.neuronsinc.com/predict se recomienda subir manualmente el archivo a analizar y luego subir el resultado (.zip) a analyzer",  userArr[random], 'Neurons')
                return {"message": f"send alert" }
            else:
                driver.quit()
                repeatedTimes += 1
                continue 
        
        # GO TO VIEW ALL FOLDERS
        try:
            ViewAll = WebDriverWait(driver, 20).until(EC.presence_of_element_located(("xpath", "//button[@class='ant-btn ant-btn-link recents-view__content__link']")))
            print("page ready")
            ViewAll.click()
        except TimeoutException:
            print("mucho tiempo")

        #GO TO TEST FOLDER
        try:
            Folder = WebDriverWait(driver, delay).until(EC.presence_of_element_located(("xpath", "//a[@href='"+folderArr[random]+"']")))
            print("page ready")
            Folder.click()
        except TimeoutException:
            print("mucho tiempo")

        #delay = 5
        if not(uploadedF):
            #UPLOAD FILES
            UploadFiles = 0
            UploadFilesFinished = False

            #time.sleep(5)

            while(UploadFiles < 3):
                try:
                    uploadButton = WebDriverWait(driver, delay).until(EC.presence_of_element_located(("xpath", "//input[@type='file']")))
                    print("page ready")
                    driver.execute_script("arguments[0].removeAttribute('style')", uploadButton)
                    uploadButton.send_keys(UploadNeuronsDir + fileName) #esta es una path local.
                    UploadFilesFinished = True
                    break
                except TimeoutException:
                    print("mucho tiempo")
                    UploadFiles = UploadFiles + 1
                    pass
                except StaleElementReferenceException:
                    print("mucho tiempo")
                    UploadFiles = UploadFiles + 1
                    pass
            
            if not (UploadFilesFinished):
                if ((loops - repeatedTimes) == 1):
                    driver.quit()
                    AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click en boton para subir el archivo para ser analizado, se recomienda revisar el archivo y subirlo manualmente para ser analizado para posteriormente subir el resultado (.zip) a analyzer",  userArr[random], 'Neurons')
                    return {"message": f"send alert" }
                else:
                    driver.quit()
                    repeatedTimes += 1
                    continue
                
            #TEMPORARY ----------------

            #awaits to go to first folder


            #time.sleep(20)
            thisdelay = 80
            timesrepeated = 0
           
            if ".mp4" in fileName:
                thisdelay = 600

            while (timesrepeated < 1):
                try:
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))

                    WebDriverWait(driver, thisdelay).until_not(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))
                    print("si lo encontro")
                    finished = True
                    break
                except TimeoutException:
                    print("no lo vio")
                    timesrepeated = timesrepeated + 1
                    pass

        if (finished):
            uploadedF = True
            if not (spanF):
                time.sleep(8)
               
                print("page ready")
                lnkss = driver.find_elements('tag name', 'a')
                
                for lnk in lnkss:
                    file = lnk.get_attribute("href")
                    if "/predict/media/" in str(file) and "knowledge.neuronsinc.com" not in str(file):
                        try:
                            span = lnk.find_element('xpath',".//strong/span[@class='highlighted-text']")
                            if str(span.text) in fileName:
                                spanFounded = True
                                break
                        except:
                            break
                        
            if spanFounded:
                spanF = True
                print(file)
                print("Aca viene el span", span.text)
                # IR al archivo despues de obtener su href
                #thisFile = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(('xpath', "//a[@href='"+file[26:]+"']")))
                #thisFile.click()

                #Moverse encima del archivo despues de obtener su href
                moveHref = 0
                moveHrefFinished = False

                while (moveHrefFinished < 2):
                    try:
                        f = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(('xpath', "//a[@href='"+file[26:]+"']")))
                        thisFile = ActionChains(driver).move_to_element(f)
                        thisFile.perform()
                        moveHrefFinished = True
                        break
                    except:
                        moveHref = moveHref + 1
                        pass

                if not (moveHrefFinished):
                     if ((loops - repeatedTimes) == 1):
                        driver.quit()
                        AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible encontrar el archivo a tiempo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                        return {"message": f"send alert" }
                     else:
                         driver.quit()
                         repeatedTimes += 1
                         continue

                #Descargar el zip


                delay = 5
                #Sí es un video unicamente aparece un boton sin dropdown sino es el dropdown
                if ".mp4" in fileName:
                    # try:
                    #     DownloadButton = WebDriverWait(driver, 30).until(EC.presence_of_element_located(("xpath", "//button[@class='ant-btn ant-btn-default download-details--without-dropdown']")))
                    #     DownloadButton.click()
                    # except TimeoutException:
                    #     print("mucho tiempo")
                    #CLICK MENU IN IMAGE (HOVER)
                    menuClick = 0
                    menuClickFinished = False

                    while (menuClick < 2):
                        try:
                            DownloadButton = WebDriverWait(driver, 15).until(EC.presence_of_element_located(("xpath", "//span[@class='anticon anticon-more ant-dropdown-trigger actions-menu__icon actions-menu item-actions__actions-menu']")))
                            DownloadButton.click()
                            menuClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            menuClick = menuClick + 1
                            pass
                    
                    if not (menuClickFinished):
                         if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón para abrir el menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return {"message": f"send alert" }
                         else:
                             driver.quit()
                             repeatedTimes +=1
                             continue

                    #CLICK EN BOTÓN DE DOWNLOAD EN MENÚ
                    downloadClick = 0
                    downloadClickFinished = False

                    while(downloadClick < 2):
                        try:
                            ResultsButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light menu-contents']/li[3]")))
                            print("page ready")
                            ResultsButton.click()
                            downloadClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            downloadClick = downloadClick + 1
                            pass
                    
                    if not (downloadClickFinished):
                         if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón de download en el  menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return {"message": f"send alert" }
                         else:
                             driver.quit()
                             repeatedTimes += 1
                             continue
                    
                else:
                    #abrir menú
                    # try:
                    #     DownloadButton = WebDriverWait(driver, 5).until(EC.presence_of_element_located(("xpath", "//button[@class='ant-btn ant-btn-default ant-dropdown-trigger download-details__action-btn download-details']")))
                    #     DownloadButton.click()
                    # except TimeoutException:
                    #     print("mucho tiempo")

                    menuClick = 0
                    menuClickFinished = False

                    while (menuClick < 2):
                        try:
                            DownloadButton = WebDriverWait(driver, 15).until(EC.presence_of_element_located(("xpath", "//span[@class='anticon anticon-more ant-dropdown-trigger actions-menu__icon actions-menu item-actions__actions-menu']")))
                            DownloadButton.click()
                            menuClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            menuClick = menuClick + 1
                            pass

                    if not (menuClickFinished):
                         if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón para abrir el menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return {"message": f"send alert" }
                         else:
                             driver.quit()
                             repeatedTimes += 1
                             continue
                    
                    #Boton de download
                    # try:
                    #     ResultsButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light']/li[1]")))
                    #     print("page ready")
                    #     ResultsButton.click()
                    # except TimeoutException:
                    #     print("mucho tiempo")

                    downloadClick = 0
                    downloadClickFinished = False

                    while(downloadClick < 2):    
                        try:
                            ResultsButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light menu-contents']/li[3]")))
                            print("page ready")
                            ResultsButton.click()
                            downloadClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            downloadClick = downloadClick + 1
                            pass

                    
                    if not (downloadClickFinished):
                         if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón de download en el  menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return {"message": f"send alert" }
                         else:
                             driver.quit()
                             repeatedTimes += 1
                             continue


                # When is downloading awaits

                if (".png" in fileName):
                    zipName = fileName.replace(".png", "_results.zip")
                    
                elif (".jpg" in fileName):
                    zipName = fileName.replace(".jpg", "_results.zip")
                elif (".jpeg" in fileName):
                    zipName = fileName.replace(".jpeg", "_results.zip")
                elif (".mp4" in fileName):
                    zipName = fileName.replace(".mp4", "_results.zip")

                satisfactorio = False
                try:
                    #WebDriverWait(driver, 1).until(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))
                    #print("paso de aca")
                    d = WebDriverWait(driver, 60).until_not(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))
                    if d:
                        # if ".mp4" in fileName:
                        #     time.sleep(60.0)
                        # else:
                        #     time.sleep(10.0)
                        src_path = ""
                        if (SrcPath):
                            src_path = r"C:\Users\Dev1\Desktop\ApiBotAnalyzer"
                        else:
                            src_path = "."

                        event_handler = Handler()
                        observer = watchdog.observers.Observer()
                        observer.schedule(event_handler, path=src_path, recursive=True)
                        observer.start()
                        t_end = time.time() + (60 * 1)
                        try:
                            while(time.time() < t_end):
                                #time.sleep(1)
                                if (zipName in str(evento) and "crdownload" not in str(evento)):
                                    satisfactorio = True
                                    print("Evento para poder descargar zip -->", evento)
                                    observer.stop()
                                    observer.join()
                                    break
                                #print("aca viene el eventon", evento)
                        except KeyboardInterrupt:
                                observer.stop()
                                observer.join()
                        if (satisfactorio):
                            print("zip descargado")
                            driver.quit()
                        else:
                            observer.stop()
                            observer.join()
                            driver.quit()
                            print("No se logró descargar el zip ya que tardó más de 60 segundos en descargarse")        
                except TimeoutException:
                    print("prolemas")

                #Sending zip to save it on backend of analyzer
                if (satisfactorio):
                    print(id_folder)
                    print(token)
                    data = {'id_folder': id_folder}
                    fo = open(RootPath + zipName, 'rb')
                    file = {'image': fo} # la ruta debe ser cambiada por la ruta del servidor
                    headers = {'Authorization': token}
                    r = requests.post(url= Backend + '/Stimulus/Upload', files=file ,data=data, headers=headers)
                    jsonResponse = r.json()
                    # Eliminar archivo y zip.
                    fo.close()
                    remove(fileName)
                    if ("successfull" in str(jsonResponse)):
                        remove(zipName)
                        return {"message": f"Successfully uploaded"}
                    else:
                        remove(zipName)
                        return {"message": f"{jsonResponse}"}
                else:
                     if ((loops - repeatedTimes) == 1):
                        driver.quit()
                        AvisoSoporte(tipo, id_folder, fileName,token, "Se tardó más de 60 segundos en descargar y armar el zip del resultado, es decir si se subió el estímulo a predict pero la descarga no se completo a tiempo", userArr[random], 'Neurons')
                        return {"message": f"send alert"}  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
                     else:
                         driver.quit()
                         repeatedTimes += 1
                         continue
            
                #return {"message": f"Successfully uploaded {jsonResponse, id_folder, userCreation}"}
            else:
                 if ((loops - repeatedTimes) == 1):
                    driver.quit()
                    AvisoSoporte(tipo, id_folder, fileName,token, "ocurrió un error al intentar encontrar el archivo en predict es posible que si se analizara o no, se recomienda revisar y sino está subir la imagen para ser analizada y subir el resultado",  userArr[random], 'Neurons')
                    return {"message": f"send alert" }  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
                 else:
                     driver.quit()
                     repeatedTimes += 1
                     continue
        else:
            driver.quit()
            AvisoSoporte(tipo, id_folder, fileName,token, "Predict tardó demasiado tiempo en responder que ya se había subido el archivo, por lo tanto se debe revisar si se subió o no",  userArr[random], 'Neurons')
            return {"message": f"send alert"}
            #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien era


@app.post("/v2/singleFile")
def singleFile(t: Request, id_folder: str = Form(), id_stimulus: str = Form(), file: str = Form(), fileN: str = Form()):
    token = t.headers.get('Authorization')
    try:
        today = datetime.now()
        originalName = fileN
        extension = ''
        tipo = 0
        if (".png" in originalName or ".PNG" in originalName):
            extension = '.png'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpg" in originalName or ".JPG" in originalName):
            extension = '.jpg'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpeg" in originalName or ".JPEG" in originalName):
            extension = '.jpeg'
            originalName = originalName[0: len(originalName) - 5]
        elif (".mp4" in originalName or ".MP4" in originalName):
            extension = '.mp4'
            originalName = originalName[0: len(originalName) - 4]
            tipo = 1

        fileName = str(today.day) + str(today.month) + str(today.year) + "_" +str(today.hour)+str(today.minute)+str(today.second) + (re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))) + extension
        
        img_data = requests.get(file).content
        with open(fileName, 'wb') as f:
            f.write(img_data)
    except Exception:
        return {"message": "Error uploading the file"}
    finally:
        f.close()

    # userArr = ['erick.moreno@neuronsinc.com', 'juan.roberto@troiatec.com']
    # passworsArr = ['Nila1976', 'Troiatec060112#']
    # folderArr = ['/predict/folder/aceacbd2-3c2d-426f-97a0-5411d18920d5', '/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e']
    #urlArr = ['https://app.neuronsinc.com/predict/folder/aceacbd2-3c2d-426f-97a0-5411d18920d5', 'https://app.neuronsinc.com/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e']

    random = GetNumber()
    
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    #------------This is for headless mode -------------------
    #chrome_options.add_argument("--headless=new") #<-- para versiones de Chrome >= 109
    #chrome_options.add_argument("--headless=chrome") #<-- para versiones de Chrome >= 96 , <= 108
    chrome_options.add_argument(Headless) #<- actual funcionando en servidor (version 108)
    chrome_options.add_argument("--window-size=1920,1080")
    #---------------------------------------------------------

    #-----------This is for download directory----------------
    if (DownloadDir):
        chrome_prefs = {"download.default_directory": r"C:\Users\Dev1\Desktop\ApiBotAnalyzer"}
        chrome_options.experimental_options["prefs"] = chrome_prefs
    #----------------------------------------------------------

    repeatedTimes = 0
    loops = 2

    uploadedF = False
    spanF = False
    finished = False
    spanFounded = False
    file =''
    span = ''

    while(repeatedTimes < loops):

        loginFinished = False

        try:
            driver = webdriver.Chrome(options=chrome_options)
            #driver.get('https://app.neuronsinc.com/')
            driver.get(urlArr[random])
            driver.maximize_window()
            input1 = driver.find_element("name", "email")
            input2 = driver.find_element("name", "password")
            input1.send_keys(userArr[random]) #Email
            input2.send_keys(passworsArr[random]) #password
            button = driver.find_element("xpath", "//button[@class='ant-btn ant-btn-primary login__signin-button__button']")
            button.click()
            loginFinished = True
        except Exception:
            pass

        if not (loginFinished):
            if ((loops - repeatedTimes) == 1):
                driver.quit()
                AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible Iniciar sesión en predict.",  userArr[random], 'Neurons')
                return {"message": f"send alert" }
            else:
                driver.quit()
                repeatedTimes += 1
                continue  

        # # GO TO PREDICT PAGE
        # delay = 5 #seconds
        # predictPage = 0 # times repeated
        # predictPageFinished = False
        # while (predictPage < 2):
        #     try:
        #         predictButton = WebDriverWait(driver, delay).until(EC.presence_of_element_located(("css selector", "div.dashboard__predict")))
        #         print("page ready")
        #         predictButton.click()
        #         predictPageFinished = True
        #         break
        #     except TimeoutException:
        #         print("mucho tiempo")
        #         predictPage = predictPage + 1
        #         pass

        # if not (predictPageFinished):
        #     driver.quit()
        #     AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible ir a al apartado de predict, es decir al dar click al botón no se logró ir a https://app.neuronsinc.com/predict se recomienda subir manualmente el archivo a analizar y luego subir el resultado (.zip) a analyzer",  userArr[random])
        #     return {"message": f"send alert" }

        # # GO TO VIEW ALL FOLDERS
        # try:
        #     ViewAll = WebDriverWait(driver, 20).until(EC.presence_of_element_located(("xpath", "//button[@class='ant-btn ant-btn-link recents-view__content__link']")))
        #     print("page ready")
        #     ViewAll.click()
        # except TimeoutException:
        #     print("mucho tiempo")

        # #GO TO TEST FOLDER
        # try:
        #     Folder = WebDriverWait(driver, delay).until(EC.presence_of_element_located(("xpath", "//a[@href='"+folderArr[random]+"']")))
        #     print("page ready")
        #     Folder.click()
        # except TimeoutException:
        #     print("mucho tiempo")
        delay = 5

        if not(uploadedF):
            #UPLOAD FILES
            UploadFiles = 0
            UploadFilesFinished = False

            while(UploadFiles < 3):
                try:
                    uploadButton = WebDriverWait(driver, delay).until(EC.presence_of_element_located(("xpath", "//input[@type='file']")))
                    print("page ready")
                    driver.execute_script("arguments[0].removeAttribute('style')", uploadButton)
                    uploadButton.send_keys(UploadNeuronsDir + fileName) #esta es una path local.
                    UploadFilesFinished = True
                    break
                except TimeoutException:
                    print("mucho tiempo")
                    UploadFiles = UploadFiles + 1
                    pass
                except StaleElementReferenceException:
                    print("mucho tiempo")
                    UploadFiles = UploadFiles + 1
                    pass
            
            if not (UploadFilesFinished):
                if ((loops - repeatedTimes) == 1):
                    driver.quit()
                    AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click en boton para subir el archivo para ser analizado, se recomienda revisar el archivo y subirlo manualmente para ser analizado para posteriormente subir el resultado (.zip) a analyzer",  userArr[random], 'Neurons')
                    return {"message": f"send alert" }
                else:
                    driver.quit()
                    repeatedTimes += 1
                    continue

            #TEMPORARY ----------------

            #awaits to go to first folder


            #time.sleep(20)
            thisdelay = 80
            timesrepeated = 0
           
            if ".mp4" in fileName:
                thisdelay = 600

            while (timesrepeated < 1):
                try:
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))

                    WebDriverWait(driver, thisdelay).until_not(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))
                    print("si lo encontro")
                    finished = True
                    break
                except TimeoutException:
                    print("no lo vio")
                    timesrepeated = timesrepeated + 1
                    pass

        if (finished):
            uploadedF = True
            if not (spanF):
                time.sleep(8)
               
                print("page ready")
                lnkss = driver.find_elements('tag name', 'a')
                
                for lnk in lnkss:
                    file = lnk.get_attribute("href")
                    if "/predict/media/" in str(file) and "knowledge.neuronsinc.com" not in str(file):
                        try:
                            span = lnk.find_element('xpath',".//strong/span[@class='highlighted-text']")
                            if str(span.text) in fileName:
                                spanFounded = True
                                break
                        except:
                            break
                        
            if spanFounded:
                spanF = True
                print(file)
                print("Aca viene el span", span.text)
                # IR al archivo despues de obtener su href
                #thisFile = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(('xpath', "//a[@href='"+file[26:]+"']")))
                #thisFile.click()

                #Moverse encima del archivo despues de obtener su href
                moveHref = 0
                moveHrefFinished = False

                while (moveHrefFinished < 2):
                    try:
                        f = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(('xpath', "//a[@href='"+file[26:]+"']")))
                        thisFile = ActionChains(driver).move_to_element(f)
                        thisFile.perform()
                        moveHrefFinished = True
                        break
                    except:
                        moveHref = moveHref + 1
                        pass

                if not (moveHrefFinished):
                     if ((loops - repeatedTimes) == 1):
                        driver.quit()
                        AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible encontrar el archivo a tiempo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                        return {"message": f"send alert" }
                     else:
                         driver.quit()
                         repeatedTimes += 1
                         continue

                #Descargar el zip


                delay = 5
                #Sí es un video unicamente aparece un boton sin dropdown sino es el dropdown
                if ".mp4" in fileName:
                    # try:
                    #     DownloadButton = WebDriverWait(driver, 30).until(EC.presence_of_element_located(("xpath", "//button[@class='ant-btn ant-btn-default download-details--without-dropdown']")))
                    #     DownloadButton.click()
                    # except TimeoutException:
                    #     print("mucho tiempo")
                    #CLICK MENU IN IMAGE (HOVER)
                    menuClick = 0
                    menuClickFinished = False

                    while (menuClick < 2):
                        try:
                            DownloadButton = WebDriverWait(driver, 15).until(EC.presence_of_element_located(("xpath", "//span[@class='anticon anticon-more ant-dropdown-trigger actions-menu__icon actions-menu item-actions__actions-menu']")))
                            DownloadButton.click()
                            menuClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            menuClick = menuClick + 1
                            pass
                    
                    if not (menuClickFinished):
                        if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón para abrir el menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return {"message": f"send alert" }
                        else:
                            driver.quit()
                            repeatedTimes +=1
                            continue

                    #CLICK EN BOTÓN DE DOWNLOAD EN MENÚ
                    downloadClick = 0
                    downloadClickFinished = False

                    while(downloadClick < 2):
                        try:
                            ResultsButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light menu-contents']/li[3]")))
                            print("page ready")
                            ResultsButton.click()
                            downloadClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            downloadClick = downloadClick + 1
                            pass
                    
                    if not (downloadClickFinished):
                        if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón de download en el  menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return {"message": f"send alert" }
                        else:
                            driver.quit()
                            repeatedTimes += 1
                            continue
                    
                else:
                    #abrir menú
                    # try:
                    #     DownloadButton = WebDriverWait(driver, 5).until(EC.presence_of_element_located(("xpath", "//button[@class='ant-btn ant-btn-default ant-dropdown-trigger download-details__action-btn download-details']")))
                    #     DownloadButton.click()
                    # except TimeoutException:
                    #     print("mucho tiempo")

                    menuClick = 0
                    menuClickFinished = False

                    while (menuClick < 2):
                        try:
                            DownloadButton = WebDriverWait(driver, 15).until(EC.presence_of_element_located(("xpath", "//span[@class='anticon anticon-more ant-dropdown-trigger actions-menu__icon actions-menu item-actions__actions-menu']")))
                            DownloadButton.click()
                            menuClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            menuClick = menuClick + 1
                            pass

                    if not (menuClickFinished):
                        if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón para abrir el menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return {"message": f"send alert" }
                        else:
                            driver.quit()
                            repeatedTimes += 1
                            continue
                    
                    #Boton de download
                    # try:
                    #     ResultsButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light']/li[1]")))
                    #     print("page ready")
                    #     ResultsButton.click()
                    # except TimeoutException:
                    #     print("mucho tiempo")

                    downloadClick = 0
                    downloadClickFinished = False

                    while(downloadClick < 2):    
                        try:
                            ResultsButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light menu-contents']/li[3]")))
                            print("page ready")
                            ResultsButton.click()
                            downloadClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            downloadClick = downloadClick + 1
                            pass

                    
                    if not (downloadClickFinished):
                        if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón de download en el  menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return {"message": f"send alert" }
                        else:
                            driver.quit()
                            repeatedTimes += 1
                            continue


                # When is downloading awaits

                if (".png" in fileName):
                    zipName = fileName.replace(".png", "_results.zip")
                    
                elif (".jpg" in fileName):
                    zipName = fileName.replace(".jpg", "_results.zip")
                elif (".jpeg" in fileName):
                    zipName = fileName.replace(".jpeg", "_results.zip")
                elif (".mp4" in fileName):
                    zipName = fileName.replace(".mp4", "_results.zip")

                satisfactorio = False
                try:
                    #WebDriverWait(driver, 1).until(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))
                    #print("paso de aca")
                    d = WebDriverWait(driver, 60).until_not(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))
                    if d:
                        # if ".mp4" in fileName:
                        #     time.sleep(60.0)
                        # else:
                        #     time.sleep(10.0)
                        src_path = ""
                        if (SrcPath):
                            src_path = r"C:\Users\Dev1\Desktop\ApiBotAnalyzer"
                        else:
                            src_path = "."

                        event_handler = Handler()
                        observer = watchdog.observers.Observer()
                        observer.schedule(event_handler, path=src_path, recursive=True)
                        observer.start()
                        t_end = time.time() + (60 * 1)
                        try:
                            while(time.time() < t_end):
                                #time.sleep(1)
                                if (zipName in str(evento) and "crdownload" not in str(evento)):
                                    satisfactorio = True
                                    print("Evento para poder descargar zip -->", evento)
                                    observer.stop()
                                    observer.join()
                                    break
                                #print("aca viene el eventon", evento)
                        except KeyboardInterrupt:
                                observer.stop()
                                observer.join()


                        if (satisfactorio):
                            print("zip descargado")
                            driver.quit()
                        else:
                            observer.stop()
                            observer.join()
                            driver.quit()
                            print("No se logró descargar el zip ya que tardó más de 60 segundos en descargarse")        
                except TimeoutException:
                    print("prolemas")

                #Sending zip to save it on backend of analyzer
                if (satisfactorio):
                    print(id_folder)
                    print(token)
                    data = {'id_folder': id_folder, 'idStimulus': id_stimulus}
                    fo = open(RootPath + zipName, 'rb')
                    file = {'image': fo} # la ruta debe ser cambiada por la ruta del servidor
                    headers = {'Authorization': token}
                    r = requests.post(url=Backend + '/Stimulus/UploadNeuronsBot', files=file ,data=data, headers=headers)
                    jsonResponse = r.json()
                    # Eliminar archivo y zip.
                    fo.close()
                    remove(fileName)
                    if ("successfull" in str(jsonResponse)):
                        remove(zipName)
                        return {"message": f"Successfully uploaded"}
                    else:
                        remove(zipName)
                        return {"message": f"{jsonResponse}"}
                else:
                    if ((loops - repeatedTimes) == 1):
                        driver.quit()
                        AvisoSoporte(tipo, id_folder, fileName,token, "Se tardó más de 60 segundos en descargar y armar el zip del resultado, es decir si se subió el estímulo a predict pero la descarga no se completo a tiempo", userArr[random], 'Neurons')
                        return {"message": f"send alert"}  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
                    else:
                        driver.quit()
                        repeatedTimes += 1
                        continue  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
            
                #return {"message": f"Successfully uploaded {jsonResponse, id_folder, userCreation}"}
            else:
                if ((loops - repeatedTimes) == 1):
                    driver.quit()
                    AvisoSoporte(tipo, id_folder, fileName,token, "ocurrió un error al intentar encontrar el archivo en predict es posible que si se analizara o no, se recomienda revisar y sino está subir la imagen para ser analizada y subir el resultado",  userArr[random], 'Neurons')
                    return {"message": f"send alert" }  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
                else:
                    driver.quit()
                    repeatedTimes += 1
                    continue  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
        else:
            driver.quit()
            AvisoSoporte(tipo, id_folder, fileName,token, "Predict tardó demasiado tiempo en responder que ya se había subido el archivo, por lo tanto se debe revisar si se subió o no",  userArr[random], 'Neurons')
            return {"message": f"send alert"}
            #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien era


@app.post("/AttentionInsight")
def singleFile(study_name: str = Form(), study_type: str = Form(), content_type: str = Form(), file: str = Form(), fileN: str = Form(), ApiKey: str = Form()):
    try:
        today = datetime.now()
        originalName = fileN
        extension = ''
        tipo = 0
        if (".png" in originalName or ".PNG" in originalName):
            extension = '.png'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpg" in originalName or ".JPG" in originalName):
            extension = '.jpg'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpeg" in originalName or ".JPEG" in originalName):
            extension = '.jpeg'
            originalName = originalName[0: len(originalName) - 5]
        elif (".mp4" in originalName or ".MP4" in originalName):
            extension = '.mp4'
            originalName = originalName[0: len(originalName) - 4]
            tipo = 1

        fileName = "Attention"+str(today.day) + str(today.month) + str(today.year) + "_" +str(today.hour)+str(today.minute)+str(today.second) + (re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))) + extension
        
        img_data = requests.get(file).content
        with open(fileName, 'wb') as f:
            f.write(img_data)
    except Exception:
        return {"message": "Error uploading the file"}
    finally:
        f.close()
    
    data = {'study_name': study_name, 'study_type': study_type, 'content_type': content_type, 'tasks[0]': 'focus', 'tasks[1]': 'clarity_score'}
    fo = open(RootPath + fileName, 'rb')
    file = {'file': fo} # la ruta debe ser cambiada por la ruta del servidor
    headers = {'Api-key': ApiKey}
    r = requests.post(url='https://ext-api.attentioninsight.com/api/v2/studies', files=file ,data=data, headers=headers)
    jsonResponse = r.json()

    fo.close()
    if ("success" in str(jsonResponse)):
        id = jsonResponse["data"]["study_id"]
        remove(fileName)
        return id
    else:
        remove(fileName)
        return {"message": f"{jsonResponse}"}

@app.post('/data')
def data(t: Request, file: UploadFile = File(...), id_folder: str = Form()):
    token = t.headers.get('Authorization')
    try:
        today = datetime.now()
        originalName = file.filename
        extension = ''
        if (".png" in originalName or ".PNG" in originalName):
            extension = '.png'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpg" in originalName or ".JPG" in originalName):
            extension = '.jpg'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpeg" in originalName or ".JPEG" in originalName):
            extension = '.jpeg'
            originalName = originalName[0: len(originalName) - 5]
        elif (".mp4" in originalName or ".MP4" in originalName):
            extension = '.mp4'
            originalName = originalName[0: len(originalName) - 4]
        
        fileName = str(today.day) + str(today.month) + str(today.year) + "_" +str(today.hour)+str(today.minute)+str(today.second) + (re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))) + extension
        
        with open(fileName, 'wb') as f:
            shutil.copyfileobj(file.file, f)

        data = {'id_folder': id_folder}
        fo = open(RootPath + fileName, 'rb')
        ff = {'image': fo} # la ruta debe ser cambiada por la ruta del servidor
        headers = {'Authorization': token}
        r = requests.post(url=Backend + '/Stimulus/UploadStimulus', files=ff ,data=data, headers=headers)
        jsonResponse = r.json()
        fo.close()

        if ("msgError" not in str(jsonResponse)):
            remove(RootPath + fileName)
            return {"idStimulus": str(jsonResponse)}
        
    except Exception:
        return {"message": "Error uploading the file"}
    finally:
        file.file.close()
    

async def ExecuteBot(t, id_folder, id_stimulus, file, fileN, userCreation=None):
    token = t
    try:
        today = datetime.now()
        originalName = fileN
        extension = ''
        tipo = 0
        if (".png" in originalName or ".PNG" in originalName):
            extension = '.png'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpg" in originalName or ".JPG" in originalName):
            extension = '.jpg'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpeg" in originalName or ".JPEG" in originalName):
            extension = '.jpeg'
            originalName = originalName[0: len(originalName) - 5]
        elif (".mp4" in originalName or ".MP4" in originalName):
            extension = '.mp4'
            originalName = originalName[0: len(originalName) - 4]
            tipo = 1

        fileName = str(today.day) + str(today.month) + str(today.year) + "_" +str(today.hour)+str(today.minute)+str(today.second) + (re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))) + extension
        
        img_data = requests.get(file).content
        with open(fileName, 'wb') as f:
            f.write(img_data)
    except Exception:
        return  "Error uploading the file"
    finally:
        f.close()

    # userArr = ['erick.moreno@neuronsinc.com', 'juan.roberto@troiatec.com']
    # passworsArr = ['Nila1976', 'Troiatec060112#']
    # folderArr = ['/predict/folder/aceacbd2-3c2d-426f-97a0-5411d18920d5', '/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e']
    #urlArr = ['https://app.neuronsinc.com/predict/folder/aceacbd2-3c2d-426f-97a0-5411d18920d5', 'https://app.neuronsinc.com/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e']

    random = GetNumber()
    
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)

    #------------This is for headless mode -------------------
    #chrome_options.add_argument("--headless=new") #<-- para versiones de Chrome >= 109
    #chrome_options.add_argument("--headless=chrome") #<-- para versiones de Chrome >= 96 , <= 108
    chrome_options.add_argument(Headless) #<- actual funcionando en servidor (version 108)
    #chrome_options.add_argument("--window-size=1920,1080")
    #---------------------------------------------------------

    #-----------This is for download directory----------------
    if (DownloadDir):
        chrome_prefs = {"download.default_directory": r"C:\Users\Dev1\Desktop\ApiBotAnalyzer"}
        chrome_options.experimental_options["prefs"] = chrome_prefs
    #----------------------------------------------------------

    repeatedTimes = 0
    loops = 2

    uploadedF = False
    spanF = False
    finished = False
    spanFounded = False
    file =''
    span = ''

    while(repeatedTimes < loops):

        loginFinished = False

        try:
            driver = webdriver.Chrome(options=chrome_options)
            #driver.get('https://app.neuronsinc.com/')
            driver.get(urlArr[random])
            driver.maximize_window()
            time.sleep(5)
            input1 = driver.find_element("name", "email")
            input2 = driver.find_element("name", "password")
            input1.send_keys(userArr[random]) #Email
            input2.send_keys(passworsArr[random]) #password
            button = driver.find_element("xpath", "//button[@class='ant-btn ant-btn-primary login__signin-button__button']")
            button.click()
            loginFinished = True
        except Exception:
            pass

        if not (loginFinished):
            if ((loops - repeatedTimes) == 1):
                driver.quit()
                AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible Iniciar sesión en predict.",  userArr[random], 'Neurons')
                return "send alert"
            else:
                driver.quit()
                repeatedTimes += 1
                continue  

        # # GO TO PREDICT PAGE
        # delay = 5 #seconds
        # predictPage = 0 # times repeated
        # predictPageFinished = False
        # while (predictPage < 2):
        #     try:
        #         predictButton = WebDriverWait(driver, delay).until(EC.presence_of_element_located(("css selector", "div.dashboard__predict")))
        #         print("page ready")
        #         predictButton.click()
        #         predictPageFinished = True
        #         break
        #     except TimeoutException:
        #         print("mucho tiempo")
        #         predictPage = predictPage + 1
        #         pass

        # if not (predictPageFinished):
        #     driver.quit()
        #     AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible ir a al apartado de predict, es decir al dar click al botón no se logró ir a https://app.neuronsinc.com/predict se recomienda subir manualmente el archivo a analizar y luego subir el resultado (.zip) a analyzer",  userArr[random])
        #     return {"message": f"send alert" }

        # # GO TO VIEW ALL FOLDERS
        # try:
        #     ViewAll = WebDriverWait(driver, 20).until(EC.presence_of_element_located(("xpath", "//button[@class='ant-btn ant-btn-link recents-view__content__link']")))
        #     print("page ready")
        #     ViewAll.click()
        # except TimeoutException:
        #     print("mucho tiempo")

        # #GO TO TEST FOLDER
        # try:
        #     Folder = WebDriverWait(driver, delay).until(EC.presence_of_element_located(("xpath", "//a[@href='"+folderArr[random]+"']")))
        #     print("page ready")
        #     Folder.click()
        # except TimeoutException:
        #     print("mucho tiempo")
        delay = 5

        if not(uploadedF):
            #UPLOAD FILES
            UploadFiles = 0
            UploadFilesFinished = False

            while(UploadFiles < 3):
                try:
                    uploadButton = WebDriverWait(driver, delay).until(EC.presence_of_element_located(("xpath", "//input[@type='file']")))
                    print("page ready")
                    driver.execute_script("arguments[0].removeAttribute('style')", uploadButton)
                    uploadButton.send_keys(UploadNeuronsDir + fileName) #esta es una path local.
                    UploadFilesFinished = True
                    break
                except TimeoutException:
                    print("mucho tiempo")
                    UploadFiles = UploadFiles + 1
                    pass
                except StaleElementReferenceException:
                    print("mucho tiempo")
                    UploadFiles = UploadFiles + 1
                    pass
            
            if not (UploadFilesFinished):
                if ((loops - repeatedTimes) == 1):
                    driver.quit()
                    AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click en boton para subir el archivo para ser analizado, se recomienda revisar el archivo y subirlo manualmente para ser analizado para posteriormente subir el resultado (.zip) a analyzer",  userArr[random], 'Neurons')
                    return "send alert"
                else:
                    driver.quit()
                    repeatedTimes += 1
                    continue

            #TEMPORARY ----------------

            #awaits to go to first folder


            #time.sleep(20)
            thisdelay = 80
            timesrepeated = 0
           
            if ".mp4" in fileName:
                thisdelay = 600

            while (timesrepeated < 1):
                try:
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))

                    WebDriverWait(driver, thisdelay).until_not(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))
                    print("si lo encontro")
                    finished = True
                    break
                except TimeoutException:
                    print("no lo vio")
                    timesrepeated = timesrepeated + 1
                    pass

        if (finished):
            uploadedF = True
            if not (spanF):
                time.sleep(8)
               
                print("page ready")
                lnkss = driver.find_elements('tag name', 'a')
                
                for lnk in lnkss:
                    file = lnk.get_attribute("href")
                    if "/predict/media/" in str(file) and "knowledge.neuronsinc.com" not in str(file):
                        try:
                            span = lnk.find_element('xpath',".//strong/span[@class='highlighted-text']")
                            if str(span.text) in fileName:
                                spanFounded = True
                                break
                        except:
                            break
                        
            if spanFounded:
                spanF = True
                print(file)
                print("Aca viene el span", span.text)
                # IR al archivo despues de obtener su href
                #thisFile = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(('xpath', "//a[@href='"+file[26:]+"']")))
                #thisFile.click()

                #Moverse encima del archivo despues de obtener su href
                moveHref = 0
                moveHrefFinished = False

                while (moveHrefFinished < 2):
                    try:
                        f = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(('xpath', "//a[@href='"+file[26:]+"']")))
                        thisFile = ActionChains(driver).move_to_element(f)
                        thisFile.perform()
                        moveHrefFinished = True
                        break
                    except:
                        moveHref = moveHref + 1
                        pass

                if not (moveHrefFinished):
                     if ((loops - repeatedTimes) == 1):
                        driver.quit()
                        AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible encontrar el archivo a tiempo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                        return "send alert" 
                     else:
                         driver.quit()
                         repeatedTimes += 1
                         continue

                #Descargar el zip


                delay = 5
                #Sí es un video unicamente aparece un boton sin dropdown sino es el dropdown
                if ".mp4" in fileName:
                    # try:
                    #     DownloadButton = WebDriverWait(driver, 30).until(EC.presence_of_element_located(("xpath", "//button[@class='ant-btn ant-btn-default download-details--without-dropdown']")))
                    #     DownloadButton.click()
                    # except TimeoutException:
                    #     print("mucho tiempo")
                    #CLICK MENU IN IMAGE (HOVER)
                    menuClick = 0
                    menuClickFinished = False

                    while (menuClick < 2):
                        try:
                            DownloadButton = WebDriverWait(driver, 15).until(EC.presence_of_element_located(("xpath", "//span[@class='anticon anticon-more ant-dropdown-trigger actions-menu__icon actions-menu item-actions__actions-menu']")))
                            DownloadButton.click()
                            menuClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            menuClick = menuClick + 1
                            pass
                    
                    if not (menuClickFinished):
                        if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón para abrir el menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return "send alert"
                        else:
                            driver.quit()
                            repeatedTimes +=1
                            continue

                    #CLICK EN BOTÓN DE DOWNLOAD EN MENÚ
                    downloadClick = 0
                    downloadClickFinished = False

                    while(downloadClick < 2):
                        try:
                            ResultsButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light menu-contents']/li[3]")))
                            print("page ready")
                            ResultsButton.click()
                            downloadClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            downloadClick = downloadClick + 1
                            pass
                    
                    if not (downloadClickFinished):
                        if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón de download en el  menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return "send alert"
                        else:
                            driver.quit()
                            repeatedTimes += 1
                            continue
                    
                else:
                    #abrir menú
                    # try:
                    #     DownloadButton = WebDriverWait(driver, 5).until(EC.presence_of_element_located(("xpath", "//button[@class='ant-btn ant-btn-default ant-dropdown-trigger download-details__action-btn download-details']")))
                    #     DownloadButton.click()
                    # except TimeoutException:
                    #     print("mucho tiempo")

                    menuClick = 0
                    menuClickFinished = False

                    while (menuClick < 2):
                        try:
                            DownloadButton = WebDriverWait(driver, 15).until(EC.presence_of_element_located(("xpath", "//span[@class='anticon anticon-more ant-dropdown-trigger actions-menu__icon actions-menu item-actions__actions-menu']")))
                            DownloadButton.click()
                            menuClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            menuClick = menuClick + 1
                            pass

                    if not (menuClickFinished):
                        if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón para abrir el menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return "send alert"
                        else:
                            driver.quit()
                            repeatedTimes += 1
                            continue
                    
                    #Boton de download
                    # try:
                    #     ResultsButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light']/li[1]")))
                    #     print("page ready")
                    #     ResultsButton.click()
                    # except TimeoutException:
                    #     print("mucho tiempo")

                    downloadClick = 0
                    downloadClickFinished = False

                    while(downloadClick < 2):    
                        try:
                            ResultsButton = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(("xpath", "//ul[@class='ant-dropdown-menu ant-dropdown-menu-root ant-dropdown-menu-vertical ant-dropdown-menu-light menu-contents']/li[3]")))
                            print("page ready")
                            ResultsButton.click()
                            downloadClickFinished = True
                            break
                        except TimeoutException:
                            print("mucho tiempo")
                            downloadClick = downloadClick + 1
                            pass

                    
                    if not (downloadClickFinished):
                        if ((loops - repeatedTimes) == 1):
                            driver.quit()
                            AvisoSoporte(tipo, id_folder, fileName,token, "No fue posible dar click al botón de download en el  menú que se encuentra encima de cada estímulo, se recomienda revisar en la carpeta 'test' de la cuenta en la que se subió el archivo ya que probablemente si se logró analizar pero no descargar el (.zip)",  userArr[random], 'Neurons')
                            return "send alert"
                        else:
                            driver.quit()
                            repeatedTimes += 1
                            continue


                # When is downloading awaits

                if (".png" in fileName):
                    zipName = fileName.replace(".png", "_results.zip")
                    
                elif (".jpg" in fileName):
                    zipName = fileName.replace(".jpg", "_results.zip")
                elif (".jpeg" in fileName):
                    zipName = fileName.replace(".jpeg", "_results.zip")
                elif (".mp4" in fileName):
                    zipName = fileName.replace(".mp4", "_results.zip")

                satisfactorio = False
                try:
                    #WebDriverWait(driver, 1).until(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))
                    #print("paso de aca")
                    d = WebDriverWait(driver, 60).until_not(EC.presence_of_element_located(("xpath", "//span[@class='ant-typography file-uploader__auxtext']")))
                    if d:
                        # if ".mp4" in fileName:
                        #     time.sleep(60.0)
                        # else:
                        #     time.sleep(10.0)
                        src_path = ""
                        if (SrcPath):
                            src_path = r"C:\Users\Dev1\Desktop\ApiBotAnalyzer"
                        else:
                            src_path = "."

                        event_handler = Handler()
                        observer = watchdog.observers.Observer()
                        observer.schedule(event_handler, path=src_path, recursive=True)
                        observer.start()
                        t_end = time.time() + (60 * 1)
                        try:
                            while(time.time() < t_end):
                                #time.sleep(1)
                                if (zipName in str(evento) and "crdownload" not in str(evento)):
                                    satisfactorio = True
                                    print("Evento para poder descargar zip -->", evento)
                                    observer.stop()
                                    observer.join()
                                    break
                                #print("aca viene el eventon", evento)
                        except KeyboardInterrupt:
                                observer.stop()
                                observer.join()
                        if (satisfactorio):
                            print("zip descargado")
                            driver.quit()
                        else:
                            observer.stop()
                            observer.join()
                            driver.quit()
                            print("No se logró descargar el zip ya que tardó más de 60 segundos en descargarse")        
                except TimeoutException:
                    print("prolemas")

                #Sending zip to save it on backend of analyzer
                if (satisfactorio):
                    print(id_folder)
                    print(token)
                    data = {'id_folder': id_folder, 'idStimulus': id_stimulus} if userCreation == None else {'id_folder': id_folder, 'idStimulus': id_stimulus, 'user_creation': userCreation}
                    fo = open(RootPath + zipName, 'rb')
                    file = {'image': fo} # la ruta debe ser cambiada por la ruta del servidor
                    headers = {'Authorization': token}
                    r = requests.post(url=Backend + '/Stimulus/UploadNeuronsBot', files=file ,data=data, headers=headers)
                    jsonResponse = r.json()
                    # Eliminar archivo y zip.
                    fo.close()
                    remove(fileName)
                    if ("successfull" in str(jsonResponse)):
                        remove(zipName)
                        return "Successfully uploaded"
                    else:
                        remove(zipName)
                        return jsonResponse
                else:
                    if ((loops - repeatedTimes) == 1):
                        driver.quit()
                        AvisoSoporte(tipo, id_folder, fileName,token, "Se tardó más de 60 segundos en descargar y armar el zip del resultado, es decir si se subió el estímulo a predict pero la descarga no se completo a tiempo", userArr[random], 'Neurons')
                        return "send alert"  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
                    else:
                        driver.quit()
                        repeatedTimes += 1
                        continue  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
            
                #return {"message": f"Successfully uploaded {jsonResponse, id_folder, userCreation}"}
            else:
                if ((loops - repeatedTimes) == 1):
                    driver.quit()
                    AvisoSoporte(tipo, id_folder, fileName,token, "ocurrió un error al intentar encontrar el archivo en predict es posible que si se analizara o no, se recomienda revisar y sino está subir la imagen para ser analizada y subir el resultado",  userArr[random], 'Neurons')
                    return "send alert"  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
                else:
                    driver.quit()
                    repeatedTimes += 1
                    continue  #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien er
        else:
            driver.quit()
            AvisoSoporte(tipo, id_folder, fileName,token, "Predict tardó demasiado tiempo en responder que ya se había subido el archivo, por lo tanto se debe revisar si se subió o no",  userArr[random], 'Neurons')
            return "send alert"
            #acaá enviar correo con video/imagen que no pudo ser subida, nombre y de quien era




@app.websocket("/StimulusAnalyze")
async def websocket_endpoint(webSocket: WebSocket):
    await webSocket.accept()
    while True:
        request = await webSocket.receive_json()
        #file = await webSocket.receive_bytes()

        # data = {'id_folder': request["idfolder"]}
        # fo = open('C:/Users/Dev1/Desktop/ApiBotAnalyzer/' + request["file"], 'rb')
        # file = {'image': fo} # la ruta debe ser cambiada por la ruta del servidor
        # headers = {'Authorization': request["token"]}
        # r = requests.post(url=Backend + '/Stimulus/UploadStimulus', files=file ,data=data, headers=headers)
        # jsonResponse = r.json()
        # fo.close()
        idStimulus = request["idStimulus"]
        isVideo = True
        tipo = 1
        if not(len(idStimulus) == 0):
            data = {'idStimulus': idStimulus} 
            headers = {'Authorization': request["token"]}

            getStimulus = requests.post(url=Backend + '/Stimulus/getStimulusUrl',data=data, headers=headers)
            getS = getStimulus.json()

            #esta linea creo que no hace nada
            Apic,d,h = ExecuteNeurons(1, getStimulus.json(), idStimulus, request["token"])
            #d = {"file": getS[""], "id_folder": 1, "id_stimulus": str(jsonResponse), "fileN": "Fondo.jpg"}
            #neurons = asyncio.create_task(async_aiohttp_post("http://127.0.0.1:8000/v2/singleFile", data=d, headers=headers))
            
            if (".mp4" not in d["file"]):
                isVideo = False
                tipo = 0
                studySettings = {"study_name": getS["title"], "study_type": "general", "content_type": "general", 'tasks[0]': 'focus', 'tasks[1]': 'clarity_score'}
                #attention = asyncio.create_task(ExecuteAttention(2, getS, idStimulus, request["token"], studySettings, webSocket))
                #await attention

            #neurons = asyncio.create_task(ExecuteBot(request["token"], d["id_folder"], d["id_stimulus"], d["file"], d["fileN"]))

            #await neurons

            if (".mp4" not in d["file"]):
                isVideo = False
                tipo = 0
                #feng = asyncio.create_task(ExecuteFengGui(3,getS, idStimulus, request["token"], webSocket))
                #await feng
            #res = asyncio.gather(asyncio.create_task(ExecuteAttention(2, getS, str(jsonResponse), request["token"], studySettings)),  asyncio.create_task(async_aiohttp_post("http://127.0.0.1:8000/v2/singleFile", data=d, headers=headers)))
            
            # async def main():
            #     tasks = [async_aiohttp_post("http://127.0.0.1:8000/v2/singleFile", data=d, headers=headers), ExecuteAttention(2, getS, str(jsonResponse), request["token"], studySettings)]
            #     await asyncio.gather(*tasks)

            
            # tasks = asyncio.create_task(main())

            # if (res.done()):
            #     webSocket.send_json({
            #         "message": f"done"
            #     })
            #Corregir el uso de attention cuando es video!!!
            #print(neurons, attention)

            if not (isVideo):
                results = asyncio.gather(ExecuteAttention(2, getS, idStimulus, request["token"], studySettings, webSocket)
                                        , ExecuteBot(request["token"], d["id_folder"], d["id_stimulus"], d["file"], d["fileN"])
                                        , ExecuteFengGui(3,getS, idStimulus, request["token"], webSocket))

                await results
                positions = [i for i in range(len(results.result())) if any([x in results.result()[i] for x in ["Successfully uploaded", "successful", "Successful"]])]
                if (len(positions) == 3):
                    await webSocket.send_json({
                             "message": f"Done"
                         })
                else:
                     await webSocket.send_json({
                            "message": f"Failed",
                            #"error": f"{neurons.result()}"
                            })

            else:
                results = asyncio.gather(ExecuteBot(request["token"], d["id_folder"], d["id_stimulus"], d["file"], d["fileN"]))

                if (positions.result()[0] == "Successfull" or positions.result()[0] == "successful"):
                    await webSocket.send_json({
                             "message": f"Done"
                         })
                else:
                     await webSocket.send_json({
                            "message": f"Failed",
                            #"error": f"{neurons.result()}"
                            })


            print(results)

           
            # if not (isVideo):
            #     print("entro a donde deberiaaaaaaa")
            #     arr = [neurons, attention, feng]
            #     names = ["Neurons", "Attention", "Feng"]
            #     if(neurons.done() and attention.done() and feng.done()):
            #         positions = [i for i in range(len(arr)) if any([x in arr[i].result() for x in ["Successfully uploaded", "successful", "Successful"]])]
            #         print("Successfully uploaded" in neurons.result() or "successful" in neurons.result())
            #         print(neurons.result())
            #         #remove('C:/Users/Dev1/Desktop/ApiBotAnalyzer/' + request["file"])
            #         if(len(positions) == len(arr)):
            #             await webSocket.send_json({
            #                 "message": f"Done"
            #             })
            #             #await webSocket.close()
            #         else:
            #             notpos = [i for i in range(len(arr)) if not any([x in arr[i].result() for x in ["Successfully uploaded", "successful", "Successful"]])]

            #             if not(len(notpos) == len(positions)):
            #                 text = ''
            #                 failed = ''
            #                 apis = ''
            #                 for i in positions:
            #                     text+= names[i] + ' done' + ' '

            #                 for i in notpos:
            #                     failed += arr[i].result() + ' '
            #                     apis += names[i] + ' '

            #                 await webSocket.send_json({
            #                     "message": f"{text}",
            #                     "error": f"{failed}"
            #                     })

            #                 AvisoSoporte(tipo, d["id_folder"], d["fileN"], request["token"], 'Alguna api falló al momento de analizar el estímulo se recomienda revisar y resubir manualmente en mantenimiento de estímulos.', userArr[random], apis)
            #             else:
            #                 await webSocket.send_json({
            #                     "message": f"Failed",
            #                     "error": f"{attention.result()} {neurons.result()} {feng.result()}"
            #                     })

            #                 apis = ''
            #                 for i in range(len(names)):
            #                     apis += names[i] + ' ' 
                                
            #                 AvisoSoporte(tipo, d["id_folder"], d["fileN"], request["token"], 'Todas las apis han fallado al analizar el estímulo', userArr[random], apis)
            #             # if("Successfully uploaded" in neurons.result() or "successful" in neurons.result()):
            #             #     await webSocket.send_json({
            #             #     "message": f"Neurons done",
            #             #     "error": f"{attention.result()}"
            #             #     })
            #             # elif("Successful" in attention.result()):
            #             #     await webSocket.send_json({
            #             #     "message": f"Attention done",
            #             #     "error": f"{neurons.result()}"
            #             #     })
            #             # else:
            #             #     await webSocket.send_json({
            #             #     "message": f"Failed",
            #             #     "error": f"{attention.result()} {neurons.result()}"
            #             #     })

            # else:
            #     print("entro donde no debe")
            #     if(neurons.done()):
            #         if( "Successfully uploaded" in neurons.result() or "successful" in neurons.result()):
            #             await webSocket.send_json({
            #                 "message": f"Done"
            #             })
            #         else:
            #             await webSocket.send_json({
            #                 "message": f"Failed",
            #                 "error": f"{neurons.result()}"
            #                 })
            #print(neurons, attention)
            

        await webSocket.send_json({
            "message": f"{idStimulus}"
        })
        


@app.websocket("/StimulusAnalyzeMaintenance")
async def websocket_endpoint(webSocket: WebSocket):
    await webSocket.accept()
    while True:
        request = await webSocket.receive_json()
        #file = await webSocket.receive_bytes()

        # data = {'id_folder': request["idfolder"]}
        # fo = open('C:/Users/Dev1/Desktop/ApiBotAnalyzer/' + request["file"], 'rb')
        # file = {'image': fo} # la ruta debe ser cambiada por la ruta del servidor
        # headers = {'Authorization': request["token"]}
        # r = requests.post(url=Backend + '/Stimulus/UploadStimulus', files=file ,data=data, headers=headers)
        # jsonResponse = r.json()
        # fo.close()
        idStimulus = request["idStimulus"]
        operation = request["operation"] # si es 0 se ejecutan todas las apis, si es 1 se ejecuta solo neurons, si es 2 attention, si es 3 feng ...
        userC = request["userCreation"]
        isVideo = True
        if not(len(idStimulus) == 0):
            data = {'idStimulus': idStimulus} 
            headers = {'Authorization': request["token"]}
            
            getStimulus = requests.post(url=Backend + '/Stimulus/getStimulusUrl',data=data, headers=headers)
            getS = getStimulus.json()
            Apic,d,h = ExecuteNeurons(1, getStimulus.json(), idStimulus, request["token"])
            #d = {"file": getS[""], "id_folder": 1, "id_stimulus": str(jsonResponse), "fileN": "Fondo.jpg"}
            #neurons = asyncio.create_task(async_aiohttp_post("http://127.0.0.1:8000/v2/singleFile", data=d, headers=headers))
            
            if (".mp4" not in d["file"]):
                if(operation == '0' or operation == '2'):
                    isVideo = False
                    studySettings = {"study_name": getS["title"], "study_type": "general", "content_type": "general", 'tasks[0]': 'focus', 'tasks[1]': 'clarity_score'}
                    attention = asyncio.create_task(ExecuteAttention(2, getS, idStimulus, request["token"], studySettings, webSocket, userCreation=userC))
                    await attention
                    
            if(operation == '0' or operation == '1'):
                neurons = asyncio.create_task(ExecuteBot(request["token"], d["id_folder"], d["id_stimulus"], d["file"], d["fileN"], userCreation=userC))
                await neurons
            #res = asyncio.gather(asyncio.create_task(ExecuteAttention(2, getS, str(jsonResponse), request["token"], studySettings)),  asyncio.create_task(async_aiohttp_post("http://127.0.0.1:8000/v2/singleFile", data=d, headers=headers)))
            
            # async def main():
            #     tasks = [async_aiohttp_post("http://127.0.0.1:8000/v2/singleFile", data=d, headers=headers), ExecuteAttention(2, getS, str(jsonResponse), request["token"], studySettings)]
            #     await asyncio.gather(*tasks)

            if (operation == '0' or operation == '3'):
                isVideo = False
                feng = asyncio.create_task(ExecuteFengGui(3,getS, idStimulus, request["token"], webSocket))
                await feng
            
            # tasks = asyncio.create_task(main())

            # if (res.done()):
            #     webSocket.send_json({
            #         "message": f"done"
            #     })
            #Corregir el uso de attention cuando es video!!!
            #print(neurons, attention)
           
            if not (isVideo):
                if(operation == '0'):
                    print("entro a donde deberiaaaaaaa")
                    arr = [neurons, attention, feng]
                    names = ["Neurons", "Attention", "Feng"]
                    if(neurons.done() and attention.done() and feng.done()):
                        positions = [i for i in range(len(arr)) if any([x in arr[i].result() for x in ["Successfully uploaded", "successful", "Successful"]])]
                        print("Successfully uploaded" in neurons.result() or "successful" in neurons.result())
                        print(neurons.result())
                        #remove('C:/Users/Dev1/Desktop/ApiBotAnalyzer/' + request["file"])
                        #if(("Successfully uploaded" in neurons.result() or "successful" in neurons.result()) and "Successful" in attention.result()  and "Successful" in feng.result()):
                        if (len(positions) == len(arr)):
                            await webSocket.send_json({
                                "message": f"Done"
                            })
                            #await webSocket.close()
                        else:
                            notpos = [i for i in range(len(arr)) if not any([x in arr[i].result() for x in ["Successfully uploaded", "successful", "Successful"]])]

                            if not(len(notpos) == len(positions)):
                                text = ''
                                failed = ''
                                for i in positions:
                                    text+= names[i] + ' done' + ' '
                                
                                for i in notpos:
                                    failed += arr[i].result() + ' '

                                await webSocket.send_json({
                                    "message": f"{text}",
                                    "error": f"{failed}"
                                })
                            else:
                               await webSocket.send_json({
                                 "message": f"Failed",
                                 "error": f"{attention.result()} {neurons.result()} {feng.result()}"
                                 }) 

                            # if("Successfully uploaded" in neurons.result() or "successful" in neurons.result()):
                            #     await webSocket.send_json({
                            #     "message": f"Neurons done",
                            #     "error": f"{attention.result()}"
                            #     })
                            # elif("Successful" in attention.result()):
                            #     await webSocket.send_json({
                            #     "message": f"Attention done",
                            #     "error": f"{neurons.result()}"
                            #     })
                            # else:
                            #     await webSocket.send_json({
                            #     "message": f"Failed",
                            #     "error": f"{attention.result()} {neurons.result()}"
                            #     })
                elif (operation == '1') :
                    if(neurons.done()):
                        if( "Successfully uploaded" in neurons.result() or "successful" in neurons.result()):
                            await webSocket.send_json({
                            "message": f"Done"
                            })
                        else:
                            await webSocket.send_json({
                            "message": f"Failed",
                            "error": f"{neurons.result()}"
                            })
                elif (operation == '2'):
                    if(attention.done()):
                        if("Successful" in attention.result()):
                            await webSocket.send_json({
                                "message": f"Done"
                                })
                        else:
                            await webSocket.send_json({
                            "message": f"Failed",
                            "error": f"{attention.result()}"
                            })
                elif (operation == '3'):
                    if(feng.done()):
                        if("Successful" in feng.result()):
                            await webSocket.send_json({
                                "message": f"Done"
                                })
                        else:
                            await webSocket.send_json({
                            "message": f"Failed",
                            "error": f"{feng.result()}"
                            })

            else:
                print("entro donde no debe")
                if(neurons.done()):
                    if( "Successfully uploaded" in neurons.result() or "successful" in neurons.result()):
                        await webSocket.send_json({
                            "message": f"Done"
                        })
                    else:
                        await webSocket.send_json({
                            "message": f"Failed",
                            "error": f"{neurons.result()}"
                            })
            #print(neurons, attention)
            

        await webSocket.send_json({
            "message": f"{idStimulus}"
        })
