import requests

BACKEND = os.getenv('BACKEND')

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