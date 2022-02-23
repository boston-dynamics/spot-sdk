FROM python:3.6
RUN apt-get update
RUN apt-get install -yq --no-install-recommends libgtk2.0-dev
RUN python3 -m pip install numpy==1.16.2
COPY requirements.txt prebuilt/*.whl ./
RUN python3 -m pip install -r requirements.txt --find-links .
COPY fire_ext.csv /app/
COPY fire_ext.h5 /app/
COPY retinanet_server.py /app/
WORKDIR /app
ENTRYPOINT ["python3", "./retinanet_server.py"]
