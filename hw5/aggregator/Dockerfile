FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY aggregator/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY aggregator /app/aggregator

WORKDIR /app/aggregator

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
