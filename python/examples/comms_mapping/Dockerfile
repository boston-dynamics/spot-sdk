FROM python:3.6

RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    iputils-ping

COPY docker-requirements.txt prebuilt/*.whl ./
RUN python3 -m pip install -r docker-requirements.txt --find-links .

COPY ./comms_image_service.py /app/comms_image_service.py

WORKDIR /app

ENTRYPOINT ["python3", "/app/comms_image_service.py"]
