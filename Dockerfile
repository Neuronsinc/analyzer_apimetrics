FROM tensorflow/tensorflow:latest

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN apt update
RUN apt install -y make automake gcc g++ libgl1
RUN pip install --upgrade pip

RUN pip install pytest
RUN pip install watchdog
RUN pip install tensorflow==2.13.0

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN apt -y install curl

COPY . /code
