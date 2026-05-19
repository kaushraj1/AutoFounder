# Container entry for Cloud Run (api / ws / worker share this image; role via AUTOFOUNDER-AI_ROLE env).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY docker/placeholder_http_server.py ./placeholder_http_server.py

ENV PORT=8080
EXPOSE 8080

CMD ["python", "placeholder_http_server.py"]
