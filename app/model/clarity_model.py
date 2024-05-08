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
import psutil
import os
import importlib

class ClarityModelManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Esta creando una nueva instancia")
            cls._instance = super(ClarityModelManager, cls).__new__(cls)
            cls._instance.model = load_model('app/keras_models/modelo_6.keras')
            cls._instance.scaler = joblib.load('app/keras_models/scaler_m6.pkl')
            cls._instance.column_names = ["max_laplace", "contraste", "max_fourier", "desviacion_fourier", "textura", "numCarac", "colorfulness", "brightness"]
        return cls._instance
      
    def get_model_instance(self):
        return self.model
    
    def get_scaler_instance(self):
        return self.scaler

    
    def get_clarity_prediction(self, caracteristicas):
        print(caracteristicas)
        df_norm = pd.DataFrame([caracteristicas], columns=self.column_names)
        print(df_norm)

        norm_carac = self.scaler.transform(df_norm)
        prediccion = self.model.predict([norm_carac])[0][0]

        return float(prediccion)
    

    # Función para obtener la instancia de ModelManager
def get_model_manager():
    if not hasattr(get_model_manager, "_instance"):
        get_model_manager._instance = ModelManager()

    return get_model_manager._instance



# Singleton pattern para garantizar una sola instancia del modelo
#model_manager = get_model_manager()
clarity_model_manager = ClarityModelManager()
