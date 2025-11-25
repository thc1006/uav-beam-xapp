# Multi-stage build for minimal production image
FROM python:3.10-slim AS builder

WORKDIR /build

# Copy package files
COPY setup.py pyproject.toml ./
COPY src/ ./src/
COPY README.md ./

# Build wheel
RUN pip install --no-cache-dir build && \
    python -m build --wheel

# Production image with RMR support
FROM python:3.10-slim

LABEL org.opencontainers.image.title="UAV Beam Tracking xApp" \
      org.opencontainers.image.description="O-RAN Near-RT RIC xApp for UAV mmWave beam management with RMR support" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.vendor="UAV O-RAN Research Team" \
      org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

# Install RMR library and runtime dependencies
# RMR requires gcc, make, cmake for building native extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        ca-certificates \
        gcc \
        g++ \
        make \
        cmake \
        git && \
    rm -rf /var/lib/apt/lists/*

# Install RMR C library from O-RAN SC
RUN wget -nv --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr_4.9.0_amd64.deb/download.deb && \
    wget -nv --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr-dev_4.9.0_amd64.deb/download.deb && \
    dpkg -i rmr_4.9.0_amd64.deb rmr-dev_4.9.0_amd64.deb || true && \
    apt-get install -f -y && \
    rm -f *.deb

# Copy and install wheel with RMR dependencies
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl /root/.cache

# Create O-RAN xApp directory structure
RUN mkdir -p /opt/ric/config && \
    chown -R root:root /opt/ric

# Copy xApp descriptor files
COPY config/config-file.json /opt/ric/config/
COPY config/schema.json /opt/ric/config/

# Create non-root user
RUN useradd -m -u 1000 xapp && \
    chown -R xapp:xapp /app && \
    chown -R xapp:xapp /opt/ric

USER xapp

# Expose HTTP port for REST API and RMR ports
EXPOSE 8080
EXPOSE 4560
EXPOSE 4561

# RMR environment variables (can be overridden by Helm/K8s)
ENV RMR_SEED_RT=/opt/ric/config/router.txt
ENV RMR_RTG_SVC=service-ricplt-rtmgr-rmr.ricplt:4561
ENV LOG_LEVEL=INFO

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default to RMR mode (can override with docker run command)
ENTRYPOINT ["python", "-m", "uav_beam.rmr_client"]
CMD ["--config", "/opt/ric/config/config-file.json"]
