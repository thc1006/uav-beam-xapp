# Changelog

All notable changes to the UAV Beam Tracking xApp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-25

### Added
- Initial release of UAV Beam Tracking xApp for O-RAN Near-RT RIC
- 3GPP TS 38.321-compliant beam management procedures (P1/P2/P3)
- mmWave beamforming support for 5G NR FR2 (28/39 GHz)
- Kalman filter-based trajectory prediction with velocity/acceleration constraints
- Angle of Arrival estimation using MUSIC and ESPRIT algorithms
- E2 interface implementation for RAN communication
- RESTful API with endpoints:
  - `POST /e2/indication` - Receive E2 indications from RIC
  - `GET /health` - Health check endpoint
  - `GET /metrics` - Prometheus-compatible metrics
  - `GET /stats` - Runtime statistics
- Comprehensive test suite (177 tests)
- Performance benchmarks for all core algorithms
- Docker containerization with multi-stage builds
- Kubernetes deployment manifests with ConfigMaps
- GitHub Actions CI/CD pipelines
- Modern Python packaging with pyproject.toml (PEP 517/518)

### Features
- Real-time beam tracking with sub-20ms decision latency
- Proactive beam switching based on predicted UAV trajectory
- Support for 3D beamforming with configurable horizontal/vertical beam arrays
- Multi-UE tracking with independent beam management
- Configurable beam failure threshold and prediction horizons
- Memory-efficient circular buffers for measurement history
- Graceful degradation on prediction failures

### Performance
- Average beam decision latency: 15ms (target: <20ms)
- Trajectory prediction: 8ms (Kalman filter)
- Angle estimation: 12ms (MUSIC algorithm, 8x8 UPA)
- Memory footprint: <256MB typical runtime

### Documentation
- Comprehensive README with architecture overview
- API documentation for all public interfaces
- Deployment guides for Docker and Kubernetes
- Performance benchmarking suite
- Contributing guidelines

### Known Limitations
- No authentication/authorization on API endpoints (development only)
- Two test cases marked as expected failures (xfail)
- No TLS/SSL support for API endpoints
- Single-threaded Flask server (not production-ready)

### Security Notes
- This release is intended for development and testing environments only
- DO NOT deploy to production without implementing proper authentication
- API endpoints are exposed without encryption
- Refer to production readiness assessment for security requirements

---

[0.1.0]: https://github.com/thc1006/uav-beam-xapp/releases/tag/v0.1.0
