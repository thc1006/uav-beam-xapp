# Contributing to UAV Beam Tracking xApp

Thank you for your interest in contributing to the UAV Beam Tracking xApp! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Performance Benchmarking](#performance-benchmarking)

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv
- Git
- Docker (optional, for containerized testing)
- Kubernetes cluster (optional, for deployment testing)

### Local Development Environment

1. **Clone the repository**

```bash
git clone https://github.com/thc1006/uav-beam-xapp.git
cd uav-beam-xapp
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode with all development dependencies including:
- pytest and pytest-cov for testing
- black for code formatting
- flake8 for linting
- isort for import sorting

4. **Verify installation**

```bash
pytest tests/ -v
```

All tests should pass (175/177 passing, 2 expected failures marked with xfail).

### Docker Development Environment

For containerized development with hot reload:

```bash
docker-compose up dev
```

This starts the xApp with volume mounts for live code updates.

## Development Workflow

### Branch Strategy

- `main` - Stable release branch
- `develop` - Integration branch for features
- `feature/*` - Feature branches
- `fix/*` - Bug fix branches
- `docs/*` - Documentation updates

### Making Changes

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

- Write clear, concise code following project conventions
- Add tests for new functionality
- Update documentation as needed

3. **Run tests locally**

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=uav_beam --cov-report=html

# Run specific test file
pytest tests/test_beam_tracker.py -v
```

4. **Format and lint code**

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/
```

5. **Commit your changes**

```bash
git add .
git commit -m "feat: Add your feature description"
```

Follow conventional commit format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test updates
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

## Testing

### Test Structure

```
tests/
├── test_beam_tracker.py       # Beam management tests
├── test_trajectory_predictor.py  # Kalman filter tests
├── test_angle_estimator.py    # AoA estimation tests
├── test_e2_client.py          # E2 interface tests
├── test_api.py                # REST API tests
└── integration/
    └── test_e2e.py            # End-to-end tests
```

### Writing Tests

- Use pytest fixtures for test setup
- Follow AAA pattern (Arrange, Act, Assert)
- Test both success and failure cases
- Mock external dependencies (E2 interface, network calls)

Example test:

```python
def test_beam_failure_detection():
    """Test beam failure detection with threshold -10dB"""
    tracker = BeamTracker(num_beams_h=16, num_beams_v=8)

    # Arrange
    ue_id = "test-ue-1"
    rsrp = -120.0  # Below failure threshold

    # Act
    decision = tracker.process_measurement(ue_id, rsrp)

    # Assert
    assert decision["action"] == "beam_failure_recovery"
    assert decision["procedure"] == "P3"
```

### Running Benchmarks

```bash
cd benchmarks
python run_benchmarks.py

# Run specific benchmark
python benchmark_beam_tracker.py
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 88 characters (Black default)
- Use docstrings for all public modules, classes, and functions

### Docstring Format

```python
def estimate_angle(self, measurements: np.ndarray) -> tuple:
    """
    Estimate angle of arrival using MUSIC algorithm.

    Args:
        measurements: Complex-valued received signal array (N_elements,)

    Returns:
        Tuple of (azimuth_deg, elevation_deg, confidence)

    Raises:
        ValueError: If measurements shape is invalid
    """
```

### Import Organization

Group imports in the following order:
1. Standard library
2. Third-party packages
3. Local modules

```python
# Standard library
from typing import Dict, Optional

# Third-party
import numpy as np
from flask import Flask, request

# Local
from uav_beam.beam_tracker import BeamTracker
from uav_beam.utils import validate_rsrp
```

## Pull Request Process

1. **Update documentation**
   - Update README.md if adding new features
   - Add docstrings to new functions/classes
   - Update CHANGELOG.md with your changes

2. **Ensure all tests pass**
   - Run full test suite locally
   - Verify CI pipeline passes on GitHub

3. **Create pull request**
   - Use a clear, descriptive title
   - Reference related issues (e.g., "Closes #123")
   - Provide detailed description of changes
   - Include test results and benchmarks if applicable

4. **Code review**
   - Address reviewer feedback promptly
   - Keep discussions focused and professional
   - Update PR based on feedback

5. **Merge requirements**
   - At least one approval from maintainer
   - All CI checks passing
   - No merge conflicts with main branch
   - Up-to-date with latest main branch

## Project Structure

```
uav-beam-xapp/
├── src/uav_beam/           # Main source code
│   ├── __init__.py         # Package exports
│   ├── beam_tracker.py     # Beam management logic
│   ├── trajectory_predictor.py  # Kalman filter
│   ├── angle_estimator.py  # AoA estimation
│   ├── e2_client.py        # E2 interface
│   └── server.py           # Flask API server
├── tests/                  # Test suite
├── benchmarks/             # Performance benchmarks
├── docs/                   # Documentation
├── deployment/             # Deployment configs
│   ├── docker/            # Docker configs
│   └── kubernetes/        # K8s manifests
├── examples/               # Usage examples
└── .github/workflows/      # CI/CD pipelines
```

## Performance Benchmarking

When making performance-critical changes:

1. **Run baseline benchmarks**

```bash
cd benchmarks
python run_benchmarks.py --output baseline.json
```

2. **Make your changes**

3. **Run new benchmarks**

```bash
python run_benchmarks.py --output new.json
```

4. **Compare results**

```bash
python compare_benchmarks.py baseline.json new.json
```

Include benchmark comparison in PR description if performance is affected.

### Performance Targets

- Beam decision latency: <20ms (p95)
- Trajectory prediction: <10ms
- Angle estimation: <15ms (MUSIC, 8x8 UPA)
- Memory footprint: <256MB (steady state)

## Questions or Issues?

- Open a GitHub issue for bugs or feature requests
- Use GitHub Discussions for questions and general discussions
- Check existing issues before creating new ones

## License

By contributing to this project, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to the UAV Beam Tracking xApp! 🚁📡
