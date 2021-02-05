FROM python:3.7-slim

COPY docker-requirements.txt .

RUN python3 -m pip install -r docker-requirements.txt

COPY ./ricoh_theta_image_service.py /app/ricoh_theta_image_service.py
COPY ./ricoh_theta.py /app/ricoh_theta.py

WORKDIR /app

ENTRYPOINT ["python3", "/app/ricoh_theta_image_service.py"]