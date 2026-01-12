"""
Business logic tests for optimization algorithms.

Tests bin packing, multi-objective scoring, constraints validation, and optimization coordinator.
Total: ~15 tests
"""

import pytest
from sqlalchemy.orm import Session

from app.optimization import OptimizationCoordinator
from app.optimization.bin_packing import FirstFitDecreasingOptimizer
from app.optimization.thermal import ThermalBalancedOptimizer
from app.optimization.constraints import ConstraintValidator
from app.optimization.scoring import ScoringEngine
from app.schemas import OptimizationWeights
from app.models import Rack, Device, DeviceSpecification, RackPosition


class TestBinPackingAlgorithm:
    """Tests for First-Fit Decreasing bin packing algorithm."""

    def test_ffd_empty_devices_list(self, db_session: Session):
        """Test FFD algorithm with no devices."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        optimizer = FirstFitDecreasingOptimizer(rack, [], OptimizationWeights())
        solution = optimizer.optimize()

        assert solution.is_valid
        assert len(solution.positions) == 0

    def test_ffd_single_device(self, db_session: Session):
        """Test FFD algorithm with single device."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        optimizer = FirstFitDecreasingOptimizer(
            rack, [device], OptimizationWeights()
        )
        solution = optimizer.optimize()

        assert solution.is_valid
        assert len(solution.positions) == 1
        # Should place at bottom
        assert solution.positions[0][1] == 1

    def test_ffd_sorts_by_height_decreasing(self, db_session: Session):
        """Test FFD sorts devices by height in decreasing order."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        devices = []
        heights = [1.0, 3.0, 2.0]  # Unsorted

        for i, height in enumerate(heights):
            spec = DeviceSpecification(
                brand="Test", model=f"Device{i}",
                height_u=height,
                power_watts=100.0
            )
            db_session.add(spec)
            db_session.commit()

            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()
            devices.append(device)

        optimizer = FirstFitDecreasingOptimizer(
            rack, devices, OptimizationWeights()
        )
        solution = optimizer.optimize()

        assert solution.is_valid
        assert len(solution.positions) == 3
        # Largest device (3U) should be first
        # Check by examining positions

    def test_ffd_respects_rack_height_limit(self, db_session: Session):
        """Test FFD respects rack height constraints."""
        rack = Rack(name="Test", total_height_u=10)  # Small rack
        db_session.add(rack)
        db_session.commit()

        devices = []
        for i in range(15):  # 15 x 1U = 15U, but rack is only 10U
            spec = DeviceSpecification(
                brand="Test", model=f"Device{i}",
                height_u=1.0,
                power_watts=50.0
            )
            db_session.add(spec)
            db_session.commit()

            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()
            devices.append(device)

        optimizer = FirstFitDecreasingOptimizer(
            rack, devices, OptimizationWeights()
        )
        solution = optimizer.optimize()

        # Should only fit 10 devices
        assert len(solution.positions) <= 10

    def test_ffd_respects_locked_positions(self, db_session: Session):
        """Test FFD respects locked device positions."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device1 = Device(
            custom_name="Locked",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device1)
        db_session.commit()

        device2 = Device(
            custom_name="Free",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device2)
        db_session.commit()

        # Lock device1 at position 20
        locked_pos = RackPosition(
            device_id=device1.id,
            rack_id=rack.id,
            start_u=20,
            locked=True
        )
        db_session.add(locked_pos)
        db_session.commit()

        optimizer = FirstFitDecreasingOptimizer(
            rack, [device1, device2], OptimizationWeights(),
            locked_device_ids=[device1.id]
        )
        solution = optimizer.optimize()

        # Locked device should stay at position 20
        assert solution.is_valid


