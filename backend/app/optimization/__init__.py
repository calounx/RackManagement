"""
Optimization module for HomeRack.

This module provides multi-objective optimization algorithms for device placement
in racks, considering thermal management, power distribution, cable routing,
and accessibility.
"""

from .base import BaseOptimizer, BaseObjective, PlacementSolution
from .constraints import ConstraintValidator
from .scoring import ScoringEngine
from .coordinator import OptimizationCoordinator

__all__ = [
    "BaseOptimizer",
    "BaseObjective",
    "PlacementSolution",
    "ConstraintValidator",
    "ScoringEngine",
    "OptimizationCoordinator",
]
