"""
Unit tests for RMR client implementation.

Tests RMR message handling, E2AP interaction, and SDL integration.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Mock RMR imports since they may not be available in test environment
try:
    from ricxappframe.xapp_frame import RMRXapp
    RMR_AVAILABLE = True
except ImportError:
    RMR_AVAILABLE = False
    RMRXapp = object

from uav_beam.beam_tracker import BeamTracker, BeamMeasurement, BeamDecision
from uav_beam.trajectory_predictor import TrajectoryPredictor
from uav_beam.angle_estimator import AngleEstimator


@pytest.mark.skipif(not RMR_AVAILABLE, reason="RMR framework not available")
class TestRMRMessageTypes:
    """Test RMR message type definitions"""

    def test_message_type_values(self):
        """Verify E2AP message type constants"""
        from uav_beam.rmr_client import RMRMessageTypes

        assert RMRMessageTypes.RIC_INDICATION == 12050
        assert RMRMessageTypes.RIC_CONTROL_REQ == 12040
        assert RMRMessageTypes.RIC_CONTROL_ACK == 12041
        assert RMRMessageTypes.RIC_CONTROL_FAILURE == 12042
        assert RMRMessageTypes.RIC_SUB_REQ == 12010
        assert RMRMessageTypes.RIC_SUB_RESP == 12011
        assert RMRMessageTypes.RIC_SUB_DELETE_REQ == 12020
        assert RMRMessageTypes.RIC_SUB_DELETE_RESP == 12021


@pytest.mark.skipif(not RMR_AVAILABLE, reason="RMR framework not available")
class TestUAVBeamRMRXapp:
    """Test UAV Beam RMR xApp implementation"""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create mock configuration file"""
        config = {
            "xapp_name": "uav-beam-xapp",
            "version": "0.1.0",
            "controls": {
                "logger_level": "DEBUG",
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
            },
            "rmr": {
                "protPort": "tcp:4560",
                "maxSize": 65536,
                "numWorkers": 1
            }
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        return str(config_file)

    @pytest.fixture
    def xapp_instance(self, mock_config):
        """Create UAVBeamRMRXapp instance with mocked dependencies"""
        from uav_beam.rmr_client import UAVBeamRMRXapp

        with patch('uav_beam.rmr_client.RMRXapp.__init__', return_value=None):
            with patch('uav_beam.rmr_client.mdclogpy.Logger'):
                xapp = UAVBeamRMRXapp(use_fake_sdl=True)
                xapp.logger = Mock()
                xapp.sdl = Mock()

                # Mock beam processing components
                xapp.beam_tracker = Mock(spec=BeamTracker)
                xapp.trajectory_predictor = Mock(spec=TrajectoryPredictor)
                xapp.angle_estimator = Mock(spec=AngleEstimator)

                return xapp

    def test_initialization(self, xapp_instance):
        """Test xApp initialization"""
        assert xapp_instance is not None
        assert hasattr(xapp_instance, 'beam_tracker')
        assert hasattr(xapp_instance, 'trajectory_predictor')
        assert hasattr(xapp_instance, 'angle_estimator')

    def test_handle_ric_indication_switch_beam(self, xapp_instance):
        """Test handling RIC Indication with beam switch decision"""
        from uav_beam.rmr_client import RMRMessageTypes

        # Mock RIC Indication message
        summary = {
            "message type": RMRMessageTypes.RIC_INDICATION,
            "payload": json.dumps({
                "ue_id": "ue_001",
                "rsrp": -85.5,
                "serving_beam": 42,
                "timestamp": 1234567890,
                "position": {"x": 100.0, "y": 200.0, "z": 50.0}
            })
        }

        # Mock beam decision
        mock_decision = BeamDecision(
            action="switch",
            new_beam=84,
            confidence=0.95,
            expected_gain_db=5.2
        )
        xapp_instance.beam_tracker.process_measurement.return_value = mock_decision

        # Mock RMR send
        xapp_instance.rmr_send = Mock()

        # Execute handler
        xapp_instance._handle_ric_indication(summary, None)

        # Verify RIC Control was sent
        assert xapp_instance.rmr_send.called
        call_args = xapp_instance.rmr_send.call_args
        assert call_args[0][1] == RMRMessageTypes.RIC_CONTROL_REQ

    def test_handle_ric_indication_maintain_beam(self, xapp_instance):
        """Test handling RIC Indication with maintain decision"""
        from uav_beam.rmr_client import RMRMessageTypes

        summary = {
            "message type": RMRMessageTypes.RIC_INDICATION,
            "payload": json.dumps({
                "ue_id": "ue_001",
                "rsrp": -75.0,
                "serving_beam": 42,
                "timestamp": 1234567890,
                "position": {"x": 100.0, "y": 200.0, "z": 50.0}
            })
        }

        # Mock maintain decision
        mock_decision = BeamDecision(
            action="maintain",
            new_beam=42,
            confidence=0.98,
            expected_gain_db=0.0
        )
        xapp_instance.beam_tracker.process_measurement.return_value = mock_decision

        xapp_instance.rmr_send = Mock()

        # Execute handler
        xapp_instance._handle_ric_indication(summary, None)

        # Verify NO RIC Control was sent for maintain action
        assert not xapp_instance.rmr_send.called

    def test_handle_ric_control_ack(self, xapp_instance):
        """Test handling RIC Control ACK"""
        from uav_beam.rmr_client import RMRMessageTypes

        summary = {
            "message type": RMRMessageTypes.RIC_CONTROL_ACK,
            "payload": json.dumps({
                "request_id": "req_123",
                "ue_id": "ue_001",
                "status": "success"
            })
        }

        xapp_instance._handle_ric_control_ack(summary, None)

        # Verify logging occurred
        assert xapp_instance.logger.info.called

    def test_handle_ric_control_failure(self, xapp_instance):
        """Test handling RIC Control Failure"""
        from uav_beam.rmr_client import RMRMessageTypes

        summary = {
            "message type": RMRMessageTypes.RIC_CONTROL_FAILURE,
            "payload": json.dumps({
                "request_id": "req_123",
                "ue_id": "ue_001",
                "cause": "RAN_NOT_CONNECTED",
                "status": "failure"
            })
        }

        xapp_instance._handle_ric_control_failure(summary, None)

        # Verify error logging occurred
        assert xapp_instance.logger.error.called

    def test_send_ric_control(self, xapp_instance):
        """Test sending RIC Control message"""
        decision = BeamDecision(
            action="switch",
            new_beam=84,
            confidence=0.95,
            expected_gain_db=5.2
        )

        summary = {
            "payload": json.dumps({
                "ue_id": "ue_001",
                "timestamp": 1234567890
            })
        }

        xapp_instance.rmr_send = Mock()
        xapp_instance._send_ric_control(decision, summary)

        # Verify message was sent
        assert xapp_instance.rmr_send.called

        # Verify payload structure
        call_args = xapp_instance.rmr_send.call_args[0]
        payload = json.loads(call_args[0])

        assert payload["ue_id"] == "ue_001"
        assert payload["control_action"] == "switch_beam"
        assert payload["target_beam"] == 84
        assert "request_id" in payload

    def test_sdl_storage(self, xapp_instance):
        """Test SDL state storage"""
        ue_id = "ue_001"
        decision = BeamDecision(
            action="switch",
            new_beam=84,
            confidence=0.95,
            expected_gain_db=5.2
        )

        xapp_instance._store_ue_state_sdl(ue_id, decision)

        # Verify SDL set was called
        assert xapp_instance.sdl.set.called

        # Verify key format
        call_args = xapp_instance.sdl.set.call_args[0]
        assert ue_id in str(call_args[0])

    def test_sdl_retrieval(self, xapp_instance):
        """Test SDL state retrieval"""
        ue_id = "ue_001"

        # Mock SDL response
        mock_state = {
            "action": "switch",
            "new_beam": 84,
            "confidence": 0.95,
            "timestamp": 1234567890
        }
        xapp_instance.sdl.get.return_value = {
            f"uav-beam:ue:{ue_id}": json.dumps(mock_state).encode()
        }

        state = xapp_instance._get_ue_state_sdl(ue_id)

        # Verify retrieval
        assert state is not None
        assert state["action"] == "switch"
        assert state["new_beam"] == 84


@pytest.mark.skipif(not RMR_AVAILABLE, reason="RMR framework not available")
class TestRMRMessageValidation:
    """Test RMR message validation and error handling"""

    def test_invalid_json_payload(self, xapp_instance):
        """Test handling of invalid JSON in RIC Indication"""
        summary = {
            "message type": 12050,
            "payload": "INVALID_JSON{"
        }

        # Should not raise exception, but log error
        xapp_instance._handle_ric_indication(summary, None)
        assert xapp_instance.logger.error.called

    def test_missing_required_fields(self, xapp_instance):
        """Test handling of missing required fields"""
        summary = {
            "message type": 12050,
            "payload": json.dumps({
                "ue_id": "ue_001"
                # Missing rsrp, serving_beam, etc.
            })
        }

        xapp_instance._handle_ric_indication(summary, None)
        assert xapp_instance.logger.error.called


@pytest.mark.skipif(not RMR_AVAILABLE, reason="RMR framework not available")
def test_e2e_message_flow(xapp_instance):
    """Test end-to-end message flow from indication to control"""
    from uav_beam.rmr_client import RMRMessageTypes

    # Simulate RIC Indication
    indication = {
        "message type": RMRMessageTypes.RIC_INDICATION,
        "payload": json.dumps({
            "ue_id": "ue_001",
            "rsrp": -85.5,
            "serving_beam": 42,
            "timestamp": 1234567890,
            "position": {"x": 100.0, "y": 200.0, "z": 50.0}
        })
    }

    # Mock beam switch decision
    mock_decision = BeamDecision(
        action="switch",
        new_beam=84,
        confidence=0.95,
        expected_gain_db=5.2
    )
    xapp_instance.beam_tracker.process_measurement.return_value = mock_decision
    xapp_instance.rmr_send = Mock()

    # Process indication
    xapp_instance._handle_ric_indication(indication, None)

    # Verify control message sent
    assert xapp_instance.rmr_send.called

    # Simulate control ACK
    ack = {
        "message type": RMRMessageTypes.RIC_CONTROL_ACK,
        "payload": json.dumps({
            "request_id": "req_123",
            "ue_id": "ue_001",
            "status": "success"
        })
    }

    xapp_instance._handle_ric_control_ack(ack, None)

    # Verify SDL was updated
    assert xapp_instance.sdl.set.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
