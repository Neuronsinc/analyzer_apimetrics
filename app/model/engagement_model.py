from keras.models import load_model
import joblib
import cv2
import numpy as np
import pandas as pd
import gc
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
import lightgbm as lgb

import keras.backend as K
import tracemalloc
import sys
import psutil
import os
import importlib



class EngagementModelManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Esta creando una nueva instancia")
            cls._instance = super(EngagementModelManager, cls).__new__(cls)
            # cls._instance.model = load_model('app/keras_models/modelo_6.keras')
            # cls._instance.scaler = joblib.load('app/keras_models/scaler_m6.pkl')
            cls._instance.model = lgb.Booster(model_file='app/keras_models/lgb3.txt')
            # cls._instance.column_names = ["max_laplace", "contraste", "max_fourier", "desviacion_fourier", "textura", "numCarac", "colorfulness", "brightness"]
            cls._instance.column_names = ["colorfulness",  "variedadColores", "media_fourier"
                                            , 'regiones', "contraste", 'local_binary_pattern'
                                            , 'brightness', 'desviacion_laplace']

        return cls._instance
      
    def get_model_instance(self):
        return self.model
    
    
    def get_prediction(self, caracteristicas):
        print(caracteristicas)
        process = psutil.Process(os.getpid())
        memory_usage_mb = process.memory_info().rss / (1024 * 1024)  # Convertir a MB
        print(f'caracteristicas 1: {memory_usage_mb}')
        
        df_norm = pd.DataFrame([caracteristicas], columns=self.column_names)

        # norm_carac = self.scaler.transform(df_norm)
        prediccion = self.model.predict([caracteristicas])
        print(f'valor {prediccion}')

        process = psutil.Process(os.getpid())
        memory_usage_mb = process.memory_info().rss / (1024 * 1024)  # Convertir a MB
        print(f'prediccion 2: {memory_usage_mb}')

        return {'predict': float(prediccion)}
    

    # Función para obtener la instancia de ModelManager
def get_model_manager():
    if not hasattr(get_model_manager, "_instance"):
        get_model_manager._instance = ModelManager()

    return get_model_manager._instance



# Singleton pattern para garantizar una sola instancia del modelo
#model_manager = get_model_manager()
engagement_model_manager = EngagementModelManager()
