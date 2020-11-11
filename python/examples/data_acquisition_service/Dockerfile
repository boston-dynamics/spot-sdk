FROM python:3.7

# Install the internal api wheels
COPY docker_requirements_files/gps-metadata-plugin-requirements.txt ./docker-requirements.txt
RUN python3 -m pip install -r docker-requirements.txt

COPY . /app
WORKDIR /app

ENTRYPOINT ["python3", "/app/plugins/gps_metadata_plugin_service.py"]

