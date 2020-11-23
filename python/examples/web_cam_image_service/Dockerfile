FROM jjanzic/docker-python3-opencv

COPY docker-requirements.txt .

RUN python3 -m pip install -r docker-requirements.txt

COPY . /app
WORKDIR /app

ENTRYPOINT ["python3", "/app/web_cam_image_service.py"]

