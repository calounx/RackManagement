"""
Constraint validation for device placement optimization.

Validates hard constraints that must be satisfied for any valid placement:
- Physical fit (devices within rack height)
- No overlaps (each U position occupied by at most one device)
- Power budget (total power consumption within rack capacity)
- Weight capacity (total weight within rack limits)
- Cooling capacity (total heat output within cooling capacity)
- Locked positions (specified devices remain in their positions)
"""

from typing import List, Tuple, Optional, Dict
from ..models import Rack, Device


class ConstraintValidator:
    """Validates hard constraints for device placement."""

    @staticmethod
    def validate_placement(
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]],  # [(device_id, start_u), ...]
        locked_positions: Optional[List[int]] = None
    ) -> List[str]:
        """
        Validate all constraints. Returns list of violations.
        Empty list means valid placement.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples
            locked_positions: Device IDs that must be in solution (optional)

        Returns:
            List of constraint violation messages (empty if valid)
        """
        violations = []
        locked_positions = locked_positions or []

        # Create lookup maps
        position_map = {dev_id: start_u for dev_id, start_u in positions}
        device_map = {dev.id: dev for dev in devices}

        # 1. Validate physical height constraint
        for device_id, start_u in positions:
            device = device_map.get(device_id)
            if not device or not device.specification:
                violations.append(f"Device {device_id} missing or has no specification")
                continue

            height = device.specification.height_u
            end_u = start_u + height

            if end_u > rack.total_height_u:
                device_name = device.custom_name or f"{device.specification.brand} {device.specification.model}"
                violations.append(
                    f"Device '{device_name}' (ID {device_id}) exceeds rack height "
                    f"(ends at U{end_u}, rack max U{rack.total_height_u})"
                )

            if start_u < 1:
                device_name = device.custom_name or f"{device.specification.brand} {device.specification.model}"
                violations.append(
                    f"Device '{device_name}' (ID {device_id}) starts below U1 (starts at U{start_u})"
                )

        # 2. Check position overlap
        occupied_units: Dict[int, int] = {}  # unit -> device_id
        for device_id, start_u in positions:
            device = device_map.get(device_id)
            if not device or not device.specification:
                continue

            height = int(device.specification.height_u)

            for u in range(int(start_u), int(start_u + height)):
                if u in occupied_units:
                    conflicting_device_id = occupied_units[u]
                    device1_name = device.custom_name or f"{device.specification.brand} {device.specification.model}"
                    conflicting_device = device_map.get(conflicting_device_id)
                    device2_name = (
                        conflicting_device.custom_name if conflicting_device else str(conflicting_device_id)
                    ) if conflicting_device and conflicting_device.custom_name else (
                        f"{conflicting_device.specification.brand} {conflicting_device.specification.model}"
                        if conflicting_device and conflicting_device.specification
                        else str(conflicting_device_id)
                    )
                    violations.append(
                        f"U{u} conflict: devices '{device1_name}' (ID {device_id}) and "
                        f"'{device2_name}' (ID {conflicting_device_id}) overlap"
                    )
                    break  # Only report first conflict per device
                occupied_units[u] = device_id

        # 3. Check power budget
        total_power = sum(
            device_map[dev_id].specification.power_watts or 0
            for dev_id, _ in positions
            if dev_id in device_map and device_map[dev_id].specification
        )
        if total_power > rack.max_power_watts:
            violations.append(
                f"Power budget exceeded: {total_power:.0f}W > {rack.max_power_watts:.0f}W "
                f"(over by {total_power - rack.max_power_watts:.0f}W)"
            )

        # 4. Check weight capacity
        total_weight = sum(
            device_map[dev_id].specification.weight_kg or 0
            for dev_id, _ in positions
            if dev_id in device_map and device_map[dev_id].specification
        )
        if total_weight > rack.max_weight_kg:
            violations.append(
                f"Weight capacity exceeded: {total_weight:.1f}kg > {rack.max_weight_kg:.1f}kg "
                f"(over by {total_weight - rack.max_weight_kg:.1f}kg)"
            )

        # 5. Check cooling capacity (if rack has cooling_capacity_btu defined)
        if rack.cooling_capacity_btu:
            total_heat_btu = sum(
                device_map[dev_id].specification.heat_output_btu or 0
                for dev_id, _ in positions
                if dev_id in device_map and device_map[dev_id].specification
            )

            if total_heat_btu > rack.cooling_capacity_btu:
                violations.append(
                    f"Cooling capacity exceeded: {total_heat_btu:.0f} BTU/hr > "
                    f"{rack.cooling_capacity_btu:.0f} BTU/hr "
                    f"(over by {total_heat_btu - rack.cooling_capacity_btu:.0f} BTU/hr)"
                )

        # 6. Check locked positions (if specified)
        if locked_positions:
            for device_id in locked_positions:
                if device_id not in position_map:
                    device = device_map.get(device_id)
                    device_name = (
                        device.custom_name if device and device.custom_name
                        else f"Device {device_id}"
                    )
                    violations.append(
                        f"Locked device '{device_name}' (ID {device_id}) missing from solution"
                    )

        return violations

    @staticmethod
    def is_valid(
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]],
        locked_positions: Optional[List[int]] = None
    ) -> bool:
        """
        Quick check if placement is valid.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples
            locked_positions: Device IDs that must be in solution (optional)

        Returns:
            True if valid (no violations), False otherwise
        """
        violations = ConstraintValidator.validate_placement(
            rack, devices, positions, locked_positions
        )
        return len(violations) == 0
