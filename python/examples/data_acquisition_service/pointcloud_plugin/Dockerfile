FROM python:3.7

# Install the API wheels and other requirements.
COPY docker-requirements.txt .
RUN python3 -m pip install -r docker-requirements.txt

COPY . /app
WORKDIR /app

ENTRYPOINT ["python3", "/app/pointcloud_plugin_service.py"]

