FROM tensorflow/tensorflow:2.1.1-gpu

RUN apt-get update && apt-get install -y libsm6 libxext6 libxrender-dev libgl1-mesa-glx

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

ENV LANG en_US.UTF-8 

COPY . /app
WORKDIR /app

ENTRYPOINT ["/usr/bin/python3", "/app/spot_detect_and_follow.py"]
