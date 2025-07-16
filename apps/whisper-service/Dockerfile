# GreekSTT Academic Research Platform - Whisper Service
# Handles only Whisper model with transformers 4.36

# Use CUDA 12.1 with cuDNN 8 base, then upgrade cuDNN via pip packages
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 AS base

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Athens

# Install Python 3.11 with proper pip setup
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3.11-distutils \
    curl \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 \
    && update-alternatives --install /usr/bin/pip3 pip3 /usr/local/bin/pip3.11 1

RUN ln -s /usr/bin/python3.11 /usr/bin/python

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    libsndfile1 \
    ffmpeg \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
# Install PyTorch with CUDA 12.1 support first (optimized for Whisper)
RUN pip3 install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    torch==2.2.0+cu121 \
    torchaudio==2.2.0+cu121

# Install the rest of the requirements
RUN pip3 install --no-cache-dir -r requirements.txt

# Force reinstall ctranslate2 and numpy to exact versions for compatibility
RUN pip3 install --force-reinstall ctranslate2==4.4.0 numpy==1.26.4

# Whisper-specific optimizations completed

# Model downloading moved to main.py startup for better flexibility

# Copy application code
COPY app/ ./app/

# Set environment variables for optimal GPU performance
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=0
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512,expandable_segments:True
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
# Optimize cuDNN for faster-whisper
ENV CUDNN_BENCHMARK=1
ENV CUDA_LAUNCH_BLOCKING=0
# Force better memory management
ENV PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.6,max_split_size_mb:128

# Development target
FROM base AS development
RUN pip3 install debugpy==1.8.0
EXPOSE 8001 5680
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5680", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# Production target  
FROM base AS production
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]