# Dockerfile

FROM python:3.11-slim

STOPSIGNAL SIGINT

VOLUME /data

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY README.md .
COPY LICENSE .
COPY keykeeper/ keykeeper/
COPY pyproject.toml .
RUN pip3 install -e .

ENTRYPOINT ["keykeeperd"]
