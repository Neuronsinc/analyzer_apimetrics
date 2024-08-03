import requests
import os
from os import remove
from datetime import datetime

# BACKEND = 'https://analyzerapiv3.troiatec.com'
#BACKEND = 'http://localhost/Analyzer/Predict_Analyzer_Back/'
os.getenv('BACKEND')

RootPath = os.getenv('ROOT')

def AvisoSoporte(tipo, id_folder, fileName, token, mensaje, cuenta, apis, imageUrl):
    data = {"type": tipo, "idF": id_folder, "Emessage": mensaje, "cuenta": cuenta, "apis": apis}

    res = requests.get(imageUrl)
    today = datetime.now()
    fname = str(today.day) + str(today.month) + str(today.year) + "_" +str(today.hour) + fileName
    if res.status_code == 200:
        with open(fname, 'wb') as file:
            file.write(res.content)

    fo = open(fname, 'rb')
    file = {'File': fo}
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.post(url= BACKEND + '/BotSupport/new_mail', files=file ,data=data, headers=headers)
    jsonResponse = r.json()
    print("jsonnn responseee de aviso =>>>>", jsonResponse)
    # Eliminar archivo y zip.
    fo.close()
    remove(fname)
    return jsonResponse