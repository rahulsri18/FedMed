FROM python:3.11-slim

# Owner: M1 (Server & Orchestration Lead)
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ /app/server/
COPY models/ /app/models/
COPY privacy/ /app/privacy/
COPY network/ /app/network/
COPY data/ /app/data/

EXPOSE 8080

CMD ["python", "-m", "server.server", "--port", "8080", "--rounds", "5", "--encrypted"]
