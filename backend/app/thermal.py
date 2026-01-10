"""
Thermal Management Module
Provides thermal analysis, heat distribution calculations, and airflow validation
"""

from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session, joinedload
from .models import Rack, RackPosition, Device, DeviceSpecification, AirflowPattern, ThermalZone


def get_thermal_zone(u_position: int, total_height_u: int) -> ThermalZone:
    """
    Determine which thermal zone a U position belongs to.

    Args:
        u_position: U position in rack (1-based)
        total_height_u: Total height of rack

    Returns:
        ThermalZone enum value
    """
    third = total_height_u / 3

    if u_position <= third:
        return ThermalZone.BOTTOM
    elif u_position <= (2 * third):
        return ThermalZone.MIDDLE
    else:
        return ThermalZone.TOP


def calculate_rack_heat_output(rack: Rack, db: Session) -> Dict[str, float]:
    """
    Calculate total heat output and distribution by zone.

    Args:
        rack: Rack object
        db: Database session

    Returns:
        Dictionary with heat metrics in BTU/hr
    """
    positions = db.query(RackPosition).filter(
        RackPosition.rack_id == rack.id
    ).options(
        joinedload(RackPosition.device).joinedload(Device.specification)
    ).all()

    total_btu = 0.0
    total_watts = 0.0
    zone_heat = {
        ThermalZone.BOTTOM.value: 0.0,
        ThermalZone.MIDDLE.value: 0.0,
        ThermalZone.TOP.value: 0.0
    }

    device_count = len(positions)

    for pos in positions:
        device_spec = pos.device.specification

        # Get heat output (BTU/hr)
        heat_btu = device_spec.heat_output_btu or 0.0
        power_watts = device_spec.power_watts or 0.0

        # If no BTU specified but has watts, calculate
        if heat_btu == 0.0 and power_watts > 0.0:
            heat_btu = power_watts * 3.412  # 1W = 3.412 BTU/hr

        total_btu += heat_btu
        total_watts += power_watts

        # Add to appropriate zone
        zone = get_thermal_zone(pos.start_u, rack.total_height_u)
        zone_heat[zone.value] += heat_btu

    return {
        "total_heat_btu_hr": round(total_btu, 2),
        "total_power_watts": round(total_watts, 2),
        "bottom_zone_btu": round(zone_heat[ThermalZone.BOTTOM.value], 2),
        "middle_zone_btu": round(zone_heat[ThermalZone.MIDDLE.value], 2),
        "top_zone_btu": round(zone_heat[ThermalZone.TOP.value], 2),
        "device_count": device_count
    }


def calculate_cooling_efficiency(rack: Rack, total_heat_btu: float) -> Dict[str, any]:
    """
    Calculate cooling efficiency and capacity utilization.

    Args:
        rack: Rack object
        total_heat_btu: Total heat load in BTU/hr

    Returns:
        Dictionary with cooling metrics
    """
    cooling_capacity = rack.cooling_capacity_btu or 17000.0  # Default 5 tons

    utilization_percent = (total_heat_btu / cooling_capacity) * 100 if cooling_capacity > 0 else 0
    remaining_capacity_btu = max(0, cooling_capacity - total_heat_btu)
    remaining_capacity_tons = remaining_capacity_btu / 12000  # 1 ton = 12000 BTU/hr

    # Determine status
    if utilization_percent < 70:
        status = "optimal"
    elif utilization_percent < 85:
        status = "acceptable"
    elif utilization_percent < 100:
        status = "warning"
    else:
        status = "critical"

    return {
        "cooling_capacity_btu_hr": cooling_capacity,
        "cooling_capacity_tons": round(cooling_capacity / 12000, 2),
        "heat_load_btu_hr": total_heat_btu,
        "utilization_percent": round(utilization_percent, 2),
        "remaining_capacity_btu_hr": round(remaining_capacity_btu, 2),
        "remaining_capacity_tons": round(remaining_capacity_tons, 2),
        "status": status
    }


