FROM python:3.10
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get update && apt-get install -yq --no-install-recommends libgtk2.0-dev
COPY docker-requirements.txt prebuilt/*.whl ./
RUN python3 -m pip install -r docker-requirements.txt --find-links .
COPY fire_ext.csv /app/
COPY fire_ext.h5 /app/
COPY retinanet_server.py /app/
WORKDIR /app
ENTRYPOINT ["python3", "./retinanet_server.py"]
