# HomeRack Performance & Load Tests

This directory contains comprehensive performance and load testing tools for the HomeRack application.

## Overview

The test suite consists of three main components:

1. **Python Performance Benchmarks** - Unit-level performance tests
2. **API Response Time Benchmarks** - End-to-end API performance tests
3. **Light Load Tests** - Concurrent request handling tests

## System Configuration

**Important:** These tests are designed for the current deployment:

- **Single-worker FastAPI** (not production-grade)
- **SQLite database** (single-user, not optimized for concurrency)
- **Development environment** (lampadas.local:8080)

The tests focus on detecting obvious performance issues rather than stress testing the system.

## Quick Start

### Run All Tests

```bash
cd /home/calounx/repositories/homerack/tests
./run_all_performance_tests.sh
```

This will run all test suites and generate comprehensive reports.

### Run Individual Test Suites

#### 1. Python Performance Benchmarks

```bash
cd /home/calounx/repositories/homerack/backend
python3 -m pytest tests/performance/test_benchmarks.py -v
```

**Coverage:** ~20 performance tests including:
- Database query performance
- Utility function benchmarks
- Thermal analysis performance
- Memory usage tests
- Large dataset handling

#### 2. API Response Time Benchmarks

```bash
cd /home/calounx/repositories/homerack/tests
./performance_test.sh
```

**Tests the following endpoints:**
- `GET /api/racks/` (target: <100ms)
- `GET /api/racks/1` (target: <100ms)
- `GET /api/racks/1/layout` (target: <200ms)
- `GET /api/racks/1/thermal-analysis` (target: <500ms)
- `GET /api/devices/` (target: <100ms)
- `GET /api/device-specs/search` (target: <150ms)
- And more...

#### 3. Light Load Tests

```bash
cd /home/calounx/repositories/homerack/tests
./load_test.sh
```

**Concurrent request tests:**
- 10 concurrent reads on list endpoints
- 5 concurrent reads on complex endpoints
- 3 concurrent reads on expensive operations

## Performance Targets

### Response Time Standards

| Category | Target | Warning | Critical |
|----------|--------|---------|----------|
| Simple queries | <100ms | <200ms | >200ms |
| Complex queries | <200ms | <400ms | >400ms |
| Thermal analysis | <500ms | <1000ms | >1000ms |
| Optimization | <2000ms | <4000ms | >4000ms |

### Status Indicators

- 🟢 **PASS**: Response time ≤ target
- 🟡 **WARN**: Response time > target but ≤ 2x target
- 🔴 **FAIL**: Response time > 2x target

## Test Details

### Python Performance Benchmarks (test_benchmarks.py)

**Test Classes:**

1. **TestDatabasePerformance** (4 tests)
   - Single rack query performance
   - Rack list query performance
   - Device spec search performance
   - N+1 query detection

2. **TestUtilityFunctionPerformance** (3 tests)
   - Width compatibility checks
   - Width conversion
   - Occupied positions calculation

3. **TestThermalAnalysisPerformance** (4 tests)
   - Heat distribution calculation
   - Cooling efficiency calculation
   - Hot spot identification
   - Airflow conflict detection

4. **TestMemoryUsage** (2 tests)
   - Rack layout memory usage
   - Bulk device creation memory

5. **TestLargeDatasetPerformance** (4 tests)
   - Fully populated rack (42U)
   - Pagination with 100+ items
   - Search with many results
   - Thermal analysis on full rack

6. **TestOptimizationPerformance** (1 test)
   - Small rack optimization time

**Total: ~20 tests**

### Performance Test Script (performance_test.sh)

**Features:**
- Runs each test 3 times and averages results
- Color-coded output (green/yellow/red)
- Generates markdown report with:
  - Performance metrics table
  - Response time distribution
  - Recommendations
  - System limitations

**Endpoints Tested:** 9 key API endpoints

### Load Test Script (load_test.sh)

**Features:**
- Concurrent request simulation
- Success rate tracking
- Average response time calculation
- Concurrency limit detection

**Tests:**
- 6 concurrent load scenarios
- Varying concurrency levels (3-10 concurrent)
- Appropriate for single-worker system

## Reports

All test runs generate reports in `tests/reports/`:

