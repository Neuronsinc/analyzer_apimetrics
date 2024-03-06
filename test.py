import redis
import json
REDIS='redis-14737.c274.us-east-1-3.ec2.cloud.redislabs.com'
REDISPORT=14737
REDISUSERNAME = 'default'
REDISPASSWORD = 'sBiMwZAb2w1jmwGDIMmi7kx941ArAGXQ'
CLAVE = "CREDITOS"

cache = redis.Redis(host=REDIS, port=REDISPORT, username=REDISUSERNAME, password=REDISPASSWORD)
json_arreglo = cache.get(CLAVE)

if json_arreglo:
    arreglo_objetos = json.loads(json_arreglo)
    print(arreglo_objetos)
else:
    print(json_arreglo)