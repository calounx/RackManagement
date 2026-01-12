#!/bin/bash
# Performance Test Script for HomeRack Application
# Tests response times for key API endpoints against target benchmarks

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://lampadas.local:8080}"
OUTPUT_DIR="$(dirname "$0")/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${OUTPUT_DIR}/performance_report_${TIMESTAMP}.md"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Test result arrays
declare -a TEST_NAMES
declare -a RESPONSE_TIMES
declare -a TARGET_TIMES
declare -a STATUSES

# Function to print colored output
print_color() {
    color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Function to test endpoint
test_endpoint() {
    name=$1
    method=$2
    endpoint=$3
    target_ms=$4
    data=${5:-""}

    print_color "$BLUE" "\n==> Testing: $name"
    print_color "$BLUE" "    Target: <${target_ms}ms"

    # Prepare curl command
    curl_cmd="curl -s -o /dev/null -w '%{time_total}'"
    curl_cmd="${curl_cmd} -X ${method}"

    if [ -n "$data" ]; then
        curl_cmd="${curl_cmd} -H 'Content-Type: application/json' -d '${data}'"
    fi

    curl_cmd="${curl_cmd} '${BASE_URL}${endpoint}'"

    # Run test 3 times and take average
    total_time=0
    runs=3

    for i in $(seq 1 $runs); do
        local time_seconds=$(eval $curl_cmd 2>/dev/null || echo "0")
        local time_ms=$(echo "$time_seconds * 1000" | bc)
        total_time=$(echo "$total_time + $time_ms" | bc)
    done

    avg_time=$(echo "scale=2; $total_time / $runs" | bc)

    # Determine status
    status=""
    color=""
    target_2x=$(echo "$target_ms * 2" | bc)

    if (( $(echo "$avg_time <= $target_ms" | bc -l) )); then
        status="PASS"
        color="$GREEN"
    elif (( $(echo "$avg_time <= $target_2x" | bc -l) )); then
        status="WARN"
        color="$YELLOW"
    else
        status="FAIL"
        color="$RED"
    fi

    # Store results
    TEST_NAMES+=("$name")
    RESPONSE_TIMES+=("$avg_time")
    TARGET_TIMES+=("$target_ms")
    STATUSES+=("$status")

    print_color "$color" "    Result: ${avg_time}ms - ${status}"
}

# Banner
print_color "$BLUE" "╔════════════════════════════════════════════════════════════╗"
print_color "$BLUE" "║         HomeRack Performance Test Suite                    ║"
print_color "$BLUE" "║         Target: ${BASE_URL}                  ║"
print_color "$BLUE" "╚════════════════════════════════════════════════════════════╝"

# Check if server is reachable
print_color "$BLUE" "\nChecking server availability..."
if ! curl -s -f "${BASE_URL}/api/racks/" > /dev/null 2>&1; then
    print_color "$RED" "ERROR: Server not reachable at ${BASE_URL}"
    exit 1
fi
print_color "$GREEN" "Server is reachable!"

# Run performance tests
print_color "$BLUE" "\n╔════════════════════════════════════════════════════════════╗"
print_color "$BLUE" "║                    Running Tests                           ║"
print_color "$BLUE" "╚════════════════════════════════════════════════════════════╝"

test_endpoint "GET /api/racks/" "GET" "/api/racks/" 100
test_endpoint "GET /api/racks/1" "GET" "/api/racks/1" 100
test_endpoint "GET /api/racks/1/layout" "GET" "/api/racks/1/layout" 200
test_endpoint "GET /api/racks/1/thermal-analysis" "GET" "/api/racks/1/thermal-analysis" 500
test_endpoint "GET /api/devices/" "GET" "/api/devices/" 100
test_endpoint "GET /api/devices/1" "GET" "/api/devices/1" 100
test_endpoint "GET /api/device-specs/" "GET" "/api/device-specs/" 150
test_endpoint "GET /api/device-specs/search?q=Cisco" "GET" "/api/device-specs/search?q=Cisco" 150
test_endpoint "GET /api/brands/" "GET" "/api/brands/" 100

# Generate markdown report
print_color "$BLUE" "\n╔════════════════════════════════════════════════════════════╗"
print_color "$BLUE" "║              Generating Report                             ║"
print_color "$BLUE" "╚════════════════════════════════════════════════════════════╝"

cat > "$REPORT_FILE" << EOF
# HomeRack Performance Test Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')
**Base URL:** ${BASE_URL}
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
EOF

# Add results to report
for i in "${!TEST_NAMES[@]}"; do
    name="${TEST_NAMES[$i]}"
    time="${RESPONSE_TIMES[$i]}"
    target="${TARGET_TIMES[$i]}"
    status="${STATUSES[$i]}"

    emoji=""
    case "$status" in
        "PASS") emoji="🟢" ;;
        "WARN") emoji="🟡" ;;
        "FAIL") emoji="🔴" ;;
    esac

    echo "| $name | $target | $time | $emoji $status |" >> "$REPORT_FILE"