- `performance_report_TIMESTAMP.md` - API response time results
- `load_test_report_TIMESTAMP.md` - Concurrent load test results
- `test_summary_TIMESTAMP.md` - Overall test execution summary
- `pytest_output.log` - Python benchmark output

## Environment Variables

```bash
# Override base URL (default: http://lampadas.local:8080)
export BASE_URL=http://localhost:8080

# Run tests
./run_all_performance_tests.sh
```

## Prerequisites

### Server Requirements
- HomeRack backend running at http://lampadas.local:8080
- Sample data loaded (at least 1 rack with devices)

### System Requirements
- bash
- curl
- bc (basic calculator)
- python3
- pytest

### Python Dependencies
```bash
cd /home/calounx/repositories/homerack/backend
pip install pytest sqlalchemy
```

## Understanding Results

### Good Performance Indicators

✅ All API endpoints within target response times
✅ No N+1 query problems detected
✅ Memory usage under limits
✅ 100% success rate on concurrent requests

### Warning Signs

⚠️ Response times between target and 2x target
⚠️ Some concurrent requests timing out
⚠️ Memory usage approaching limits
⚠️ Query count increasing with dataset size

### Critical Issues

🔴 Response times >2x target
🔴 Failed concurrent requests
🔴 Memory leaks detected
🔴 Database locking issues

## Optimization Strategies

### If Tests Show Performance Issues

1. **Database Optimization**
   - Add indexes for frequently queried fields
   - Use eager loading to prevent N+1 queries
   - Implement query result caching

2. **API Optimization**
   - Enable response compression
   - Implement pagination properly
   - Cache expensive computations

3. **Code Optimization**
   - Profile slow functions
   - Optimize algorithms
   - Reduce unnecessary database queries

4. **Deployment Optimization**
   - Use multiple workers (gunicorn)
   - Migrate to PostgreSQL
   - Implement Redis caching
   - Use load balancing

## System Limitations

### Current Deployment

The current system has known limitations:

1. **Single Worker**
   - Processes requests sequentially
   - No parallelism
   - Limited throughput

2. **SQLite Database**
   - Locks entire database for writes
   - Not optimized for concurrent reads
   - Limited to local file system

3. **No Caching**
   - Every request hits the database
   - Expensive computations repeated
   - No distributed cache

### Production Recommendations

For production deployment:

1. **Multi-worker Setup**
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```

2. **PostgreSQL Database**
   - Better concurrency support
   - Advanced indexing
   - Connection pooling

3. **Redis Caching**
   - Cache device specifications
   - Cache thermal analysis results
   - Distributed session storage

4. **Load Balancing**
   - nginx or HAProxy
   - Multiple backend instances
   - Geographic distribution

## Continuous Performance Testing

### Integration with CI/CD

Add to your CI/CD pipeline:

```yaml
performance-tests:
  script:
    - ./tests/run_all_performance_tests.sh
  artifacts:
    paths:
      - tests/reports/
    when: always
```

### Performance Monitoring

Set up alerts for:
- Response times exceeding targets
- Error rates above 1%
- Memory usage above 80%
- Database query times increasing

## Troubleshooting

### Server Not Reachable

```bash
# Check if server is running
curl http://lampadas.local:8080/api/racks/

# Check server logs
docker logs homerack-backend

# Restart server if needed
docker-compose restart backend
```

### Tests Timing Out

```bash
# Increase timeout in scripts
# Edit performance_test.sh or load_test.sh
# Adjust curl timeout: --max-time 30
```

### Permission Errors

```bash
# Make scripts executable
chmod +x tests/*.sh
```

### Missing Dependencies

```bash
# Install required tools
sudo apt-get install bc curl

# Install Python dependencies
cd backend
pip install pytest sqlalchemy
```

## Contributing

When adding new performance tests:

1. Follow existing patterns in `test_benchmarks.py`
2. Set appropriate performance targets
3. Add test to relevant test class
4. Update this README with new test details
5. Ensure tests pass on single-worker system

## License

Same as HomeRack project.

## Support

For issues or questions:
1. Check the reports in `tests/reports/`
2. Review server logs
3. Consult the main HomeRack documentation
