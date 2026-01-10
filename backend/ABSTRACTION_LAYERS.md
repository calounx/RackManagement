# Abstraction Layers Implementation Summary

This document provides an overview of the abstraction layers implemented for the HomeRack API system.

## Overview

The abstraction layers provide a robust foundation for three major systems:
1. **API Reliability Patterns** - Error handling, retries, circuit breakers
2. **Web Spec Fetching** - Automatic device specification retrieval
3. **Cable/Rack Management Validation** - Industry best practices enforcement

## 1. API Reliability Patterns

### Exception Hierarchy (`app/exceptions.py`)

Structured exception classes for consistent error handling:

- **HomeRackBaseException** - Base for all custom exceptions
- **DatabaseError** - Database operation failures (503)
- **ResourceNotFoundError** - 404 errors
- **ResourceConflictError** - 409 conflicts
- **ValidationError** - Enhanced 422 validation errors
- **ExternalServiceError** - External API failures (502)
- **RateLimitExceededError** - Rate limit violations (429)
- **CircuitBreakerOpenError** - Service temporarily unavailable (503)
- **TimeoutError** - Request timeouts (408)
- **ThermalAnalysisError** - Thermal calculation failures
- **CableValidationError** - Cable validation failures
- **RackCapacityError** - Rack capacity exceeded

Each exception includes:
- Appropriate HTTP status code
- Error code for client-side handling
- Detailed error information
- Request ID for tracing

### Configuration Management (`app/config.py`)

Environment-based configuration using Pydantic settings:

**Application Settings:**
- App name, version, debug mode, environment

**Database:**
- Connection URL, pool size, timeouts, recycling

**Rate Limiting:**
- Enable/disable, default limits, endpoint-specific limits
- Redis URL for distributed rate limiting

**Timeouts:**
- Default, health check, thermal analysis, optimization, bulk operations

**Retry Configuration:**
- Max attempts, max delay, exponential backoff, jitter

**Circuit Breaker:**
- Enable/disable, failure threshold, timeout, recovery timeout

**Logging:**
- Level, format (JSON/console), request/response logging, slow query threshold

**Caching:**
- Enable/disable, Redis URL, TTL for different data types

**Web Spec Fetching:**
- Enable/disable, timeout, user agent, max PDF size

**Security:**
- CORS origins, secret key, token expiration

### Retry Mechanisms (`app/utils/retry.py`)

Decorators for automatic retry with exponential backoff:

**`@retry_on_db_error(max_attempts, max_delay, exponential_base)`**
- Retries database operations on transient failures
- Uses exponential backoff with jitter
- Only retries operational errors (not integrity violations)
- Converts to `DatabaseError` on final failure

**`@retry_on_http_error(max_attempts, max_delay, retry_on_status)`**
- Retries HTTP requests on 5xx errors and 429 rate limits
- For external API calls (PDF fetching, manufacturer sites)
- Supports both sync and async functions

**`@retry_thermal_analysis(max_attempts)`**
- Specialized retry for computationally expensive operations
- Limited retries with moderate backoff

### Circuit Breakers (`app/utils/circuit_breaker.py`)

Fault tolerance using pybreaker library:

**Global Circuit Breakers:**
- `database_breaker` - Database operations
- `thermal_calculation_breaker` - Heavy computational operations
- `external_api_breaker` - External HTTP calls

**Features:**
- Configurable failure threshold (default: 5 failures in 60 seconds)
- Timeout before testing recovery (default: 30 seconds)
- State logging (CLOSED → OPEN → HALF_OPEN)
- Status monitoring for health checks

**Usage:**
```python
execute_with_breaker(database_breaker, my_function, *args, **kwargs)
```

### Middleware

**Error Handlers (`app/middleware/error_handlers.py`)**
- Global exception handlers for all exception types
- Consistent error response format with request IDs
- Detailed logging with context
- Sanitized errors in production (no stack traces)

**Request ID Middleware (`app/middleware/request_id.py`)**
- Generates unique UUID for each request
- Stores in request.state for access by handlers
- Includes in response headers (X-Request-ID)
- Enables request tracing and log correlation

---

## 2. Web Spec Fetching Abstraction

### Base Fetcher (`app/fetchers/base.py`)

Abstract base class for manufacturer-specific fetchers:

