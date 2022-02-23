FROM python:3.7-slim

# Needed for OpenCV
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

COPY docker-requirements_client.txt prebuilt/*.whl ./
RUN python3 -m pip install -r docker-requirements_client.txt --find-links .

COPY . /app
WORKDIR /app

ENTRYPOINT ["python3", "/app/identify_object.py"]
