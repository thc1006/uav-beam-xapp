# Docker Deployment Examples

This directory contains examples for deploying the UAV Beam Tracking xApp using Docker and Docker Compose.

## Quick Start

### 1. Production Deployment

Deploy the xApp in production mode:

```bash
docker-compose up -d prod
```

This uses the optimized production Dockerfile with:
- Multi-stage build for minimal image size
- Non-root user for security
- Health checks enabled
- Resource limits configured

Check logs:
```bash
docker-compose logs -f prod
```

### 2. Development Deployment

Deploy the xApp in development mode with hot reload:

```bash
docker-compose up dev
```

This uses `Dockerfile.dev` with:
- Source code mounted as volume (live updates)
- Debug logging enabled
- Development dependencies installed
- Flask debug mode for auto-reload

### 3. Test Deployment

Run the test suite in Docker:

```bash
docker-compose run test
```

This runs:
- Full pytest suite with coverage
- Linting (flake8)
- Type checking (mypy)
- Code formatting verification (black)

## Configuration

### Environment Variables

Create a `.env` file to customize configuration:

```bash
# Server settings
HOST=0.0.0.0
PORT=5001
LOG_LEVEL=INFO

# Beam configuration
BEAM_NUM_BEAMS_H=16
BEAM_NUM_BEAMS_V=8
BEAM_FAILURE_THRESHOLD_DB=-10.0

# Predictor configuration
PREDICTOR_MAX_VELOCITY=30.0
PREDICTOR_MAX_ACCELERATION=5.0

# Estimator configuration
ESTIMATOR_NUM_ELEMENTS_H=8
ESTIMATOR_NUM_ELEMENTS_V=8
ESTIMATOR_METHOD=music
```

### Custom Configuration File

Mount a custom `config.json`:

```bash
docker run -v $(pwd)/my-config.json:/app/config/config.json \
  -p 5001:5001 \
  ghcr.io/thc1006/uav-beam-xapp:latest
```

## Docker Commands

### Build Image Locally

```bash
# Production image
docker build -t uav-beam-xapp:latest .

# Development image
docker build -f Dockerfile.dev -t uav-beam-xapp:dev .
```

### Run Container

```bash
# Basic run
docker run -p 5001:5001 uav-beam-xapp:latest

# With environment variables
docker run -p 5001:5001 \
  -e LOG_LEVEL=DEBUG \
  -e BEAM_NUM_BEAMS_H=32 \
  uav-beam-xapp:latest

# With volume mount
docker run -p 5001:5001 \
  -v $(pwd)/logs:/app/logs \
  uav-beam-xapp:latest
```

### Health Check

```bash
docker exec <container-id> curl http://localhost:5001/health
```

## Docker Compose Profiles

The `docker-compose.yml` includes multiple profiles:

### Production Profile
```yaml
services:
  prod:
    image: ghcr.io/thc1006/uav-beam-xapp:latest
    ports:
      - "5001:5001"
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

### Development Profile
```yaml
services:
  dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src:ro  # Read-only mount for hot reload
    ports:
      - "5001:5001"
    environment:
      - LOG_LEVEL=DEBUG
      - FLASK_ENV=development
```

### Testing Profile
```yaml
services:
  test:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: pytest tests/ -v --cov=uav_beam
    volumes:
      - ./tests:/app/tests:ro
      - ./src:/app/src:ro
```

## Kubernetes Deployment

For production deployments, use Kubernetes manifests in `deployment/kubernetes/`:

```bash
# Apply all manifests
kubectl apply -f deployment/kubernetes/

# Check deployment
kubectl get pods -l app=uav-beam-xapp
kubectl logs -l app=uav-beam-xapp -f

# Test health endpoint
kubectl port-forward svc/uav-beam-xapp 5001:5001
curl http://localhost:5001/health
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker logs <container-id>
```

Common issues:
- Port 5001 already in use: change port mapping `-p 5002:5001`
- Missing dependencies: rebuild image
- Permission denied: check volume mount permissions

### Health check failing

Verify from inside container:
```bash
docker exec -it <container-id> bash
curl http://localhost:5001/health
```

### Performance issues

Check resource usage:
```bash
docker stats <container-id>
```

Adjust limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## CI/CD Integration

GitHub Actions automatically builds and publishes Docker images:

- **On push to main**: Builds and pushes `latest` tag
- **On version tag**: Builds and pushes versioned tags (e.g., `v0.1.0`)
- **On PR**: Builds image but doesn't push

View published images:
https://github.com/thc1006/uav-beam-xapp/pkgs/container/uav-beam-xapp

## Security Best Practices

1. **Run as non-root user**: ✅ Implemented in Dockerfile
2. **Minimal base image**: ✅ Using `python:3.10-slim`
3. **Scan for vulnerabilities**: ✅ Trivy scanning in CI/CD
4. **No secrets in image**: ✅ Use environment variables
5. **Health checks**: ✅ Configured with 30s interval
6. **Resource limits**: ✅ Set in docker-compose.yml

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [O-RAN SC Documentation](https://docs.o-ran-sc.org/)
