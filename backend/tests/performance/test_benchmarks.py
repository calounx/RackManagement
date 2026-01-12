"""
Performance benchmarks for HomeRack backend.

Phase 5: Performance Tests (~20 tests)
Tests response times, memory usage, and database query performance.
"""

import pytest
import time
import tracemalloc
from typing import Generator, Dict, Any
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Rack, Device, DeviceSpecification, RackPosition, Connection,
    WidthType, AirflowPattern, Brand
)
from app.api.racks import (
    get_occupied_positions,
    is_width_compatible,
    width_type_to_inches
)
from app.thermal import (
    calculate_rack_heat_output,
    calculate_cooling_efficiency,
    identify_hot_spots,
    check_airflow_conflicts
)


# Database setup for performance tests
@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def query_counter(db_session: Session):
    """Count SQL queries executed during a test."""
    queries = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        queries.append({
            'statement': statement,
            'parameters': parameters,
            'timestamp': time.time()
        })

    event.listen(db_session.bind, "before_cursor_execute", before_cursor_execute)

    yield queries

    event.remove(db_session.bind, "before_cursor_execute", before_cursor_execute)


@pytest.fixture
def sample_brand(db_session: Session) -> Brand:
    """Create a sample brand."""
    brand = Brand(name="Cisco", logo_url="https://example.com/cisco.png")
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def sample_rack(db_session: Session) -> Rack:
    """Create a sample rack for testing."""
    rack = Rack(
        name="Test Rack",
        location="Data Center A",
        total_height_u=42,
        width_inches=WidthType.NINETEEN_INCH,
        depth_mm=1000,
        max_weight_kg=1000,
        max_power_watts=5000
    )
    db_session.add(rack)
    db_session.commit()
    db_session.refresh(rack)
    return rack


@pytest.fixture
def sample_device_spec(db_session: Session, sample_brand: Brand) -> DeviceSpecification:
    """Create a sample device specification."""
    spec = DeviceSpecification(
        brand=sample_brand.name,
        model="Catalyst 9300",
        height_u=1,
        width_type=WidthType.NINETEEN_INCH,
        depth_mm=400,
        weight_kg=10,
        power_watts=150,
        airflow_pattern=AirflowPattern.FRONT_TO_BACK
    )
    db_session.add(spec)
    db_session.commit()
    db_session.refresh(spec)
    return spec


