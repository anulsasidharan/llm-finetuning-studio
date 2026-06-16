FROM python:3.11-slim AS development
WORKDIR /training_engine
RUN apt-get update && apt-get install -y curl gcc git && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt
COPY . .

FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 AS gpu
WORKDIR /training_engine
RUN apt-get update && apt-get install -y python3.11 git curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY requirements.txt ./
RUN uv pip install --system torch==2.3.0 torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121
RUN uv pip install --system -r requirements.txt
COPY . .
