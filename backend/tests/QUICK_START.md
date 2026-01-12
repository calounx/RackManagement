# HomeRack Tests - Quick Start Guide

## Install & Run (5 minutes)

### 1. Install Dependencies

```bash
cd /home/calounx/repositories/homerack/backend
pip install -r requirements-test.txt
```

### 2. Run Tests

```bash
# Quick test run
./run_tests.sh

# With coverage report
./run_tests.sh --coverage

# Verbose output
./run_tests.sh --verbose
```

### 3. View Results

```bash
# If you ran with --coverage
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html   # Linux
```

---

## Common Commands

```bash
# Run all tests
pytest

# Run specific category
pytest tests/unit/
pytest tests/business_logic/

# Run with verbose output
pytest -vv

# Run with coverage
pytest --cov=app --cov-report=html

# Run in parallel (fast)
pytest -n auto
```

---

## Test Count Summary

| Category | Tests |
|----------|-------|
| Device Specs CRUD | 40+ |
| Devices CRUD | 35+ |
| Racks CRUD | 35+ |
| Connections CRUD | 25+ |
| Brands CRUD | 20+ |
| Models CRUD | 15+ |
| Device Types CRUD | 12+ |
| Thermal Calculations | 20+ |
| Optimization | 15+ |
| Cable Calculations | 10+ |
| Validations | 10+ |
| **TOTAL** | **~190+** |

---

## Resources

- **Full Guide**: `tests/README.md`
- **Implementation Summary**: `tests/TEST_IMPLEMENTATION_SUMMARY.md`
- **Fixtures**: `tests/conftest.py`
- **Test Runner**: `run_tests.sh --help`

**Status**: Ready to run! 🚀
