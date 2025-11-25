#!/usr/bin/env python3
"""
E2 Integration example for UAV Beam Tracking xApp.

This example demonstrates:
1. Simulating UAV movement through multiple cells
2. Handling beam management procedures (P1, P2, P3)
3. Processing neighbor cell measurements
4. Tracking beam decisions over time
"""

import requests
import time
import math
from typing import List, Dict, Any


class UAVTrajectorySimulator:
    """Simulate UAV movement and generate realistic RSRP measurements."""

    def __init__(self, initial_x: float = 100.0, initial_y: float = 100.0):
        self.x = initial_x
        self.y = initial_y
        self.velocity = 15.0  # m/s
        self.time_step = 0.05  # 50ms intervals

        # Cell tower positions (eNB locations)
        self.cells = [
            {"cell_id": 1, "x": 100, "y": 100},
            {"cell_id": 2, "x": 500, "y": 500},
            {"cell_id": 3, "x": 900, "y": 900},
        ]

    def update_position(self):
        """Update UAV position based on velocity."""
        # Move diagonally from (100,100) to (900,900)
        dx = 800 * math.cos(math.radians(45))
        dy = 800 * math.sin(math.radians(45))

        self.x += dx * self.velocity * self.time_step / 800
        self.y += dy * self.velocity * self.time_step / 800

    def calculate_rsrp(self, cell_id: int) -> float:
        """
        Calculate RSRP based on distance to cell.

        RSRP model: RSRP = P_tx - PL(d) + shadowing
        where PL(d) = 128.1 + 37.6*log10(d_km)
        """
        cell = next(c for c in self.cells if c["cell_id"] == cell_id)
        distance = math.sqrt((self.x - cell["x"])**2 + (self.y - cell["y"])**2)

        # Prevent log(0)
        distance_km = max(distance / 1000, 0.001)

        # Path loss model (Urban Macro from 3GPP TR 38.901)
        pl_db = 128.1 + 37.6 * math.log10(distance_km)

        # Transmit power (typical eNB)
        p_tx = 46.0  # dBm

        # RSRP with some random shadowing
        import random
        shadowing = random.gauss(0, 4)  # 4dB standard deviation

        rsrp = p_tx - pl_db + shadowing
        return round(rsrp, 1)

    def get_measurements(self) -> Dict[str, Any]:
        """Get current measurements for all cells."""
        measurements = {}
        for cell in self.cells:
            measurements[cell["cell_id"]] = self.calculate_rsrp(cell["cell_id"])
        return measurements


def send_e2_indication_with_neighbors(
    ue_id: str,
    serving_cell_id: int,
    rsrp: float,
    neighbor_measurements: Dict[int, float],
    base_url: str = "http://localhost:5001"
) -> Dict[str, Any]:
    """Send E2 indication with neighbor cell measurements."""
    payload = {
        "ue_id": ue_id,
        "rsrp": rsrp,
        "serving_cell_id": serving_cell_id,
        "neighbor_cells": [
            {"cell_id": cell_id, "rsrp": cell_rsrp}
            for cell_id, cell_rsrp in neighbor_measurements.items()
            if cell_id != serving_cell_id
        ],
        "timestamp": int(time.time() * 1000)
    }

    try:
        response = requests.post(
            f"{base_url}/e2/indication",
            json=payload,
            timeout=5
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ E2 indication failed: {response.status_code}")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {}


def run_uav_simulation(duration_seconds: int = 10, base_url: str = "http://localhost:5001"):
    """
    Run UAV trajectory simulation.

    Args:
        duration_seconds: How long to run the simulation
        base_url: Base URL of the xApp server
    """
    print("=" * 60)
    print("UAV E2 Integration Simulation")
    print("=" * 60)

    simulator = UAVTrajectorySimulator()
    ue_id = "UAV-SIM-001"
    current_serving_cell = 1

    decisions_log: List[Dict[str, Any]] = []

    start_time = time.time()
    iteration = 0

    while time.time() - start_time < duration_seconds:
        iteration += 1

        # Update UAV position
        simulator.update_position()

        # Get RSRP measurements for all cells
        measurements = simulator.get_measurements()

        # Determine serving cell (highest RSRP)
        serving_cell = max(measurements, key=measurements.get)
        serving_rsrp = measurements[serving_cell]

        # Check if handover occurred
        if serving_cell != current_serving_cell:
            print(f"\n🔄 HANDOVER: Cell {current_serving_cell} → Cell {serving_cell}")
            current_serving_cell = serving_cell

        # Send E2 indication
        decision = send_e2_indication_with_neighbors(
            ue_id=ue_id,
            serving_cell_id=current_serving_cell,
            rsrp=serving_rsrp,
            neighbor_measurements=measurements
        )

        if decision:
            decisions_log.append({
                "iteration": iteration,
                "position": (round(simulator.x, 1), round(simulator.y, 1)),
                "serving_cell": current_serving_cell,
                "rsrp": serving_rsrp,
                "action": decision.get("action"),
                "procedure": decision.get("procedure"),
                "beam_id": decision.get("beam_id")
            })

            # Print summary every 5 iterations
            if iteration % 5 == 0:
                print(f"\n📍 Iteration {iteration}:")
                print(f"   Position: ({simulator.x:.1f}, {simulator.y:.1f})")
                print(f"   Serving Cell: {current_serving_cell}, RSRP: {serving_rsrp:.1f} dBm")
                print(f"   Decision: {decision.get('action')} (Beam {decision.get('beam_id')})")

        # Wait for next measurement interval (50ms)
        time.sleep(simulator.time_step)

    # Print summary
    print("\n" + "=" * 60)
    print("Simulation Summary")
    print("=" * 60)
    print(f"Total iterations: {len(decisions_log)}")
    print(f"Beam switches: {sum(1 for i in range(1, len(decisions_log)) if decisions_log[i]['beam_id'] != decisions_log[i-1]['beam_id'])}")
    print(f"Handovers: {sum(1 for i in range(1, len(decisions_log)) if decisions_log[i]['serving_cell'] != decisions_log[i-1]['serving_cell'])}")

    # Count procedure types
    from collections import Counter
    procedures = Counter(d['procedure'] for d in decisions_log if d.get('procedure'))
    print(f"\nProcedure usage:")
    for proc, count in procedures.items():
        print(f"   {proc}: {count}")

    print("=" * 60)


def main():
    """Run E2 integration example."""
    base_url = "http://localhost:5001"

    # Check health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("⚠️  xApp is not running. Start it with:")
            print("   docker-compose up -d")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to xApp. Make sure it's running.")
        return

    # Run simulation
    run_uav_simulation(duration_seconds=10, base_url=base_url)


if __name__ == "__main__":
    main()