@pytest.fixture
def sample_device(db_session: Session, sample_device_spec: DeviceSpecification) -> Device:
    """Create a sample device."""
    device = Device(
        specification_id=sample_device_spec.id,
        custom_name="Switch 1"
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


class TestDatabasePerformance:
    """Test database query performance."""

    def test_rack_query_performance(self, db_session: Session, sample_rack: Rack, query_counter):
        """Test single rack query performance."""
        start = time.time()

        rack = db_session.query(Rack).filter(Rack.id == sample_rack.id).first()

        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert rack is not None
        assert elapsed < 50  # Should be very fast for single query
        assert len(query_counter) == 1  # Should execute exactly 1 query

    def test_rack_list_query_performance(self, db_session: Session):
        """Test rack list query performance with multiple racks."""
        # Create 50 racks
        for i in range(50):
            rack = Rack(
                name=f"Rack {i}",
                location=f"Location {i}",
                total_height_u=42,
                width_inches=WidthType.NINETEEN_INCH
            )
            db_session.add(rack)
        db_session.commit()

        start = time.time()

        racks = db_session.query(Rack).limit(20).all()

        elapsed = (time.time() - start) * 1000

        assert len(racks) == 20
        assert elapsed < 100  # Should fetch 20 racks quickly

    def test_device_spec_search_performance(self, db_session: Session, sample_brand: Brand):
        """Test device specification search performance."""
        # Create multiple device specs
        for i in range(20):
            spec = DeviceSpecification(
                brand=sample_brand.name,
                model=f"Model {i}",
                height_u=1,
                width_type=WidthType.NINETEEN_INCH
            )
            db_session.add(spec)
        db_session.commit()

        start = time.time()

        specs = db_session.query(DeviceSpecification).filter(
            DeviceSpecification.brand == sample_brand.name
        ).all()

        elapsed = (time.time() - start) * 1000

        assert len(specs) == 20
        assert elapsed < 100  # Should search quickly

    def test_rack_layout_query_complexity(self, db_session: Session, sample_rack: Rack,
                                          sample_device_spec: DeviceSpecification, query_counter):
        """Test query complexity for rack layout (N+1 query detection)."""
        # Create 10 devices in the rack
        for i in range(10):
            device = Device(specification_id=sample_device_spec.id, custom_name=f"Device {i}")
            db_session.add(device)
            db_session.flush()

            position = RackPosition(
                rack_id=sample_rack.id,
                device_id=device.id,
                start_u=i * 2 + 1
            )
            db_session.add(position)

        db_session.commit()

        # Clear query counter
        query_counter.clear()

        start = time.time()

        # Fetch rack layout with eager loading
        from sqlalchemy.orm import joinedload
        positions = db_session.query(RackPosition).filter(
            RackPosition.rack_id == sample_rack.id
        ).options(
            joinedload(RackPosition.device).joinedload(Device.specification)
        ).all()

        elapsed = (time.time() - start) * 1000

        assert len(positions) == 10
        assert elapsed < 150  # Should be fast with eager loading
        # Should use joinedload, not individual queries per device
        # The exact number of queries depends on SQLAlchemy's optimization
        assert len(query_counter) <= 3  # Should not have N+1 problem


class TestUtilityFunctionPerformance:
    """Test performance of utility functions."""

    def test_width_compatibility_check_performance(self):
        """Test width compatibility check performance."""
        iterations = 1000

        start = time.time()

        for _ in range(iterations):
            is_width_compatible(WidthType.NINETEEN_INCH, WidthType.NINETEEN_INCH)
            is_width_compatible(WidthType.NINETEEN_INCH, WidthType.ELEVEN_INCH)

        elapsed = (time.time() - start) * 1000
        per_call = elapsed / (iterations * 2)

        assert per_call < 0.01  # Should be very fast (<0.01ms per call)

    def test_width_conversion_performance(self):
        """Test width conversion performance."""
        iterations = 1000

        start = time.time()

        for _ in range(iterations):
            width_type_to_inches(WidthType.NINETEEN_INCH)
            width_type_to_inches(WidthType.ELEVEN_INCH)

        elapsed = (time.time() - start) * 1000
        per_call = elapsed / (iterations * 2)

        assert per_call < 0.01  # Should be very fast

    def test_occupied_positions_performance(self, db_session: Session, sample_rack: Rack,
                                           sample_device_spec: DeviceSpecification):
        """Test performance of getting occupied positions."""
        # Create 20 devices in rack
        for i in range(20):
            device = Device(specification_id=sample_device_spec.id, custom_name=f"Device {i}")
            db_session.add(device)
            db_session.flush()

            position = RackPosition(
                rack_id=sample_rack.id,
                device_id=device.id,
                start_u=i * 2 + 1
            )
            db_session.add(position)

        db_session.commit()

        start = time.time()

        occupied = get_occupied_positions(sample_rack.id, db_session)

        elapsed = (time.time() - start) * 1000

        assert len(occupied) == 20
        assert elapsed < 150  # Should compute quickly


class TestThermalAnalysisPerformance:
    """Test thermal analysis performance."""

    def test_heat_distribution_calculation_performance(self, db_session: Session,
                                                       sample_rack: Rack,
                                                       sample_device_spec: DeviceSpecification):
        """Test heat distribution calculation performance."""
        # Create rack with 10 devices
        for i in range(10):
            device = Device(specification_id=sample_device_spec.id, custom_name=f"Device {i}")
            db_session.add(device)
            db_session.flush()

            position = RackPosition(
                rack_id=sample_rack.id,
                device_id=device.id,
                start_u=i * 3 + 1
            )
            db_session.add(position)

        db_session.commit()

        start = time.time()

        heat_dist = calculate_rack_heat_output(sample_rack, db_session)

        elapsed = (time.time() - start) * 1000

        assert heat_dist is not None
        assert heat_dist["total_heat_btu_hr"] > 0
        assert elapsed < 200  # Should calculate quickly

    def test_cooling_efficiency_calculation_performance(self, sample_rack: Rack):
        """Test cooling efficiency calculation performance."""
        iterations = 100

        start = time.time()

        for _ in range(iterations):
            cooling_eff = calculate_cooling_efficiency(sample_rack, 1000.0)

        elapsed = (time.time() - start) * 1000
        per_call = elapsed / iterations

        assert per_call < 10  # Should be fast calculation

    def test_hot_spot_identification_performance(self, db_session: Session,
                                                 sample_rack: Rack,
                                                 sample_brand: Brand):
        """Test hot spot identification performance."""
        # Create mix of high and low power devices
        for i in range(15):
            power = 500 if i % 3 == 0 else 100  # Every 3rd device is high power

            spec = DeviceSpecification(
                brand=sample_brand.name,
                model=f"Device {i}",
                height_u=2,
                power_watts=power,
                width_type=WidthType.NINETEEN_INCH
            )
            db_session.add(spec)
            db_session.flush()

            device = Device(specification_id=spec.id, custom_name=f"Server {i}")
            db_session.add(device)
            db_session.flush()

            position = RackPosition(
                rack_id=sample_rack.id,
                device_id=device.id,
                start_u=i * 2 + 1
            )
            db_session.add(position)

        db_session.commit()

        start = time.time()

        hot_spots = identify_hot_spots(sample_rack, db_session, threshold_btu=1000.0)

        elapsed = (time.time() - start) * 1000

        assert isinstance(hot_spots, list)
        assert elapsed < 200  # Should identify hot spots quickly

    def test_airflow_conflict_detection_performance(self, db_session: Session,
                                                    sample_rack: Rack,
                                                    sample_brand: Brand):
        """Test airflow conflict detection performance."""
        # Create devices with different airflow patterns
        patterns = [AirflowPattern.FRONT_TO_BACK, AirflowPattern.BACK_TO_FRONT,
                   AirflowPattern.SIDE_TO_SIDE, AirflowPattern.FRONT_TO_BACK]

        for i, pattern in enumerate(patterns * 3):  # 12 devices total
            spec = DeviceSpecification(
                brand=sample_brand.name,
                model=f"Device {i}",
                height_u=1,
                airflow_pattern=pattern,
                width_type=WidthType.NINETEEN_INCH
            )
            db_session.add(spec)
            db_session.flush()

            device = Device(specification_id=spec.id, custom_name=f"Device {i}")
            db_session.add(device)
            db_session.flush()

            position = RackPosition(
                rack_id=sample_rack.id,
                device_id=device.id,
                start_u=i * 2 + 1
            )
            db_session.add(position)

        db_session.commit()

        start = time.time()

        conflicts = check_airflow_conflicts(sample_rack, db_session)

        elapsed = (time.time() - start) * 1000

        assert isinstance(conflicts, list)
        assert elapsed < 200  # Should detect conflicts quickly


class TestMemoryUsage:
    """Test memory usage of critical operations."""

    def test_rack_layout_memory_usage(self, db_session: Session, sample_rack: Rack,
                                      sample_device_spec: DeviceSpecification):
        """Test memory usage when fetching rack layout."""
        # Create 30 devices
        for i in range(30):
            device = Device(specification_id=sample_device_spec.id, custom_name=f"Device {i}")
            db_session.add(device)
            db_session.flush()

            position = RackPosition(
                rack_id=sample_rack.id,
                device_id=device.id,
                start_u=i + 1
            )
            db_session.add(position)

        db_session.commit()

        # Measure memory
        tracemalloc.start()

        from sqlalchemy.orm import joinedload
        positions = db_session.query(RackPosition).filter(
            RackPosition.rack_id == sample_rack.id
        ).options(
            joinedload(RackPosition.device).joinedload(Device.specification)
        ).all()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_kb = peak / 1024

        assert len(positions) == 30
        assert peak_kb < 5000  # Should use less than 5MB for 30 devices

    def test_bulk_device_creation_memory(self, db_session: Session, sample_brand: Brand):
        """Test memory usage when creating many device specifications."""
        tracemalloc.start()

        specs = []
        for i in range(100):
            spec = DeviceSpecification(
                brand=sample_brand.name,
                model=f"Model {i}",
                height_u=1,
                width_type=WidthType.NINETEEN_INCH
            )
            specs.append(spec)

        db_session.bulk_save_objects(specs)
        db_session.commit()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_kb = peak / 1024

        assert peak_kb < 2000  # Should use less than 2MB for 100 specs


class TestLargeDatasetPerformance:
    """Test performance with large datasets."""

    def test_fully_populated_rack_performance(self, db_session: Session,
                                              sample_rack: Rack,
                                              sample_device_spec: DeviceSpecification):
        """Test performance with a fully populated 42U rack."""
        # Fill the entire rack (42 x 1U devices)
        for u in range(1, 43):
            device = Device(specification_id=sample_device_spec.id, custom_name=f"Device U{u}")
            db_session.add(device)
            db_session.flush()

            position = RackPosition(
                rack_id=sample_rack.id,
                device_id=device.id,
                start_u=u
            )
            db_session.add(position)

        db_session.commit()

        # Test layout fetch performance
        start = time.time()

        from sqlalchemy.orm import joinedload
        positions = db_session.query(RackPosition).filter(
            RackPosition.rack_id == sample_rack.id
        ).options(
            joinedload(RackPosition.device).joinedload(Device.specification)
        ).all()

        elapsed = (time.time() - start) * 1000

        assert len(positions) == 42
        assert elapsed < 250  # Should fetch fully populated rack quickly

    def test_pagination_performance_100_items(self, db_session: Session):
        """Test pagination performance with 100+ items."""
        # Create 150 racks
        for i in range(150):
            rack = Rack(
                name=f"Rack {i}",
                location=f"DC {i // 10}",
                total_height_u=42,
                width_inches=WidthType.NINETEEN_INCH
            )
            db_session.add(rack)
        db_session.commit()

        # Test first page
        start = time.time()
        page1 = db_session.query(Rack).offset(0).limit(20).all()
        elapsed1 = (time.time() - start) * 1000

        # Test middle page
        start = time.time()
        page5 = db_session.query(Rack).offset(80).limit(20).all()
        elapsed2 = (time.time() - start) * 1000

        # Test last page
        start = time.time()
        page8 = db_session.query(Rack).offset(140).limit(20).all()
        elapsed3 = (time.time() - start) * 1000

        assert len(page1) == 20
        assert len(page5) == 20
        assert len(page8) == 10  # Last page has fewer items

        # All pagination queries should be fast
        assert elapsed1 < 100
        assert elapsed2 < 100
        assert elapsed3 < 100

    def test_search_performance_many_results(self, db_session: Session, sample_brand: Brand):
        """Test search performance when returning many results."""
        # Create 100 device specifications with similar names
        for i in range(100):
            spec = DeviceSpecification(
                brand=sample_brand.name,
                model=f"Catalyst {i}",
                height_u=1,
                width_type=WidthType.NINETEEN_INCH
            )
            db_session.add(spec)
        db_session.commit()

        start = time.time()

        results = db_session.query(DeviceSpecification).filter(
            DeviceSpecification.model.like("%Catalyst%")
        ).all()

        elapsed = (time.time() - start) * 1000

        assert len(results) == 100
        assert elapsed < 200  # Should search through 100 items quickly

    def test_thermal_analysis_fully_populated_rack(self, db_session: Session,
                                                    sample_rack: Rack,
                                                    sample_brand: Brand):
        """Test thermal analysis performance on fully populated rack."""
        # Create 21 x 2U devices (filling 42U rack)
        for i in range(21):
            spec = DeviceSpecification(
                brand=sample_brand.name,
                model=f"Server {i}",
                height_u=2,
                power_watts=300,
                width_type=WidthType.NINETEEN_INCH,
                airflow_pattern=AirflowPattern.FRONT_TO_BACK
            )
            db_session.add(spec)
            db_session.flush()

            device = Device(specification_id=spec.id, custom_name=f"Server {i}")
            db_session.add(device)
            db_session.flush()

            position = RackPosition(
                rack_id=sample_rack.id,
                device_id=device.id,
                start_u=i * 2 + 1
            )
            db_session.add(position)

        db_session.commit()

        start = time.time()

        # Full thermal analysis
        heat_dist = calculate_rack_heat_output(sample_rack, db_session)
        cooling_eff = calculate_cooling_efficiency(sample_rack, heat_dist["total_heat_btu_hr"])
        hot_spots = identify_hot_spots(sample_rack, db_session, threshold_btu=1000.0)
        conflicts = check_airflow_conflicts(sample_rack, db_session)

        elapsed = (time.time() - start) * 1000

        assert heat_dist["total_heat_btu_hr"] > 0
        assert cooling_eff is not None
        assert isinstance(hot_spots, list)
        assert isinstance(conflicts, list)
        assert elapsed < 500  # Full thermal analysis should complete in <500ms


class TestOptimizationPerformance:
    """Test optimization algorithm performance (when available)."""

    def test_small_rack_optimization_time(self, db_session: Session,
                                          sample_rack: Rack,
                                          sample_brand: Brand):
        """Test optimization time for small rack (5 devices)."""
        try:
            from app.optimization import OptimizationCoordinator
        except ImportError:
            pytest.skip("Optimization module not available")

        # Create 5 devices
        devices = []
        for i in range(5):
            spec = DeviceSpecification(
                brand=sample_brand.name,
                model=f"Device {i}",
                height_u=1,
                power_watts=150,
                width_type=WidthType.NINETEEN_INCH
            )
            db_session.add(spec)
            db_session.flush()

            device = Device(specification_id=spec.id, custom_name=f"Switch {i}")
            db_session.add(device)
            db_session.flush()
            devices.append(device)

        db_session.commit()

        start = time.time()

        coordinator = OptimizationCoordinator(
            rack=sample_rack,
            devices=devices,
            connections=[],
            weights={"cable": 0.3, "weight": 0.25, "thermal": 0.25, "access": 0.2}
        )
        best_solution, improvements, metadata = coordinator.optimize()

        elapsed = (time.time() - start) * 1000

        assert best_solution is not None
        assert elapsed < 2000  # Should optimize 5 devices in <2s
