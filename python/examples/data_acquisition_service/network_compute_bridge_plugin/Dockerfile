FROM python:3.7

COPY docker-requirements.txt prebuilt/*.whl ./
RUN python3 -m pip install -r docker-requirements.txt --find-links .

COPY network_compute_bridge_plugin_service.py /app/network_compute_bridge_plugin_service.py
WORKDIR /app

ENTRYPOINT ["python3", "/app/network_compute_bridge_plugin_service.py"]
