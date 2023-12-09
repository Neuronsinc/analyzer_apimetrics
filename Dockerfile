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
# RUN apt install -y make automake gcc g++ 

# RUN snap install chromium
# RUN snap install chromium

# upgrade pip
RUN pip install --upgrade pip

# install selenium
# RUN pip install selenium
RUN pip install pytest
RUN pip install watchdog

# RUN pip install tensorflow
# RUN pip install 'uvicorn[standard]'

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# RUN pip freeze > requirements_container.txt
COPY . /code

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--ws-ping-interval", "1", "--ws-ping-timeout", "180"]
# CMD ["pytest"]