FROM python:3.12-slim

LABEL maintainer="mihai@developerakademie.com"
LABEL version="1.0"
LABEL description="Python 3.12 Slim Debian-based image for Videoflix backend"

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        ffmpeg \
        libpq-dev \
        gcc && \
    rm -rf /var/lib/apt/lists/* && \
    chmod +x backend.entrypoint.sh

EXPOSE 8000

ENTRYPOINT [ "sh", "/app/backend.entrypoint.sh" ]
