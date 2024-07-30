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

import tensorflow as tf

# Obtener la ruta absoluta del directorio actual de script.py
directorio_script = os.path.dirname(os.path.abspath(__file__))

# Construir la ruta al archivo de modelo keras
#ruta_modelo_keras = os.path.join(directorio_script, '../keras_models/modelo_6.keras')
ruta_modelo_quantized = os.path.join(directorio_script, '../keras_models/modelo_6_quantized.tflite')
ruta_scaler = os.path.join(directorio_script, '../keras_models/scaler_m6.pkl')

class ClarityModelManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Esta creando una nueva instancia")
            cls._instance = super(ClarityModelManager, cls).__new__(cls)
            #cls._instance.model = load_model(ruta_modelo_keras)
            cls.interpreter = tf.lite.Interpreter(model_path=ruta_modelo_quantized)
            cls.interpreter.allocate_tensors()
            cls.input_details = cls.interpreter.get_input_details()
            cls.output_details = cls.interpreter.get_output_details()
            cls._instance.scaler = joblib.load(ruta_scaler)
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

        #model = load_model(ruta_modelo_keras)
        #scaler = joblib.load(ruta_scaler)

        #print(self.model)

        norm_carac = self.scaler.transform(df_norm)

        print("normalizado")

        norm_carac = np.array(norm_carac, dtype=np.float32)

        #prediccion = self.model.predict([norm_carac])[0][0]

        self.interpreter.set_tensor(self.input_details[0]['index'], norm_carac)
        self.interpreter.invoke()
        prediccion = self.interpreter.get_tensor(self.output_details[0]['index'])

        print("predicho")

        # norm_carac = self.scaler.transform(df_norm)
        # prediccion = self.model.predict([norm_carac])[0][0]

        return float(prediccion)
    

    # Función para obtener la instancia de ModelManager
def get_model_manager():
    if not hasattr(get_model_manager, "_instance"):
        get_model_manager._instance = ModelManager()

    return get_model_manager._instance



if(os.getenv('LOAD_CLARITY_MODEL') == 'true'):
    clarity_model_manager = ClarityModelManager()
else:
    clarity_model_manager = None
