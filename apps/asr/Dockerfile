FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-venv python3-pip \
        ffmpeg libsndfile1 git \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.11 /usr/bin/python

WORKDIR /app
COPY pyproject.toml .

RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache-dir \
        fastapi uvicorn[standard] pydantic pydantic-settings python-multipart \
        transformers accelerate soundfile numpy && \
    uv pip install --system --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cu124 \
        torch torchaudio

COPY src ./src

EXPOSE 8002
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
