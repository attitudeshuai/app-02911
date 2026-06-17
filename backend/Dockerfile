# Rust Cargo DOS Commander - Docker Build
# Note: This is a GUI application. Docker is provided for CI/testing purposes.
# For actual usage, run natively with: python main.py
#
# Usage:
#   docker build -t cargo-commander .
#   docker run --rm cargo-commander              # Smoke test (default)
#   docker run --rm cargo-commander test         # Run full test suite
#   docker run --rm cargo-commander check        # Same as smoke test
#   docker run --rm cargo-commander version      # Show version
#   docker run --rm -it cargo-commander headless # Interactive headless mode

FROM python:3.12-slim AS base

# 配置国内镜像源加速
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies for tkinter and Rust
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk-dev \
    xvfb \
    curl \
    gcc \
    git \
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

# Entry point script for convenience
ENTRYPOINT ["python", "main.py"]

# Default command: smoke test
CMD ["--check"]
