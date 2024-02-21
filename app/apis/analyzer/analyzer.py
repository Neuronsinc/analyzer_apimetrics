import requests
import os
import math
from pydantic import BaseModel

from app.model.analyzer_model import Stimulus
from app.model.analyzer_model import ApiCredential
from app.model.cache_model import cache_manager


# class Stimulu:
#     image_url: str
#     title: str



BACKEND = 'https://analyzerapi.troiatec.com'
#BACKEND = 'http://localhost/Analyzer/Predict_Analyzer_Back/'
# BACKEND = os.getenv('BACKEND')

def seleccionar_cuenta(cuentas, type, duration = 1):
    """
    Esta función permite realizar la seleccion de que cuenta de Feng será posible subir el archivo a ser analizado.

    retorna un dict con la información sobre la cuenta seleccionada.
    También si falla retorna "Ninguna" o "NingunaEspecifica" para cuando ya no hay creditos

    Argumentos:
    cuentas -- un arreglo de cuentas a seleccionar, debe ser un array.
    type -- tipo de archivo 0 es imagen, 1 es video, debe ser int.
    duration -- duración de los videos, debe ser int.
    """
    mayores_uno = [cuenta for cuenta in cuentas if cuenta["creditosRestantes"] > 1]

    if mayores_uno:
        cuentas_validas = []
        for cuenta in cuentas:
            if type == 0: # imagen
                # Se ve que sea mayor a 1 el crédito ya que 1 es lo que consume una imágen
                if cuenta["creditosRestantes"] > 1:
                    cuentas_validas.append(cuenta)
                
            else: # video 10 segundos = 1 credito
                total_creditos_videos = math.ceil(int(duration) / 10)
                if cuenta["creditosRestantes"] > total_creditos_videos:
                    cuentas_validas.append(cuenta)
                    
        if cuentas_validas:
            return min(cuentas_validas, key=lambda x: x["creditosRestantes"])
        else:
            return "NingunaEspecifica"
    else:
        return "Ninguno"


