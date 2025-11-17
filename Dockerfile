FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

VOLUME ["/app"]

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
