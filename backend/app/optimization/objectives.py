"""
Additional optimization objectives for multi-objective placement optimization.

Includes:
- Power distribution (balanced across zones)
- Cable management (minimize cable lengths)
- Access frequency (frequently accessed devices in middle zones)
- Weight distribution (balanced weight across rack height)
"""

from typing import List, Tuple
from .base import BaseObjective
from ..models import Rack, Device, ThermalZone, Connection
from ..thermal import get_thermal_zone


class PowerDistributionObjective(BaseObjective):
    """
    Objective: Balance power distribution across thermal zones.

    Prevents overloading single zone or PDU circuit.
    Balances electrical load for reliability and safety.

    Score components:
    - Zone power balance (60%)
    - Total power headroom (40%)
    """

    def calculate_score(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> float:
        """
        Calculate power distribution score.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            Score between 0.0 (poor distribution) and 1.0 (excellent)
        """
        if not positions:
            return 1.0

        device_map = {d.id: d for d in devices}

        # Calculate power per zone
        zone_power = {
            ThermalZone.BOTTOM.value: 0.0,
            ThermalZone.MIDDLE.value: 0.0,
            ThermalZone.TOP.value: 0.0
        }

        total_power = 0.0

        for dev_id, start_u in positions:
            device = device_map.get(dev_id)
            if not device or not device.specification:
                continue

            power = device.specification.power_watts or 0.0
            total_power += power

            # Assign to zone (use midpoint)
            device_height = device.specification.height_u
            midpoint_u = start_u + (device_height / 2)
            zone = get_thermal_zone(int(midpoint_u), rack.total_height_u)
            zone_power[zone.value] += power

        # Zone balance score (60%)
        powers = list(zone_power.values())
        if max(powers) > 0:
            balance_ratio = min(powers) / max(powers)
        else:
            balance_ratio = 1.0

        # Power headroom score (40%)
        if rack.max_power_watts > 0:
            utilization = total_power / rack.max_power_watts
            headroom_score = 1.0 - min(utilization, 1.0)
        else:
            headroom_score = 0.8  # No limit defined

        # Combined score
        power_score = balance_ratio * 0.6 + headroom_score * 0.4

        return min(power_score, 1.0)

    def get_objective_name(self) -> str:
        """Return objective name."""
        return "power_distribution"


class CableManagementObjective(BaseObjective):
    """
    Objective: Minimize cable lengths and routing complexity.

    Places connected devices near each other to:
    - Reduce cable costs
    - Simplify cable management
    - Improve airflow (fewer cable obstructions)
    - Enhance maintainability

    Score components:
    - Average cable distance (60%)
    - Connection locality (same zone) (40%)
    """

    def __init__(self, connections: List[Connection] = None):
        """
        Initialize cable management objective.

        Args:
            connections: List of network connections between devices
        """
        self.connections = connections or []

    def calculate_score(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> float:
        """
        Calculate cable management score.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            Score between 0.0 (poor cable management) and 1.0 (excellent)
        """
        if not self.connections:
            return 1.0  # No connections = perfect cable management

        position_map = {dev_id: start_u for dev_id, start_u in positions}
        device_map = {d.id: d for d in devices}

        total_distance = 0
        same_zone_connections = 0
        rack_connections = 0  # Connections where both devices are in this rack

        for conn in self.connections:
            # Only consider connections where both devices are in this rack
            source_id = conn.source_device_id
            target_id = conn.target_device_id

            if source_id not in position_map or target_id not in position_map:
                continue  # One or both devices not in rack

            rack_connections += 1

            from_u = position_map[source_id]
            to_u = position_map[target_id]

            # Calculate U distance
            distance = abs(to_u - from_u)
            total_distance += distance

            # Check if same zone
            from_zone = get_thermal_zone(int(from_u), rack.total_height_u)
            to_zone = get_thermal_zone(int(to_u), rack.total_height_u)

            if from_zone == to_zone:
                same_zone_connections += 1

        if rack_connections == 0:
            return 1.0  # No connections in this rack

        # Calculate scores
        avg_distance = total_distance / rack_connections
        normalized_distance = avg_distance / rack.total_height_u
        distance_score = 1.0 - min(normalized_distance, 1.0)

        locality_score = same_zone_connections / rack_connections

        # Combined score
        cable_score = distance_score * 0.6 + locality_score * 0.4

        return min(cable_score, 1.0)

    def get_objective_name(self) -> str:
        """Return objective name."""
        return "cable_management"


class AccessFrequencyObjective(BaseObjective):
    """
    Objective: Place frequently-accessed devices in middle zones.

    Ergonomics and accessibility:
    - HIGH access devices in middle zone (easiest to reach)
    - MEDIUM access devices anywhere
    - LOW access devices in top/bottom (less convenient)

    Score = percentage of HIGH-access devices in middle zone
    """

    def calculate_score(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> float:
        """
        Calculate access frequency optimization score.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            Score between 0.0 (poor accessibility) and 1.0 (excellent)
        """
        if not positions:
            return 1.0

        device_map = {d.id: d for d in devices}

        # Find HIGH-access devices
        high_access_devices = [
            dev_id for dev_id in device_map
            if hasattr(device_map[dev_id], 'access_frequency') and
               device_map[dev_id].access_frequency == "HIGH"
        ]

        if not high_access_devices:
            return 1.0  # No high-access devices = perfect score

        # Count how many HIGH-access devices are in middle zone
        high_access_in_middle = 0
        for device_id, start_u in positions:
            if device_id in high_access_devices:
                # Use midpoint of device
                device = device_map[device_id]
                device_height = device.specification.height_u if device.specification else 1
                midpoint_u = start_u + (device_height / 2)
                zone = get_thermal_zone(int(midpoint_u), rack.total_height_u)

                if zone == ThermalZone.MIDDLE:
                    high_access_in_middle += 1

        score = high_access_in_middle / len(high_access_devices)
        return score

    def get_objective_name(self) -> str:
        """Return objective name."""
        return "access_frequency"


class WeightDistributionObjective(BaseObjective):
    """
    Objective: Balance weight across rack height.

    Prevents:
    - Structural issues from unbalanced weight
    - Rack tipping (top-heavy configurations)
    - Overloading of specific zones

    Score components:
    - Zone weight balance (70%)
    - Total weight headroom (30%)

    Note: Bottom-heavy is acceptable, but extreme imbalance is penalized.
    """

    def calculate_score(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> float:
        """
        Calculate weight distribution score.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            Score between 0.0 (poor distribution) and 1.0 (excellent)
        """
        if not positions:
            return 1.0

        device_map = {d.id: d for d in devices}

        # Calculate weight per zone
        zone_weight = {
            ThermalZone.BOTTOM.value: 0.0,
            ThermalZone.MIDDLE.value: 0.0,
            ThermalZone.TOP.value: 0.0
        }

        total_weight = 0.0

        for dev_id, start_u in positions:
            device = device_map.get(dev_id)
            if not device or not device.specification:
                continue

            weight = device.specification.weight_kg or 0.0
            total_weight += weight

            # Assign to zone (use midpoint)
            device_height = device.specification.height_u
            midpoint_u = start_u + (device_height / 2)
            zone = get_thermal_zone(int(midpoint_u), rack.total_height_u)
            zone_weight[zone.value] += weight

        # Zone balance score (70%)
        # Bottom-heavy is okay, but severe imbalance is bad
        weights = list(zone_weight.values())
        if max(weights) > 0:
            # Modified balance: allow bottom to be heavier
            bottom = zone_weight[ThermalZone.BOTTOM.value]
            middle = zone_weight[ThermalZone.MIDDLE.value]
            top = zone_weight[ThermalZone.TOP.value]

            # Penalize top-heavy configurations
            if top > middle or top > bottom:
                # Top is heaviest - bad
                balance_ratio = min(bottom, middle) / top if top > 0 else 1.0
            else:
                # Bottom or middle heaviest - good, just check not too extreme
                if max(weights) > 0:
                    balance_ratio = min(weights) / max(weights)
                else:
                    balance_ratio = 1.0
        else:
            balance_ratio = 1.0

        # Weight headroom score (30%)
        if rack.max_weight_kg > 0:
            utilization = total_weight / rack.max_weight_kg
            headroom_score = 1.0 - min(utilization, 1.0)
        else:
            headroom_score = 0.8  # No limit defined

        # Combined score
        weight_score = balance_ratio * 0.7 + headroom_score * 0.3

        return min(weight_score, 1.0)

    def get_objective_name(self) -> str:
        """Return objective name."""
        return "weight_distribution"
