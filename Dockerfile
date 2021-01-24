FROM python:3.9-slim-buster

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt
           
WORKDIR /app
COPY main /app/main

EXPOSE 8000

CMD ["gunicorn", "-w", "10" , "-b", "0.0.0.0:8000", "main:create_app(dsn='')"]
