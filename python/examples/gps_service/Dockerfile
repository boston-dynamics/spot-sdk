FROM python:3.7-slim

# Copy required and optional files into the image
COPY docker-requirements.txt gps_listener.py *builder.txt *prebuilt/* /

# Install the API wheels and other requirements.
RUN python3 -m pip install -r docker-requirements.txt --find-links /

WORKDIR /

ENTRYPOINT ["python3", "/gps_listener.py"]
