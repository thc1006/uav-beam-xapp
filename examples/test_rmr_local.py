#!/usr/bin/env python3
"""
Local RMR testing script for UAV Beam xApp.

This script simulates RMR messages locally without requiring a full O-RAN SC deployment.
Useful for development and debugging.

Usage:
    python examples/test_rmr_local.py [--config CONFIG_PATH] [--fake-sdl]
"""

import argparse
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def create_mock_ric_indication(ue_id: str, rsrp: float, serving_beam: int) -> Dict[str, Any]:
    """Create mock RIC Indication message"""
    return {
        "message type": 12050,  # RIC_INDICATION
        "payload": json.dumps({
            "ue_id": ue_id,
            "rsrp": rsrp,
            "serving_beam": serving_beam,
            "timestamp": int(time.time() * 1000),
            "position": {
                "x": 100.0,
                "y": 200.0,
                "z": 50.0
            },
            "velocity": {
                "vx": 10.0,
                "vy": 5.0,
                "vz": 0.0
            }
        })
    }


def create_mock_ric_control_ack(request_id: str, ue_id: str) -> Dict[str, Any]:
    """Create mock RIC Control ACK message"""
    return {
        "message type": 12041,  # RIC_CONTROL_ACK
        "payload": json.dumps({
            "request_id": request_id,
            "ue_id": ue_id,
            "status": "success",
            "timestamp": int(time.time() * 1000)
        })
    }


def create_mock_ric_control_failure(request_id: str, ue_id: str, cause: str) -> Dict[str, Any]:
    """Create mock RIC Control Failure message"""
    return {
        "message type": 12042,  # RIC_CONTROL_FAILURE
        "payload": json.dumps({
            "request_id": request_id,
            "ue_id": ue_id,
            "cause": cause,
            "status": "failure",
            "timestamp": int(time.time() * 1000)
        })
    }


class MockRMRXapp:
    """Mock RMR xApp for local testing"""

    def __init__(self, config_path: str, use_fake_sdl: bool = True):
        print(f"Initializing Mock RMR xApp with config: {config_path}")
        self.config_path = config_path
        self.use_fake_sdl = use_fake_sdl
        self.sent_messages = []

        # Import here to allow testing without RMR installed
        try:
            from uav_beam.rmr_client import UAVBeamRMRXapp
            self.xapp = UAVBeamRMRXapp(use_fake_sdl=use_fake_sdl)
            print("Using real UAVBeamRMRXapp")
        except ImportError as e:
            print(f"Warning: Cannot import UAVBeamRMRXapp: {e}")
            print("Running in mock-only mode")
            self.xapp = None

    def send_mock_message(self, message: Dict[str, Any]):
        """Send mock message to xApp"""
        print(f"\nSending message type {message['message type']}:")
        payload = json.loads(message['payload'])
        print(f"  Payload: {json.dumps(payload, indent=2)}")

        if self.xapp is None:
            print("  [Mock mode - no actual processing]")
            self.sent_messages.append(message)
            return

        # Route to appropriate handler
        msg_type = message['message type']
        if msg_type == 12050:  # RIC_INDICATION
            self.xapp._handle_ric_indication(message, None)
        elif msg_type == 12041:  # RIC_CONTROL_ACK
            self.xapp._handle_ric_control_ack(message, None)
        elif msg_type == 12042:  # RIC_CONTROL_FAILURE
            self.xapp._handle_ric_control_failure(message, None)
        else:
            print(f"  Unknown message type: {msg_type}")

        self.sent_messages.append(message)


def test_scenario_1_beam_switch():
    """Test Scenario 1: Weak signal triggers beam switch"""
    print("\n" + "=" * 70)
    print("SCENARIO 1: Weak RSRP Triggers Beam Switch")
    print("=" * 70)

    # UE with weak signal should trigger beam switch
    indication = create_mock_ric_indication(
        ue_id="ue_test_001",
        rsrp=-95.0,  # Weak signal
        serving_beam=42
    )

    return indication


