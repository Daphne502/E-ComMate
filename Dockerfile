FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HF Docker Space 默认检查 7860
EXPOSE 7860

ENV ECOMMATE_API_URL=http://127.0.0.1:8000
ENV REDIS_URL=
ENV PYTHONUNBUFFERED=1

CMD ["supervisord", "-c", "supervisord.conf"]