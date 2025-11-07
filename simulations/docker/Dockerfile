FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY scheme/ ./scheme/
COPY simulations/ ./simulations/

# Install Python dependencies
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache tinyec cryptography hydra-core omegaconf

# Set environment variables for device type
ENV DEVICE_TYPE="generic"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "simulations.run_simulation"]
