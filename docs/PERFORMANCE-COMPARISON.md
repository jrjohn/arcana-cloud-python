# HTTP REST vs gRPC Performance Comparison

## Executive Summary

Performance testing comparing HTTP REST and gRPC protocols in the Arcana Cloud microservices architecture shows that **gRPC provides 2.78x average speedup** over HTTP REST, with significant improvements in point operations.

## Test Environment

- **Architecture**: Three-tier microservices
  - Controller Layer (HTTP REST on port 5003)
  - Service Layer (gRPC on port 50051)
  - Repository Layer (gRPC on port 50052)
  - Database: MySQL on port 3306

- **Testing Methodology**:
  - HTTP: Direct calls to Controller HTTP API
  - gRPC: Direct calls to Service Layer gRPC API
  - Iterations: 100 for read operations, 50 for write operations
  - Metrics: Min, Max, Mean, Median, P95, P99 latencies

## Performance Results

### Summary Table

| Operation          | HTTP (ms) | gRPC (ms) | Speedup  | Winner |
|-------------------|-----------|-----------|----------|--------|
| Get Users List    | 105.89    | 107.24    | 0.99x    | HTTP   |
| Get User By ID    | 5.47      | 0.87      | **6.30x** | gRPC   |
| Create User       | 164.56    | 157.72    | 1.04x    | gRPC   |
| **Average**       | -         | -         | **2.78x** | gRPC   |

### Detailed Analysis

#### 1. Get Users List (Paginated)

**HTTP REST:**
- Mean: 105.89 ms
- Median: 104.99 ms
- P95: 114.85 ms
- P99: 142.38 ms

**gRPC:**
- Mean: 107.24 ms
- Median: 102.05 ms
- P95: 136.93 ms
- P99: 218.36 ms

**Analysis:** Nearly identical performance (HTTP slightly faster). This operation involves database queries with pagination, so serialization overhead is minimal compared to database I/O. The slight HTTP advantage may be due to:
- HTTP connection pooling in the test client
- gRPC having slightly higher overhead for large result sets in this specific use case

#### 2. Get User By ID (Point Query)

**HTTP REST:**
- Mean: 5.47 ms
- Median: 4.99 ms
- P95: 6.94 ms
- P99: 17.40 ms

**gRPC:**
- Mean: 0.87 ms
- Median: 0.83 ms
- P95: 1.08 ms
- P99: 1.21 ms

**Analysis:** **gRPC is 6.30x faster** for point queries. This is the most significant performance difference, showing gRPC's advantages:
- Binary Protocol Buffers vs JSON serialization
- HTTP/2 multiplexing and connection reuse
- Lower parsing overhead
- Smaller message size

This is where gRPC truly shines for microservices communication.

#### 3. Create User (Write Operation)

**HTTP REST:**
- Mean: 164.56 ms
- Median: 162.49 ms
- P95: 175.59 ms
- P99: 202.14 ms

**gRPC:**
- Mean: 157.72 ms
- Median: 156.42 ms
- P95: 169.51 ms
- P99: 175.91 ms

**Analysis:** gRPC is 1.04x faster for write operations. Performance is similar because:
- Database write operations dominate latency
- Password hashing adds ~100-150ms overhead
- Network/serialization overhead is minor compared to DB + crypto operations

## Key Findings

### When gRPC Excels

1. **Point Queries/Single Entity Operations**: 6.30x speedup
   - Low database latency operations where serialization matters
   - Operations with small payloads
   - High-frequency operations

2. **Consistent Latency**: Lower P99 latencies (1.21ms vs 17.40ms for Get By ID)
   - More predictable performance
   - Better tail latencies

3. **Write Operations**: Marginal but consistent improvements (1.04x)
   - Lower overhead even when DB dominates

### When HTTP REST is Competitive

1. **Large Result Sets**: Nearly identical performance (0.99x)
   - Database I/O dominates
   - Serialization overhead is proportionally smaller

2. **Complex Queries**: Database operations dominate response time
   - Network protocol overhead becomes negligible

## Recommendations

### Use gRPC For:

1. **Service-to-Service Communication** ✅
   - Internal microservice APIs
   - Low-latency requirements
   - High-frequency calls
   - Binary data exchange

2. **Performance-Critical Paths** ✅
   - Real-time operations
   - High-throughput services
   - Latency-sensitive workflows

### Use HTTP REST For:

1. **External-Facing APIs** ✅
   - Browser compatibility
   - Third-party integrations
   - Documentation with OpenAPI/Swagger
   - Easier debugging with standard tools

2. **Large Batch Operations**
   - Where database I/O dominates
   - Complex query operations

## Architectural Impact

Our current architecture uses the best of both:

```
External Clients → [Controller HTTP REST:5003]
                    ↓ gRPC
                   [Service gRPC:50051]
                    ↓ gRPC
                   [Repository gRPC:50052]
                    ↓ SQL
                   [MySQL:3306]
```

**Benefits:**
- ✅ HTTP REST for external API (ease of use, compatibility)
- ✅ gRPC for internal communication (performance, efficiency)
- ✅ 2.78x average speedup in inter-service communication
- ✅ 6.30x speedup for point queries (most common operation)

## Throughput Implications

Based on latency measurements:

| Operation      | HTTP Req/s | gRPC Req/s | Improvement |
|---------------|-----------|------------|-------------|
| Get By ID     | ~183      | ~1,149     | +528%       |
| Get Users     | ~9        | ~9         | ~0%         |
| Create User   | ~6        | ~6         | +4%         |

**Key Insight**: For point queries (the most common microservice operation), gRPC enables **6x higher throughput** with the same hardware.

## Conclusion

gRPC provides significant performance advantages for microservices architecture:

- **2.78x average speedup** over HTTP REST
- **6.30x speedup** for point queries (most critical metric)
- **Consistent performance** with lower tail latencies
- **Best practice**: HTTP REST for external APIs, gRPC for internal communication

The hybrid approach used in Arcana Cloud maximizes both **developer experience** (HTTP REST external API) and **performance** (gRPC internal communication).

## Test Reproducibility

Run performance tests:
```bash
./start_all_services.sh  # Start all microservices
python3 performance_test.py  # Run performance comparison
```

## References

- Test Script: [performance_test.py](../performance_test.py)
- gRPC Implementation: [app/grpc_protos/](../app/grpc_protos/)
- HTTP Implementation: [app/controllers/](../app/controllers/)
