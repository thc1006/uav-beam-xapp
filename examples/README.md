# UAV Beam xApp - Testing Examples

This directory contains testing and validation tools for the UAV Beam xApp.

## Available Tests

### 1. Local RMR Testing (`test_rmr_local.py`)

Simulates RMR messages locally without requiring a full O-RAN SC deployment. Useful for development and debugging.

#### Usage:

```bash
# Run all test scenarios
python examples/test_rmr_local.py

# Run specific scenario
python examples/test_rmr_local.py --scenario 1

# Use custom config
python examples/test_rmr_local.py --config /path/to/config.json
```

#### Test Scenarios:

1. **Scenario 1**: Weak RSRP triggers beam switch
2. **Scenario 2**: Strong RSRP maintains current beam
3. **Scenario 3**: RIC Control ACK handling
4. **Scenario 4**: RIC Control Failure handling
5. **Scenario 5**: Multiple UEs with different signal conditions

### 2. Kubernetes Deployment Testing (`deploy_and_test.sh`)

Automated deployment and validation script for O-RAN SC Near-RT RIC.

#### Prerequisites:

- Docker
- kubectl (configured for target cluster)
- Helm 3.x
- Access to O-RAN SC RIC cluster

#### Usage:

```bash
# Full deployment and testing
./examples/deploy_and_test.sh

# Skip Docker build
./examples/deploy_and_test.sh --skip-build

# Test existing deployment only
./examples/deploy_and_test.sh --test-only

# Custom namespace and release name
./examples/deploy_and_test.sh --namespace ricxapp --release-name my-uav-xapp
```

#### What it tests:

1. Pod status and health
2. Container logs for errors
3. RMR initialization
4. Health endpoint
5. ConfigMap existence
6. Service creation (HTTP + RMR)
7. RMR ports listening
8. SDL connection

## Unit Tests

Unit tests are located in the `tests/` directory:

```bash
# Run all tests
pytest tests/

# Run RMR client tests specifically
pytest tests/test_rmr_client.py -v

# Run with coverage
pytest tests/ --cov=uav_beam --cov-report=html
```

## Integration Testing with O-RAN SC

### Prerequisites

1. **O-RAN SC Near-RT RIC** deployed with:
   - E2 Termination
   - Routing Manager (rtmgr)
   - Shared Data Layer (Redis/DBAAS)
   - Subscription Manager

2. **E2 Simulator** or real RAN node for E2 interface testing

### Quick Start

```bash
# 1. Build and deploy xApp
./examples/deploy_and_test.sh

# 2. Check xApp logs
kubectl logs -f -n ricxapp -l app.kubernetes.io/name=uav-beam-xapp

# 3. Send test E2 message via E2 Simulator
# (Refer to O-RAN SC documentation for E2 Simulator usage)
```

### Manual Testing

#### Check RMR routing:

```bash
kubectl exec -n ricxapp <xapp-pod-name> -- cat /opt/ric/config/router.txt
```

#### Test health endpoint:

```bash
kubectl exec -n ricxapp <xapp-pod-name> -- curl http://localhost:8080/health
```

#### Check SDL connection:

```bash
kubectl exec -n ricxapp <xapp-pod-name> -- env | grep -i dbaas
```

#### View RMR messages (if RMR logging enabled):

```bash
kubectl logs -n ricxapp <xapp-pod-name> | grep -i "rmr\|e2"
```

## Performance Testing

Monitor xApp performance:

```bash
# CPU/Memory usage
kubectl top pod -n ricxapp -l app.kubernetes.io/name=uav-beam-xapp

# Metrics endpoint (if Prometheus enabled)
kubectl port-forward -n ricxapp <xapp-pod-name> 8080:8080
curl http://localhost:8080/metrics
```

## Troubleshooting

### Common Issues

**Pod CrashLoopBackOff:**
```bash
# Check logs
kubectl logs -n ricxapp <xapp-pod-name>

# Check events
kubectl describe pod -n ricxapp <xapp-pod-name>

# Common causes:
# - RMR library not installed (check Dockerfile)
# - Invalid config-file.json
# - SDL connection failure
```

**RMR Initialization Failure:**
```bash
# Check RMR environment variables
kubectl exec -n ricxapp <xapp-pod-name> -- env | grep RMR

# Verify routing table
kubectl exec -n ricxapp <xapp-pod-name> -- cat $RMR_SEED_RT

# Check RTG service
kubectl get svc -n ricplt service-ricplt-rtmgr-rmr
```

**SDL Connection Issues:**
```bash
# Check Redis service
kubectl get svc -n ricplt | grep dbaas

# Test Redis connection
kubectl exec -n ricxapp <xapp-pod-name> -- \
  redis-cli -h service-ricplt-dbaas-tcp-cluster-0.ricplt ping
```

## Continuous Integration

Example CI pipeline configuration (GitHub Actions):

```yaml
name: Test UAV Beam xApp

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest tests/ -v --cov=uav_beam

      - name: Run local RMR tests
        run: python examples/test_rmr_local.py
```

## Additional Resources

- [O-RAN SC Documentation](https://docs.o-ran-sc.org/)
- [RMR User Guide](https://docs.o-ran-sc.org/projects/o-ran-sc-ric-plt-lib-rmr/)
- [xApp Framework Documentation](https://docs.o-ran-sc.org/projects/o-ran-sc-ric-plt-xapp-frame-py/)
- [E2 Interface Specifications](https://www.o-ran.org/specifications)

## Support

For issues or questions:
- Check logs: `kubectl logs -n ricxapp -l app.kubernetes.io/name=uav-beam-xapp`
- Review O-RAN SC troubleshooting guides
- Open an issue in the project repository
