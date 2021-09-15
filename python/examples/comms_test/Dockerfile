FROM python:3.7-slim-buster

RUN apt-get update && apt-get install -y iperf3 iputils-ping

# Install the internal api wheels
COPY docker-requirements.txt .
RUN python3 -m pip install -r docker-requirements.txt

COPY . /app
WORKDIR /app

ENTRYPOINT ["python3", "/app/client.py"]
