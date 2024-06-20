from celery import Celery
import gc
from app.model.api_model import ARequest
from app.model.api_model import Apis
from app.apis.analyzer.analyzer import get_api_credentials
from app.apis.analyzer.analyzer import get_stimulus

from app.model.image_model import ImageCaracteristics
from app.model.clarity_model import clarity_model_manager
from app.apis.feng.feng import handleStatus

from app.apis.feng.feng import analyzeVids, getAndSaveCsv, getAndSaveVids, sendMail, handleStatus
from app.apis.avisos.avisos import AvisoSoporte

from app.apis.analyzer.analyzer import get_api_credentials
from app.apis.analyzer.analyzer import get_stimulus
from app.model.cache_model import cache_manager

from app.apis.feng.feng import analyze

#Configuración
BROKER_URL = 'redis://127.0.0.1:6379/0'
BACKEND_URL = 'redis://127.0.0.1:6379/0'

#correr en windows celery (https://github.com/celery/celery/issues/4178#issuecomment-344176336):
#python -m celery -A app.model.celery_model worker --pool=solo -l info

celery_app = Celery(
    'apimetrics',
    broker= BROKER_URL,
    backend= BACKEND_URL
)

@celery_app.task
def clarity_pred(data: dict):
    # feng.analyze_file()
    arequest = ARequest(
                id_stimulus=data["id_stimulus"],
                analyzer_token=data["analyzer_token"],
                clarity=data["clarity"]
                )
    print(arequest)
    stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)
    
    response = ""
    try:
        img = ImageCaracteristics(stimulus.image_url)
        # clarity = clarity_model_manager.get_prediction(stimulus.image_url) #clarity engagement
        clarity = clarity_model_manager.get_clarity_prediction(img.clarity()) #clarity engagement
        print(clarity)
        if clarity is not None:
            response = {"clarity": str(clarity)}
            print(response)
            handleStatus(arequest.id_stimulus, 1, arequest.analyzer_token)
            #feng_analyze(arequest=arequest).apply_async()
            del clarity
            gc.collect()
        else:
            del clarity
            gc.collect()
            raise Exception
    except:
        handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token)
        return "failed"
        #return JSONResponse(content="failed", status_code=500)

    return "success"


@celery_app.task
def feng_analyze(arequest: ARequest):
    cache = cache_manager.get_cache_instance()
    credentials = get_api_credentials(Apis.FENGUI.value, arequest.analyzer_token, True, 0, cache)
    stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)

    if credentials == "Ninguno" or credentials == "NingunaEspecifica":
        mensaje = ""
        if credentials == "Ninguno":
            mensaje = "Se acabaron los créditos en todas las cuentas y no es posible analizar nada más."
        elif credentials == "NingunaEspecifica":
            mensaje = "En ninguna cuenta hay disponibilidad para subir el estímulo requerido."

        AvisoSoporte(0, stimulus.id_folder, stimulus.filename, arequest.analyzer_token, mensaje, "Todas", "Feng", stimulus.image_url)
        handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token)
        return "failed"

    # studySettings = {"study_name": getS["title"], "study_type": "general", "content_type": "general", 'tasks[0]': 'focus', 'tasks[1]': 'clarity_score'}
    response = ""
    #model = model_manager.get_model_instance()
    #scaler = model_manager.scaler()
    try:
        response = analyze(stimulus, float(arequest.clarity), arequest.analyzer_token, credentials)

        if "Successful" in response:
            handleStatus(arequest.id_stimulus, 2, arequest.analyzer_token)
        else:
            handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token) # fallo
            return "failed"
    except:
        handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token) # fallo
        return "failed"

    return "success"