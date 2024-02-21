#from cachetools import TTLCache
import redis
import json
import time

REDIS='redis-14737.c274.us-east-1-3.ec2.cloud.redislabs.com'
REDISPORT=14737
REDISUSERNAME = 'default'
REDISPASSWORD = 'sBiMwZAb2w1jmwGDIMmi7kx941ArAGXQ'
CLAVE = "CREDITOS"
class CacheManager:
    def __init__(self):
        #self.cache = TTLCache(maxsize=1000, ttl=10800) # expiramos el cache en 3 horas
        self.cache = redis.Redis(host=REDIS, port=REDISPORT, username=REDISUSERNAME, password=REDISPASSWORD)

    def get_cache_instance(self):
        json_arreglo = self.cache.get(CLAVE)
        if json_arreglo:
            arreglo_objetos = json.loads(json_arreglo)
            return arreglo_objetos
        else:
            return None
    
    def set_data_to_cache(self, data):
        #self.cache.update({"uno": data})
        tiempo_vencimiento = 10800  # expiramos el cache en 3 horas
        self.cache.setex(CLAVE, tiempo_vencimiento, json.dumps(data))

    
    def extract_credits(self, account, amount):
        # if "uno" in self.cache:
        #     nueva_data =  []
        #     for cuenta in self.cache["uno"]:
        #         if cuenta["cuenta"] == account:
        #             cuenta["creditosRestantes"] = cuenta["creditosRestantes"] - amount
        #         nueva_data.append(cuenta)

        #     self.cache.update({"uno": nueva_data})
        lock_key = f"{CLAVE}_lock"
        
        # Intentar obtener el bloqueo
        adquirido = self.cache.setnx(lock_key, "LOCK")
        
        if adquirido:
            try:
                tiempo_vencimiento = self.cache.ttl(CLAVE)
                if tiempo_vencimiento > 0:
                    valor_actual = self.cache.get(CLAVE)
                    if valor_actual is not None:
                        arreglo_objetos = json.loads(valor_actual)
                        nueva_data = []
                        for cuenta in arreglo_objetos:
                            if cuenta["cuenta"] == account:
                                cuenta["creditosRestantes"] -= amount
                            nueva_data.append(cuenta)

                        # Actualizar los datos de la cola
                        self.cache.setex(CLAVE, tiempo_vencimiento, json.dumps(nueva_data))
            finally:
                # Liberar el bloqueo
                self.cache.delete(lock_key)
        else:
            # Si no se puede adquirir el bloqueo, esperar y volver a intentarlo
            time.sleep(0.1)
            self.extract_credits(account, amount)



    # Función para obtener la instancia de CacheManager
def get_cache_manager():
    if not hasattr(get_cache_manager, "_instance"):
        get_cache_manager._instance = CacheManager()

    return get_cache_manager._instance

# Singleton pattern para garantizar una sola instancia de la caché
cache_manager = get_cache_manager()
