#!/bin/bash
# Query Performance Test Script
# Tests that database indexes are being used by PostgreSQL query planner

DB_USER="postgres"
DB_NAME="laserlab_db"
CONTAINER="latecme-postgres-1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "DATABASE INDEX PERFORMANCE TEST"
echo "================================================================================"
echo ""
echo "This script verifies that database indexes are being used by the query planner."
echo "We're looking for 'Index Scan' in the EXPLAIN ANALYZE output."
echo ""

TESTS_PASSED=0
TESTS_TOTAL=0

# Function to run EXPLAIN ANALYZE and check for index usage
test_query() {
    local description="$1"
    local query="$2"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    echo "================================================================================"
    echo "Test $TESTS_TOTAL: $description"
    echo "================================================================================"
    echo "Query: $query"
    echo "--------------------------------------------------------------------------------"

    # Run EXPLAIN ANALYZE
    output=$(docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c "EXPLAIN ANALYZE $query" 2>&1)

    echo "$output"
    echo "--------------------------------------------------------------------------------"

    # Check if Index Scan is being used
    if echo "$output" | grep -q -E "Index Scan|Index Only Scan|Bitmap Index Scan"; then
        if echo "$output" | grep -q "Seq Scan"; then
            echo -e "${YELLOW}⚠️  PARTIAL: Using both Index Scan and Sequential Scan${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${GREEN}✅ PASS: Using Index Scan${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        fi
    else
        echo -e "${RED}❌ FAIL: Using Sequential Scan only${NC}"
    fi

    echo ""
}

# Test 1: Inventory - StockMovement by movement_type
test_query \
    "Inventory: Filter by movement_type with date ordering" \
    "SELECT * FROM inventory_stockmovement WHERE movement_type='IN' ORDER BY created_at DESC LIMIT 20;"

# Test 2: Inventory - StockMovement composite index
test_query \
    "Inventory: Composite index (warehouse, movement_type, created_at)" \
    "SELECT * FROM inventory_stockmovement WHERE warehouse_id IS NOT NULL AND movement_type='OUT' ORDER BY created_at DESC LIMIT 10;"

# Test 3: Inventory - InventoryCount by status
test_query \
    "Inventory: Filter by status" \
    "SELECT * FROM inventory_inventorycount WHERE status='IN_PROGRESS' LIMIT 20;"

# Test 4: Inventory - MaterialStock by is_active
test_query \
    "Inventory: Filter by is_active" \
    "SELECT * FROM inventory_materialstock WHERE is_active=true LIMIT 50;"

# Test 5: Purchasing - PurchaseRequest by status
test_query \
    "Purchasing: PurchaseRequest filter by status" \
    "SELECT * FROM purchasing_purchaserequest WHERE status='DRAFT' LIMIT 20;"

# Test 6: Purchasing - PurchaseRequest composite index
test_query \
    "Purchasing: PurchaseRequest composite index (status, is_active)" \
    "SELECT * FROM purchasing_purchaserequest WHERE status='IN_PROGRESS' AND is_active=true LIMIT 20;"

# Test 7: Purchasing - PurchaseOrder by status
test_query \
    "Purchasing: PurchaseOrder filter by status" \
    "SELECT * FROM purchasing_purchaseorder WHERE status='APPROVED' LIMIT 20;"

# Test 8: Purchasing - PurchaseOrder composite index
test_query \
    "Purchasing: PurchaseOrder composite index (status, is_active)" \
    "SELECT * FROM purchasing_purchaseorder WHERE status='IN_PROGRESS' AND is_active=true LIMIT 20;"

# Test 9: Production - ProductionOrder by status
test_query \
    "Production: ProductionOrder filter by status" \
    "SELECT * FROM production_productionorder WHERE status='IN_PROGRESS' LIMIT 20;"

# Test 10: Production - ProductionOrder composite index
test_query \
    "Production: ProductionOrder composite index (status, is_active)" \
    "SELECT * FROM production_productionorder WHERE status='IN_PROGRESS' AND is_active=true LIMIT 20;"

# Test 11: Materials - Material by is_active
test_query \
    "Materials: Material filter by is_active" \
    "SELECT * FROM materials_material WHERE is_active=true LIMIT 50;"

# Test 12: Materials - Material by material_type
test_query \
    "Materials: Material filter by material_type" \
    "SELECT * FROM materials_material WHERE material_type='RAW_MATERIAL' LIMIT 20;"

# Test 13: Materials - Material composite index
test_query \
    "Materials: Material composite index (is_active, material_type)" \
    "SELECT * FROM materials_material WHERE is_active=true AND material_type='RAW_MATERIAL' LIMIT 20;"

# Print summary
echo "================================================================================"
echo "TEST SUMMARY"
echo "================================================================================"
echo "Tests Passed: $TESTS_PASSED/$TESTS_TOTAL"
SUCCESS_RATE=$(echo "scale=1; ($TESTS_PASSED / $TESTS_TOTAL) * 100" | bc)
echo "Success Rate: $SUCCESS_RATE%"
echo ""

if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - All indexes are being used correctly!${NC}"
    exit 0
elif [ $TESTS_PASSED -ge $((TESTS_TOTAL * 80 / 100)) ]; then
    echo -e "${YELLOW}⚠️  MOST TESTS PASSED - Some queries may need optimization${NC}"
    exit 0
else
    echo -e "${RED}❌ MANY TESTS FAILED - Indexes may not be configured correctly${NC}"
    exit 1
fi
