FROM python:3.7-slim

# Install the API wheels and other requirements.
COPY docker-requirements.txt prebuilt/*.whl ./

RUN python3 -m pip install -r docker-requirements.txt --find-links .

COPY area_callback_look_both_ways.py /app/
WORKDIR /app

ENTRYPOINT ["python3", "/app/area_callback_look_both_ways.py"]
# Default arguments for running on the Spot CORE
CMD [ "192.168.50.3", "--payload-credentials-file=/creds/payload_guid_and_secret"]

