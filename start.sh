#!/bin/bash

# Iniciar Redis en segundo plano
redis-server --daemonize yes

# Iniciar Uvicorn en segundo plano
uvicorn app.main:app --host 0.0.0.0 --port 80 --reload --ws-ping-interval 1 --ws-ping-timeout 180 &

# Iniciar Celery worker para cola de extraccion de caracteristicas
celery -A app.model.celery_model worker --pool prefork -l info --queues=caracteristicas

# Iniciar Celery worker para cola de prediccion
celery -A app.model.celery_model worker --pool threads -l info --queues=prediccion

