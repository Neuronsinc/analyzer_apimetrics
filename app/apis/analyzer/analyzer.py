import requests
import os
from pydantic import BaseModel

from app.model.analyzer_model import Stimulus
from app.model.analyzer_model import ApiCredential


# class Stimulu:
#     image_url: str
#     title: str



BACKEND = 'https://analyzerapi.troiatec.com'
#BACKEND = 'http://localhost/Analyzer/Predict_Analyzer_Back/'
# BACKEND = os.getenv('BACKEND')


def get_api_credentials(api, token) -> ApiCredential:
    data = {'api': api}
    headers = {'Authorization': f'Bearer {token}'}
    # headers = {'Authorization': f'{token}'}

    request_credentials = requests.post(url= f'{BACKEND}/Stimulus/getApiCredentials' ,data=data, headers=headers)
    api_credentials = request_credentials.json()
    print(api_credentials)

    return ApiCredential(clave=api_credentials['clave'], url=api_credentials['url'])

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