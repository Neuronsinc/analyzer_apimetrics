from cachetools import TTLCache

class CacheManager:
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=10800) # expiramos el cache en 3 horas

    def get_cache_instance(self):
        return self.cache
    
    def set_data_to_cache(self, data):
        self.cache.update({"uno": data})
    
    def extract_credits(self, account, amount):
        if "uno" in self.cache:
            nueva_data =  []
            for cuenta in self.cache["uno"]:
                if cuenta["cuenta"] == account:
                    cuenta["creditosRestantes"] = cuenta["creditosRestantes"] - amount
                nueva_data.append(cuenta)

            self.cache.update({"uno": nueva_data})



    # Función para obtener la instancia de CacheManager
def get_cache_manager():
    if not hasattr(get_cache_manager, "_instance"):
        get_cache_manager._instance = CacheManager()

    return get_cache_manager._instance

# Singleton pattern para garantizar una sola instancia de la caché
cache_manager = get_cache_manager()
