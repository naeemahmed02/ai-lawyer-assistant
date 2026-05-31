FROM python:3.12-slim

# =========================
# ENVIRONMENT (ML + PYTHON)
# =========================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    HF_HOME=/models/huggingface \
    TRANSFORMERS_CACHE=/models/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/models/huggingface \
    RAPIDOCR_MODEL_DIR=/models/rapidocr

# =========================
# WORKDIR
# =========================
WORKDIR /app

# =========================
# SYSTEM DEPENDENCIES
# =========================
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    build-essential \
    libpq-dev \
    libgl1 libglib2.0-0 \
    libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# =========================
# PYTHON DEPENDENCIES
# =========================
COPY requirements/base.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /app/requirements.txt

RUN mkdir -p /models/rapidocr \
 && mkdir -p /usr/local/lib/python3.12/site-packages/rapidocr/models \
 && rm -rf /usr/local/lib/python3.12/site-packages/rapidocr/models \
 && ln -s /models/rapidocr /usr/local/lib/python3.12/site-packages/rapidocr/models

# =========================
# CREATE USER + DIRECTORIES
# =========================
RUN useradd -m appuser && \
    mkdir -p /app/media /models/rapidocr /models/huggingface && \
    chown -R appuser:appuser /app /models

# =========================
# COPY APPLICATION CODE
# =========================
COPY ./backend /app

# =========================
# ENSURE PERMISSIONS
# =========================
RUN chown -R appuser:appuser /app /models

# =========================
# SWITCH USER (SECURE)
# =========================
USER appuser

# =========================
# PORT
# =========================
EXPOSE 8000

# =========================
# START COMMAND
# =========================
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]