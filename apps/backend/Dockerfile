FROM python:3.11-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y curl gcc libpq-dev && rm -rf /var/lib/apt/lists/*
RUN pip install uv

FROM base AS development
COPY requirements.txt requirements-dev.txt ./
RUN uv pip install --system -r requirements.txt -r requirements-dev.txt
EXPOSE 8000

FROM base AS production
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
