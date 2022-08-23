FROM python:3.7-slim

RUN apt update && apt install -y libgpiod-dev gpiod

WORKDIR /app
# Install requirements.
COPY docker-requirements.txt ./
RUN python3 -m pip install -r docker-requirements.txt

COPY gpio_blink.py /app/
COPY pwm_control.py /app/
COPY core_io_gpio_helpers.py /app/

RUN apt install -y vim

ENTRYPOINT ["python3", "/app/gpio_blink.py"]
