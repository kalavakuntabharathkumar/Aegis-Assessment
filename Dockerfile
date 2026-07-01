FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libopenjp2-7-dev \
    libharfbuzz-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    aiosqlite \
    pymupdf \
    python-multipart \
    pydantic \
    pinecone \
    requests \
    "python-jose[cryptography]" \
    "passlib[bcrypt]" \
    langchain \
    langchain-openai \
    huggingface_hub

COPY backend/ ./backend/

EXPOSE 8080

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080", "--app-dir", "/app"]