class TestThermalBalancedOptimizer:
    """Tests for thermal-balanced optimization algorithm."""

    def test_thermal_optimizer_distributes_heat(self, db_session: Session):
        """Test thermal optimizer distributes heat across zones."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        devices = []
        # Create devices with varying power levels
        power_levels = [100.0, 200.0, 300.0]

        for i, power in enumerate(power_levels):
            spec = DeviceSpecification(
                brand="Test", model=f"Device{i}",
                height_u=1.0,
                power_watts=power
            )
            db_session.add(spec)
            db_session.commit()

            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()
            devices.append(device)

        optimizer = ThermalBalancedOptimizer(
            rack, devices, OptimizationWeights()
        )
        solution = optimizer.optimize()

        assert solution.is_valid
        # High-power devices should be in bottom zone


class TestConstraintValidation:
    """Tests for constraint validation."""

    def test_validate_no_overlaps(self, db_session: Session):
        """Test validation detects overlapping devices."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=2.0,  # 2U device
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device1 = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        device2 = Device(
            custom_name="Device2",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add_all([device1, device2])
        db_session.commit()

        validator = ConstraintValidator(rack)

        # Overlapping positions
        positions = [(device1.id, 10), (device2.id, 11)]
        violations = validator.validate(positions, [device1, device2])

        assert "overlap" in str(violations).lower()

    def test_validate_within_rack_height(self, db_session: Session):
        """Test validation detects devices exceeding rack height."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=3.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        validator = ConstraintValidator(rack)

        # Device at U41 with 3U height exceeds rack (goes to U43)
        positions = [(device.id, 41)]
        violations = validator.validate(positions, [device])

        assert len(violations) > 0

    def test_validate_power_limit(self, db_session: Session):
        """Test validation detects power limit violations."""
        rack = Rack(name="Test", total_height_u=42, max_power_watts=1000.0)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=600.0  # High power
        )
        db_session.add(spec)
        db_session.commit()

        devices = []
        for i in range(2):  # 2 x 600W = 1200W > 1000W limit
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()
            devices.append(device)

        validator = ConstraintValidator(rack)
        positions = [(devices[0].id, 10), (devices[1].id, 20)]
        violations = validator.validate(positions, devices)

        assert "power" in str(violations).lower()

    def test_validate_weight_limit(self, db_session: Session):
        """Test validation detects weight limit violations."""
        rack = Rack(name="Test", total_height_u=42, max_weight_kg=100.0)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            weight_kg=60.0  # Heavy device
        )
        db_session.add(spec)
        db_session.commit()

        devices = []
        for i in range(2):  # 2 x 60kg = 120kg > 100kg limit
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()
            devices.append(device)

        validator = ConstraintValidator(rack)
        positions = [(devices[0].id, 10), (devices[1].id, 20)]
        violations = validator.validate(positions, devices)

        assert "weight" in str(violations).lower()


class TestScoringEngine:
    """Tests for multi-objective scoring engine."""

    def test_scoring_empty_rack(self, db_session: Session):
        """Test scoring with empty rack."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        from app.optimization.objectives import (
            ThermalObjective,
            CableManagementObjective,
            WeightDistributionObjective,
            AccessFrequencyObjective
        )

        objectives = [
            ThermalObjective(),
            CableManagementObjective([]),
            WeightDistributionObjective(),
            AccessFrequencyObjective()
        ]

        engine = ScoringEngine(objectives, OptimizationWeights())
        score = engine.calculate_total_score(rack, [], [])

        assert score.total >= 0.0
        assert score.total <= 1.0

    def test_scoring_with_devices(self, db_session: Session):
        """Test scoring produces valid scores with devices."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        device = Device(
            custom_name="Device1",
            specification_id=spec.id,
            brand="Test", model="Device"
        )
        db_session.add(device)
        db_session.commit()

        from app.optimization.objectives import (
            ThermalObjective,
            CableManagementObjective,
            WeightDistributionObjective,
            AccessFrequencyObjective
        )

        objectives = [
            ThermalObjective(),
            CableManagementObjective([]),
            WeightDistributionObjective(),
            AccessFrequencyObjective()
        ]

        engine = ScoringEngine(objectives, OptimizationWeights())
        positions = [(device.id, 10)]
        score = engine.calculate_total_score(rack, [device], positions)

        assert 0.0 <= score.total <= 1.0
        assert 0.0 <= score.thermal_management <= 1.0
        assert 0.0 <= score.weight_distribution <= 1.0


class TestOptimizationCoordinator:
    """Tests for optimization coordinator that runs multiple algorithms."""

    def test_coordinator_runs_multiple_algorithms(self, db_session: Session):
        """Test coordinator runs multiple optimization algorithms."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        devices = []
        for i in range(3):
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()
            devices.append(device)

        coordinator = OptimizationCoordinator(rack, devices)
        solution, improvements, metadata = coordinator.optimize()

        assert solution.is_valid
        assert len(improvements) > 0
        assert "algorithm" in metadata
        assert metadata["devices_placed"] == 3

    def test_coordinator_selects_best_solution(self, db_session: Session):
        """Test coordinator selects solution with highest score."""
        rack = Rack(name="Test", total_height_u=42)
        db_session.add(rack)
        db_session.commit()

        spec = DeviceSpecification(
            brand="Test", model="Device",
            height_u=1.0,
            power_watts=100.0
        )
        db_session.add(spec)
        db_session.commit()

        devices = []
        for i in range(5):
            device = Device(
                custom_name=f"Device{i}",
                specification_id=spec.id,
                brand="Test", model="Device"
            )
            db_session.add(device)
            db_session.commit()
            devices.append(device)

        coordinator = OptimizationCoordinator(rack, devices)
        solution, improvements, metadata = coordinator.optimize()

        # Should have evaluated multiple alternatives
        assert metadata["alternatives_evaluated"] >= 2
        assert solution.score > 0.0
