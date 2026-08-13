FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/salarzeidanlou/whisper-server" \
      org.opencontainers.image.description="Self-hosted relay for end-to-end encrypted messaging and WebRTC signaling" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --no-log-init --shell /bin/false appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
