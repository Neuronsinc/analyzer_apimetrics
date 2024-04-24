from keras.models import load_model
import joblib
import cv2
import numpy as np
import pandas as pd
import requests
from io import BytesIO
import gc
from skimage.feature import graycomatrix, graycoprops
import keras.backend as K
import tracemalloc
import sys



class ModelManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Esta creando una nueva instancia")
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.model = load_model('app/keras_models/modelo_6.keras')
            cls._instance.scaler = joblib.load('app/keras_models/scaler_m6.pkl')
            cls._instance.column_names = ["max_laplace", "contraste", "max_fourier", "desviacion_fourier", "textura", "numCarac", "colorfulness", "brightness"]
        return cls._instance
      
    def get_model_instance(self):
        return self.model
    
    def get_scaler_instance(self):
        return self.scaler

    def extraer_carac(self, imagen):
        # max laplace
        laplaciano = cv2.Laplacian(imagen, cv2.CV_64F)
        max_val_laplace = np.max(laplaciano)

        # contraste
        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        contraste = np.std(imagen_gris)

        # max fourier
        f_transformada = np.fft.fft2(imagen)
        f_shift = np.fft.fftshift(f_transformada)
        magnitud_espectro = 20 * np.log(np.abs(f_shift) + 1e-10)
        max_val_fourier = np.max(magnitud_espectro)  

        # desviacion fourier
        std_dev = np.std(magnitud_espectro)

        # textura
        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        glcm = graycomatrix(imagen_gris, [1], [0], levels=256, symmetric=True, normed=True)
        textura = graycoprops(glcm, 'contrast')[0, 0]
        
        # numero de características

        # Convertir la imagen a escala de grises
        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        # Inicializar el detector de características
        detector_caracteristicas = cv2.ORB_create()
        puntos_clave, descriptores = detector_caracteristicas.detectAndCompute(imagen_gris, None)
        num_caracteristicas = len(puntos_clave)

        # colorfulness

        # split the image into its respective RGB components
        (B, G, R) = cv2.split(imagen.astype("float"))
        # compute rg = R - G
        rg = np.absolute(R - G)
        # compute yb = 0.5 * (R + G) - B
        yb = np.absolute(0.5 * (R + G) - B)
        # compute the mean and standard deviation of both `rg` and `yb`
        (rbMean, rbStd) = (np.mean(rg), np.std(rg))
        (ybMean, ybStd) = (np.mean(yb), np.std(yb))
        # combine the mean and standard deviations
        stdRoot = np.sqrt((rbStd ** 2) + (ybStd ** 2))
        meanRoot = np.sqrt((rbMean ** 2) + (ybMean ** 2))
        # derive the "colorfulness" metric and return it
        colorfulness = stdRoot + (0.3 * meanRoot)


        # brightness
        hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
        brightness = hsv[...,2].mean()

        # Liberar memoria de variables temporales
        imagen_gris = None
        laplaciano = None
        f_shift = None
        magnitud_espectro = None
        glcm = None

        return [max_val_laplace, contraste, max_val_fourier, std_dev, textura, num_caracteristicas, colorfulness, brightness]
    
    def get_prediction(self, img_route):
        self.model = load_model('app/keras_models/modelo_6.keras')
        self.scaler = joblib.load('app/keras_models/scaler_m6.pkl')
        tracemalloc.start()
        
        res = requests.get(img_route)

        if res.status_code == 200:
            image_bytes = BytesIO(res.content)
            img = cv2.imdecode(np.frombuffer(image_bytes.read(), np.uint8), cv2.IMREAD_COLOR)
            carac = self.extraer_carac(img)

            del image_bytes
            del img
            del res
            gc.collect()

            cv2.destroyAllWindows()
            
            df_norm = pd.DataFrame([carac], columns=self.column_names)
            norm_carac = self.scaler.transform(df_norm)

            prediccion = self.model.predict([norm_carac])[0][0]

            del df_norm
            del norm_carac
            del carac
            gc.collect()
    
            K.clear_session()

            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')

            print('----top 10 memalloc----')
            print(sys.getsizeof(self.model))
            for s in top_stats[:10]:
                print(s)
            print('-----------------------')

            return prediccion
        
        return None

    
    # Función para obtener la instancia de ModelManager
def get_model_manager():
    if not hasattr(get_model_manager, "_instance"):
        get_model_manager._instance = ModelManager()

    return get_model_manager._instance



# Singleton pattern para garantizar una sola instancia del modelo
#model_manager = get_model_manager()
model_manager = ModelManager()
