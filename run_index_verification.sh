#!/bin/bash
# Index Verification Runner Script
#
# This script runs the SQL-based index verification and saves the results.
# It requires PostgreSQL connection credentials.
#
# Usage:
#   ./run_index_verification.sh
#
# Or with custom credentials:
#   DB_USER=myuser DB_NAME=mydb ./run_index_verification.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================================================${NC}"
echo -e "${GREEN}Database Index Performance Verification${NC}"
echo -e "${GREEN}================================================================================${NC}"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql command not found. Please install PostgreSQL client.${NC}"
    exit 1
fi

# Check if verification script exists
if [ ! -f "verify_indexes.sql" ]; then
    echo -e "${RED}Error: verify_indexes.sql not found in current directory.${NC}"
    exit 1
fi

# Default database credentials (can be overridden by environment variables)
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-laserlab_db}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo -e "${YELLOW}Database Connection:${NC}"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Prompt for password if not in .pgpass
echo -e "${YELLOW}Note: You may be prompted for the database password.${NC}"
echo ""

# Output file for results
OUTPUT_FILE="index_verification_results_$(date +%Y%m%d_%H%M%S).txt"

echo -e "${GREEN}Running verification script...${NC}"
echo ""

# Run the verification script
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f verify_indexes.sql > "$OUTPUT_FILE" 2>&1; then
    echo -e "${GREEN}✓ Verification completed successfully!${NC}"
    echo ""
    echo -e "${GREEN}Results saved to: $OUTPUT_FILE${NC}"
    echo ""
    echo -e "${YELLOW}Summary:${NC}"

    # Extract key metrics from output
    if grep -q "total_custom_indexes" "$OUTPUT_FILE"; then
        INDEX_COUNT=$(grep -A1 "total_custom_indexes" "$OUTPUT_FILE" | tail -1 | tr -d ' ')
        echo "  Total Custom Indexes: $INDEX_COUNT"
    fi

    echo ""
    echo -e "${YELLOW}View full results:${NC}"
    echo "  cat $OUTPUT_FILE"
    echo ""
    echo -e "${YELLOW}Search for specific tests:${NC}"
    echo "  grep -A5 'Test 1:' $OUTPUT_FILE"
    echo "  grep 'Index Scan' $OUTPUT_FILE"
    echo "  grep 'Seq Scan' $OUTPUT_FILE"
    echo ""
else
    echo -e "${RED}✗ Verification failed with errors.${NC}"
    echo ""
    echo -e "${RED}Error output saved to: $OUTPUT_FILE${NC}"
    echo ""
    echo -e "${YELLOW}Common issues:${NC}"
    echo "  1. Database not running - Start PostgreSQL service"
    echo "  2. Wrong credentials - Check DB_USER, DB_NAME, DB_HOST"
    echo "  3. Permission denied - Ensure user has SELECT permissions"
    echo "  4. Connection refused - Check DB_HOST and DB_PORT"
    echo ""
    exit 1
fi

echo -e "${GREEN}================================================================================${NC}"
echo -e "${GREEN}Next Steps:${NC}"
echo -e "${GREEN}================================================================================${NC}"
echo ""
echo "1. Review the verification results in $OUTPUT_FILE"
echo "2. Check that all 37 indexes are listed"
echo "3. Verify forced index tests show 'Index Scan using...'"
echo "4. Re-run this script after data accumulates (1,000+ rows)"
echo "5. Monitor index usage monthly using pg_stat_user_indexes"
echo ""
echo -e "${GREEN}For production monitoring, see:${NC}"
echo "  doc/index_performance_verification_report.md"
echo ""
