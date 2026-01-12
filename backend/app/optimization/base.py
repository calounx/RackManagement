"""
Base classes for optimization algorithms.

Provides abstract interfaces for optimizers and objectives, along with
data structures for representing placement solutions.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from dataclasses import dataclass
from ..models import Rack, Device
from ..schemas import OptimizationWeights, ScoreBreakdown


@dataclass
class PlacementSolution:
    """
    Represents a device placement solution.

    Attributes:
        positions: List of (device_id, start_u) tuples
        score: Overall optimization score (0.0-1.0)
        breakdown: Detailed score breakdown by objective
        violations: List of constraint violation messages
    """
    positions: List[Tuple[int, int]]  # [(device_id, start_u), ...]
    score: float
    breakdown: Optional[ScoreBreakdown]
    violations: List[str]

    @property
    def is_valid(self) -> bool:
        """Solution has no constraint violations."""
        return len(self.violations) == 0

    @property
    def device_count(self) -> int:
        """Number of devices in solution."""
        return len(self.positions)


class BaseOptimizer(ABC):
    """
    Abstract base class for optimization algorithms.

    All optimization algorithms must inherit from this class and implement
    the optimize() method. The optimizer should respect the provided weights
    and locked device positions.
    """

    def __init__(
        self,
        rack: Rack,
        devices: List[Device],
        weights: OptimizationWeights,
        locked_device_ids: Optional[List[int]] = None
    ):
        """
        Initialize optimizer.

        Args:
            rack: Target rack for optimization
            devices: List of devices to place
            weights: Objective weights for multi-objective optimization
            locked_device_ids: Device IDs that cannot be moved (optional)
        """
        self.rack = rack
        self.devices = devices
        self.weights = weights
        self.locked_device_ids = locked_device_ids or []

    @abstractmethod
    def optimize(self) -> PlacementSolution:
        """
        Run optimization algorithm and return best solution.

        Returns:
            PlacementSolution with device positions and scores
        """
        pass

    @abstractmethod
    def get_algorithm_name(self) -> str:
        """
        Return algorithm name for metadata.

        Returns:
            Human-readable algorithm name
        """
        pass


class BaseObjective(ABC):
    """
    Abstract base class for optimization objectives.

    Each objective calculates a score (0.0-1.0) for a given placement,
    where higher scores indicate better performance for that objective.
    """

    @abstractmethod
    def calculate_score(
        self,
        rack: Rack,
        devices: List[Device],
        positions: List[Tuple[int, int]]
    ) -> float:
        """
        Calculate objective score for given placement.

        Args:
            rack: Target rack
            devices: List of all devices
            positions: List of (device_id, start_u) tuples

        Returns:
            Score between 0.0 (worst) and 1.0 (best)
        """
        pass

    @abstractmethod
    def get_objective_name(self) -> str:
        """
        Return objective name.

        Returns:
            Unique objective identifier (e.g., "thermal_management")
        """
        pass
