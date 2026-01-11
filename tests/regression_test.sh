#!/bin/bash

# HomeRack v1.0.1 - Final Comprehensive Regression Test Suite
# Tests all critical API endpoints with proper response validation

BASE_URL="http://lampadas.local"
PASS=0
FAIL=0
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║        HomeRack v1.0.1 - Final Regression Test Suite                 ║"
echo "║        $TIMESTAMP                                          ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Test HTTP endpoint
test_http() {
    local name="$1"
    local url="$2"
    local expected_code="$3"

    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1)

    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $name (HTTP $http_code)"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $name (Expected $expected_code, got $http_code)"
        ((FAIL++))
        return 1
    fi
}

# Test JSON response
test_json() {
    local name="$1"
    local url="$2"
    local jq_filter="$3"
    local desc="$4"

    response=$(curl -s "$url" 2>&1)
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1)

    if [ "$http_code" = "200" ]; then
        if echo "$response" | jq -e "$jq_filter" > /dev/null 2>&1; then
            result=$(echo "$response" | jq -r "$jq_filter" 2>/dev/null)
            echo -e "${GREEN}✅ PASS${NC}: $name → $desc: $result"
            ((PASS++))
            return 0
        else
            echo -e "${RED}❌ FAIL${NC}: $name (Response validation failed)"
            ((FAIL++))
            return 1
        fi
    else
        echo -e "${RED}❌ FAIL${NC}: $name (HTTP $http_code)"
        ((FAIL++))
        return 1
    fi
}

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}📦 FRONTEND DEPLOYMENT TESTS${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
test_http "Frontend HTML page" "$BASE_URL/" "200"
test_http "Frontend JavaScript bundle" "$BASE_URL/assets/index-DivnFuvK.js" "200"
test_http "Frontend CSS bundle" "$BASE_URL/assets/index-BHw5A44q.css" "200"
echo ""

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}🏥 API HEALTH & CORE TESTS${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
test_json "Basic health check" "$BASE_URL/api/health" '.status' "status"
test_json "API version check" "$BASE_URL/api/health" '.version' "version"
test_json "Environment check" "$BASE_URL/api/health" '.environment' "environment"
echo ""

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}🗄️  RACKS API TESTS${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
test_json "List all racks (collection)" "$BASE_URL/api/racks/" 'length' "count"
test_json "Get rack #1 (individual)" "$BASE_URL/api/racks/1" '.name' "name"
test_json "Get rack #1 ID" "$BASE_URL/api/racks/1" '.id' "id"
test_json "Get rack #1 layout" "$BASE_URL/api/racks/1/layout" '.rack.id' "rack_id"
test_json "Get rack layout positions" "$BASE_URL/api/racks/1/layout" '.positions | length' "positions_count"
test_json "Get rack thermal analysis" "$BASE_URL/api/racks/1/thermal-analysis" '.rack_id' "rack_id"
test_json "Get rack thermal total power" "$BASE_URL/api/racks/1/thermal-analysis" '.heat_distribution.total_power_watts' "total_power"
echo ""

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}💾 DEVICES API TESTS${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
test_json "List all devices (collection)" "$BASE_URL/api/devices/" 'length' "count"
test_json "Get device #1 (individual)" "$BASE_URL/api/devices/1" '.custom_name' "name"
test_json "Get device #1 ID" "$BASE_URL/api/devices/1" '.id' "id"
test_json "Get device #1 specification" "$BASE_URL/api/devices/1" '.specification.brand' "spec_brand"
echo ""

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}📋 DEVICE SPECIFICATIONS API TESTS${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
test_json "List all device specs" "$BASE_URL/api/device-specs/" 'length' "count"
test_json "Get device spec #1" "$BASE_URL/api/device-specs/1" '.brand' "brand"
test_json "Get device spec #1 model" "$BASE_URL/api/device-specs/1" '.model' "model"
test_json "Search device specs (Cisco)" "$BASE_URL/api/device-specs/search?q=Cisco" 'length' "results_count"
test_http "Get supported manufacturers" "$BASE_URL/api/device-specs/fetch/supported-manufacturers" "200"
echo ""

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}🔌 CONNECTIONS API TESTS${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
test_json "List all connections" "$BASE_URL/api/connections/" 'length' "count"
echo ""

echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "${BLUE}📊 FINAL SUMMARY${NC}"
echo "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
TOTAL=$((PASS + FAIL))
SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($PASS / $TOTAL) * 100}")

echo ""
echo "Test Date:       $TIMESTAMP"
echo "Total Tests:     $TOTAL"
echo -e "Passed:          ${GREEN}$PASS ✅${NC}"
echo -e "Failed:          ${RED}$FAIL ❌${NC}"
echo "Success Rate:    $SUCCESS_RATE%"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo -e "║           ${GREEN}✅ ALL TESTS PASSED - DEPLOYMENT SUCCESSFUL${NC}                 ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo -e "║           ${YELLOW}⚠️  $FAIL TEST(S) FAILED - REVIEW REQUIRED${NC}                     ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    exit 1
fi
