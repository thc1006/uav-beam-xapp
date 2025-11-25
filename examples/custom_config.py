#!/usr/bin/env python3
"""
Custom configuration example for UAV Beam Tracking xApp.

This example demonstrates:
1. Loading custom configuration
2. Creating BeamTracker with specific parameters
3. Customizing trajectory predictor settings
4. Using different angle estimation methods (MUSIC vs ESPRIT)
"""

import json
from pathlib import Path
from uav_beam import BeamTracker, TrajectoryPredictor, AngleEstimator


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file."""
    config_file = Path(config_path)

    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        print(f"⚠️  Config file not found: {config_path}")
        print("Using default configuration")
        return get_default_config()


def get_default_config() -> dict:
    """Return default configuration."""
    return {
        "beam": {
            "num_beams_h": 16,
            "num_beams_v": 8,
            "beam_failure_threshold_db": -10.0,
            "prediction_horizon_ms": 20.0
        },
        "predictor": {
            "max_velocity": 30.0,
            "max_acceleration": 5.0,
            "process_noise_std": 0.1,
            "measurement_noise_std": 1.0
        },
        "estimator": {
            "num_elements_h": 8,
            "num_elements_v": 8,
            "spacing": 0.5,
            "method": "music"
        }
    }


def create_beam_tracker_from_config(config: dict) -> BeamTracker:
    """Create BeamTracker instance with custom configuration."""
    beam_config = config.get("beam", {})

    tracker = BeamTracker(
        num_beams_h=beam_config.get("num_beams_h", 16),
        num_beams_v=beam_config.get("num_beams_v", 8),
        beam_failure_threshold_db=beam_config.get("beam_failure_threshold_db", -10.0),
        prediction_horizon_ms=beam_config.get("prediction_horizon_ms", 20.0)
    )

    print(f"✅ BeamTracker created:")
    print(f"   Beam array: {tracker.num_beams_h}x{tracker.num_beams_v}")
    print(f"   Failure threshold: {tracker.beam_failure_threshold_db} dB")
    print(f"   Prediction horizon: {tracker.prediction_horizon_ms} ms")

    return tracker


def create_trajectory_predictor_from_config(config: dict) -> TrajectoryPredictor:
    """Create TrajectoryPredictor with custom parameters."""
    pred_config = config.get("predictor", {})

    predictor = TrajectoryPredictor(
        max_velocity=pred_config.get("max_velocity", 30.0),
        max_acceleration=pred_config.get("max_acceleration", 5.0),
        process_noise_std=pred_config.get("process_noise_std", 0.1),
        measurement_noise_std=pred_config.get("measurement_noise_std", 1.0)
    )

    print(f"\n✅ TrajectoryPredictor created:")
    print(f"   Max velocity: {predictor.max_velocity} m/s")
    print(f"   Max acceleration: {predictor.max_acceleration} m/s²")
    print(f"   Process noise: {predictor.process_noise_std}")
    print(f"   Measurement noise: {predictor.measurement_noise_std}")

    return predictor


def create_angle_estimator_from_config(config: dict) -> AngleEstimator:
    """Create AngleEstimator with custom configuration."""
    est_config = config.get("estimator", {})

    estimator = AngleEstimator(
        num_elements_h=est_config.get("num_elements_h", 8),
        num_elements_v=est_config.get("num_elements_v", 8),
        spacing=est_config.get("spacing", 0.5),
        method=est_config.get("method", "music")
    )

    print(f"\n✅ AngleEstimator created:")
    print(f"   Antenna array: {estimator.num_elements_h}x{estimator.num_elements_v}")
    print(f"   Element spacing: {estimator.spacing}λ")
    print(f"   Method: {estimator.method.upper()}")

    return estimator


def example_high_speed_uav_config() -> dict:
    """Configuration for high-speed UAV (e.g., racing drone)."""
    return {
        "beam": {
            "num_beams_h": 32,  # More beams for finer tracking
            "num_beams_v": 16,
            "beam_failure_threshold_db": -8.0,  # Stricter threshold
            "prediction_horizon_ms": 10.0  # Shorter horizon for faster updates
        },
        "predictor": {
            "max_velocity": 50.0,  # Higher max velocity
            "max_acceleration": 10.0,  # Higher acceleration
            "process_noise_std": 0.2,  # Higher uncertainty
            "measurement_noise_std": 1.5
        },
        "estimator": {
            "num_elements_h": 16,  # Larger array for better resolution
            "num_elements_v": 16,
            "spacing": 0.5,
            "method": "music"
        }
    }


def example_low_power_uav_config() -> dict:
    """Configuration for low-power, slow-moving UAV."""
    return {
        "beam": {
            "num_beams_h": 8,  # Fewer beams to reduce computation
            "num_beams_v": 4,
            "beam_failure_threshold_db": -12.0,  # More tolerant threshold
            "prediction_horizon_ms": 50.0  # Longer horizon for less frequent updates
        },
        "predictor": {
            "max_velocity": 15.0,  # Lower max velocity
            "max_acceleration": 3.0,  # Lower acceleration
            "process_noise_std": 0.05,  # Lower uncertainty
            "measurement_noise_std": 0.5
        },
        "estimator": {
            "num_elements_h": 4,  # Smaller array
            "num_elements_v": 4,
            "spacing": 0.5,
            "method": "esprit"  # ESPRIT may be faster than MUSIC
        }
    }


def main():
    """Run custom configuration examples."""
    print("=" * 60)
    print("UAV Beam Tracking xApp - Custom Configuration Examples")
    print("=" * 60)

    # Example 1: Load from file (if exists)
    print("\n1️⃣  Loading configuration from file...")
    config = load_config("config.json")

    # Example 2: High-speed UAV configuration
    print("\n" + "=" * 60)
    print("2️⃣  High-Speed UAV Configuration (Racing Drone)")
    print("=" * 60)
    high_speed_config = example_high_speed_uav_config()
    tracker_hs = create_beam_tracker_from_config(high_speed_config)
    predictor_hs = create_trajectory_predictor_from_config(high_speed_config)
    estimator_hs = create_angle_estimator_from_config(high_speed_config)

    # Example 3: Low-power UAV configuration
    print("\n" + "=" * 60)
    print("3️⃣  Low-Power UAV Configuration (Surveillance Drone)")
    print("=" * 60)
    low_power_config = example_low_power_uav_config()
    tracker_lp = create_beam_tracker_from_config(low_power_config)
    predictor_lp = create_trajectory_predictor_from_config(low_power_config)
    estimator_lp = create_angle_estimator_from_config(low_power_config)

    # Save custom configuration
    print("\n" + "=" * 60)
    print("4️⃣  Saving custom configuration...")
    print("=" * 60)

    custom_config_path = "custom_uav_config.json"
    with open(custom_config_path, 'w') as f:
        json.dump(high_speed_config, f, indent=2)
    print(f"✅ Configuration saved to: {custom_config_path}")

    print("\n" + "=" * 60)
    print("✅ Custom configuration examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
