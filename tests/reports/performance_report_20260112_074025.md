# HomeRack Performance Test Report

**Generated:** 2026-01-12 07:40:26
**Base URL:** http://lampadas.local:8080
**Test Runs per Endpoint:** 3 (averaged)

## System Configuration

- **Deployment:** Single-worker FastAPI (not production-grade)
- **Database:** SQLite (single-user)
- **Server:** lampadas.local:8080

## Performance Targets

- 🟢 **PASS**: Response time ≤ target
- 🟡 **WARN**: Response time > target but ≤ 2x target
- 🔴 **FAIL**: Response time > 2x target

## Test Results

| Endpoint | Target (ms) | Actual (ms) | Status |
|----------|-------------|-------------|--------|
| GET /api/racks/ | 100 | 6.34 | 🟢 PASS |
| GET /api/racks/1 | 100 | 6.00 | 🟢 PASS |
| GET /api/racks/1/layout | 200 | 6.38 | 🟢 PASS |
| GET /api/racks/1/thermal-analysis | 500 | 9.31 | 🟢 PASS |
| GET /api/devices/ | 100 | 6.64 | 🟢 PASS |
| GET /api/devices/1 | 100 | 6.28 | 🟢 PASS |
| GET /api/device-specs/ | 150 | 5.96 | 🟢 PASS |
| GET /api/device-specs/search?q=Cisco | 150 | 6.77 | 🟢 PASS |
| GET /api/brands/ | 100 | 7.09 | 🟢 PASS |
