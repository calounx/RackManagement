# Redis Cache Implementation

## Overview

HomeRack now implements Redis-based caching for expensive operations, with a focus on thermal analysis caching. The implementation includes connection pooling, retry logic with exponential backoff, circuit breaker pattern, and graceful degradation.

## Features

- **Performance**: >90% faster on cache hit for thermal analysis
- **Reliability**: Graceful degradation when Redis is unavailable
- **Monitoring**: Comprehensive cache statistics and health checks
- **Automatic Invalidation**: Cache invalidates on data changes
- **Circuit Breaker**: Prevents cascade failures

## Architecture

### Cache Layers

```
┌─────────────────────────────────────────────────┐
│              API Endpoints                      │
│  (thermal analysis, optimization, search)       │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│           Cache Layer (Redis)                   │
│  • 5-60 min TTL based on operation type        │
│  • Automatic invalidation on updates           │
│  • Pattern-based cache keys                    │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│        Business Logic / Computation             │
│  (thermal calculations, optimization)           │
└─────────────────────────────────────────────────┘
```

### Components

1. **Redis Client** (`app/cache/redis.py`)
   - Connection pooling (max 50 connections)
   - Retry logic with exponential backoff
   - Circuit breaker (opens after 5 failures)
   - Health checks

2. **Cache Decorators** (`app/cache/decorators.py`)
   - Function result caching
   - Cache key generation
   - Invalidation helpers

3. **API Integration** (`app/api/racks.py`)
   - Thermal analysis caching
   - Optimization result caching
   - Automatic invalidation on updates

4. **Management Endpoints** (`app/api/health.py`)
   - Cache statistics
   - Manual cache clearing
   - Pattern-based invalidation

## Configuration

### Docker Compose (Production)

Redis service is configured in `docker-compose.prod.yml`:

```yaml
redis:
  image: redis:7-alpine
  container_name: homerack-redis
  command: >
    redis-server
    --maxmemory 256mb
    --maxmemory-policy allkeys-lru
    --save 60 1
    --loglevel warning
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 3
```

### Environment Variables

```bash
# Redis Configuration
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_HEALTH_CHECK_INTERVAL=30

# Cache Configuration
CACHE_ENABLED=true
CACHE_REDIS_URL=redis://redis:6379/0  # Optional, defaults to REDIS_URL
CACHE_TTL_THERMAL=300       # 5 minutes
CACHE_TTL_OPTIMIZATION=600  # 10 minutes
CACHE_TTL_SEARCH=3600       # 1 hour
```

## Cache Keys

### Structure

All cache keys follow a hierarchical pattern:

```
{operation}:{resource}:{id}:{hash}
```

### Examples

```
thermal:rack:123:a1b2c3d4          # Thermal analysis for rack 123
optimization:rack:123:e5f6g7h8     # Optimization result for rack 123
search:specs:i9j0k1l2              # Device spec search result
```

### Key Components

- **Operation**: `thermal`, `optimization`, `search`
- **Resource**: `rack`, `specs`
- **ID**: Resource identifier
- **Hash**: Configuration hash (for cache variation)

## TTL (Time To Live)

| Operation | TTL | Reason |
|-----------|-----|--------|
| Thermal Analysis | 300s (5 min) | Frequently updated, safety-critical |
| Optimization | 600s (10 min) | Expensive computation, stable results |
| Search | 3600s (1 hour) | Stable data, less critical |

## Cache Invalidation

### Automatic Invalidation

Cache is automatically invalidated when:

1. **Rack updates**: `PUT /api/racks/{id}`
2. **Device position changes**: `POST /api/racks/{id}/positions`
3. **Device removal**: `DELETE /api/racks/{id}/positions/{position_id}`
4. **Rack deletion**: `DELETE /api/racks/{id}`

### Manual Invalidation

```bash
# Invalidate thermal cache for specific rack
curl -X DELETE "http://localhost:8000/health/cache/invalidate/thermal:rack:123:*"

# Invalidate all thermal cache
curl -X DELETE "http://localhost:8000/health/cache/invalidate/thermal:*"

# Invalidate all optimization cache
curl -X DELETE "http://localhost:8000/health/cache/invalidate/optimization:*"

# Clear entire cache (use with caution!)
curl -X POST "http://localhost:8000/health/cache/clear"
```

## API Endpoints

### Cache Statistics

```bash
GET /health/cache/stats
```

**Response:**
```json
{
  "timestamp": "2026-01-12T10:30:00Z",
  "cache": {
    "enabled": true,
    "available": true,
    "failure_count": 0,
    "keyspace_hits": 1523,
    "keyspace_misses": 234,
    "hit_rate": 86.68,
    "used_memory": "12.45M",
    "used_memory_bytes": 13058048,
    "connected_clients": 5
  }
}
```

### Clear Cache

```bash
POST /health/cache/clear
```

**Response:**
```json
{
  "status": "success",
  "message": "All cache entries cleared",
  "timestamp": "2026-01-12T10:30:00Z"
}
```

### Invalidate Pattern

```bash
DELETE /health/cache/invalidate/{pattern}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/health/cache/invalidate/thermal:rack:*"
```

**Response:**
```json
{
  "status": "success",
  "pattern": "thermal:rack:*",
  "deleted_count": 5,
  "message": "Invalidated 5 cache entries",
  "timestamp": "2026-01-12T10:30:00Z"
}
```

## Performance Metrics

### Without Cache (Cold)

