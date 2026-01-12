#!/bin/bash
#
# HomeRack Test Runner Script
# Runs the comprehensive test suite with various options
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if pytest is installed
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest is not installed"
        print_info "Install with: pip install -r requirements-test.txt"
        exit 1
    fi
}

# Function to print usage
usage() {
    cat << EOF
HomeRack Test Runner

Usage: ./run_tests.sh [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -a, --all               Run all tests (default)
    -u, --unit              Run only unit tests
    -b, --business          Run only business logic tests
    -c, --coverage          Run with coverage report
    -v, --verbose           Run with verbose output
    -f, --fast              Run in parallel (fast mode)
    -s, --specific FILE     Run specific test file
    --failed                Run only previously failed tests

EXAMPLES:
    ./run_tests.sh                          # Run all tests
    ./run_tests.sh --unit --verbose         # Run unit tests with verbose output
    ./run_tests.sh --coverage               # Run with coverage report
    ./run_tests.sh --specific test_racks    # Run specific test file
    ./run_tests.sh --fast                   # Run tests in parallel

EOF
}

# Default options
RUN_ALL=true
RUN_UNIT=false
RUN_BUSINESS=false
COVERAGE=false
VERBOSE=""
PARALLEL=false
SPECIFIC=""
FAILED_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -a|--all)
            RUN_ALL=true
            shift
            ;;
        -u|--unit)
            RUN_ALL=false
            RUN_UNIT=true
            shift
            ;;
        -b|--business)
            RUN_ALL=false
            RUN_BUSINESS=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE="-vv"
            shift
            ;;
        -f|--fast)
            PARALLEL=true
            shift
            ;;
        -s|--specific)
            RUN_ALL=false
            SPECIFIC="$2"
            shift 2
            ;;
        --failed)
            FAILED_ONLY=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check prerequisites
check_pytest

# Set PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Build pytest command
PYTEST_CMD="pytest"

# Add verbosity
if [ -n "$VERBOSE" ]; then
    PYTEST_CMD="$PYTEST_CMD $VERBOSE"
fi

# Add parallel execution
if [ "$PARALLEL" = true ]; then
    if command -v pytest-xdist &> /dev/null; then
        PYTEST_CMD="$PYTEST_CMD -n auto"
        print_info "Running tests in parallel mode"
    else
        print_warning "pytest-xdist not installed, running sequentially"
        print_info "Install with: pip install pytest-xdist"
    fi
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=html --cov-report=term-missing"
    print_info "Coverage report will be generated"
fi

# Add failed only
if [ "$FAILED_ONLY" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --lf"
    print_info "Running only previously failed tests"
fi

# Determine what to run
if [ "$RUN_ALL" = true ]; then
    print_info "Running all tests..."
    TEST_PATH="tests/"
elif [ "$RUN_UNIT" = true ]; then
    print_info "Running unit tests..."
    TEST_PATH="tests/unit/"
elif [ "$RUN_BUSINESS" = true ]; then
    print_info "Running business logic tests..."
    TEST_PATH="tests/business_logic/"
elif [ -n "$SPECIFIC" ]; then
    print_info "Running specific test: $SPECIFIC"
    # Find test file matching the pattern
    TEST_PATH=$(find tests -name "*${SPECIFIC}*.py" | head -1)
    if [ -z "$TEST_PATH" ]; then
        print_error "Test file matching '$SPECIFIC' not found"
        exit 1
    fi
    print_info "Found test file: $TEST_PATH"
else
    print_error "No test selection specified"
    exit 1
fi

# Run tests
print_info "Executing: $PYTEST_CMD $TEST_PATH"
echo ""

$PYTEST_CMD $TEST_PATH

# Capture exit code
EXIT_CODE=$?

# Print summary
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    print_info "All tests passed! ✓"
else
    print_error "Some tests failed! ✗"
fi

# Show coverage report location if generated
if [ "$COVERAGE" = true ] && [ $EXIT_CODE -eq 0 ]; then
    print_info "Coverage report: htmlcov/index.html"
    print_info "Open with: open htmlcov/index.html (macOS) or xdg-open htmlcov/index.html (Linux)"
fi

exit $EXIT_CODE
