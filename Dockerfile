FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 7860

ENV ECOMMATE_API_URL=http://127.0.0.1:8000
ENV REDIS_URL=
ENV PYTHONUNBUFFERED=1

CMD ["/docker-entrypoint.sh"]