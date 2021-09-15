FROM python:3.7-slim

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

COPY ./daq_upload_docking_callback.py /app/daq_upload_docking_callback.py
# COPY ./config ~/.aws/config

WORKDIR /app

ENTRYPOINT ["python3", "/app/daq_upload_docking_callback.py"]
