# Rust Cargo DOS Commander - Docker Build
# Note: This is a GUI application. Docker is provided for CI/testing purposes.
# For actual usage, run natively with: python main.py
#
# Stages:
#   base     - runtime with all dependencies
#   test     - base + test dependencies (for CI)
#
# Usage:
#   Build:            docker build -t cargo-commander .
#   Run smoke test:   docker run --rm cargo-commander smoke
#   Run unit tests:   docker run --rm cargo-commander test
#   Run all tests:    docker run --rm cargo-commander all

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

# Install runtime Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir Pillow==10.4.0

# Copy application code
COPY . .

# Create workspace directory
RUN mkdir -p /root/rust_projects

# Default command (headless validation - imports check)
CMD ["python", "-c", "import app; print(f'Cargo Commander v{app.__version__} - OK')"]

# ---- Test stage ----
FROM base AS test

# Install test dependencies
RUN pip install --no-cache-dir pytest==8.3.3 pytest-cov==5.0.0

# Entry point script for different test modes
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["all"]
