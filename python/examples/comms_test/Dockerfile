FROM python:3.7-slim-buster

RUN apt-get update && apt-get install -y iperf3 iputils-ping

# Install the internal api wheels
COPY docker-requirements.txt prebuilt/*.whl ./
RUN python3 -m pip install -r docker-requirements.txt --find-links .

COPY client.py /app/
WORKDIR /app

ENTRYPOINT ["python3", "/app/client.py"]
