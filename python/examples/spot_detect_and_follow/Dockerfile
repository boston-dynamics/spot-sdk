FROM tensorflow/tensorflow:2.1.1-gpu

RUN apt-get update && apt-get install -y libsm6 libxext6 libxrender-dev libgl1-mesa-glx

COPY docker-requirements.txt prebuilt/*.whl ./
RUN python3 -m pip install -r docker-requirements.txt --find-links .

ENV LANG en_US.UTF-8 

COPY tensorflow_object_detection.py /app/
COPY spot_detect_and_follow.py /app/
WORKDIR /app

ENTRYPOINT ["/usr/bin/python3", "/app/spot_detect_and_follow.py"]
