FROM python:3.7

# Install the API wheels and other requirements.
COPY docker-requirements.txt prebuilt/*.whl ./
RUN python3 -m pip install -r docker-requirements.txt --find-links .

COPY ./pointcloud_plugin_service.py /app/
WORKDIR /app

ENTRYPOINT ["python3", "/app/pointcloud_plugin_service.py"]

