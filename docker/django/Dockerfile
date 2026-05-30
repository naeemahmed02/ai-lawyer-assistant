# =========================================================
# BASE IMAGE
# =========================================================
FROM python:3.12-slim

# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models/huggingface \
    TRANSFORMERS_CACHE=/models/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/models/huggingface

# =========================================================
# WORK DIRECTORY
# =========================================================
WORKDIR /app

# =========================================================
# SYSTEM DEPENDENCIES
# =========================================================
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libx11-6 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# =========================================================
# INSTALL PYTHON DEPENDENCIES
# =========================================================

# Copy requirements separately for Docker cache optimization
COPY requirements/base.txt .

RUN pip install --upgrade pip setuptools wheel

RUN pip install -r base.txt

# =========================================================
# PRE-DOWNLOAD AI MODELS
# =========================================================

# SentenceTransformer model preload
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Optional: preload Docling models
RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"

# =========================================================
# COPY APPLICATION
# =========================================================
COPY ./backend /app

# =========================================================
# CREATE NON-ROOT USER (SECURITY)
# =========================================================
RUN useradd -m appuser

RUN chown -R appuser:appuser /app /models

USER appuser

# =========================================================
# EXPOSE PORT
# =========================================================
EXPOSE 8000

# =========================================================
# DEFAULT COMMAND
# =========================================================
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]