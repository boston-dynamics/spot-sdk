FROM python:3.7-slim

RUN apt-get update && apt-get install -y libgtk2.0-dev libglib2.0-0

COPY docker-requirements.txt .

RUN python3 -m pip install -r docker-requirements.txt

COPY . /app
WORKDIR /app

ENTRYPOINT ["python3", "/app/web_cam_image_service.py"]

