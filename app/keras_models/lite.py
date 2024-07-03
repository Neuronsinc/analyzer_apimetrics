import tensorflow as tf
from keras.models import load_model
import numpy as np
import joblib
# Conversión del modelo a TFLite (se realiza una vez)
# Cargar el modelo TFLite (se hace una sola vez al iniciar la aplicación)
interpreter = tf.lite.Interpreter(model_path="modelo_6_quantized.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

scaled_features = [542.0, 30.830106248023224, 368.5529940848128, 22.686042915312324, 103.02074741272781, 500, 9.415530103934145, 57.22764130015432]
scaler = joblib.load('scaler_m6.pkl')
norm_carac = scaler.transform([scaled_features])
# Convertir las características a FLOAT32
norm_carac = np.array(norm_carac, dtype=np.float32)
print(norm_carac)
interpreter.set_tensor(input_details[0]['index'], norm_carac)
interpreter.invoke()
prediction = interpreter.get_tensor(output_details[0]['index'])

print(prediction)
m2 = load_model('modelo_6.keras')
print(m2.predict([norm_carac])[0][0])


#converter = tf.lite.TFLiteConverter.from_keras_model(modelo)

