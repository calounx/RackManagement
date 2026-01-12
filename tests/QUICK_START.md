# Performance Tests - Quick Start Guide

## TL;DR - Run Everything

```bash
cd /home/calounx/repositories/homerack/tests
./run_all_performance_tests.sh
```

## Individual Test Suites

### 1. API Performance Tests (Shell-based) ✅ READY TO USE

```bash
cd /home/calounx/repositories/homerack/tests
./performance_test.sh
```

**What it tests:**
- 9 API endpoints
- Response times (GET requests)
- 3 runs per endpoint (averaged)

**Output:**
- Color-coded terminal output
- Markdown report in `reports/performance_report_*.md`

**Current Results:** ✅ ALL PASS (5-8ms avg, targets 100-500ms)

---

### 2. Python Performance Benchmarks ⚠️ REQUIRES SETUP

```bash
# First time: Install dependencies
cd /home/calounx/repositories/homerack/backend
pip install -r requirements-test.txt

# Run tests
pytest tests/performance/test_benchmarks.py -v
```

**What it tests:**
- 20 performance benchmarks
- Database query performance
- Memory usage
- Thermal analysis performance
- Large dataset handling

**Requirements:**
- pytest
- pytest-asyncio
- sqlalchemy

---

### 3. Light Load Tests ⚠️ IN DEVELOPMENT

```bash
cd /home/calounx/repositories/homerack/tests
./load_test.sh
```

**What it tests:**
- Concurrent request handling
- 3-10 concurrent requests per test
- Success rates

**Note:** Currently has parsing issues. Use for manual validation.

---

## Quick Commands

```bash
# Make scripts executable (if needed)
chmod +x /home/calounx/repositories/homerack/tests/*.sh

# Run just API performance tests
cd /home/calounx/repositories/homerack/tests && ./performance_test.sh

# Run Python benchmarks (after pip install)
cd /home/calounx/repositories/homerack/backend && pytest tests/performance/ -v

# View latest performance report
ls -t /home/calounx/repositories/homerack/tests/reports/performance_report_*.md | head -1 | xargs cat

# View latest load test report
ls -t /home/calounx/repositories/homerack/tests/reports/load_test_report_*.md | head -1 | xargs cat
```

---

## Expected Results

### API Performance Tests

```
✅ GET /api/racks/              ~6ms   (target: 100ms)
✅ GET /api/racks/1             ~6ms   (target: 100ms)
✅ GET /api/racks/1/layout      ~7ms   (target: 200ms)
✅ GET /api/thermal-analysis    ~8ms   (target: 500ms)
✅ GET /api/devices/            ~7ms   (target: 100ms)
✅ GET /api/device-specs/       ~6ms   (target: 150ms)
✅ GET /api/brands/             ~8ms   (target: 100ms)
```

All tests should PASS with green status.

---

## Prerequisites

### For Shell Tests (API & Load)
- ✅ bash
- ✅ curl
- ✅ bc (basic calculator)
- ✅ Server running at http://lampadas.local:8080

### For Python Tests
- ⚠️ Python 3.11+
- ⚠️ pytest and dependencies (see requirements-test.txt)

---

## Troubleshooting

### "Server not reachable"
```bash
# Check if server is running
curl http://lampadas.local:8080/api/racks/

# If not, start it
docker-compose up -d backend
```

### "Permission denied"
```bash
chmod +x /home/calounx/repositories/homerack/tests/*.sh
```

### "pytest: command not found"
```bash
cd /home/calounx/repositories/homerack/backend
pip install pytest pytest-asyncio sqlalchemy
```

---

## Files Created

```
tests/
├── README.md                      # Full documentation
├── QUICK_START.md                 # This file
├── PERFORMANCE_TEST_SUMMARY.md    # Results summary
├── performance_test.sh            # API performance tests ✅
├── load_test.sh                   # Load tests ⚠️
├── run_all_performance_tests.sh   # Master runner
└── reports/                       # Generated reports
    ├── performance_report_*.md
    ├── load_test_report_*.md
    └── test_summary_*.md

backend/tests/performance/
├── __init__.py
├── test_benchmarks.py             # 20 Python tests ⚠️
└── (requires pytest)
```

---

## Performance Targets

| Type | Target | Status |
|------|--------|--------|
| Simple GET | <100ms | ✅ 6-8ms |
| Complex GET | <200ms | ✅ 7ms |
| Thermal analysis | <500ms | ✅ 8ms |
| Optimization | <2000ms | ⚠️ Not tested yet |

---

## Next Steps

1. ✅ **Run API performance tests** - Ready to use!
   ```bash
   cd tests && ./performance_test.sh
   ```

2. ⚠️ **Install pytest** - For Python benchmarks
   ```bash
   cd backend && pip install -r requirements-test.txt
   ```

3. ⚠️ **Run Python benchmarks** - After pytest install
   ```bash
   cd backend && pytest tests/performance/ -v
   ```

4. 📊 **Review reports** - Check `tests/reports/`

---

*For full documentation, see [README.md](README.md)*