def check_airflow_conflicts(rack: Rack, db: Session) -> List[Dict[str, any]]:
    """
    Identify airflow pattern conflicts between adjacent devices.

    Args:
        rack: Rack object
        db: Database session

    Returns:
        List of conflicts with details
    """
    positions = db.query(RackPosition).filter(
        RackPosition.rack_id == rack.id
    ).options(
        joinedload(RackPosition.device).joinedload(Device.specification)
    ).order_by(RackPosition.start_u).all()

    conflicts = []

    for i in range(len(positions) - 1):
        current_pos = positions[i]
        next_pos = positions[i + 1]

        current_spec = current_pos.device.specification
        next_spec = next_pos.device.specification

        current_airflow = current_spec.airflow_pattern or AirflowPattern.FRONT_TO_BACK
        next_airflow = next_spec.airflow_pattern or AirflowPattern.FRONT_TO_BACK

        # Check for opposing airflow patterns
        if (current_airflow == AirflowPattern.FRONT_TO_BACK and
            next_airflow == AirflowPattern.BACK_TO_FRONT):
            conflicts.append({
                "type": "opposing_airflow",
                "severity": "high",
                "device1": {
                    "id": current_pos.device_id,
                    "name": current_pos.device.custom_name or f"{current_spec.brand} {current_spec.model}",
                    "position": f"U{current_pos.start_u}",
                    "airflow": current_airflow.value
                },
                "device2": {
                    "id": next_pos.device_id,
                    "name": next_pos.device.custom_name or f"{next_spec.brand} {next_spec.model}",
                    "position": f"U{next_pos.start_u}",
                    "airflow": next_airflow.value
                },
                "message": "Adjacent devices have opposing airflow patterns, causing hot air recirculation"
            })

        elif (current_airflow == AirflowPattern.BACK_TO_FRONT and
              next_airflow == AirflowPattern.FRONT_TO_BACK):
            conflicts.append({
                "type": "opposing_airflow",
                "severity": "high",
                "device1": {
                    "id": current_pos.device_id,
                    "name": current_pos.device.custom_name or f"{current_spec.brand} {current_spec.model}",
                    "position": f"U{current_pos.start_u}",
                    "airflow": current_airflow.value
                },
                "device2": {
                    "id": next_pos.device_id,
                    "name": next_pos.device.custom_name or f"{next_spec.brand} {next_spec.model}",
                    "position": f"U{next_pos.start_u}",
                    "airflow": next_airflow.value
                },
                "message": "Adjacent devices have opposing airflow patterns, causing hot air recirculation"
            })

    return conflicts


def identify_hot_spots(rack: Rack, db: Session, threshold_btu: float = 1000.0) -> List[Dict[str, any]]:
    """
    Identify thermal hot spots where heat is concentrated.

    Args:
        rack: Rack object
        db: Database session
        threshold_btu: Heat threshold for flagging (default 1000 BTU/hr)

    Returns:
        List of hot spots with details
    """
    positions = db.query(RackPosition).filter(
        RackPosition.rack_id == rack.id
    ).options(
        joinedload(RackPosition.device).joinedload(Device.specification)
    ).all()

    hot_spots = []

    for pos in positions:
        spec = pos.device.specification
        heat_btu = spec.heat_output_btu or (spec.power_watts * 3.412 if spec.power_watts else 0)

        if heat_btu >= threshold_btu:
            zone = get_thermal_zone(pos.start_u, rack.total_height_u)

            hot_spots.append({
                "device_id": pos.device_id,
                "device_name": pos.device.custom_name or f"{spec.brand} {spec.model}",
                "position": f"U{pos.start_u}",
                "zone": zone.value,
                "heat_output_btu_hr": round(heat_btu, 2),
                "power_watts": spec.power_watts or 0,
                "airflow_pattern": (spec.airflow_pattern or AirflowPattern.FRONT_TO_BACK).value,
                "severity": "high" if heat_btu >= 2000 else "medium"
            })

    # Sort by heat output (descending)
    hot_spots.sort(key=lambda x: x["heat_output_btu_hr"], reverse=True)

    return hot_spots


def get_thermal_recommendations(rack: Rack, db: Session) -> List[str]:
    """
    Generate thermal management recommendations.

    Args:
        rack: Rack object
        db: Database session

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Get heat distribution
    heat_dist = calculate_rack_heat_output(rack, db)
    total_heat = heat_dist["total_heat_btu_hr"]

    # Get cooling efficiency
    cooling = calculate_cooling_efficiency(rack, total_heat)

    # Check for overcooling/undercooling
    if cooling["utilization_percent"] > 90:
        recommendations.append(
            f"⚠️ Cooling capacity is {cooling['utilization_percent']:.1f}% utilized. "
            "Consider upgrading cooling or redistributing heat load."
        )
    elif cooling["utilization_percent"] < 40:
        recommendations.append(
            f"ℹ️ Cooling capacity is only {cooling['utilization_percent']:.1f}% utilized. "
            "System is over-provisioned for current load."
        )

    # Check zone balance
    zones = [heat_dist["bottom_zone_btu"], heat_dist["middle_zone_btu"], heat_dist["top_zone_btu"]]
    max_zone = max(zones)
    min_zone = min(zones)

    if max_zone > 0 and min_zone > 0:
        imbalance_ratio = max_zone / min_zone
        if imbalance_ratio > 3.0:
            recommendations.append(
                "⚠️ Significant thermal imbalance detected between zones. "
                "Consider redistributing high-heat devices for better airflow."
            )

    # Check for top-heavy heat
    if heat_dist["top_zone_btu"] > (total_heat * 0.5):
        recommendations.append(
            "⚠️ More than 50% of heat is in top zone. "
            "Move high-heat devices to bottom zone where intake air is coolest."
        )

    # Check for airflow conflicts
    conflicts = check_airflow_conflicts(rack, db)
    if conflicts:
        recommendations.append(
            f"⚠️ Found {len(conflicts)} airflow pattern conflict(s). "
            "Ensure all devices have consistent airflow direction."
        )

    # Check hot spots
    hot_spots = identify_hot_spots(rack, db, threshold_btu=1500.0)
    if hot_spots:
        recommendations.append(
            f"ℹ️ {len(hot_spots)} high-heat device(s) detected (>1500 BTU/hr). "
            "Ensure adequate spacing and airflow around these devices."
        )

    if not recommendations:
        recommendations.append("✓ Thermal configuration is optimal. No issues detected.")

    return recommendations
