FROM python:3.10-slim

WORKDIR /app

COPY gpio_example.py /app/
COPY pwm_control.py /app/
COPY core_io_gpio_helpers.py /app/
COPY docker-requirements.txt /app/

# Install requirements
RUN python3 -m pip install -r docker-requirements.txt

ENTRYPOINT ["python3", "/app/gpio_example.py"]