# type = 0 => imagen, type = 1 => video
def get_api_credentials(api, token, check, type = 0, cache = None, duration = 1, account = None) -> ApiCredential:
    """
    Esta función permite obtener las credenciales de las apis y hacer un proceso de seleccion para las multiples
    cuentas de Feng (por el momento).

    retorna un objeto ApiCredential("clave", "url", "cuenta").
    También si falla retorna "Ninguna" o "NingunaEspecifica" para cuando ya no hay creditos

    Argumentos:
    api -- Id del api de quien se quieren las credenciales, Debe ser un numero
    token -- Clave del usuario para enviar peticiones al backend, Debe ser un string
    check -- Para poder indicar si se debe chequear el conteo de créditos de Feng o no, debe ser un booleano.
    type -- Indica el tipo de archivo dónde 0 es imagen y 1 es video, debe ser int.
    cache -- Referencia hacia el objeto de la clase cache_model el cuál es un cache con tiempo de expiración, debe ser un objeto de cache_model
    duration -- Duración del video en segundos, debe ser un int.
    account -- cuenta a la que se subió el video, solo aplicable a videos y sirve para ir a traer la cuenta en la que se subió el análisis
    """
    print("cache =>>", cache)
    if check:
        if not cache:
            print("=============entre a no cache ===========")
            data = {'api': api}
            headers = {'Authorization': f'Bearer {token}'}
            # headers = {'Authorization': f'{token}'}

            request_credentials = requests.post(url= f'{BACKEND}/Stimulus/getApiCredentials' ,data=data, headers=headers)
            api_credentials = request_credentials.json()
            print(api_credentials)

            jsonrpc = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "GetAccountCredits"
            }

           
            cuentas = []
            for cuenta in api_credentials:
                clave = cuenta['clave']
                headers = {'Authorization': f'Basic {clave}'}
                r = requests.post(url=cuenta['url'], json=jsonrpc, headers=headers)
                r = r.json()
                cuentas.append({"cuenta": r["result"]["credits"][0]["userName"], "clave": clave, "url": cuenta['url'], "creditosRestantes": r["result"]["remainCredit"]})
            
             # ------------------------- para pruebas ------------------------------------
            #cuentas.append({'cuenta': 'erick.moreno.troiatec.com', 'clave': 'ZXJpY2subW9yZW5vLnRyb2lhdGVjLmNvbTpUcm9pYXRlYzIwMjM=', 'url': ' https://service.feng-gui.com/json/api.ashx', 'creditosRestantes': 1})
            #cuentas.append({'cuenta': 'juan.roberto.troiatec.com', 'clave': 'ZXJpY2subW9yZW5vLnRyb2lhdGVjLmNvbTpUcm9pYXRlYzIwMjM=', 'url': ' https://service.feng-gui.com/json/api.ashx', 'creditosRestantes': 1})

            # -------------------------- para pruebas -----------------------------------

            cuenta_seleccionada = ""

            if type == 0:
                cuenta_seleccionada = seleccionar_cuenta(cuentas, 0)
            else:
                cuenta_seleccionada = seleccionar_cuenta(cuentas, 1, duration)
            
            if cuenta_seleccionada == "Ninguno":
                # Avisar que ya no hay créditos
                return "Ninguno"
            elif cuenta_seleccionada == "NingunaEspecifica":
                # Avisar que ya no hay créditos para procesar dicho analisis en ninguna cuenta
                return "NingunaEspecifica"
                
            #cache = cuentas
            cache_manager.set_data_to_cache(cuentas)
            #print("cachecito =>" , cache)
            return ApiCredential(clave=cuenta_seleccionada['clave'], url=cuenta_seleccionada['url'], name=cuenta_seleccionada['cuenta'])
        else:
            print("=============entre a SII cache ===========")
            if type == 0:
                cuenta_seleccionada = seleccionar_cuenta(cache["uno"], 0)
            else:
                cuenta_seleccionada = seleccionar_cuenta(cache["uno"], 1, duration)
            
            if cuenta_seleccionada == "Ninguno":
                # Avisar que ya no hay créditos
                return "Ninguno"
            elif cuenta_seleccionada == "NingunaEspecifica":
                # Avisar que ya no hay créditos para procesar dicho analisis en ninguna cuenta
                return "NingunaEspecifica"
        
            return ApiCredential(clave=cuenta_seleccionada['clave'], url=cuenta_seleccionada['url'], name=cuenta_seleccionada['cuenta'])
    else: 
        # Este else no va a buscar explicitamente al cache si es imágenes sirve para otras apis que no tengan multicuentas
        # Mientras que también funciona para solo obtener la cuenta seleccionada anteriormente en los videos.
        if type == 1: #videos
            if not cache:
                data = {'api': api}
                headers = {'Authorization': f'Bearer {token}'}
                # headers = {'Authorization': f'{token}'}

                request_credentials = requests.post(url= f'{BACKEND}/Stimulus/getApiCredentials' ,data=data, headers=headers)
                api_credentials = request_credentials.json()
                print(api_credentials)

                jsonrpc = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "GetAccountCredits"
                }

                cuentas = []
                cuenta_seleccionada = []
                for cuenta in api_credentials:
                    clave = cuenta['clave']
                    headers = {'Authorization': f'Basic {clave}'}
                    r = requests.post(url=cuenta['url'], json=jsonrpc, headers=headers)
                    r = r.json()
                    cuentas.append({"cuenta": r["result"]["credits"][0]["userName"], "clave": clave, "url": cuenta['url'], "creditosRestantes": r["result"]["remainCredit"]})
                    if r["result"]["credits"][0]["userName"] == account:
                        cuenta_seleccionada.append({"cuenta": r["result"]["credits"][0]["userName"], "clave": clave, "url": cuenta['url']})

                cache_manager.set_data_to_cache(cuentas)

                return ApiCredential(clave=cuenta_seleccionada[0]['clave'], url=cuenta_seleccionada[0]['url'], name=cuenta_seleccionada[0]['cuenta'])
            else:
                for cuenta in cache["uno"]:
                    if cuenta["cuenta"] == account:
                        return ApiCredential(clave=cuenta['clave'], url=cuenta['url'], name=cuenta["cuenta"])
                return None
        else:    
            data = {'api': api}
            headers = {'Authorization': f'Bearer {token}'}
            # headers = {'Authorization': f'{token}'}

            request_credentials = requests.post(url= f'{BACKEND}/Stimulus/getApiCredentials' ,data=data, headers=headers)
            api_credentials = request_credentials.json()
            api_credentials = api_credentials[0]
            print(api_credentials)

            return ApiCredential(clave=api_credentials['clave'], url=api_credentials['url'], name="none") 

    #return ApiCredential(clave=api_credentials['clave'], url=api_credentials['url'])

