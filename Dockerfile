FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y awscli default-mysql-client postgresql-client redis-tools iputils-ping mtr procps && \
    apt-get clean

RUN pip install flask flask-socketio cryptography

WORKDIR /app

COPY . /app

EXPOSE 5000

CMD ["python", "app.py"]
