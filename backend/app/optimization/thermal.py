"""
Thermal zone balancing optimization.

Optimizes device placement for thermal efficiency by:
1. Balancing heat across zones (avoid top-heavy configurations)
2. Placing high-heat devices in bottom zone (coolest air)
3. Minimizing hot spots
4. Maintaining cooling headroom
5. Avoiding airflow conflicts

Integrates with existing thermal analysis module (app.thermal).
"""

from typing import List, Tuple, Dict
from .base import BaseOptimizer, PlacementSolution, BaseObjective
from .constraints import ConstraintValidator
from ..models import Rack, Device, ThermalZone
from ..thermal import get_thermal_zone


class ThermalObjective(BaseObjective):
    """
    Objective: Optimize thermal distribution.

    Goals:
    1. Balance heat across zones (avoid top-heavy)
    2. Minimize hot spots (spread high-heat devices)
    3. Cooling headroom (stay below capacity)
    4. Bottom-heavy preference (cool air at bottom)

    Score components:
    - Zone balance (30%)
    - Hot spot distribution (30%)
    - Cooling headroom (20%)
    - Bottom-heavy bonus (20%)
    """

    def calculate_score(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> float:
        """
        Calculate thermal management score.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            Score between 0.0 (poor thermal distribution) and 1.0 (excellent)
        """
        if not positions:
            return 1.0  # Empty rack has perfect thermal distribution

        device_map = {d.id: d for d in devices}

        # 1. Calculate zone heat distribution (30%)
        zone_heat = {
            ThermalZone.BOTTOM.value: 0.0,
            ThermalZone.MIDDLE.value: 0.0,
            ThermalZone.TOP.value: 0.0
        }

        total_heat = 0.0

        for dev_id, start_u in positions:
            device = device_map.get(dev_id)
            if not device or not device.specification:
                continue

            # Calculate heat (BTU/hr)
            heat_btu = device.specification.heat_output_btu or 0.0
            if heat_btu == 0.0 and device.specification.power_watts:
                heat_btu = device.specification.power_watts * 3.412  # 1W = 3.412 BTU/hr

            total_heat += heat_btu

            # Assign to zone (use midpoint of device)
            device_height = device.specification.height_u
            midpoint_u = start_u + (device_height / 2)
            zone = get_thermal_zone(int(midpoint_u), rack.total_height_u)
            zone_heat[zone.value] += heat_btu

        # Calculate zone balance score
        zone_heats = list(zone_heat.values())
        if max(zone_heats) > 0:
            # Balance ratio: min/max (higher is better)
            zone_balance_ratio = min(zone_heats) / max(zone_heats)
        else:
            zone_balance_ratio = 1.0

        zone_balance_score = zone_balance_ratio

        # 2. Hot spot distribution (30%)
        # Identify high-heat devices (>1500 BTU/hr or >400W)
        high_heat_devices = []
        for dev_id, start_u in positions:
            device = device_map.get(dev_id)
            if not device or not device.specification:
                continue

            heat_btu = device.specification.heat_output_btu or 0.0
            if heat_btu == 0.0 and device.specification.power_watts:
                heat_btu = device.specification.power_watts * 3.412

            if heat_btu > 1500:  # High heat threshold
                high_heat_devices.append((dev_id, start_u, heat_btu))

        # Calculate average distance between high-heat devices
        if len(high_heat_devices) > 1:
            distances = []
            for i in range(len(high_heat_devices)):
                for j in range(i + 1, len(high_heat_devices)):
                    dist = abs(high_heat_devices[j][1] - high_heat_devices[i][1])
                    distances.append(dist)

            avg_distance = sum(distances) / len(distances) if distances else 0

            # Ideal distance is about 1/3 of rack height
            ideal_distance = rack.total_height_u / 3
            if avg_distance >= ideal_distance:
                hotspot_score = 1.0
            else:
                hotspot_score = avg_distance / ideal_distance
        else:
            # 0 or 1 high-heat device = perfect distribution
            hotspot_score = 1.0

        # 3. Cooling headroom (20%)
        if rack.cooling_capacity_btu and rack.cooling_capacity_btu > 0:
            cooling_utilization = total_heat / rack.cooling_capacity_btu
            # Lower utilization is better (more headroom)
            cooling_score = 1.0 - min(cooling_utilization, 1.0)
        else:
            # No cooling capacity defined, assume adequate
            cooling_score = 0.8

        # 4. Bottom-heavy bonus (20%)
        # Calculate center of heat mass
        if total_heat > 0:
            heat_weighted_position = 0.0
            for dev_id, start_u in positions:
                device = device_map.get(dev_id)
                if not device or not device.specification:
                    continue

                heat_btu = device.specification.heat_output_btu or 0.0
                if heat_btu == 0.0 and device.specification.power_watts:
                    heat_btu = device.specification.power_watts * 3.412

                device_height = device.specification.height_u
                midpoint_u = start_u + (device_height / 2)
                heat_weighted_position += (midpoint_u / rack.total_height_u) * heat_btu

            center_of_heat = heat_weighted_position / total_heat

            # Ideal center is in bottom third (< 0.33)
            if center_of_heat <= 0.33:
                bottom_heavy_score = 1.0
            elif center_of_heat <= 0.5:
                # Middle is okay
                bottom_heavy_score = 0.7
            else:
                # Top-heavy is bad
                bottom_heavy_score = 0.3
        else:
            bottom_heavy_score = 1.0

        # Weighted combination
        thermal_score = (
            zone_balance_score * 0.30 +
            hotspot_score * 0.30 +
            cooling_score * 0.20 +
            bottom_heavy_score * 0.20
        )

        return min(thermal_score, 1.0)

    def get_objective_name(self) -> str:
        """Return objective name."""
        return "thermal_management"


class ThermalBalancedOptimizer(BaseOptimizer):
    """
    Optimizer that prioritizes thermal distribution.
    Places high-heat devices in bottom zone, balances zones.

    Strategy:
    1. Categorize devices by heat output (high, medium, low)
    2. Place high-heat devices in bottom zone
    3. Place medium-heat devices in middle zone
    4. Fill remaining spaces with low-heat devices
    5. Sort within each category by height for compactness
    """

    def optimize(self) -> PlacementSolution:
        """
        Execute thermal-first placement algorithm.

        Returns:
            PlacementSolution with thermally optimized device positions
        """
        # Categorize devices by heat output
        high_heat = []  # >1500 BTU/hr (>400W)
        medium_heat = []  # 500-1500 BTU/hr (150-400W)
        low_heat = []  # <500 BTU/hr (<150W)

        for device in self.devices:
            if not device.specification:
                continue

            heat_btu = device.specification.heat_output_btu or 0.0
            if heat_btu == 0.0 and device.specification.power_watts:
                heat_btu = device.specification.power_watts * 3.412

            if heat_btu > 1500:
                high_heat.append(device)
            elif heat_btu > 500:
                medium_heat.append(device)
            else:
                low_heat.append(device)

        # Sort each category by height (tallest first) for compactness
        high_heat.sort(key=lambda d: -(d.specification.height_u if d.specification else 1))
        medium_heat.sort(key=lambda d: -(d.specification.height_u if d.specification else 1))
        low_heat.sort(key=lambda d: -(d.specification.height_u if d.specification else 1))

        # Calculate zone boundaries
        zone_height = rack.total_height_u / 3
        bottom_zone_max = int(zone_height)
        middle_zone_max = int(2 * zone_height)

        occupied = set()
        positions = []

        # Phase 1: Place high-heat devices in bottom zone
        current_u = 1
        for device in high_heat:
            height = int(device.specification.height_u)

            # Try to place in bottom zone first
            placed = False
            for start_u in range(1, min(bottom_zone_max - height + 2, self.rack.total_height_u - height + 2)):
                units_needed = set(range(start_u, start_u + height))
                if not units_needed.intersection(occupied):
                    positions.append((device.id, start_u))
                    occupied.update(units_needed)
                    placed = True
                    break

            if not placed:
                # Bottom zone full, try anywhere
                for start_u in range(1, self.rack.total_height_u - height + 2):
                    units_needed = set(range(start_u, start_u + height))
                    if not units_needed.intersection(occupied):
                        positions.append((device.id, start_u))
                        occupied.update(units_needed)
                        placed = True
                        break

        # Phase 2: Place medium-heat devices in middle zone (prefer) or bottom
        for device in medium_heat:
            height = int(device.specification.height_u)
            placed = False

            # Try middle zone first
            for start_u in range(bottom_zone_max + 1, min(middle_zone_max - height + 2, self.rack.total_height_u - height + 2)):
                units_needed = set(range(start_u, start_u + height))
                if not units_needed.intersection(occupied):
                    positions.append((device.id, start_u))
                    occupied.update(units_needed)
                    placed = True
                    break

            if not placed:
                # Try anywhere
                for start_u in range(1, self.rack.total_height_u - height + 2):
                    units_needed = set(range(start_u, start_u + height))
                    if not units_needed.intersection(occupied):
                        positions.append((device.id, start_u))
                        occupied.update(units_needed)
                        placed = True
                        break

        # Phase 3: Fill remaining spaces with low-heat devices
        for device in low_heat:
            height = int(device.specification.height_u)

            for start_u in range(1, self.rack.total_height_u - height + 2):
                units_needed = set(range(start_u, start_u + height))
                if not units_needed.intersection(occupied):
                    positions.append((device.id, start_u))
                    occupied.update(units_needed)
                    break

        # Validate constraints
        violations = ConstraintValidator.validate_placement(
            self.rack,
            self.devices,
            positions,
            self.locked_device_ids
        )

        return PlacementSolution(
            positions=positions,
            score=0.0,  # Will be calculated by scoring engine
            breakdown=None,
            violations=violations
        )

    def get_algorithm_name(self) -> str:
        """Return algorithm name."""
        return "Thermal Zone Balancing"
