# HomeRack Performance Test Report

**Generated:** 2026-01-12 07:40:14
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
| GET /api/racks/ | 100 | 5.37 | 🟢 PASS |
| GET /api/racks/1 | 100 | 7.37 | 🟢 PASS |
| GET /api/racks/1/layout | 200 | 5.80 | 🟢 PASS |
| GET /api/racks/1/thermal-analysis | 500 | 6.40 | 🟢 PASS |
| GET /api/devices/ | 100 | 7.12 | 🟢 PASS |
| GET /api/devices/1 | 100 | 7.19 | 🟢 PASS |
| GET /api/device-specs/ | 150 | 6.81 | 🟢 PASS |
| GET /api/device-specs/search?q=Cisco | 150 | 6.72 | 🟢 PASS |
| GET /api/brands/ | 100 | 8.09 | 🟢 PASS |
