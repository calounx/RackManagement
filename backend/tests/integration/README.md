# Integration Tests for HomeRack

This directory contains comprehensive integration tests for the HomeRack application, validating complete workflows and data relationships across multiple endpoints.

## Test Structure

### Test Files

1. **test_crud_workflows.py** (~15 tests)
   - Complete device lifecycle workflows
   - Rack management workflows
   - Catalog creation workflows
   - Tests both legacy (specification) and new (catalog model) approaches

2. **test_data_integrity.py** (~12 tests)
   - Foreign key constraint validation
   - Cascade delete behavior
   - Orphan prevention (referential integrity)
   - Data consistency across relationships

3. **test_cross_endpoint.py** (~10 tests)
   - Device movement between racks
   - Bulk operations
   - Data consistency across endpoints
   - Complex multi-step operations

4. **test_thermal_workflow.py** (~10 tests)
   - Complete thermal analysis workflow
   - Heat distribution verification
   - Hot spot identification
   - Airflow conflict detection
   - Cooling capacity warnings

5. **test_optimization_workflow.py** (~8 tests)
   - Rack optimization workflow
   - Custom weight configurations
   - Locked position handling
   - Optimization result verification

6. **test_catalog_workflow.py** (~10 tests)
   - Complete catalog management
   - Brand and model creation
   - Device creation from models
   - Catalog browsing and filtering

**Total: ~65 integration tests**

## Prerequisites

1. Python 3.11+
2. Virtual environment with dependencies installed
3. SQLite support (in-memory database for tests)

## Installation

```bash
# From the backend directory
cd /home/calounx/repositories/homerack/backend

# Create and activate virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio httpx
```

## Running Tests

### Run All Integration Tests
```bash
pytest tests/integration/ -v
```

### Run Specific Test File
```bash
pytest tests/integration/test_crud_workflows.py -v
```

### Run Specific Test Class
```bash
pytest tests/integration/test_crud_workflows.py::TestDeviceLifecycle -v
```

### Run Specific Test
```bash
pytest tests/integration/test_crud_workflows.py::TestDeviceLifecycle::test_device_lifecycle_with_specification -v
```

### Run with Coverage
```bash
pytest tests/integration/ --cov=app --cov-report=html
```

### Run with Verbose Output
```bash
pytest tests/integration/ -vv --tb=short
```

### Run Tests Matching Pattern
```bash
pytest tests/integration/ -k "thermal" -v
```

## Test Configuration

Tests use the following configuration:

- **Database**: In-memory SQLite (created fresh for each test)
- **Test Client**: FastAPI TestClient with dependency override
- **Isolation**: Each test gets a fresh database session
- **Fixtures**: Shared fixtures defined in `conftest.py`

## Fixtures

The `conftest.py` file provides shared fixtures:

### Session Fixtures
- `db_session`: Fresh database session for each test
- `client`: TestClient with database dependency override

### Catalog Fixtures
- `device_type_switch`, `device_type_server`, `device_type_firewall`
- `brand_cisco`, `brand_dell`
- `model_catalyst_9300`, `model_poweredge_r740`

### Legacy Specification Fixtures
- `spec_switch`, `spec_server`, `spec_firewall`

### Device Fixtures
- `device_switch`, `device_server`, `device_from_model`

### Rack Fixtures
- `rack_standard`, `rack_with_devices`

### Connection Fixtures
- `connection_switch_to_server`

## Test Patterns

### Arrange-Act-Assert (AAA)

All tests follow the AAA pattern:

```python
def test_example(self, client: TestClient, db_session: Session):
    # Arrange: Set up test data
    device_data = {"name": "Test Device", ...}

    # Act: Execute the operation
    response = client.post("/api/devices", json=device_data)

    # Assert: Verify the results
    assert response.status_code == 201
    assert response.json()["name"] == "Test Device"
```

### Workflow Tests

Workflow tests validate complete multi-step operations:

```python
def test_complete_workflow(self, client: TestClient):
    # Step 1: Create prerequisite
    # Step 2: Create main entity
    # Step 3: Perform operations
    # Step 4: Verify results
    # Step 5: Cleanup/delete
    # Step 6: Verify deletion
```

### Error Handling Tests

Tests validate both success and failure cases:

```python
def test_validation(self, client: TestClient):
    # Test invalid data
    response = client.post("/api/devices", json={})
    assert response.status_code == 400

    # Test non-existent resource
    response = client.get("/api/devices/99999")
    assert response.status_code == 404
```

## Expected Test Coverage

These integration tests provide coverage for:

1. **API Endpoints**: All CRUD operations
2. **Business Logic**: Validation, calculations, optimizations
3. **Database**: Relationships, constraints, cascades
4. **Workflows**: Complete end-to-end user journeys
5. **Error Handling**: Invalid inputs, missing resources
6. **Data Integrity**: Referential integrity, consistency

## Common Issues

### Import Errors

If you see import errors, ensure you're running tests from the backend directory:

```bash
cd /home/calounx/repositories/homerack/backend
pytest tests/integration/
```

### Database Errors

If tests fail with database errors, ensure SQLite is installed:

```bash
python3 -c "import sqlite3; print(sqlite3.version)"
```

### Fixture Errors

If fixtures are not found, ensure `conftest.py` is in the tests directory:

```bash
ls tests/conftest.py
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx
      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short
```

## Contributing

When adding new integration tests:

1. Follow the AAA pattern
2. Use descriptive test names (test_should_do_something_when_condition)
3. Test both success and failure cases
4. Clean up resources in test (or rely on fixture cleanup)
5. Document complex workflows with comments
6. Keep tests independent (no shared state)

## Related Documentation

- Main test documentation: `/backend/tests/README.md`
- Unit tests: `/backend/tests/unit/`
- API documentation: `/docs` (when server is running)
