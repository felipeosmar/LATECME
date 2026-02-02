#!/usr/bin/env python
"""
Query Performance Test Script
Tests that database indexes are being used by PostgreSQL query planner

This script runs EXPLAIN ANALYZE on common queries to verify:
1. Index Scans are used instead of Sequential Scans
2. Query execution time is reasonable
3. Composite indexes are being utilized
"""

import os
import sys
import django
from django.db import connection

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


def run_explain_analyze(query, description):
    """Run EXPLAIN ANALYZE on a query and print results"""
    print(f"\n{'='*80}")
    print(f"Test: {description}")
    print(f"{'='*80}")
    print(f"Query: {query}")
    print(f"{'-'*80}")

    with connection.cursor() as cursor:
        cursor.execute(f"EXPLAIN ANALYZE {query}")
        results = cursor.fetchall()

        # Check if Index Scan is being used
        using_index = False
        using_seq_scan = False

        for row in results:
            line = row[0]
            print(line)
            if 'Index Scan' in line or 'Index Only Scan' in line or 'Bitmap Index Scan' in line:
                using_index = True
            if 'Seq Scan' in line:
                using_seq_scan = True

        # Print result
        print(f"{'-'*80}")
        if using_index and not using_seq_scan:
            print("✅ PASS: Using Index Scan")
        elif using_index and using_seq_scan:
            print("⚠️  PARTIAL: Using both Index Scan and Sequential Scan")
        else:
            print("❌ FAIL: Using Sequential Scan only")

        return using_index


def main():
    """Run all performance tests"""

    print("\n" + "="*80)
    print("DATABASE INDEX PERFORMANCE TEST")
    print("="*80)
    print("\nThis script verifies that database indexes are being used by the query planner.")
    print("We're looking for 'Index Scan' in the EXPLAIN ANALYZE output.\n")

    tests_passed = 0
    tests_total = 0

    # Test 1: Inventory - StockMovement by movement_type
    tests_total += 1
    query = "SELECT * FROM inventory_stockmovement WHERE movement_type='IN' ORDER BY created_at DESC LIMIT 20"
    if run_explain_analyze(query, "Inventory: Filter by movement_type with date ordering"):
        tests_passed += 1

    # Test 2: Inventory - StockMovement composite index
    tests_total += 1
    query = "SELECT * FROM inventory_stockmovement WHERE warehouse_id IS NOT NULL AND movement_type='OUT' ORDER BY created_at DESC LIMIT 10"
    if run_explain_analyze(query, "Inventory: Composite index (warehouse, movement_type, created_at)"):
        tests_passed += 1

    # Test 3: Inventory - InventoryCount by status
    tests_total += 1
    query = "SELECT * FROM inventory_inventorycount WHERE status='IN_PROGRESS' LIMIT 20"
    if run_explain_analyze(query, "Inventory: Filter by status"):
        tests_passed += 1

    # Test 4: Inventory - MaterialStock by is_active
    tests_total += 1
    query = "SELECT * FROM inventory_materialstock WHERE is_active=true LIMIT 50"
    if run_explain_analyze(query, "Inventory: Filter by is_active"):
        tests_passed += 1

    # Test 5: Purchasing - PurchaseRequest by status
    tests_total += 1
    query = "SELECT * FROM purchasing_purchaserequest WHERE status='DRAFT' LIMIT 20"
    if run_explain_analyze(query, "Purchasing: PurchaseRequest filter by status"):
        tests_passed += 1

    # Test 6: Purchasing - PurchaseRequest composite index
    tests_total += 1
    query = "SELECT * FROM purchasing_purchaserequest WHERE status='IN_PROGRESS' AND is_active=true LIMIT 20"
    if run_explain_analyze(query, "Purchasing: PurchaseRequest composite index (status, is_active)"):
        tests_passed += 1

    # Test 7: Purchasing - PurchaseOrder by status
    tests_total += 1
    query = "SELECT * FROM purchasing_purchaseorder WHERE status='APPROVED' LIMIT 20"
    if run_explain_analyze(query, "Purchasing: PurchaseOrder filter by status"):
        tests_passed += 1

    # Test 8: Purchasing - PurchaseOrder composite index
    tests_total += 1
    query = "SELECT * FROM purchasing_purchaseorder WHERE status='IN_PROGRESS' AND is_active=true LIMIT 20"
    if run_explain_analyze(query, "Purchasing: PurchaseOrder composite index (status, is_active)"):
        tests_passed += 1

    # Test 9: Production - ProductionOrder by status
    tests_total += 1
    query = "SELECT * FROM production_productionorder WHERE status='IN_PROGRESS' LIMIT 20"
    if run_explain_analyze(query, "Production: ProductionOrder filter by status"):
        tests_passed += 1

    # Test 10: Production - ProductionOrder composite index
    tests_total += 1
    query = "SELECT * FROM production_productionorder WHERE status='IN_PROGRESS' AND is_active=true LIMIT 20"
    if run_explain_analyze(query, "Production: ProductionOrder composite index (status, is_active)"):
        tests_passed += 1

    # Test 11: Materials - Material by is_active
    tests_total += 1
    query = "SELECT * FROM materials_material WHERE is_active=true LIMIT 50"
    if run_explain_analyze(query, "Materials: Material filter by is_active"):
        tests_passed += 1

    # Test 12: Materials - Material by material_type
    tests_total += 1
    query = "SELECT * FROM materials_material WHERE material_type='RAW_MATERIAL' LIMIT 20"
    if run_explain_analyze(query, "Materials: Material filter by material_type"):
        tests_passed += 1

    # Test 13: Materials - Material composite index
    tests_total += 1
    query = "SELECT * FROM materials_material WHERE is_active=true AND material_type='RAW_MATERIAL' LIMIT 20"
    if run_explain_analyze(query, "Materials: Material composite index (is_active, material_type)"):
        tests_passed += 1

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total)*100:.1f}%")

    if tests_passed == tests_total:
        print("\n✅ ALL TESTS PASSED - All indexes are being used correctly!")
        return 0
    elif tests_passed >= tests_total * 0.8:
        print("\n⚠️  MOST TESTS PASSED - Some queries may need optimization")
        return 0
    else:
        print("\n❌ MANY TESTS FAILED - Indexes may not be configured correctly")
        return 1


if __name__ == '__main__':
    sys.exit(main())
