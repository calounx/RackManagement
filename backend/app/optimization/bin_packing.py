"""
First-Fit Decreasing (FFD) bin packing algorithm for rack optimization.

This algorithm maximizes rack height utilization by:
1. Sorting devices by height (tallest first)
2. Placing each device in the first available position (bottom-up)
3. Ensuring no overlaps and all constraints satisfied

FFD is a simple but effective greedy algorithm for bin packing problems.
"""

from typing import List, Tuple
from .base import BaseOptimizer, PlacementSolution, BaseObjective
from .constraints import ConstraintValidator
from ..models import Rack, Device


class FirstFitDecreasingOptimizer(BaseOptimizer):
    """
    First-Fit Decreasing (FFD) bin packing algorithm.
    Sorts devices by height (descending) and places in first available position.
    Simple but effective for height utilization.
    """

    def optimize(self) -> PlacementSolution:
        """
        Execute FFD algorithm.

        Steps:
        1. Sort devices by height (tallest first)
        2. For each device, find first available position from bottom
        3. Validate constraints
        4. Return solution

        Returns:
            PlacementSolution with device positions and initial score
        """
        # Sort devices by height (descending), then by weight for tie-breaking
        sorted_devices = sorted(
            self.devices,
            key=lambda d: (
                -(d.specification.height_u if d.specification else 1),  # Tallest first
                -(d.specification.weight_kg or 0) if d.specification else 0  # Heaviest first for ties
            )
        )

        # Track occupied units
        occupied = set()
        positions = []

        for device in sorted_devices:
            if not device.specification:
                # Skip devices without specifications
                continue

            height = int(device.specification.height_u)
            placed = False

            # Try to place from bottom to top (U1 upward)
            for start_u in range(1, self.rack.total_height_u - height + 2):
                # Check if all required units are available
                units_needed = set(range(start_u, start_u + height))

                if not units_needed.intersection(occupied):
                    # Place device here
                    positions.append((device.id, start_u))
                    occupied.update(units_needed)
                    placed = True
                    break

            if not placed:
                # Could not place device (rack full or insufficient contiguous space)
                # This is not a violation yet - just means device doesn't fit
                pass

        # Validate constraints
        violations = ConstraintValidator.validate_placement(
            self.rack,
            self.devices,
            positions,
            self.locked_device_ids
        )

        # Calculate simple utilization score (will be replaced by scoring engine)
        total_height_used = sum(
            next((d.specification.height_u for d in self.devices if d.id == dev_id), 0)
            for dev_id, _ in positions
        )
        utilization_score = min(total_height_used / self.rack.total_height_u, 1.0)

        return PlacementSolution(
            positions=positions,
            score=utilization_score,
            breakdown=None,  # Will be calculated by coordinator with scoring engine
            violations=violations
        )

    def get_algorithm_name(self) -> str:
        """Return algorithm name."""
        return "First-Fit Decreasing (FFD)"


class HeightUtilizationObjective(BaseObjective):
    """
    Objective: Maximize rack height utilization.

    Score = (total height used) / (total rack height)
    Higher is better. Encourages compact packing.
    """

    def calculate_score(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> float:
        """
        Calculate height utilization score.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            Score between 0.0 (empty rack) and 1.0 (fully utilized)
        """
        device_map = {d.id: d for d in devices}

        # Calculate total height used
        total_height_used = 0.0
        for dev_id, _ in positions:
            device = device_map.get(dev_id)
            if device and device.specification:
                total_height_used += device.specification.height_u

        # Calculate utilization ratio
        utilization = total_height_used / rack.total_height_u

        # Cap at 1.0 (shouldn't exceed, but safety check)
        return min(utilization, 1.0)

    def get_objective_name(self) -> str:
        """Return objective name."""
        return "height_utilization"


class CompactnessObjective(BaseObjective):
    """
    Objective: Minimize gaps between devices.

    Encourages devices to be placed close together with minimal empty space.
    Calculated as the ratio of used units to the range of positions.
    """

    def calculate_score(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> float:
        """
        Calculate compactness score.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            Score between 0.0 (very spread out) and 1.0 (very compact)
        """
        if not positions:
            return 1.0  # Empty rack is perfectly compact

        device_map = {d.id: d for d in devices}

        # Find min and max positions
        min_u = min(start_u for _, start_u in positions)
        max_u_end = max(
            start_u + (device_map[dev_id].specification.height_u if device_map[dev_id].specification else 1)
            for dev_id, start_u in positions
        )

        # Calculate range
        range_used = max_u_end - min_u

        if range_used == 0:
            return 1.0

        # Calculate actual height occupied
        total_height = sum(
            device_map[dev_id].specification.height_u
            for dev_id, _ in positions
            if dev_id in device_map and device_map[dev_id].specification
        )

        # Compactness = actual height / range
        compactness = total_height / range_used

        return min(compactness, 1.0)

    def get_objective_name(self) -> str:
        """Return objective name."""
        return "compactness"
