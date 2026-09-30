FROM python:3.11-slim

# Owner: M1, M2, M3
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY client/ /app/client/
COPY models/ /app/models/
COPY data/ /app/data/
COPY privacy/ /app/privacy/
COPY network/ /app/network/

ENV NODE_ID=1
ENV PORT=8081
ENV SERVER_ADDRESS=server:8080

CMD python -m client.client --node-id ${NODE_ID} --port ${PORT} --server-address ${SERVER_ADDRESS} --use-encryption --use-dp