def test_scenario_2_maintain_beam():
    """Test Scenario 2: Strong signal maintains beam"""
    print("\n" + "=" * 70)
    print("SCENARIO 2: Strong RSRP Maintains Current Beam")
    print("=" * 70)

    # UE with strong signal should maintain beam
    indication = create_mock_ric_indication(
        ue_id="ue_test_002",
        rsrp=-70.0,  # Strong signal
        serving_beam=84
    )

    return indication


def test_scenario_3_control_ack():
    """Test Scenario 3: Control ACK handling"""
    print("\n" + "=" * 70)
    print("SCENARIO 3: RIC Control ACK")
    print("=" * 70)

    ack = create_mock_ric_control_ack(
        request_id="req_12345",
        ue_id="ue_test_001"
    )

    return ack


def test_scenario_4_control_failure():
    """Test Scenario 4: Control Failure handling"""
    print("\n" + "=" * 70)
    print("SCENARIO 4: RIC Control Failure")
    print("=" * 70)

    failure = create_mock_ric_control_failure(
        request_id="req_12346",
        ue_id="ue_test_003",
        cause="RAN_NOT_CONNECTED"
    )

    return failure


def test_scenario_5_multiple_ues():
    """Test Scenario 5: Multiple UEs with different signal conditions"""
    print("\n" + "=" * 70)
    print("SCENARIO 5: Multiple UEs")
    print("=" * 70)

    indications = []

    # UE 1: Weak signal
    indications.append(create_mock_ric_indication("ue_multi_001", -92.0, 10))

    # UE 2: Medium signal
    indications.append(create_mock_ric_indication("ue_multi_002", -80.0, 20))

    # UE 3: Strong signal
    indications.append(create_mock_ric_indication("ue_multi_003", -65.0, 30))

    return indications


def run_all_tests(config_path: str, use_fake_sdl: bool):
    """Run all test scenarios"""
    print("\n" + "=" * 70)
    print("UAV BEAM XAPP - LOCAL RMR TESTING")
    print("=" * 70)
    print(f"Config: {config_path}")
    print(f"Fake SDL: {use_fake_sdl}")

    mock_xapp = MockRMRXapp(config_path, use_fake_sdl)

    # Run test scenarios
    scenarios = [
        (test_scenario_1_beam_switch, True),
        (test_scenario_2_maintain_beam, True),
        (test_scenario_3_control_ack, True),
        (test_scenario_4_control_failure, True),
        (test_scenario_5_multiple_ues, False),  # Returns list
    ]

    for scenario_func, single_msg in scenarios:
        message_or_messages = scenario_func()

        if single_msg:
            mock_xapp.send_mock_message(message_or_messages)
        else:
            for i, msg in enumerate(message_or_messages, 1):
                print(f"\n  UE {i}:")
                mock_xapp.send_mock_message(msg)

        time.sleep(0.5)  # Small delay between scenarios

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total messages sent: {len(mock_xapp.sent_messages)}")
    print(f"Message types: {set(m['message type'] for m in mock_xapp.sent_messages)}")
    print("\nAll scenarios completed!")


def main():
    parser = argparse.ArgumentParser(
        description="Local RMR testing for UAV Beam xApp"
    )
    parser.add_argument(
        "--config",
        default="config/config-file.json",
        help="Path to xApp configuration file"
    )
    parser.add_argument(
        "--fake-sdl",
        action="store_true",
        default=True,
        help="Use fake SDL implementation (default: True)"
    )
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Run specific scenario only (1-5)"
    )

    args = parser.parse_args()

    if args.scenario:
        # Run specific scenario
        scenarios = {
            1: test_scenario_1_beam_switch,
            2: test_scenario_2_maintain_beam,
            3: test_scenario_3_control_ack,
            4: test_scenario_4_control_failure,
            5: test_scenario_5_multiple_ues,
        }
        mock_xapp = MockRMRXapp(args.config, args.fake_sdl)
        result = scenarios[args.scenario]()

        if isinstance(result, list):
            for msg in result:
                mock_xapp.send_mock_message(msg)
        else:
            mock_xapp.send_mock_message(result)
    else:
        # Run all tests
        run_all_tests(args.config, args.fake_sdl)


if __name__ == "__main__":
    main()
