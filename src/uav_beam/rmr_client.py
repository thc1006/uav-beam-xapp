"""
RMR (RIC Message Router) Client for UAV Beam xApp

Provides O-RAN SC compliant RMR messaging integration.
"""

import logging
from typing import Dict, Callable, Optional, Any
import json
from ricxappframe.xapp_frame import RMRXapp, Xapp
from ricxappframe.xapp_sdl import SDLWrapper
from mdclogpy import Logger

logger = logging.getLogger(__name__)


# RMR Message Types for UAV Beam xApp
# Based on O-RAN WG3 E2AP specifications
class RMRMessageTypes:
    """RMR message type definitions"""
    # E2AP Indication (from E2 Node to xApp)
    RIC_INDICATION = 12050

    # E2AP Control (from xApp to E2 Node)
    RIC_CONTROL_REQ = 12040
    RIC_CONTROL_ACK = 12041
    RIC_CONTROL_FAILURE = 12042

    # E2 Subscription Management
    RIC_SUB_REQ = 12010
    RIC_SUB_RESP = 12011
    RIC_SUB_FAILURE = 12012
    RIC_SUB_DEL_REQ = 12020
    RIC_SUB_DEL_RESP = 12021

    # Health Check
    RIC_HEALTH_CHECK_REQ = 100
    RIC_HEALTH_CHECK_RESP = 101


