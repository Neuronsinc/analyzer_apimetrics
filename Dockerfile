# FROM python:3.9-alpine
FROM tensorflow/tensorflow:latest

WORKDIR /code

# update apk repo
# RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
#     echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories

COPY ./requirements.txt /code/requirements.txt

# install chromedriver
RUN mkdir files
RUN apt update

RUN apt update
# RUN apt install -y chromium-browser chromium-chromedriver  make automake gcc g++ 
# RUN apt install -y chromium-chromedriver make automake gcc g++ 
RUN apt install -y make automake gcc g++ libgl1

# RUN snap install chromium
# RUN snap install chromium

# upgrade pip
RUN pip install --upgrade pip

# install selenium
# RUN pip install selenium
RUN pip install pytest
RUN pip install watchdog
RUN pip install tensorflow==2.13.0

# RUN pip install tensorflow
# RUN pip install 'uvicorn[standard]'

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Instalar Redis
# RUN apt-get update && apt-get install -y redis-server

# RUN pip freeze > requirements_container.txt
RUN apt -y install curl

COPY . /code

# COPY dbuild.sh /dbuild.sh
# RUN chmod +x /dbuild.sh


ARG TIME
ENV BUILD_TIME=$TIME

ARG START
ENV BUILD_START=$START

ARG BRANCH
ENV BUILD_BRANCH=$BRANCH

ARG COMMIT
ENV BUILD_COMMIT=$COMMIT

ARG DEV_END
ENV DEVELOP_END=$DEV_END

# Copiar el script de inicio y darle permisos de ejecución
# COPY start.sh /app/start.sh
# RUN chmod +x /app/start.sh

# Exponer los puertos necesarios
#EXPOSE 80 6379

# Establecer el script de inicio como el comando de inicio del contenedor
#CMD ["/app/start.sh"]

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--ws-ping-interval", "1", "--ws-ping-timeout", "180"]
#CMD ["celery", "-A", "app.model.celery_model", "worker", "-l", "info", "--queues=clarity"]
# CMD ["pytest"]