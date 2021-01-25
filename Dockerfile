FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
           
ENV PYTHONUNBUFFERED 1

COPY main ./main
COPY tests ./tests
COPY setup.py .
COPY setup.cfg .

CMD ["gunicorn", "-b", "0.0.0.0:8000", "main:create_app(dsn='')"]
