#!/usr/bin/env python3
"""
Basic usage example for UAV Beam Tracking xApp.

This example demonstrates:
1. Starting the xApp server
2. Checking health status
3. Sending a simple E2 indication
4. Retrieving statistics
"""

import requests
import time
from typing import Dict, Any


def check_health(base_url: str = "http://localhost:5001") -> bool:
    """Check if xApp server is healthy."""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ xApp is healthy: {data}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to xApp: {e}")
        return False


def send_e2_indication(
    ue_id: str,
    rsrp: float,
    serving_cell_id: int,
    base_url: str = "http://localhost:5001"
) -> Dict[str, Any]:
    """
    Send an E2 indication to the xApp.

    Args:
        ue_id: Unique identifier for the UE (e.g., "UAV-001")
        rsrp: Reference Signal Received Power in dBm (e.g., -95.0)
        serving_cell_id: ID of the serving cell (e.g., 1)
        base_url: Base URL of the xApp server

    Returns:
        Dictionary containing beam decision
    """
    payload = {
        "ue_id": ue_id,
        "rsrp": rsrp,
        "serving_cell_id": serving_cell_id,
        "timestamp": int(time.time() * 1000)  # Current time in milliseconds
    }

    try:
        response = requests.post(
            f"{base_url}/e2/indication",
            json=payload,
            timeout=5
        )

        if response.status_code == 200:
            decision = response.json()
            print(f"\n📡 E2 Indication sent successfully!")
            print(f"   UE: {ue_id}")
            print(f"   RSRP: {rsrp} dBm")
            print(f"   Decision: {decision}")
            return decision
        else:
            print(f"❌ E2 indication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {}


def get_statistics(base_url: str = "http://localhost:5001") -> Dict[str, Any]:
    """Retrieve runtime statistics from the xApp."""
    try:
        response = requests.get(f"{base_url}/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"\n📊 Runtime Statistics:")
            print(f"   Total indications: {stats.get('total_indications', 0)}")
            print(f"   Active UEs: {stats.get('active_ues', 0)}")
            print(f"   Beam switches: {stats.get('beam_switches', 0)}")
            return stats
        else:
            print(f"❌ Failed to get statistics: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {}


def main():
    """Run basic usage example."""
    print("=" * 60)
    print("UAV Beam Tracking xApp - Basic Usage Example")
    print("=" * 60)

    base_url = "http://localhost:5001"

    # Step 1: Check health
    print("\n1️⃣  Checking xApp health...")
    if not check_health(base_url):
        print("\n⚠️  Make sure xApp is running:")
        print("   docker-compose up -d")
        print("   or: python -m uav_beam.main")
        return

    # Step 2: Send E2 indications
    print("\n2️⃣  Sending E2 indications...")

    # Good signal - should maintain beam
    send_e2_indication(
        ue_id="UAV-001",
        rsrp=-85.0,  # Strong signal
        serving_cell_id=1
    )

    time.sleep(1)

    # Weaker signal - might trigger beam adjustment
    send_e2_indication(
        ue_id="UAV-001",
        rsrp=-100.0,  # Weaker signal
        serving_cell_id=1
    )

    time.sleep(1)

    # Very weak signal - might trigger beam failure recovery
    send_e2_indication(
        ue_id="UAV-001",
        rsrp=-115.0,  # Very weak signal
        serving_cell_id=1
    )

    # Step 3: Get statistics
    print("\n3️⃣  Retrieving statistics...")
    get_statistics(base_url)

    print("\n" + "=" * 60)
    print("✅ Basic usage example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
