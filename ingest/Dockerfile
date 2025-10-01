FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ADD THIS FILE TO THE COPY LIST
COPY ingest.py parsers.py chunking.py embed.py wiki_stream.py ./
