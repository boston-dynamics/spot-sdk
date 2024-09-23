# Import the base environments
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install necessary packages for your application (if any)
# rm -rf /var/lib/apt/lists/* cleans up the list of available packages to reduce the image size for a faster upload
# Please use the below line as a template for future installations
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements and wheels for installation.
COPY docker-requirements.txt .

# Install requirements from docker-requirements.txt
RUN python3 -m pip install -r docker-requirements.txt

# Copy the script.
COPY webhook_integration.py /app/

# Copy the rest of your application into the container
COPY extension/.env /app/extension/

# Make port 21800 available to the world outside this container
EXPOSE 21800

# Add entrypoints
ENTRYPOINT ["python3", "webhook_integration.py"]
CMD ["--hostname", "172.17.0.1", "--verify", "False", "--webhook-host", "172.17.0.1", "--webhook-port", "21800"]

