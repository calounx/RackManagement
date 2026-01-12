"""
Multi-objective scoring engine for optimization.

Calculates weighted total scores across multiple optimization objectives:
- Thermal management (heat distribution, zone balancing)
- Power distribution (balanced across zones)
- Cable management (minimize cable lengths, keep connections local)
- Access frequency (place frequently accessed devices in middle zones)
- Weight distribution (balanced weight across rack height)
"""

from typing import List, Tuple
from ..models import Rack, Device
from ..schemas import ScoreBreakdown, OptimizationWeights
from .base import BaseObjective


class ScoringEngine:
    """Calculates weighted multi-objective scores."""

    def __init__(self, objectives: List[BaseObjective], weights: OptimizationWeights):
        """
        Initialize scoring engine.

        Args:
            objectives: List of objective calculators
            weights: Weights for each objective type
        """
        self.objectives = objectives
        self.weights = weights

    def calculate_total_score(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> ScoreBreakdown:
        """
        Calculate weighted total score across all objectives.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            ScoreBreakdown with individual objective scores and total
        """
        # Calculate individual objective scores
        scores = {}
        for objective in self.objectives:
            name = objective.get_objective_name()
            score = objective.calculate_score(rack, devices, positions)
            scores[name] = score

        # Apply weights and calculate total
        # Map objective names to weight fields
        cable_score = scores.get("cable_management", 0.0)
        weight_score = scores.get("weight_distribution", 0.0)
        thermal_score = scores.get("thermal_management", 0.0)
        access_score = scores.get("access_frequency", 0.0)

        # Calculate weighted total
        total = (
            cable_score * self.weights.cable +
            weight_score * self.weights.weight +
            thermal_score * self.weights.thermal +
            access_score * self.weights.access
        )

        # Ensure total is between 0.0 and 1.0
        total = max(0.0, min(1.0, total))

        return ScoreBreakdown(
            cable_management=cable_score,
            weight_distribution=weight_score,
            thermal_management=thermal_score,
            access_frequency=access_score,
            total=total
        )

    def get_objective_scores(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> dict:
        """
        Get individual objective scores without weighting.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            Dictionary mapping objective name to score
        """
        scores = {}
        for objective in self.objectives:
            name = objective.get_objective_name()
            score = objective.calculate_score(rack, devices, positions)
            scores[name] = score
        return scores
