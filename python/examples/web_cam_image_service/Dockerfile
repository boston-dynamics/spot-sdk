FROM python:3.7-slim

# Requirements for opencv to work.
RUN apt-get update && apt-get install -y libsm6 libglib2.0-0 libxrender1 libxext6

COPY docker-requirements.txt prebuilt/*.whl ./

RUN python3 -m pip install -r docker-requirements.txt --find-links .

COPY web_cam_image_service.py /app/
WORKDIR /app

ENTRYPOINT ["python3", "/app/web_cam_image_service.py"]
# Default arguments for running on the Spot CORE
CMD [ "192.168.50.3", "--host-ip=192.168.50.5", "--payload-credentials-file=/creds/payload_guid_and_secret" ]
