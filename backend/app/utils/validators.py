"""
Validation utilities for cable management and rack management best practices.
Implements industry standards for cable separation, bend radius, weight distribution, etc.
"""
from typing import Dict, List, Tuple, Optional, Any
from app.models import CableType, RoutingPath, ThermalZone
from app.exceptions import CableValidationError, RackCapacityError


class CableValidator:
    """
    Validates cable configurations against industry best practices.

    Implements standards from:
    - ANSI/TIA-606-C (labeling)
    - ANSI/TIA-568-C (bend radius, separation)
    - Industry best practices for EMI prevention
    """

    # Minimum separation distances (cm)
    MIN_POWER_DATA_SEPARATION_CM = 30.0  # 12 inches for unshielded
    MIN_POWER_DATA_SEPARATION_SHIELDED_CM = 15.0  # 6 inches for shielded

    # Cable diameters (mm)
    CABLE_DIAMETERS_MM = {
        CableType.CAT5E: 5.0,
        CableType.CAT6: 6.0,
        CableType.CAT6A: 7.5,
        CableType.CAT7: 8.5,
        CableType.FIBER_SM: 3.0,
        CableType.FIBER_MM: 3.0,
        CableType.POWER: 10.0,
        CableType.CONSOLE: 4.0,
    }

    # Bend radius multipliers
    BEND_RADIUS_MULTIPLIERS = {
        CableType.CAT5E: 4,  # UTP
        CableType.CAT6: 4,   # UTP
        CableType.CAT6A: 8,  # STP
        CableType.CAT7: 8,   # STP
        CableType.FIBER_SM: 10,  # Fiber (installed/static)
        CableType.FIBER_MM: 10,
        CableType.POWER: 8,
        CableType.CONSOLE: 4,
    }

    # Maximum cable lengths (meters)
    MAX_CABLE_LENGTHS_M = {
        CableType.CAT5E: 100,
        CableType.CAT6: 100,  # 50m for 10G
        CableType.CAT6A: 100,
        CableType.CAT7: 100,
        CableType.FIBER_SM: 10000,
        CableType.FIBER_MM: 550,  # OM3 at 10G
        CableType.POWER: None,  # No standard limit
        CableType.CONSOLE: 100,
    }

    # Service loop recommendations (meters)
    SERVICE_LOOP_WORK_AREA_M = 0.3  # 1 foot
    SERVICE_LOOP_CLOSET_M = 3.0  # 10 feet
    SERVICE_LOOP_FIBER_M = 3.0  # 3 meters per end

    @classmethod
    def validate_separation(
        cls,
        cable_type: CableType,
        runs_parallel_to_power: bool,
        separation_distance_cm: Optional[float] = None,
        is_shielded: bool = False
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate cable separation from power cables.

        Args:
            cable_type: Type of cable
            runs_parallel_to_power: Whether cable runs parallel to power cables
            separation_distance_cm: Distance from power cables in cm
            is_shielded: Whether cable is shielded

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []

        # Only validate data cables
        if cable_type == CableType.POWER:
            return True, warnings

        if runs_parallel_to_power:
            min_separation = (
                cls.MIN_POWER_DATA_SEPARATION_SHIELDED_CM if is_shielded
                else cls.MIN_POWER_DATA_SEPARATION_CM
            )

            if separation_distance_cm is None:
                warnings.append({
                    "severity": "warning",
                    "code": "SEPARATION_UNKNOWN",
                    "message": "Data cable runs parallel to power - specify separation distance",
                    "recommendation": f"Maintain minimum {min_separation}cm separation"
                })
            elif separation_distance_cm < min_separation:
                warnings.append({
                    "severity": "high",
                    "code": "SEPARATION_INSUFFICIENT",
                    "message": f"Separation {separation_distance_cm}cm is below minimum {min_separation}cm",
                    "recommendation": (
                        f"Increase separation to {min_separation}cm or use shielded cables "
                        f"(reduces minimum to {cls.MIN_POWER_DATA_SEPARATION_SHIELDED_CM}cm)"
                    )
                })
                return False, warnings

        return True, warnings

    @classmethod
    def calculate_min_bend_radius(cls, cable_type: CableType) -> float:
        """
        Calculate minimum bend radius in millimeters.

        Args:
            cable_type: Type of cable

        Returns:
            Minimum bend radius in mm
        """
        diameter = cls.CABLE_DIAMETERS_MM.get(cable_type, 6.0)
        multiplier = cls.BEND_RADIUS_MULTIPLIERS.get(cable_type, 4)
        return diameter * multiplier

    @classmethod
    def validate_bend_radius(
        cls,
        cable_type: CableType,
        routing_path: Optional[RoutingPath] = None,
        vertical_distance_u: Optional[int] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate cable routing doesn't violate bend radius requirements.

        Args:
            cable_type: Type of cable
            routing_path: Cable routing method
            vertical_distance_u: Vertical distance between devices (U)

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        min_bend_radius_mm = cls.calculate_min_bend_radius(cable_type)

        # Warn for tight routing paths
        if routing_path == RoutingPath.CONDUIT:
            warnings.append({
                "severity": "info",
                "code": "BEND_RADIUS_CONDUIT",
                "message": f"Minimum bend radius: {min_bend_radius_mm}mm for {cable_type.value}",
                "recommendation": "Ensure conduit bends meet minimum radius requirement"
            })

        # Warn for vertically close devices
        if vertical_distance_u is not None and vertical_distance_u <= 2:
            warnings.append({
                "severity": "warning",
                "code": "BEND_RADIUS_TIGHT",
                "message": f"Devices only {vertical_distance_u}U apart may cause tight bends",
                "recommendation": (
                    f"Ensure bends meet {min_bend_radius_mm}mm minimum radius. "
                    "Consider service loop or gentler routing."
                )
            })

        return True, warnings

    @classmethod
    def validate_cable_length(
        cls,
        cable_type: CableType,
        cable_length_m: float,
        intended_speed: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate cable length against standards.

        Args:
            cable_type: Type of cable
            cable_length_m: Cable length in meters
            intended_speed: Intended network speed (e.g., "10G")

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        max_length = cls.MAX_CABLE_LENGTHS_M.get(cable_type)

        if max_length is None:
            return True, warnings

        if cable_length_m > max_length:
            warnings.append({
                "severity": "high",
                "code": "LENGTH_EXCEEDED",
                "message": f"Length {cable_length_m}m exceeds maximum {max_length}m for {cable_type.value}",
                "recommendation": f"Reduce length to {max_length}m or use different cable type"
            })
            return False, warnings

        # Special case: Cat6 10G limited to 50m
        if cable_type == CableType.CAT6 and cable_length_m > 50:
            if intended_speed == "10G":
                warnings.append({
                    "severity": "high",
                    "code": "LENGTH_SPEED_LIMIT",
                    "message": f"Cat6 limited to 50m for 10 Gbps (cable is {cable_length_m}m)",
                    "recommendation": "Use Cat6A for 10G over 50m, or limit to 1 Gbps"
                })
                return False, warnings
            else:
                warnings.append({
                    "severity": "info",
                    "code": "LENGTH_SPEED_WARNING",
                    "message": f"Cable length {cable_length_m}m limits Cat6 to 1 Gbps (10G max 50m)",
                    "recommendation": "Use Cat6A if 10 Gbps needed"
                })

        return True, warnings

    @classmethod
    def recommend_service_loop(
        cls,
        cable_type: CableType,
        location_type: str = "closet"
    ) -> Dict[str, Any]:
        """
        Recommend service loop length based on cable type and location.

        Args:
            cable_type: Type of cable
            location_type: Location type ("work_area" or "closet")

        Returns:
            Service loop recommendations
        """
        is_fiber = cable_type in [CableType.FIBER_SM, CableType.FIBER_MM]

        recommendations = {
            "work_area_slack_m": cls.SERVICE_LOOP_WORK_AREA_M,
            "closet_slack_m": cls.SERVICE_LOOP_CLOSET_M,
            "total_recommended_m": cls.SERVICE_LOOP_WORK_AREA_M + cls.SERVICE_LOOP_CLOSET_M,
            "installation_tips": [
                "Use Velcro straps, NOT zip ties to avoid cable pinching",
                "Create circular loop above distribution frame for slack storage",
                "Alternative: S-shaped bundle for more compact storage",
                f"Maintain minimum {cls.calculate_min_bend_radius(cable_type)}mm bend radius in loops",
                "Limit loops per tray to avoid airflow obstruction"
            ]
        }

        if is_fiber:
            recommendations["fiber_end_slack_m"] = cls.SERVICE_LOOP_FIBER_M
            recommendations["installation_tips"].append(
                "Use dedicated slack spools for fiber optic cables"
            )

        return recommendations


class RackValidator:
    """
    Validates rack configurations against industry best practices.

    Implements standards for:
    - Weight distribution
    - Thermal management
    - U-space utilization
    - Power capacity
    """

    # Optimal utilization ranges
    OPTIMAL_U_UTILIZATION_MIN = 0.60  # 60%
    OPTIMAL_U_UTILIZATION_MAX = 0.85  # 85%

    # Weight distribution limits
    MAX_UPPER_HALF_WEIGHT_PERCENT = 50.0  # 50% max in upper half
    RECOMMENDED_CAPACITY_MARGIN = 0.20  # 20% safety margin

    @classmethod
    def validate_weight_distribution(
        cls,
        zone_weights: Dict[str, float],
        total_weight_kg: float,
        max_weight_kg: float
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate weight distribution across rack zones.

        Args:
            zone_weights: Weight in each zone (bottom, middle, top)
            total_weight_kg: Total weight
            max_weight_kg: Maximum rack capacity

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []

        # Check upper half weight percentage
        upper_half_weight = zone_weights.get("middle", 0) + zone_weights.get("top", 0)
        upper_half_percent = (upper_half_weight / total_weight_kg * 100) if total_weight_kg > 0 else 0

        if upper_half_percent > cls.MAX_UPPER_HALF_WEIGHT_PERCENT:
            warnings.append({
                "severity": "high",
                "code": "WEIGHT_TOP_HEAVY",
                "message": f"{upper_half_percent:.1f}% of weight in upper half (max {cls.MAX_UPPER_HALF_WEIGHT_PERCENT}%)",
                "recommendation": "Move heavy equipment to lower U positions for stability"
            })

        # Check total capacity with safety margin
        capacity_used_percent = (total_weight_kg / max_weight_kg * 100) if max_weight_kg > 0 else 0
        recommended_max_percent = (1 - cls.RECOMMENDED_CAPACITY_MARGIN) * 100

        if capacity_used_percent > recommended_max_percent:
            warnings.append({
                "severity": "warning",
                "code": "WEIGHT_CAPACITY_HIGH",
                "message": f"Weight capacity {capacity_used_percent:.1f}% utilized (recommend <{recommended_max_percent:.0f}%)",
                "recommendation": f"Maintain {cls.RECOMMENDED_CAPACITY_MARGIN*100:.0f}% safety margin"
            })

        is_valid = len([w for w in warnings if w["severity"] == "high"]) == 0
        return is_valid, warnings

    @classmethod
    def validate_u_utilization(
        cls,
        used_u: int,
        total_u: int
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate U-space utilization is within optimal range.

        Args:
            used_u: Number of U used
            total_u: Total U available

        Returns:
            Tuple of (is_valid, list_of_infos)
        """
        infos = []
        utilization = used_u / total_u if total_u > 0 else 0

        if utilization < cls.OPTIMAL_U_UTILIZATION_MIN:
            infos.append({
                "severity": "info",
                "code": "U_UNDERUTILIZED",
                "message": f"Rack {utilization*100:.1f}% utilized (optimal: {cls.OPTIMAL_U_UTILIZATION_MIN*100:.0f}-{cls.OPTIMAL_U_UTILIZATION_MAX*100:.0f}%)",
                "recommendation": "Consider consolidation or leaving space for growth"
            })
        elif utilization > cls.OPTIMAL_U_UTILIZATION_MAX:
            infos.append({
                "severity": "warning",
                "code": "U_OVER_UTILIZED",
                "message": f"Rack {utilization*100:.1f}% utilized (optimal: {cls.OPTIMAL_U_UTILIZATION_MIN*100:.0f}-{cls.OPTIMAL_U_UTILIZATION_MAX*100:.0f}%)",
                "recommendation": "High utilization may restrict airflow and future flexibility"
            })

        return True, infos

    @classmethod
    def identify_blanking_panel_needs(
        cls,
        occupied_positions: List[int],
        total_u: int
    ) -> List[Dict[str, Any]]:
        """
        Identify U positions that need blanking panels.

        Args:
            occupied_positions: List of occupied U positions
            total_u: Total U in rack

        Returns:
            List of gap ranges needing blanking panels
        """
        blanking_needed = []
        current_gap_start = None

        for u in range(1, total_u + 1):
            if u not in occupied_positions:
                if current_gap_start is None:
                    current_gap_start = u
            else:
                if current_gap_start is not None:
                    u_count = u - current_gap_start
                    blanking_needed.append({
                        "start_u": current_gap_start,
                        "end_u": u - 1,
                        "u_count": u_count,
                        "panel_size_recommendation": "1U" if u_count <= 2 else "2U"
                    })
                    current_gap_start = None

        # Handle gap at the end
        if current_gap_start is not None:
            blanking_needed.append({
                "start_u": current_gap_start,
                "end_u": total_u,
                "u_count": total_u - current_gap_start + 1,
                "panel_size_recommendation": "2U"
            })

        return blanking_needed
