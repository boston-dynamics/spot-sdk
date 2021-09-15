FROM python:3.6
COPY . /app
RUN apt-get update
RUN apt-get install -yq --no-install-recommends libgtk2.0-dev
RUN python3 -m pip install numpy==1.16.2
RUN python3 -m pip install -r /app/requirements.txt
WORKDIR /app
ENTRYPOINT ["python3", "./retinanet_server.py"]
