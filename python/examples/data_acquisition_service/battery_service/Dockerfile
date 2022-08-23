FROM python:3.7-slim

# Install the API wheels and other requirements.
COPY docker-requirements.txt prebuilt/*.whl ./

RUN python3 -m pip install -r docker-requirements.txt --find-links .

COPY battery_service.py /app/
WORKDIR /app

ENTRYPOINT ["python3", "/app/battery_service.py"]
# Default arguments for running on the CORE I/O
CMD [ "192.168.50.3", "--host-ip=192.168.50.5", "--payload-credentials-file=/creds/payload_guid_and_secret"]

