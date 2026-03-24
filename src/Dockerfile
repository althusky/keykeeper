# Dockerfile

FROM python:3.11-slim

STOPSIGNAL SIGINT

VOLUME /data

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY keykeeper_pack/ keykeeper_pack/
COPY server_pack/ server_pack/

COPY keykeeper_protocol.py keykeeper_protocol.py
COPY server.py server.py
COPY keykeeper.py keykeeper.py


ENTRYPOINT ["python3", "server.py"]
