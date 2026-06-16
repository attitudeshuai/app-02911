# Rust Cargo DOS Commander - Docker Build
# Note: This is a GUI application. Docker is provided for CI/testing purposes.
# For actual usage, run natively with: python main.py

FROM python:3.12-slim AS base

# 配置国内镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies for tkinter and Rust
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk-dev \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (for cargo commands to work)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create workspace directory
RUN mkdir -p /root/rust_projects

# Default command (headless validation - imports check)
CMD ["python", "-c", "import app; print(f'Cargo Commander v{app.__version__} - OK')"]