```
Thermal Analysis: ~500-1000ms
Optimization: ~2000-5000ms
Search: ~100-300ms
```

### With Cache (Warm)

```
Thermal Analysis: ~10-50ms (95-98% faster)
Optimization: ~10-50ms (99% faster)
Search: ~5-20ms (95-98% faster)
```

### Cache Hit Rates (Expected)

- **Thermal Analysis**: 70-85%
- **Optimization**: 40-60%
- **Search**: 80-90%

## Circuit Breaker

The cache client implements a circuit breaker pattern:

1. **Closed** (Normal): All cache operations work
2. **Open** (Failed): After 5 consecutive failures, circuit opens
3. **Graceful Degradation**: Operations continue without cache

### Circuit Breaker States

```python
# Circuit open after 5 failures
if cache._failure_count >= 5:
    # All cache operations return None
    # Application continues without caching
```

## Graceful Degradation

When Redis is unavailable:

1. **No Application Errors**: Cache misses return `None`
2. **Logging**: Failures logged for monitoring
3. **Automatic Fallback**: Direct computation used
4. **Circuit Breaker**: Prevents repeated failures

## Monitoring

### Health Check Integration

```bash
GET /health/detailed
```

Includes Redis status:

```json
{
  "checks": {
    "redis": {
      "status": "up",
      "message": "Redis connection successful",
      "enabled": true,
      "available": true,
      "keyspace_hits": 1523,
      "keyspace_misses": 234,
      "hit_rate": 86.68,
      "used_memory": "12.45M"
    }
  }
}
```

### Logging

Cache operations are logged:

```
INFO: Cache HIT for get_thermal_analysis: thermal:rack:123:a1b2c3d4
INFO: Cache MISS for get_thermal_analysis: thermal:rack:124:e5f6g7h8
INFO: Cache SET: thermal:rack:124:e5f6g7h8 (TTL: 300s)
INFO: Invalidated cache for rack 123 after update
WARNING: Redis circuit breaker OPEN: 5 failures
```

## Testing

### Manual Testing

```bash
# Run cache test suite
cd backend
python scripts/test_cache.py
```

### Test Coverage

- Basic operations (get, set, delete)
- TTL expiration
- Pattern-based deletion
- Statistics retrieval
- Health checks
- Graceful degradation

### Integration Testing

```bash
# Test thermal analysis caching
curl http://localhost:8000/api/racks/1/thermal-analysis

# Check cache hit
curl http://localhost:8000/api/racks/1/thermal-analysis

# Verify cache stats
curl http://localhost:8000/health/cache/stats
```

## Deployment

### Docker Deployment

```bash
# Build and deploy with Redis
docker-compose -f docker-compose.prod.yml up -d

# Verify Redis is running
docker ps | grep redis

# Check logs
docker logs homerack-redis
docker logs homerack-backend | grep -i cache
```

### Verification

```bash
# Check Redis connectivity
docker exec homerack-redis redis-cli ping

# Monitor cache keys
docker exec homerack-redis redis-cli KEYS "*"

# Monitor cache memory
docker exec homerack-redis redis-cli INFO memory
```

## Troubleshooting

### Redis Not Available

**Symptom**: Cache statistics show `"available": false`

**Solution**:
```bash
# Check Redis container
docker ps | grep redis

# Restart Redis
docker restart homerack-redis

# Check backend logs
docker logs homerack-backend | grep -i redis
```

### High Memory Usage

**Symptom**: Redis using >90% of 256MB

**Solution**:
```bash
# Check memory usage
docker exec homerack-redis redis-cli INFO memory

# Clear cache if needed
curl -X POST http://localhost:8000/health/cache/clear

# Increase max memory in docker-compose.prod.yml
--maxmemory 512mb
```

### Low Cache Hit Rate

**Symptom**: Hit rate <50%

**Potential Causes**:
- TTL too short
- Frequent data updates
- Cache being cleared too often

**Solution**:
- Increase TTL values
- Review invalidation logic
- Check application access patterns

### Circuit Breaker Open

**Symptom**: Logs show "Redis circuit breaker OPEN"

**Solution**:
```bash
# Check Redis connectivity
docker exec homerack-redis redis-cli ping

# Restart backend to reset circuit breaker
docker restart homerack-backend
```

## Best Practices

1. **Monitor Hit Rates**: Target 70%+ hit rate
2. **Regular Backups**: Redis persistence enabled (save 60 1)
3. **Resource Limits**: 256MB max memory with LRU eviction
4. **Pattern Invalidation**: Use specific patterns to avoid over-invalidation
5. **Logging**: Monitor cache failures and circuit breaker events

## Security Considerations

1. **No Sensitive Data**: Don't cache authentication tokens
2. **Admin Endpoints**: Restrict cache clearing to admin users
3. **Network Isolation**: Redis only accessible within Docker network
4. **No External Access**: Redis not exposed to host

## Future Enhancements

- [ ] Redis Sentinel for high availability
- [ ] Redis Cluster for horizontal scaling
- [ ] Cache warming on startup
- [ ] Predictive cache prefetching
- [ ] Advanced eviction policies
- [ ] Multi-level caching (memory + Redis)

## References

- **Redis Documentation**: https://redis.io/docs/
- **Circuit Breaker Pattern**: https://martinfowler.com/bliki/CircuitBreaker.html
- **Cache Invalidation**: https://martinfowler.com/bliki/TwoHardThings.html