**DeviceSpec Data Class:**
- Standardized structure for fetched specifications
- All standard fields (height_u, depth_mm, weight_kg, power_watts, etc.)
- Confidence level tracking
- Source URL tracking
- Extra data fields for manufacturer-specific info

**BaseSpecFetcher Abstract Class:**
- `fetch_spec(brand, model)` - Fetch specification from source
- `search_product(brand, model)` - Search for product URLs
- `get_confidence_level(data_source)` - Determine data quality
- `fetch_with_cache(brand, model)` - Main entry point with caching

**Built-in Features:**
- HTTP client with timeout and user agent
- Rate limiting integration
- Cache integration
- Validation pipeline
- Error handling

**Validation:**
- Required fields checking
- Range validation (height, depth, weight, power)
- Consistency checks
- Returns validation issues list

### Parsers (`app/parsers/base.py`)

Abstract parser classes for extracting specifications:

**BaseParser:**
- `parse(content, content_type)` - Parse content and extract specs
- `extract_measurements(text)` - Extract measurements from text
- `normalize_units(value, from_unit, to_unit)` - Unit conversion

**HTMLParser:**
- Parses HTML specification pages
- Extracts JSON-LD structured data
- Parses specification tables
- Extracts definition lists (`<dl>`)
- Regex-based measurement extraction
- Unit conversion (inches↔mm, lbs↔kg, watts↔BTU)

**PDFParser:**
- Uses pdfplumber for table extraction
- Uses PyMuPDF for text extraction
- Parses specification tables from PDFs
- Regex-based measurement extraction
- Same unit conversion as HTMLParser

**Supported Measurements:**
- Rack units (1U, 2 RU, 1.75 inches)
- Depth (mm, inches)
- Weight (kg, lbs)
- Power (watts, W)

---

## 3. Cable/Rack Management Validation

### Cable Validator (`app/utils/validators.py`)

Implements ANSI/TIA standards and industry best practices:

