from keras.models import load_model

class ModelManager:
    def __init__(self):
        self.model = load_model('app/keras_models/Modelo.keras')
    
    def get_model_instance(self):
        return self.model
    
    # Función para obtener la instancia de ModelManager
def get_model_manager():
    if not hasattr(get_model_manager, "_instance"):
        get_model_manager._instance = ModelManager()

    return get_model_manager._instance

# Singleton pattern para garantizar una sola instancia del modelo
model_manager = get_model_manager()
