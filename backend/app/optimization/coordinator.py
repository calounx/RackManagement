"""
Multi-objective optimization coordinator.

Orchestrates multiple optimization algorithms and objectives to find
the best device placement solution. Runs multiple algorithms in parallel,
evaluates them using weighted multi-objective scoring, and returns the
best valid solution with improvement recommendations.
"""

from typing import List, Optional, Tuple
from ..models import Rack, Device, Connection
from ..schemas import OptimizationWeights, ScoreBreakdown
from .base import PlacementSolution
from .bin_packing import FirstFitDecreasingOptimizer
from .thermal import ThermalBalancedOptimizer, ThermalObjective
from .objectives import (
    PowerDistributionObjective,
    CableManagementObjective,
    AccessFrequencyObjective,
    WeightDistributionObjective
)
from .scoring import ScoringEngine
import logging

logger = logging.getLogger(__name__)


class OptimizationCoordinator:
    """
    Coordinates multi-objective optimization.
    Runs multiple algorithms and selects best solution.
    """

    def __init__(
        self,
        rack: Rack,
        devices: List[Device],
        connections: List[Connection] = None,
        weights: Optional[OptimizationWeights] = None,
        locked_device_ids: Optional[List[int]] = None,
        current_positions: Optional[List[Tuple[int, int]]] = None
    ):
        """
        Initialize optimization coordinator.

        Args:
            rack: Target rack for optimization
            devices: List of devices to place
            connections: Network connections between devices (optional)
            weights: Objective weights (optional, uses defaults if None)
            locked_device_ids: Device IDs that cannot be moved (optional)
            current_positions: Current device positions for comparison (optional)
        """
        self.rack = rack
        self.devices = devices
        self.connections = connections or []
        self.weights = weights or OptimizationWeights()
        self.locked_device_ids = locked_device_ids or []
        self.current_positions = current_positions

        # Initialize objectives
        self.objectives = [
            ThermalObjective(),
            PowerDistributionObjective(),
            CableManagementObjective(self.connections),
            AccessFrequencyObjective(),
            WeightDistributionObjective()
        ]

        self.scoring_engine = ScoringEngine(self.objectives, self.weights)

    def optimize(self) -> Tuple[PlacementSolution, List[str], dict]:
        """
        Run optimization and return best solution with improvements.

        Strategy:
        1. Calculate current layout score (if exists)
        2. Run multiple optimization algorithms
        3. Score each solution with all objectives
        4. Select best valid solution
        5. Generate improvement recommendations

        Returns:
            Tuple of (best_solution, improvements_list, metadata_dict)

        Raises:
            ValueError: If no valid solutions found
        """
        logger.info(f"Starting optimization for rack {self.rack.id} with {len(self.devices)} devices")

        # Calculate current score as baseline (if positions provided)
        current_score = None
        if self.current_positions:
            try:
                current_score = self.scoring_engine.calculate_total_score(
                    self.rack,
                    self.devices,
                    self.current_positions
                )
                logger.info(f"Current layout score: {current_score.total:.3f}")
            except Exception as e:
                logger.warning(f"Could not calculate current score: {e}")

        # Run optimization algorithms
        solutions = []

        # Algorithm 1: First-Fit Decreasing (height utilization)
        try:
            logger.info("Running FFD algorithm...")
            ffd_optimizer = FirstFitDecreasingOptimizer(
                self.rack,
                self.devices,
                self.weights,
                self.locked_device_ids
            )
            ffd_solution = ffd_optimizer.optimize()

            if ffd_solution.is_valid:
                # Calculate full score breakdown
                ffd_solution.breakdown = self.scoring_engine.calculate_total_score(
                    self.rack,
                    self.devices,
                    ffd_solution.positions
                )
                ffd_solution.score = ffd_solution.breakdown.total
                solutions.append(("First-Fit Decreasing", ffd_solution))
                logger.info(f"FFD solution: score={ffd_solution.score:.3f}, devices={len(ffd_solution.positions)}")
            else:
                logger.warning(f"FFD solution invalid: {ffd_solution.violations}")
        except Exception as e:
            logger.error(f"FFD algorithm failed: {e}", exc_info=True)

        # Algorithm 2: Thermal-Balanced
        try:
            logger.info("Running Thermal-Balanced algorithm...")
            thermal_optimizer = ThermalBalancedOptimizer(
                self.rack,
                self.devices,
                self.weights,
                self.locked_device_ids
            )
            thermal_solution = thermal_optimizer.optimize()

            if thermal_solution.is_valid:
                # Calculate full score breakdown
                thermal_solution.breakdown = self.scoring_engine.calculate_total_score(
                    self.rack,
                    self.devices,
                    thermal_solution.positions
                )
                thermal_solution.score = thermal_solution.breakdown.total
                solutions.append(("Thermal Zone Balancing", thermal_solution))
                logger.info(f"Thermal solution: score={thermal_solution.score:.3f}, devices={len(thermal_solution.positions)}")
            else:
                logger.warning(f"Thermal solution invalid: {thermal_solution.violations}")
        except Exception as e:
            logger.error(f"Thermal algorithm failed: {e}", exc_info=True)

        # Select best solution
        if not solutions:
            raise ValueError(
                "No valid optimization solutions found. "
                "Check that devices fit within rack constraints (height, power, weight, cooling)."
            )

        best_algorithm, best_solution = max(solutions, key=lambda x: x[1].score)
        logger.info(f"Best algorithm: {best_algorithm} (score={best_solution.score:.3f})")

        # Generate improvements list
        improvements = self._generate_improvements(
            current_score,
            best_solution.breakdown,
            best_algorithm
        )

        # Build metadata
        metadata = {
            "algorithm": best_algorithm,
            "alternatives_evaluated": len(solutions),
            "devices_placed": len(best_solution.positions),
            "total_devices": len(self.devices),
            "current_score": current_score.total if current_score else None,
            "optimized_score": best_solution.score,
            "improvement_percentage": self._calculate_improvement_percentage(current_score, best_solution),
            "weights": {
                "cable": self.weights.cable,
                "weight": self.weights.weight,
                "thermal": self.weights.thermal,
                "access": self.weights.access
            },
            "score_breakdown": {
                "cable_management": best_solution.breakdown.cable_management,
                "weight_distribution": best_solution.breakdown.weight_distribution,
                "thermal_management": best_solution.breakdown.thermal_management,
                "access_frequency": best_solution.breakdown.access_frequency
            }
        }

        return best_solution, improvements, metadata

    def _calculate_improvement_percentage(
        self,
        current_score: Optional[ScoreBreakdown],
        best_solution: PlacementSolution
    ) -> Optional[float]:
        """Calculate percentage improvement over current layout."""
        if not current_score or current_score.total == 0:
            return None

        improvement = ((best_solution.score - current_score.total) / current_score.total) * 100
        return round(improvement, 1)

    def _generate_improvements(
        self,
        current_score: Optional[ScoreBreakdown],
        new_score: ScoreBreakdown,
        algorithm: str
    ) -> List[str]:
        """
        Generate human-readable improvement descriptions.

        Args:
            current_score: Current layout scores (optional)
            new_score: Optimized layout scores
            algorithm: Algorithm name used

        Returns:
            List of improvement descriptions
        """
        improvements = []

        if not current_score:
            # New layout (no current layout to compare)
            improvements.append(f"Generated optimized layout using {algorithm} algorithm")
            improvements.append(f"Overall optimization score: {new_score.total:.2f}/1.00")

            # Add specific strengths
            if new_score.thermal_management >= 0.8:
                improvements.append(f"Excellent thermal distribution ({new_score.thermal_management:.2%})")
            if new_score.power_distribution >= 0.8:
                improvements.append(f"Well-balanced power distribution ({new_score.power_distribution:.2%})")
            if new_score.cable_management >= 0.8:
                improvements.append(f"Optimized cable routing ({new_score.cable_management:.2%})")
            if new_score.access_frequency >= 0.8:
                improvements.append(f"Optimal device accessibility ({new_score.access_frequency:.2%})")

        else:
            # Compare with current layout
            total_improvement = ((new_score.total - current_score.total) / current_score.total) * 100

            if total_improvement > 1:
                improvements.append(f"Overall improvement: +{total_improvement:.1f}%")
            elif total_improvement > 0:
                improvements.append(f"Minor optimization improvement: +{total_improvement:.1f}%")
            else:
                improvements.append("Current layout is already well-optimized")

            # Individual objective improvements
            thermal_diff = new_score.thermal_management - current_score.thermal_management
            if thermal_diff > 0.05:
                improvements.append(
                    f"Thermal efficiency improved by {thermal_diff * 100:.1f}% "
                    f"({current_score.thermal_management:.2%} → {new_score.thermal_management:.2%})"
                )

            power_diff = new_score.power_distribution - current_score.power_distribution
            if power_diff > 0.05:
                improvements.append(
                    f"Power distribution balance improved by {power_diff * 100:.1f}% "
                    f"({current_score.power_distribution:.2%} → {new_score.power_distribution:.2%})"
                )

            cable_diff = new_score.cable_management - current_score.cable_management
            if cable_diff > 0.05:
                improvements.append(
                    f"Cable routing efficiency improved by {cable_diff * 100:.1f}% "
                    f"({current_score.cable_management:.2%} → {new_score.cable_management:.2%})"
                )

            access_diff = new_score.access_frequency - current_score.access_frequency
            if access_diff > 0.05:
                improvements.append(
                    f"Device accessibility improved by {access_diff * 100:.1f}% "
                    f"({current_score.access_frequency:.2%} → {new_score.access_frequency:.2%})"
                )

        # Add algorithm info
        improvements.append(f"Optimization algorithm: {algorithm}")

        # Add final score
        improvements.append(f"Final optimization score: {new_score.total:.2f}/1.00")

        return improvements
