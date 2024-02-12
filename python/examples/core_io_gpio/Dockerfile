FROM python:3.7-slim

WORKDIR /app
# Install requirementss

COPY gpio_blink.py /app/
COPY pwm_control.py /app/
COPY core_io_gpio_helpers.py /app/

ENTRYPOINT ["python3", "/app/gpio_blink.py"]
