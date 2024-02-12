# Import the base environments
FROM arm64v8/python:3.10-slim

# Copy the requirements and wheels for installation.
COPY docker-requirements.txt prebuilt/*.whl ./

# Install requirements from docker-requirements.txt
RUN python3 -m pip install -r docker-requirements.txt --find-links .

# Set the working directory and copy the script.
COPY src/metrics_over_coreio.py src/uploader.py src/metric_file_group.py /app/

WORKDIR /app/

# Add entrypoints
ENTRYPOINT ["python3", "/app/metrics_over_coreio.py"]
CMD ["192.168.50.3",  "--host-ip=192.168.50.5", "--payload-credentials-file=/creds/payload_guid_and_secret", "--dir-metrics=/performance_logs"]