def get_analyzer(api, getStimulus, idstimulus, token):
    '''
    params: 
    @api=datos del api que se va a subir
    '''
    data = {'api': api}
    headers = {'Authorization': token}
    ApiCredentials = requests.post(url= Backend + '/Stimulus/getApiCredentials',data=data, headers=headers)
    ApiC = ApiCredentials.json()
    split_up = os.path.splitext(getStimulus["imageUrl"])

    d = {"file": getStimulus["imageUrl"]
            , "id_folder": getStimulus["id_folder"]
            , "id_stimulus": idstimulus
            , "fileN": f'{getStimulus["title"]}{split_up[1]}'}

    return ApiC, d, headers

def send_to_analyzer(analyzer_token:str, id_folder:str, zipfile_path:str):
    if (satisfactorio):
        print(id_folder)
        print(token)
        # fo = open(RootPath + zipName, 'rb')

        fo = open(zipfile_path, 'rb')
        data = {'id_folder': id_folder}

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


def get_stimulus(stimulus_id: str, analyzer_token: str) -> Stimulus:

    print(f'se entro a get_stimulus {stimulus_id}, {analyzer_token[0:10]}')

    if not(len(stimulus_id) == 0):

        data = {'idStimulus': stimulus_id} 
        headers = {'Authorization': f'Bearer {analyzer_token}'}

        response_stimulus = requests.post(url= f'{BACKEND}/Stimulus/getStimulusUrl',data=data, headers=headers)
        stimulus_json = response_stimulus.json()


        fn = f'{stimulus_json["title"]}{os.path.splitext(stimulus_json["imageUrl"])[1]}' 
        stimulus = Stimulus(image_url=stimulus_json["imageUrl"]
                            , id_folder=stimulus_json["id_folder"]
                            , title=stimulus_json["title"]
                            , filename=fn
                            , id_stimulus=stimulus_id)

        # Apic,d,h = ExecuteNeurons(1, getStimulus.json(), idStimulus, request["token"])
        print(stimulus_json)

        return stimulus
    
    raise Exception("No se encontro el stimulo")


def upload_zip(stimulus: Stimulus, token:str, user_creation = None) -> bool:
    try:
        data = {"id_folder": stimulus.id_folder 
            , "idStimulus": stimulus.id_stimulus }

        if user_creation != None:
            data.update({"userCreation": user_creation})


        print(f'{stimulus.title}_results.zip')

        fo = open(f'{stimulus.title}_results.zip', 'rb')
        print(fo)

        file = {'image': fo}
        headers = {'Authorization': f'Bearer {token}'}

        r = requests.post(url= f'{BACKEND}/Stimulus/UploadNeuronsBot', files=file ,data=data, headers=headers)

        jsonResponse = r.json()

        fo.close()
        return 
    except Exception as ex:
        raise ex


def upload_file(analyzer_token: str, file, id_folder: str):

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