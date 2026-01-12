#!/bin/bash
# Master script to run all performance and load tests

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")/backend"
OUTPUT_DIR="${SCRIPT_DIR}/reports"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Print banner
clear
print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
print_color "$CYAN" "║                                                              ║"
print_color "$CYAN" "║       HomeRack Performance & Load Test Suite                 ║"
print_color "$CYAN" "║                                                              ║"
print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if server is running
print_color "$BLUE" "Checking if server is running..."
if ! curl -s -f http://lampadas.local:8080/api/racks/ > /dev/null 2>&1; then
    print_color "$RED" "ERROR: Server not reachable at http://lampadas.local:8080"
    print_color "$YELLOW" "Please start the server before running tests."
    exit 1
fi
print_color "$GREEN" "✓ Server is running"
echo ""

# Test counters
total_test_suites=0
passed_test_suites=0
failed_test_suites=0

# Run Python performance benchmarks
print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
print_color "$CYAN" "║  1. Python Performance Benchmarks                            ║"
print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
echo ""
((total_test_suites++))

cd "$BACKEND_DIR"
if python3 -m pytest tests/performance/test_benchmarks.py -v --tb=short 2>&1 | tee "${OUTPUT_DIR}/pytest_output.log"; then
    print_color "$GREEN" "✓ Python benchmarks passed"
    ((passed_test_suites++))
else
    print_color "$RED" "✗ Python benchmarks failed"
    ((failed_test_suites++))
fi
echo ""

# Run shell-based performance tests
print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
print_color "$CYAN" "║  2. API Response Time Benchmarks                             ║"
print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
echo ""
((total_test_suites++))

if bash "${SCRIPT_DIR}/performance_test.sh"; then
    print_color "$GREEN" "✓ Performance tests passed"
    ((passed_test_suites++))
else
    print_color "$RED" "✗ Performance tests failed"
    ((failed_test_suites++))
fi
echo ""

# Run load tests
print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
print_color "$CYAN" "║  3. Light Load Tests                                         ║"
print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
echo ""
((total_test_suites++))

if bash "${SCRIPT_DIR}/load_test.sh"; then
    print_color "$GREEN" "✓ Load tests passed"
    ((passed_test_suites++))
else
    print_color "$RED" "✗ Load tests failed"
    ((failed_test_suites++))
fi
echo ""

# Summary
print_color "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
print_color "$CYAN" "║                    Test Summary                              ║"
print_color "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
echo ""
print_color "$BLUE" "Total test suites:    $total_test_suites"
print_color "$GREEN" "Passed:               $passed_test_suites"
print_color "$RED" "Failed:               $failed_test_suites"
echo ""

# List generated reports
print_color "$BLUE" "Generated reports:"
ls -1 "${OUTPUT_DIR}"/*.md 2>/dev/null | while read report; do
    print_color "$BLUE" "  - $(basename "$report")"
done
echo ""

# Generate summary report
SUMMARY_FILE="${OUTPUT_DIR}/test_summary_$(date +%Y%m%d_%H%M%S).md"

cat > "$SUMMARY_FILE" << EOF
# HomeRack Performance Test Summary

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')

## Test Execution Summary

| Test Suite | Status |
|------------|--------|
| Python Performance Benchmarks | $([ $passed_test_suites -ge 1 ] && echo "✅ PASS" || echo "❌ FAIL") |
| API Response Time Benchmarks | $([ $passed_test_suites -ge 2 ] && echo "✅ PASS" || echo "❌ FAIL") |
| Light Load Tests | $([ $passed_test_suites -ge 3 ] && echo "✅ PASS" || echo "❌ FAIL") |

## Statistics

- **Total Test Suites:** $total_test_suites
- **Passed:** $passed_test_suites
- **Failed:** $failed_test_suites
- **Success Rate:** $(echo "scale=1; $passed_test_suites * 100 / $total_test_suites" | bc)%

## Individual Reports

EOF

# Link to individual reports
for report in "${OUTPUT_DIR}"/*_report_*.md; do
    if [ -f "$report" ]; then
        echo "- [$(basename "$report")](./$(basename "$report"))" >> "$SUMMARY_FILE"
    fi
done

cat >> "$SUMMARY_FILE" << EOF

## Python Benchmark Output

\`\`\`
$(tail -30 "${OUTPUT_DIR}/pytest_output.log" 2>/dev/null || echo "No output available")
\`\`\`

## System Information

- **Target:** http://lampadas.local:8080
- **Deployment:** Single-worker FastAPI
- **Database:** SQLite
- **Test Date:** $(date '+%Y-%m-%d %H:%M:%S')

## Notes

These tests are designed for a development/single-user deployment:
- Single worker process (not production-grade)
- SQLite database (not optimized for concurrency)
- Light load testing (not stress testing)

## Next Steps

EOF

if [ $failed_test_suites -gt 0 ]; then
    cat >> "$SUMMARY_FILE" << EOF
1. ⚠️ Review failed test suites
2. Investigate performance bottlenecks
3. Optimize slow endpoints
4. Re-run tests to verify improvements
EOF
else
    cat >> "$SUMMARY_FILE" << EOF
1. ✅ All tests passed!
2. Monitor performance in production
3. Set up continuous performance testing
4. Consider additional optimization as needed
EOF
fi

cat >> "$SUMMARY_FILE" << EOF

---
*Generated by HomeRack Performance Test Suite*
EOF

print_color "$BLUE" "Summary report saved to: $(basename "$SUMMARY_FILE")"
echo ""

# Final result
if [ $failed_test_suites -eq 0 ]; then
    print_color "$GREEN" "╔══════════════════════════════════════════════════════════════╗"
    print_color "$GREEN" "║                 ✓ ALL TESTS PASSED                           ║"
    print_color "$GREEN" "╚══════════════════════════════════════════════════════════════╝"
    exit 0
else
    print_color "$RED" "╔══════════════════════════════════════════════════════════════╗"
    print_color "$RED" "║              ✗ SOME TESTS FAILED                             ║"
    print_color "$RED" "╚══════════════════════════════════════════════════════════════╝"
    print_color "$YELLOW" "Review the reports in ${OUTPUT_DIR}/"
    exit 1
fi
