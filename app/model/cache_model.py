#from cachetools import TTLCache
import redis
import json
import time

REDIS='redis-14737.c274.us-east-1-3.ec2.cloud.redislabs.com'
REDISPORT=14737
REDISUSERNAME = 'default'
REDISPASSWORD = 'sBiMwZAb2w1jmwGDIMmi7kx941ArAGXQ'
#CLAVE = "CREDITOS"
CLAVE = "CREDITOSDOS"
class CacheManager:
    def __init__(self):
        #self.cache = TTLCache(maxsize=1000, ttl=10800) # expiramos el cache en 3 horas
        self.cache = redis.Redis(host=REDIS, port=REDISPORT, username=REDISUSERNAME, password=REDISPASSWORD)

    def get_cache_instance(self):
        # json_arreglo = self.cache.get(CLAVE)
        # if json_arreglo:
        #     arreglo_objetos = json.loads(json_arreglo)
        #     return arreglo_objetos
        # else:
        #     return None
        elementos = self.cache.lrange(CLAVE, 0, -1)

        if elementos:
            objetos = [json.loads(elemento.decode('utf-8')) for elemento in elementos]
            return objetos
        else:
            return None
    
    def set_data_to_cache(self, data):
        #self.cache.update({"uno": data})
        tiempo_vencimiento = 10800  # expiramos el cache en 3 horas
        self.cache.setex(CLAVE, tiempo_vencimiento, json.dumps(data))

    def push_elements(self, data, expiry):
        self.cache.rpush(CLAVE, *data)

        if expiry:
            tiempo_vencimiento = 10800  # expiramos el cache en 3 horas
            self.cache.expire(CLAVE, tiempo_vencimiento)

    def pop_elements(self):
        element = self.cache.lpop(CLAVE)
        if element is not None:
            return json.loads(element.decode('utf-8'))
        else:
            return None
    
    def creditos_videos(self, num_creditos):
        while True:
            try:
                # Iniciar una transacción WATCH
                with self.cache.pipeline() as pipe:
                    while True:
                        try:
                            # Verificar disponibilidad de créditos de la misma cuenta
                            creditos_obtenidos = []

                            # Obtener el primer crédito de la cola
                            primer_credito = self.cache.lindex(CLAVE, 0)
                            if primer_credito is None:
                                return None

                            # Convertir el primer crédito a un diccionario
                            primer_credito = json.loads(primer_credito)
                            cuenta = primer_credito['cuenta']
                            creditos_obtenidos.append(primer_credito)
                            pipe.lpop(CLAVE)

                            # Obtener el resto de los créditos
                            for _ in range(num_creditos - 1):
                                siguiente_credito = self.cache.lindex(CLAVE, 0)
                                if siguiente_credito is None:
                                    return None

                                # Convertir el siguiente crédito a un diccionario
                                siguiente_credito = json.loads(siguiente_credito)

                                # Verificar si el crédito pertenece a la misma cuenta
                                if siguiente_credito['cuenta'] != cuenta:
                                    # Si no pertenece a la misma cuenta, abortar y volver a intentar
                                    raise redis.exceptions.WatchError

                                # Agregar el crédito a la lista de créditos obtenidos
                                creditos_obtenidos.append(siguiente_credito)
                                pipe.lpop(CLAVE)

                            # Ejecutar la transacción
                            pipe.execute()

                            return creditos_obtenidos[0]

                        except redis.exceptions.WatchError:
                            # Si se produce una WatchError, otro proceso está modificando la cola,
                            # por lo que reintentamos la transacción
                            continue

            except redis.exceptions.RedisError as e:
                # Manejar cualquier otra excepción de Redis
                print("Error Redis:", e)
                return None

    def largo_cola(self):
        return self.cache.llen(CLAVE)
    
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
