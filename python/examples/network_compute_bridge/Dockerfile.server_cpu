FROM tensorflow/tensorflow:2.0.4-py3

# Needed for OpenCV
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

COPY docker-requirements_server_cpu.txt prebuilt/*.whl ./
RUN python3 -m pip install -r docker-requirements_server_cpu.txt --find-links .

COPY tensorflow_server.py /app/
WORKDIR /app

ENTRYPOINT ["python3", "/app/tensorflow_server.py"]
