import cv2
import numpy as np

import pandas as pd
import requests
from io import BytesIO
import gc

from skimage.feature import graycomatrix, graycoprops, local_binary_pattern

import sys
import psutil
import os

from typing import List



class ImageCaracteristics:

    def __init__(self, image_url):
        print("imagen -----------------")
        print(image_url)
        res = requests.get(image_url)
        print(res)
        if res.status_code != 200:
            return None

        self.size = len(res.content)
        image_bytes = BytesIO(res.content)
        imagen = cv2.imdecode(np.frombuffer(image_bytes.read(), np.uint8), cv2.IMREAD_COLOR)

        laplaciano = cv2.Laplacian(imagen, cv2.CV_64F)
        self.max_val_laplace = np.max(laplaciano)
        self.desv_val_laplace = np.std(laplaciano)

        imagen_gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
        self.contraste = np.std(imagen_gris)

        f_transformada = np.fft.fft2(imagen)
        f_shift = np.fft.fftshift(f_transformada)
        magnitud_espectro = 20 * np.log(np.abs(f_shift) + 1e-10)
        self.max_val_fourier = np.max(magnitud_espectro)  
        self.media_fourier = np.mean(magnitud_espectro)  


        self.std_dev = np.std(magnitud_espectro)

        glcm = graycomatrix(imagen_gris, [1], [0], levels=256, symmetric=True, normed=True)
        self.textura = graycoprops(glcm, 'contrast')[0, 0]

        detector_caracteristicas = cv2.ORB_create()
        puntos_clave, descriptores = detector_caracteristicas.detectAndCompute(imagen_gris, None)
        self.num_caracteristicas = len(puntos_clave)

        (B, G, R) = cv2.split(imagen.astype("float"))
        rg = np.absolute(R - G)
        yb = np.absolute(0.5 * (R + G) - B)
        (rbMean, rbStd) = (np.mean(rg), np.std(rg))
        (ybMean, ybStd) = (np.mean(yb), np.std(yb))
        stdRoot = np.sqrt((rbStd ** 2) + (ybStd ** 2))
        meanRoot = np.sqrt((rbMean ** 2) + (ybMean ** 2))
        self.colorfulness = stdRoot + (0.3 * meanRoot)

        hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
        self.brightness = hsv[...,2].mean()

        colores_unicos = np.unique(imagen.reshape(-1, imagen.shape[2]), axis=0)
        self.variedad_colores = len(colores_unicos) / (imagen.shape[0] * imagen.shape[1])

        _, imagen_binaria = cv2.threshold(imagen_gris, 128, 255, cv2.THRESH_BINARY)
        contornos, _ = cv2.findContours(imagen_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.regiones = len(contornos)

        lbp = local_binary_pattern(imagen_gris, 8, 1, method="uniform")
        (hist, _) = np.histogram(lbp.ravel(),
            bins=np.arange(0, 8 + 3),
            range=(0, 8 + 2))
        hist = hist.astype("float")
        hist /= (hist.sum())
        self.var_lbp = np.var(hist)


    # ["max_laplace", "contraste", "max_fourier", "desviacion_fourier", "textura", "numCarac", "colorfulness", "brightness"]
    def clarity(self) -> List[float]:
        return [self.max_val_laplace 
                    , self.contraste 
                    , self.max_val_fourier
                    , self.std_dev
                    , self.textura
                    , self.num_caracteristicas
                    , self.colorfulness
                    , self.brightness]

    def engagement(self) -> List[float]:
        return [self.colorfulness
          , self.variedad_colores
          , self.media_fourier
          , self.regiones
          , self.contraste
          , self.var_lbp
          , self.brightness
          , self.desv_val_laplace]
