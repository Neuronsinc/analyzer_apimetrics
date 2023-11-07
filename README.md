# ApiBotAnalyzer
Esta Api está realizada con FastApi, y utiliza el codigo del analyzer bot.

Para ejecutar esta api se debe hacer:
> python -m uvicorn Api:app --reload

o sino:

> uvicorn Api:app --reload

## Rutas
### **/singleFile**
Esta ruta guarda la imagen recibida en su directorio y envía por medio del bot dicha imagen a ser procesada por predict para así almacenar envíar el resultado al backend 
de Analyzer y almacenarlo.
Esta ruta recibe tres parámetros fundamentales para su funcionamiento los cuáles son:
- **idFolder**: el cuál es el id del folder al cuál se le introducirá el resultado de lo procesado.
- **userCreation**: el cuál es el id del usuario que está solicitando el procesamiento.
- **file**: imagen de tipo png, jpg o jpeg que se procesará.

Aparte a la hora de ejecutarlo en algun servidor es necesario revisar el path del .zip ya que este es descargado del navegador y puede cambiar en base
al lugar dónde esté esta api ejecutandose.

NOTA: uvicorn corre por defecto en  http://127.0.0.1:8000

# AnalyzerBot

Se utilizó selenium para la creación de este bot, cualquier duda revisar la [Documentación de selenium](https://selenium-python.readthedocs.io/locating-elements.html).

## Instalación:
Se debe instalar selenium y puede ser realizado con:
> pip install selenium

Se utilizará Chrome webdriver, por ello en el entorno que se ejecute este bot debe tener ***Google Chrome*** y ***webdriver*** según la versión de Chrome.

## Ejecución:
Para ejeuctar este bot unicamente debe hacerse:
> python bot.py

Por el momento no recibe parametros pero se espera que reciba el nombre de la imagen o video que deberá subir (path).

## NOTA:
Actualmente este bot tiene quemada la cuenta de Erick Moreno para ingresar a Predict de neurons, aparte es requerido para el funcionamiento correcto la pestaña de chrome que se abre sea en pantalla completa en dado caso selenium corra en modo gráfico.

## EC2:
Existe una versión de esta api ejecutandose en una instancia de ec2 (producción), para configurar todo en dicha instancia debe hacerse lo siguiente:

### 1. Instalar ChromeDriver:
Es necesario buscar la version necesaria en este enlace [ChromeDriver storage apis](https://chromedriver.storage.googleapis.com) tratando de buscar el que diga **chromedriver_linux64.zip** luego debe ejecutarse los siguientes comandos:
- navegar al folder /tmp/
> cd /tmp/
- utilizar wget para descargar chromedriver:
>sudo wget https://chromedriver.storage.googleapis.com/versionSeleccionadaEnStorageApis/chromedriver_linux64.zip

- Descomprimir chromedriver:
> sudo unzip chromedriver_linux64.zip
- Mover chromedriver al folder usr/bin:
>sudo mv chromedriver /usr/bin/chromedriver
- Inspeccionar la version actual de chromedriver:
>chromedriver --version

### 2. Instalar Google Chrome:
Es necesario instalar una version compatible de Chrome con la version de Chromedriver. Para su instalación deberá hacerse:
- Instalar la version actual de Chrome:
> wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb                         
sudo apt install ./google-chrome-stable_current_amd64.deb
- Inspeccionar la version instalada:
> google-chrome-stable --version

### 3. Instalar selenium y los requirements:
- Instalar selenium:
> pip install selenium --user
- Instalar los requirements:
> pip install -r requirements.txt

### 4. Nginx, uvicorn y nohup:
Para sue ejecución se utiliza uvicorn pero se requiere que esta ejeución sea persistente por ello se utilizó nohup dónde el comando para lograrlo es:
>  nohup uvicorn Api:app --host 0.0.0.0 --port 3038 --reload &    

El api se encontrará ejecutandose en el puerto **3038** internamente pero se utilizó Nginx para hacer un reverse proxy hacia el host: ip de servidor de producción y puerto **3037** aparte se dejo el dominio http://botapi.predictanalyzer.com que aputara a la dirección de nginx es decir apunta hacia ipservidor:3037 para ser accesible en cualquier lugar

