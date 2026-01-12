# HomeRack Backend Test Suite

Comprehensive test suite for HomeRack API endpoints and business logic.

## Test Overview

### Test Structure

```
tests/
├── conftest.py                          # Pytest configuration and fixtures
├── unit/                                # API endpoint unit tests (~150 tests)
│   ├── test_device_specs_crud.py       # Device specifications CRUD (40 tests)
│   ├── test_devices_crud.py            # Devices CRUD (35 tests)
│   ├── test_racks_crud.py              # Racks CRUD and layout (35 tests)
│   ├── test_connections_crud.py        # Connections CRUD (25 tests)
│   ├── test_brands_crud.py             # Brands CRUD (20 tests)
│   ├── test_models_crud.py             # Models CRUD (15 tests)
│   └── test_device_types_crud.py       # Device types CRUD (12 tests)
└── business_logic/                      # Business logic tests (~40 tests)
    ├── test_thermal_calculations.py    # Thermal analysis (20 tests)
    ├── test_optimization_algorithm.py  # Optimization algorithms (15 tests)
    ├── test_cable_calculations.py      # Cable calculations (10 tests)
    └── test_validations.py             # Validation rules (10 tests)
```

### Test Coverage

- **Total Tests**: ~190 tests
- **API Endpoints**: All CRUD operations tested
- **Business Logic**: Thermal, optimization, cable calculations
- **Validation**: Input validation, constraints, limits
- **Edge Cases**: Boundary conditions, error handling

## Prerequisites

### Install Dependencies

```bash
cd /home/calounx/repositories/homerack/backend
pip install pytest pytest-cov httpx
```

### Dependencies Required

- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `httpx` - HTTP client for FastAPI TestClient
- `sqlalchemy` - Database ORM
- `fastapi` - Web framework

## Running Tests

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with detailed output
pytest -vv
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only business logic tests
pytest tests/business_logic/

# Run specific test file
pytest tests/unit/test_device_specs_crud.py

# Run specific test class
pytest tests/unit/test_device_specs_crud.py::TestDeviceSpecsList

# Run specific test
pytest tests/unit/test_device_specs_crud.py::TestDeviceSpecsList::test_list_device_specs_empty
```

### Run Tests with Coverage

```bash
# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4
```

### Run Tests with Markers

```bash
# Run only fast tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Skip specific tests
pytest --ignore=tests/integration/
```

## Test Fixtures

### Database Fixtures

- `db_session` - Fresh database session with transaction rollback
- `client` - FastAPI TestClient with overridden database

### Factory Fixtures

- `device_spec_factory` - Create device specifications
- `device_factory` - Create devices
- `rack_factory` - Create racks
- `rack_position_factory` - Create rack positions
- `connection_factory` - Create connections
- `brand_factory` - Create brands
- `model_factory` - Create catalog models
- `device_type_factory` - Create device types

### Sample Data Fixtures

- `sample_rack` - Pre-created sample rack
- `sample_device_spec` - Pre-created device specification
- `sample_device` - Pre-created device
- `sample_rack_with_devices` - Rack with multiple positioned devices

### Usage Example

```python
def test_create_device(client, device_spec_factory):
    """Test creating a device with a factory-created spec."""
    spec = device_spec_factory(brand="Cisco", model="Test")

    data = {
        "specification_id": spec.id,
        "custom_name": "My Device"
    }
    response = client.post("/api/devices/", json=data)
    assert response.status_code == 201
```

## Test Guidelines

### Writing New Tests

1. **Use descriptive test names**: `test_<action>_<scenario>_<expected_result>`
2. **Add docstrings**: Explain what the test validates
3. **Use AAA pattern**: Arrange, Act, Assert
4. **Test one thing**: Each test should validate one behavior
5. **Use fixtures**: Reuse setup code via fixtures

### Example Test

```python
def test_create_device_spec_with_all_fields_success(self, client: TestClient):
    """
    Test creating device specification with all fields populated.

    Validates:
    - All fields are accepted
    - Response contains all provided values
    - Returns 201 Created status
    """
    # Arrange
    data = {
        "brand": "Cisco",
        "model": "Catalyst 9300",
        "height_u": 1.0,
        "power_watts": 215.0,
        # ... more fields
    }

    # Act
    response = client.post("/api/device-specs/", json=data)

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert result["brand"] == "Cisco"
    assert result["power_watts"] == 215.0
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests with coverage
      run: |
        cd backend
        pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./backend/coverage.xml
```

## Test Database

Tests use an in-memory SQLite database that is:

- Created fresh for each test
- Automatically rolled back after each test
- Fast (no disk I/O)
- Isolated (no test interference)

## Troubleshooting

### Tests Failing

```bash
# Run with detailed output
pytest -vv

# Run with print statements visible
pytest -s

# Run specific failing test
pytest tests/unit/test_device_specs_crud.py::test_name -vv
```

### Database Issues

```bash
# Check if conftest.py is loaded
pytest --fixtures

# Verify database session is created
pytest -vv --setup-show
```

### Import Errors

```bash
# Ensure backend directory is in PYTHONPATH
export PYTHONPATH=/home/calounx/repositories/homerack/backend:$PYTHONPATH

# Or install package in development mode
pip install -e .
```

## Test Metrics

### Coverage Goals

- **Overall Coverage**: Target 85%+
- **API Endpoints**: Target 95%+
- **Business Logic**: Target 90%+
- **Models**: Target 80%+

### Performance Goals

- **Unit Tests**: < 0.1s per test
- **Business Logic Tests**: < 0.5s per test
- **Full Suite**: < 30s total

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure tests pass: `pytest`
3. Check coverage: `pytest --cov=app`
4. Add test documentation
5. Update this README if needed

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html)
- [Pydantic Validation Testing](https://pydantic-docs.helpmanual.io/usage/models/#model-properties)

## Contact

For questions about tests:
- Review test docstrings for detailed explanations
- Check conftest.py for available fixtures
- Refer to existing tests as examples
