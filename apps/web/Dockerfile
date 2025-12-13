# JAI Website (FastAPI) Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system deps (ffmpeg optional for /api/voice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements-core.txt requirements-web.txt /app/
RUN pip install --upgrade pip && pip install -r requirements-web.txt

# Copy the whole project
COPY . /app

EXPOSE 8080

# Use env file at runtime if provided
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