**Separation Validation:**
- Minimum 30cm (12") for unshielded cables near power
- Minimum 15cm (6") for shielded cables near power
- Returns warnings with severity levels

**Bend Radius Validation:**
- Cable-specific multipliers (4x for UTP, 8x for STP, 10x for fiber)
- Warnings for tight routing (conduit, close devices)
- Automatic calculation based on cable type

**Cable Length Validation:**
- Maximum 100m for Ethernet
- Special 50m limit for Cat6 at 10 Gbps
- Speed/distance relationship warnings

**Service Loop Recommendations:**
- 0.3m (1 ft) at work area
- 3m (10 ft) at telecommunications closet
- 3m per end for fiber optics
- Installation tips (Velcro straps, bend radius, etc.)

**Standards Implemented:**
- ANSI/TIA-606-C (labeling)
- ANSI/TIA-568-C (bend radius, separation)
- BICSI service loop standards

### Rack Validator (`app/utils/validators.py`)

Industry best practices for rack management:

**Weight Distribution Validation:**
- Maximum 50% weight in upper half
- 20% safety margin below total capacity
- Zone-based weight tracking (bottom/middle/top)

**U-Space Utilization:**
- Optimal range: 60-85%
- Warnings for under/over-utilization
- Airflow and flexibility considerations

**Blanking Panel Identification:**
- Identifies continuous empty U ranges
- Recommends 1U vs 2U panel sizes
- Critical for airflow management

---

## File Structure

```
backend/app/
├── exceptions.py              # Custom exception hierarchy
├── config.py                  # Environment-based configuration
├── utils/
│   ├── retry.py              # Retry decorators
│   ├── circuit_breaker.py    # Circuit breaker utilities
│   └── validators.py         # Cable/rack validation
├── middleware/
│   ├── error_handlers.py     # Global exception handlers
│   └── request_id.py         # Request ID middleware
├── fetchers/
│   └── base.py               # Base fetcher abstract class
├── parsers/
│   └── base.py               # HTML and PDF parsers
└── data/                     # Future: cache manager, rate limiter
```

---

## Dependencies Added

```
tenacity==8.2.3          # Retry logic
pybreaker==1.0.1         # Circuit breaker
structlog==24.1.0        # Structured logging
slowapi==0.1.9           # Rate limiting
```

---

## Next Steps for Integration

### Phase 1: Main Application Integration
1. Update `app/main.py`:
   - Register exception handlers
   - Add request ID middleware
   - Configure settings from config.py

### Phase 2: API Endpoint Enhancement
1. Update `app/api/device_specs.py`:
   - Apply `@retry_on_db_error` to write operations
   - Add rate limiting decorators
   - Use custom exceptions

2. Update `app/api/devices.py`:
   - Apply retry decorators
   - Add cable validation on connections

3. Update `app/api/racks.py`:
   - Apply retry decorators
   - Add weight distribution validation
   - Add blanking panel recommendations
   - Wrap thermal analysis in circuit breaker

4. Update `app/api/connections.py`:
   - Add cable separation validation
   - Add bend radius validation
   - Add length validation
   - Service loop recommendations

### Phase 3: Database Integration
1. Update `app/database.py`:
   - Configure connection pooling
   - Add retry logic to session creation

### Phase 4: Health Checks
1. Create `app/api/health.py`:
   - Basic liveness probe (`/health`)
   - Readiness probe (`/health/ready`)
   - Detailed health (`/health/detailed`)
   - Circuit breaker status
   - Database connection status

### Phase 5: Manufacturer Implementations
1. Implement specific fetchers:
   - `app/fetchers/cisco.py`
   - `app/fetchers/ubiquiti.py`
   - `app/fetchers/dell.py`
   - `app/fetchers/hp.py`
   - `app/fetchers/generic.py`

2. Create `app/fetchers/factory.py`:
   - Fetcher factory pattern
   - Automatic fetcher selection based on brand

### Phase 6: Caching and Rate Limiting
1. Implement `app/data/cache_manager.py`:
   - Redis caching for specs
   - TTL management
   - Negative result caching

2. Implement `app/data/rate_limiter.py`:
   - Per-manufacturer rate limits
   - Token bucket algorithm

---

## Benefits

### API Reliability
- **Automatic recovery** from transient failures
- **Consistent error responses** across all endpoints
- **Request tracing** for debugging
- **Graceful degradation** when services fail
- **Protection against cascading failures**

### Web Spec Fetching
- **Extensible architecture** for adding manufacturers
- **Consistent data format** regardless of source
- **Quality tracking** via confidence levels
- **Automatic caching** to reduce external calls

### Cable/Rack Management
- **Industry compliance** (ANSI/TIA, BICSI standards)
- **Proactive warnings** before installation
- **Best practices enforcement** automatically
- **Professional documentation** support

---

## Testing Recommendations

### Unit Tests
- Exception hierarchy and error responses
- Retry logic with mock failures
- Circuit breaker state transitions
- Parser accuracy on sample data
- Validator logic with edge cases

### Integration Tests
- End-to-end error handling flow
- Database retry on connection failures
- Cache hit/miss behavior
- Parser integration with real PDFs/HTML

### Load Tests
- Rate limiting under concurrent requests
- Connection pool behavior under load
- Circuit breaker triggers under failures
- Timeout behavior with slow operations

---

## Monitoring and Observability

### Metrics to Track
- Request count by endpoint
- Error rate by exception type
- Retry attempt distribution
- Circuit breaker state changes
- Cache hit rates
- Database connection pool usage

### Logging Strategy
- Structured JSON logs in production
- Request IDs for correlation
- Context-rich error logging
- Slow query logging
- Circuit breaker state transitions

### Health Monitoring
- Database connectivity
- Circuit breaker states
- Connection pool availability
- Cache connectivity (Redis)
- Response time percentiles

---

## Configuration Example

Create `.env` file:

```env
# Application
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@localhost/homerack
DB_POOL_SIZE=20

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_URL=redis://localhost:6379/0

# Circuit Breaker
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5

# Caching
CACHE_ENABLED=true
CACHE_REDIS_URL=redis://localhost:6379/1
```

---

## Summary

These abstraction layers provide a production-ready foundation for:
1. **Resilient API operations** with automatic retry and fallback
2. **Extensible web scraping** for device specifications
3. **Standards-based validation** for cable and rack management

All layers are designed to be:
- **Modular** - Can be used independently
- **Configurable** - Environment-based settings
- **Observable** - Comprehensive logging and monitoring
- **Extensible** - Easy to add new manufacturers, validators, etc.