done

# Calculate statistics
total_tests=${#TEST_NAMES[@]}
passed=$(printf '%s\n' "${STATUSES[@]}" | grep -c "PASS" || echo 0)
warned=$(printf '%s\n' "${STATUSES[@]}" | grep -c "WARN" || echo 0)
failed=$(printf '%s\n' "${STATUSES[@]}" | grep -c "FAIL" || echo 0)

cat >> "$REPORT_FILE" << EOF

## Summary

- **Total Tests:** $total_tests
- **Passed:** $passed (🟢)
- **Warnings:** $warned (🟡)
- **Failed:** $failed (🔴)
- **Success Rate:** $(echo "scale=1; $passed * 100 / $total_tests" | bc)%

## Performance Analysis

### Response Time Distribution

EOF

# Add response time analysis
for i in "${!TEST_NAMES[@]}"; do
    name="${TEST_NAMES[$i]}"
    time="${RESPONSE_TIMES[$i]}"
    target="${TARGET_TIMES[$i]}"
    ratio=$(echo "scale=2; $time / $target" | bc)

    echo "- **${name}**: ${time}ms (${ratio}x target)" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" << EOF

## System Limitations

This system is deployed with the following limitations:

1. **Single Worker**: FastAPI running with a single worker process
2. **SQLite Database**: Not optimized for concurrent access
3. **Development Environment**: Not production-grade configuration

These tests focus on detecting obvious performance issues rather than stress testing the system.

## Recommendations

EOF

# Add recommendations based on results
if [ $failed -gt 0 ]; then
    cat >> "$REPORT_FILE" << EOF
### Critical Issues ⚠️

The following endpoints exceeded 2x their target response time:

EOF
    for i in "${!TEST_NAMES[@]}"; do
        if [ "${STATUSES[$i]}" = "FAIL" ]; then
            echo "- **${TEST_NAMES[$i]}**: ${RESPONSE_TIMES[$i]}ms (target: ${TARGET_TIMES[$i]}ms)" >> "$REPORT_FILE"
        fi
    done
    echo "" >> "$REPORT_FILE"
fi

if [ $warned -gt 0 ]; then
    cat >> "$REPORT_FILE" << EOF
### Performance Warnings ⚠️

The following endpoints exceeded their target response time:

EOF
    for i in "${!TEST_NAMES[@]}"; do
        if [ "${STATUSES[$i]}" = "WARN" ]; then
            echo "- **${TEST_NAMES[$i]}**: ${RESPONSE_TIMES[$i]}ms (target: ${TARGET_TIMES[$i]}ms)" >> "$REPORT_FILE"
        fi
    done
    echo "" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

### General Recommendations

1. **Database Optimization**
   - Add indexes for frequently queried fields
   - Consider caching for read-heavy endpoints
   - Use query optimization for complex joins

2. **API Response Optimization**
   - Implement response compression (gzip)
   - Use pagination for large result sets
   - Consider lazy loading for related entities

3. **Caching Strategy**
   - Cache device specifications (rarely change)
   - Cache thermal analysis results (expensive computation)
   - Consider Redis for distributed caching

4. **Production Deployment**
   - Use multiple worker processes
   - Consider PostgreSQL instead of SQLite
   - Implement load balancing
   - Use CDN for static assets

## Next Steps

1. Review endpoints that exceeded targets
2. Profile slow endpoints to identify bottlenecks
3. Implement optimization strategies
4. Re-run tests to verify improvements
5. Set up continuous performance monitoring

---
*Generated by HomeRack Performance Test Suite*
EOF

# Print summary
print_color "$BLUE" "\n╔════════════════════════════════════════════════════════════╗"
print_color "$BLUE" "║                  Test Summary                              ║"
print_color "$BLUE" "╚════════════════════════════════════════════════════════════╝"
echo ""
print_color "$GREEN" "Total Tests:  $total_tests"
print_color "$GREEN" "Passed:       $passed"
print_color "$YELLOW" "Warnings:     $warned"
print_color "$RED" "Failed:       $failed"
echo ""
print_color "$BLUE" "Report saved to: $REPORT_FILE"

# Exit with appropriate code
if [ $failed -gt 0 ]; then
    exit 1
elif [ $warned -gt 0 ]; then
    exit 0  # Warnings are acceptable
else
    exit 0
fi
