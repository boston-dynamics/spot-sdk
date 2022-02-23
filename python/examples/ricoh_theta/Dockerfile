FROM python:3.7-slim

COPY docker-requirements.txt prebuilt/*.whl ./

RUN python3 -m pip install -r docker-requirements.txt --find-links .

COPY ricoh_theta_image_service.py ricoh_theta.py /app/

WORKDIR /app

ENTRYPOINT ["python3", "/app/ricoh_theta_image_service.py"]
CMD [ "192.168.50.3", "--host-ip=192.168.50.5", "--payload-credentials-file=/creds/payload_guid_and_secret"]
