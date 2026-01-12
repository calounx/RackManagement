# HomeRack Performance Test Report

**Generated:** 2026-01-12 07:39:49
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