class UAVBeamRMRXapp(RMRXapp):
    """
    UAV Beam Tracking xApp with RMR support

    Extends O-RAN SC RMRXapp for standard RIC integration.
    """

    def __init__(self,
                 config_path: str = "/opt/ric/config/config-file.json",
                 use_fake_sdl: bool = False):
        """
        Initialize RMR-enabled xApp

        Args:
            config_path: Path to xApp config-file.json
            use_fake_sdl: Use fake SDL for testing (no Redis required)
        """
        # Load config
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Initialize parent RMRXapp
        super().__init__(
            default_handler=self._default_handler,
            config_path=config_path,
            use_fake_sdl=use_fake_sdl
        )

        # SDL (Shared Data Layer) wrapper
        self.sdl = SDLWrapper(use_fake_sdl=use_fake_sdl)

        # Setup MDC logging
        self.mdc_logger = Logger(name="uav-beam-xapp")
        self.mdc_logger.mdclog_format_init(configmap_monitor=True)

        # Beam tracker components (imported lazily to avoid circular deps)
        self.beam_tracker = None
        self.trajectory_predictor = None
        self.angle_estimator = None

        # Statistics
        self.stats = {
            "indications_received": 0,
            "controls_sent": 0,
            "subscriptions_active": 0,
        }

        logger.info("UAV Beam RMR xApp initialized")

    def initialize_components(self):
        """Initialize beam tracking components"""
        from .beam_tracker import BeamTracker, BeamConfig
        from .trajectory_predictor import TrajectoryPredictor, PredictorConfig
        from .angle_estimator import AngleEstimator, AngleEstimatorConfig

        # Load config
        beam_cfg = self.config.get("beam", {})
        predictor_cfg = self.config.get("predictor", {})
        estimator_cfg = self.config.get("estimator", {})

        self.beam_tracker = BeamTracker(BeamConfig(**beam_cfg))
        self.trajectory_predictor = TrajectoryPredictor(PredictorConfig(**predictor_cfg))
        self.angle_estimator = AngleEstimator(AngleEstimatorConfig(**estimator_cfg))

        logger.info("Beam tracking components initialized")

    def start(self, thread: bool = False):
        """
        Start the xApp and register RMR handlers

        Args:
            thread: Run in separate thread (False = blocking)
        """
        # Initialize components
        self.initialize_components()

        # Register RMR message handlers
        self.register_handlers()

        # Start xApp framework
        logger.info("Starting UAV Beam xApp with RMR...")
        super().start(thread=thread)

    def register_handlers(self):
        """Register RMR message type handlers"""
        # E2 Indication handler
        self.register_callback(
            RMRMessageTypes.RIC_INDICATION,
            self._handle_ric_indication
        )

        # E2 Subscription response handler
        self.register_callback(
            RMRMessageTypes.RIC_SUB_RESP,
            self._handle_subscription_response
        )

        # E2 Control ACK handler
        self.register_callback(
            RMRMessageTypes.RIC_CONTROL_ACK,
            self._handle_control_ack
        )

        # E2 Control Failure handler
        self.register_callback(
            RMRMessageTypes.RIC_CONTROL_FAILURE,
            self._handle_control_failure
        )

        # Health check handler
        self.register_callback(
            RMRMessageTypes.RIC_HEALTH_CHECK_REQ,
            self._handle_health_check
        )

        logger.info("RMR message handlers registered")

    def _default_handler(self, summary: Dict, sbuf: Any):
        """Default handler for unhandled RMR messages"""
        self.mdc_logger.warning(f"Unhandled RMR message type: {summary.get('message type')}")
        self.rmr_free(sbuf)

    def _handle_ric_indication(self, summary: Dict, sbuf: Any):
        """
        Handle E2 RIC Indication message

        Receives beam measurements from E2 Node via RMR.
        """
        try:
            self.stats["indications_received"] += 1

            # Decode E2AP payload
            payload = json.loads(summary["payload"])

            # Extract beam measurement
            ue_id = payload.get("ue_id")
            serving_beam_id = payload.get("serving_beam_id")
            rsrp = payload.get("rsrp_dbm")

            self.mdc_logger.info(f"RIC Indication: UE={ue_id}, Beam={serving_beam_id}, RSRP={rsrp}")

            # Process through beam tracker
            from .beam_tracker import BeamMeasurement
            measurement = BeamMeasurement(
                timestamp_ms=payload.get("timestamp_ms"),
                ue_id=ue_id,
                serving_beam_id=serving_beam_id,
                serving_rsrp_dbm=rsrp,
                neighbor_beams=payload.get("neighbor_beams", {}),
            )

            decision = self.beam_tracker.process_measurement(measurement)

            # Send control if needed
            if decision.action in ("switch", "recover"):
                self._send_ric_control(decision, summary)

            # Store UE state in SDL
            self._store_ue_state_sdl(ue_id, decision)

        except Exception as e:
            self.mdc_logger.error(f"Error handling RIC indication: {e}")
        finally:
            self.rmr_free(sbuf)

    def _send_ric_control(self, decision, indication_summary: Dict):
        """
        Send E2 RIC Control message

        Sends beam control decision to E2 Node via RMR.
        """
        try:
            # Build E2AP Control Request payload
            control_payload = {
                "ue_id": decision.ue_id,
                "target_beam_id": decision.target_beam_id,
                "action": decision.action,
                "confidence": decision.confidence,
                "reason": decision.reason,
            }

            # Send RMR message
            self.rmr_send(
                json.dumps(control_payload).encode(),
                RMRMessageTypes.RIC_CONTROL_REQ,
                retries=3
            )

            self.stats["controls_sent"] += 1
            self.mdc_logger.info(f"RIC Control sent: UE={decision.ue_id}, Beam={decision.target_beam_id}")

        except Exception as e:
            self.mdc_logger.error(f"Error sending RIC control: {e}")

    def _handle_subscription_response(self, summary: Dict, sbuf: Any):
        """Handle E2 Subscription Response"""
        try:
            payload = json.loads(summary["payload"])
            subscription_id = payload.get("subscription_id")

            self.stats["subscriptions_active"] += 1
            self.mdc_logger.info(f"Subscription established: {subscription_id}")

        except Exception as e:
            self.mdc_logger.error(f"Error handling subscription response: {e}")
        finally:
            self.rmr_free(sbuf)

    def _handle_control_ack(self, summary: Dict, sbuf: Any):
        """Handle E2 Control ACK"""
        try:
            self.mdc_logger.info("RIC Control ACK received")
        except Exception as e:
            self.mdc_logger.error(f"Error handling control ACK: {e}")
        finally:
            self.rmr_free(sbuf)

    def _handle_control_failure(self, summary: Dict, sbuf: Any):
        """Handle E2 Control Failure"""
        try:
            payload = json.loads(summary["payload"])
            self.mdc_logger.error(f"RIC Control failed: {payload.get('cause')}")
        except Exception as e:
            self.mdc_logger.error(f"Error handling control failure: {e}")
        finally:
            self.rmr_free(sbuf)

    def _handle_health_check(self, summary: Dict, sbuf: Any):
        """Handle health check request"""
        try:
            # Respond with health status
            response = {
                "status": "healthy",
                "xapp": "uav-beam",
                "version": "0.1.0",
                "stats": self.stats,
            }

            self.rmr_send(
                json.dumps(response).encode(),
                RMRMessageTypes.RIC_HEALTH_CHECK_RESP
            )

        except Exception as e:
            self.mdc_logger.error(f"Error handling health check: {e}")
        finally:
            self.rmr_free(sbuf)

    def _store_ue_state_sdl(self, ue_id: str, decision):
        """Store UE state in SDL (Shared Data Layer)"""
        try:
            key = f"uav-beam:ue:{ue_id}"
            value = {
                "ue_id": decision.ue_id,
                "current_beam": decision.current_beam_id,
                "target_beam": decision.target_beam_id,
                "action": decision.action,
                "confidence": decision.confidence,
                "timestamp_ms": decision.timestamp_ms,
            }

            self.sdl.set(key, json.dumps(value))

        except Exception as e:
            self.mdc_logger.error(f"Error storing UE state in SDL: {e}")

    def get_ue_state_from_sdl(self, ue_id: str) -> Optional[Dict]:
        """Retrieve UE state from SDL"""
        try:
            key = f"uav-beam:ue:{ue_id}"
            value = self.sdl.get(key)

            if value:
                return json.loads(value)
            return None

        except Exception as e:
            self.mdc_logger.error(f"Error retrieving UE state from SDL: {e}")
            return None


def create_rmr_xapp(config_path: str = "/opt/ric/config/config-file.json",
                    use_fake_sdl: bool = False) -> UAVBeamRMRXapp:
    """
    Factory function to create RMR-enabled xApp

    Args:
        config_path: Path to xApp descriptor
        use_fake_sdl: Use fake SDL for testing

    Returns:
        Configured UAVBeamRMRXapp instance
    """
    return UAVBeamRMRXapp(config_path=config_path, use_fake_sdl=use_fake_sdl)


def main():
    """Main entry point for RMR-enabled xApp"""
    import argparse

    parser = argparse.ArgumentParser(description="UAV Beam xApp with RMR")
    parser.add_argument("--config", default="/opt/ric/config/config-file.json",
                        help="Path to config-file.json")
    parser.add_argument("--fake-sdl", action="store_true",
                        help="Use fake SDL (no Redis)")

    args = parser.parse_args()

    # Create and start xApp
    xapp = create_rmr_xapp(config_path=args.config, use_fake_sdl=args.fake_sdl)
    xapp.start(thread=False)  # Blocking mode


if __name__ == "__main__":
    main()
