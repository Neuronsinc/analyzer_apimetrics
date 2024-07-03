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
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial



class ImageCaracteristics:

    def extract_features(self, image):
        features = {}

        if image is None or image.size == 0:
            raise ValueError("Image is empty or None")

        # Convertir a escala de grises una vez
        image_gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Laplaciano
        laplaciano = cv2.Laplacian(image, cv2.CV_32F)
        features['max_val_laplace'] = float(np.max(laplaciano))
        features['desv_val_laplace'] = float(np.std(laplaciano))
        del laplaciano

        # Contraste
        features['contraste'] = float(np.std(image_gris))

        # Transformada de Fourier
        f_transformada = np.fft.fft2(image)
        f_shift = np.fft.fftshift(f_transformada)
        magnitud_espectro = 20 * np.log(np.abs(f_shift) + 1e-10)
        features['max_val_fourier'] = float(np.max(magnitud_espectro))
        features['media_fourier'] = float(np.mean(magnitud_espectro))
        features['std_dev'] = float(np.std(magnitud_espectro))
        del f_transformada, f_shift, magnitud_espectro

        # Textura GLCM
        glcm = graycomatrix(image_gris, [1], [0], levels=256, symmetric=True, normed=True)
        features['textura'] = float(graycoprops(glcm, 'contrast')[0, 0])

        # Detectar características
        detector_caracteristicas = cv2.ORB_create()
        puntos_clave, descriptores = detector_caracteristicas.detectAndCompute(image_gris, None)
        features['num_caracteristicas'] = len(puntos_clave)
        del puntos_clave, descriptores

        # Colorfulness
        (B, G, R) = cv2.split(image.astype("float32"))
        rg = np.absolute(R - G)
        yb = np.absolute(0.5 * (R + G) - B)
        (rbMean, rbStd) = (np.mean(rg), np.std(rg))
        (ybMean, ybStd) = (np.mean(yb), np.std(yb))
        stdRoot = np.sqrt((rbStd ** 2) + (ybStd ** 2))
        meanRoot = np.sqrt((rbMean ** 2) + (rbMean ** 2))
        features['colorfulness'] = float(stdRoot + (0.3 * meanRoot))
        del B, G, R, rg, yb, rbMean, rbStd, ybMean, ybStd, stdRoot, meanRoot

        # Brillo
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        features['brightness'] = float(hsv[..., 2].mean())
        del hsv

        # Variedad de colores
        colores_unicos = np.unique(image.reshape(-1, image.shape[2]), axis=0)
        features['variedad_colores'] = float(len(colores_unicos) / (image.shape[0] * image.shape[1]))

        # Regiones
        _, imagen_binaria = cv2.threshold(image_gris, 128, 255, cv2.THRESH_BINARY)
        contornos, _ = cv2.findContours(imagen_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        features['regiones'] = len(contornos)
        del imagen_binaria, contornos

        # LBP
        lbp = local_binary_pattern(image_gris, 8, 1, method="uniform")
        hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 8 + 3), range=(0, 8 + 2))
        hist = hist.astype("float32")
        hist /= hist.sum()
        features['var_lbp'] = float(np.var(hist))
        del lbp, hist

        return features

    def unify_features(self, features_list):
        unified_features = {}
        for key in features_list[0].keys():
            unified_features[key] = np.median([f[key] for f in features_list])
        return unified_features

    def divide_imagen_en_bloques_iguales(imagen, L):
        alto, ancho, canales = imagen.shape
        tamano_bloque_alto = alto // L
        tamano_bloque_ancho = ancho // L
        
        bloques = []
        
        for i in range(L):
            for j in range(L):
                bloque = imagen[i*tamano_bloque_alto:(i+1)*tamano_bloque_alto,
                                j*tamano_bloque_ancho:(j+1)*tamano_bloque_ancho]
                bloques.append(bloque)
        
        return bloques

    def __init__(self, image_url):
        print("imagen -----------------")
        print(image_url)
        res = requests.get(image_url)
        print(res)
        if res.status_code != 200:
            return None

        # self.size = len(res.content)
        image_bytes = BytesIO(res.content)
        imagen = cv2.imdecode(np.frombuffer(image_bytes.read(), np.uint8), cv2.IMREAD_COLOR)
        self.size_in_bytes = len(res.content)
        self.image_height, self.image_width = imagen.shape[:2]

        print(f"imagen  {imagen}")
        
        if imagen is None:
            raise ValueError("Failed to decode image")

        # print(len(res.content))
        # N = len(res.content) / 40
        #porcentaje_bloques_altura = 0.01
        #print(f'multiplicacion =>> {int(imagen.shape[0] * porcentaje_bloques_altura)}')
        #N = 4 # ver en dependencia de tamaño 300kb para abajo dejar en 1
        # features = self.extract_features(imagen)
        # print(f'fokin features =>>> {features}')
        #N = int(imagen.shape[0] * porcentaje_bloques_altura)
        #N = max(1, int(imagen.shape[0] * porcentaje_bloques_altura))
        N = 1
        # N = ""

        # if N_param == "size":
        #     bytes_per_block = 100 * 1024  # Asumir que un bloque razonable tiene 100KB
        #     N = max(1, int(self.size_in_bytes / bytes_per_block))
        # elif N_param == "dimensions":
        #     min_block_size_pixels = 100 * 100  # Tamaño mínimo del bloque en píxeles
        #     N = max(1, int(self.image_height * self.image_width / min_block_size_pixels))
        # else:
        #     N = N_param

        try:
            # Dividir la imagen en bloques
            bloques = np.array_split(imagen, N, axis=0)
            features_list = []
            print(bloques)
            with ThreadPoolExecutor() as executor:
                # Usar partial para fijar el primer argumento self
                futures = [executor.submit(partial(self.extract_features), bloque) for bloque in bloques]
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        features_list.append(result)
                    except Exception as e:
                        print(f"Error processing block: {e}")

            self.unified_features = self.unify_features(features_list)
        except Exception as e:
            print(f"Error during feature extraction: {e}")

    # ["max_laplace", "contraste", "max_fourier", "desviacion_fourier", "textura", "numCarac", "colorfulness", "brightness"]
    def clarity(self) -> List[float]:
        return [self.unified_features["max_val_laplace"],
                self.unified_features["contraste"],
                self.unified_features["max_val_fourier"],
                self.unified_features["std_dev"],
                self.unified_features["textura"],
                self.unified_features["num_caracteristicas"],
                self.unified_features["colorfulness"],
                self.unified_features["brightness"]]

    def engagement(self) -> List[float]:
        return [self.unified_features["colorfulness"],
                self.unified_features["variedad_colores"],
                self.unified_features["media_fourier"],
                self.unified_features["regiones"],
                self.unified_features["contraste"],
                self.unified_features["var_lbp"],
                self.unified_features["brightness"],
                self.unified_features["desv_val_laplace"]]

    def get_meta_datos(self):
        return self.size_in_bytes, self.image_height, self.image_width