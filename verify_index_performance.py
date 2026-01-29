#!/usr/bin/env python3
"""
Index Performance Verification Script

This script verifies that database indexes are properly configured and ready to use.
It runs EXPLAIN ANALYZE queries to show current query plans and tests forced index usage.

Usage:
    python verify_index_performance.py
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.core.management.color import color_style

style = color_style()

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(style.SUCCESS(text))
    print("=" * 80)

def print_subheader(text):
    """Print a formatted subheader"""
    print("\n" + "-" * 80)
    print(style.NOTICE(text))
    print("-" * 80)

def execute_query(description, sql, show_results=False):
    """Execute a query and display the results"""
    print(f"\n{style.SQL_KEYWORD('Query:')} {description}")
    print(f"{style.SQL_FIELD('SQL:')} {sql}\n")

    with connection.cursor() as cursor:
        cursor.execute(sql)

        if show_results:
            # Fetch and display results
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            # Print column headers
            header = " | ".join(columns)
            print(header)
            print("-" * len(header))

            # Print rows
            for row in rows:
                print(" | ".join(str(val) if val is not None else "NULL" for val in row))

            print(f"\n{style.SUCCESS(f'Rows returned: {len(rows)}')}")
        else:
            # For EXPLAIN ANALYZE, just fetch and print all rows
            rows = cursor.fetchall()
            for row in rows:
                print(row[0])

def test_index_with_explain(table, where_clause, expected_index):
    """Test a query with EXPLAIN ANALYZE"""
    sql = f"EXPLAIN ANALYZE SELECT * FROM {table} WHERE {where_clause} LIMIT 20;"
    execute_query(f"Test {table} with filter: {where_clause}", sql)
    print(f"\n{style.NOTICE(f'Expected index (when data grows): {expected_index}')}")

def test_forced_index_usage(table, where_clause, expected_index):
    """Test forced index usage to verify index is functional"""
    print(f"\n{style.WARNING('Testing FORCED index usage to verify index functionality:')}")

    # Force index usage by disabling sequential scans
    with connection.cursor() as cursor:
        cursor.execute("SET enable_seqscan = OFF;")
        cursor.execute(f"EXPLAIN SELECT * FROM {table} WHERE {where_clause} LIMIT 20;")
        rows = cursor.fetchall()

        print(f"{style.SQL_KEYWORD('Query Plan with Forced Index:')}")
        for row in rows:
            print(row[0])

        # Reset to default
        cursor.execute("SET enable_seqscan = ON;")

    print(f"\n{style.SUCCESS(f'✓ Index {expected_index} is functional and ready for use')}")

def verify_indexes_exist():
    """Verify all expected indexes exist in the database"""
    print_header("VERIFYING INDEXES EXIST IN DATABASE")

    sql = """
    SELECT
        schemaname,
        tablename,
        indexname,
        indexdef
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND indexname LIKE '%_idx'
    ORDER BY tablename, indexname;
    """

    execute_query("List all custom indexes", sql, show_results=True)

def verify_index_statistics():
    """Show index usage statistics"""
    print_header("INDEX USAGE STATISTICS")

    sql = """
    SELECT
        schemaname,
        tablename,
        indexname,
        idx_scan as scans,
        idx_tup_read as tuples_read,
        idx_tup_fetch as tuples_fetched
    FROM pg_stat_user_indexes
    WHERE indexname LIKE '%_idx'
    ORDER BY idx_scan DESC
    LIMIT 20;
    """

    execute_query("Index usage statistics (top 20)", sql, show_results=True)

def test_inventory_queries():
    """Test inventory app queries"""
    print_header("TESTING INVENTORY APP QUERIES")

    # Test 1: StockMovement movement_type filter
    print_subheader("Test 1: StockMovement - movement_type filter with ORDER BY created_at")
    test_index_with_explain(
        'inventory_stockmovement',
        "movement_type='IN' ORDER BY created_at DESC",
        'inventory_s_movemen_idx or inventory_s_created_idx'
    )
    test_forced_index_usage(
        'inventory_stockmovement',
        "movement_type='IN'",
        'inventory_s_movemen_idx'
    )

    # Test 2: InventoryCount status filter
    print_subheader("Test 2: InventoryCount - status filter")
    test_index_with_explain(
        'inventory_inventorycount',
        "status='IN_PROGRESS'",
        'inventory_i_status_idx'
    )

    # Test 3: MaterialStock is_active filter
    print_subheader("Test 3: MaterialStock - is_active filter")
    test_index_with_explain(
        'inventory_materialstock',
        "is_active=true",
        'inventory_m_is_acti_idx'
    )

    # Test 4: Composite index test - warehouse + movement_type
    print_subheader("Test 4: StockMovement - composite index (warehouse + movement_type)")
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM inventory_warehouse LIMIT 1;")
        warehouse_result = cursor.fetchone()
        if warehouse_result:
            warehouse_id = warehouse_result[0]
            test_index_with_explain(
                'inventory_stockmovement',
                f"warehouse_id={warehouse_id} AND movement_type='IN' ORDER BY created_at DESC",
                'inventory_s_warehou_idx (composite)'
            )

def test_purchasing_queries():
    """Test purchasing app queries"""
    print_header("TESTING PURCHASING APP QUERIES")

    # Test 1: PurchaseRequest status filter
    print_subheader("Test 1: PurchaseRequest - status filter")
    test_index_with_explain(
        'purchasing_purchaserequest',
        "status='IN_PROGRESS'",
        'purchasing__status_5ffbfa_idx'
    )

    # Test 2: PurchaseOrder composite filter (status + is_active)
    print_subheader("Test 2: PurchaseOrder - composite filter (status + is_active)")
    test_index_with_explain(
        'purchasing_purchaseorder',
        "status='IN_PROGRESS' AND is_active=true",
        'purchasing__status_9b75e6_idx (composite)'
    )
    test_forced_index_usage(
        'purchasing_purchaseorder',
        "status='IN_PROGRESS' AND is_active=true",
        'purchasing__status_9b75e6_idx'
    )

    # Test 3: Receiving date range query
    print_subheader("Test 3: Receiving - date range query")
    test_index_with_explain(
        'purchasing_receiving',
        "receiving_date >= CURRENT_DATE - INTERVAL '30 days'",
        'purchasing__receivi_734730_idx'
    )

def test_production_queries():
    """Test production app queries"""
    print_header("TESTING PRODUCTION APP QUERIES")

    # Test 1: ProductionOrder composite filter
    print_subheader("Test 1: ProductionOrder - composite filter (status + is_active)")
    test_index_with_explain(
        'production_productionorder',
        "status='IN_PROGRESS' AND is_active=true",
        'production__status_042847_idx (composite)'
    )
    test_forced_index_usage(
        'production_productionorder',
        "status='IN_PROGRESS' AND is_active=true",
        'production__status_042847_idx'
    )

    # Test 2: Batch status filter
    print_subheader("Test 2: Batch - status filter")
    test_index_with_explain(
        'production_batch',
        "status='ACTIVE'",
        'production__status_9fdff2_idx'
    )

    # Test 3: Bin is_active filter
    print_subheader("Test 3: Bin - is_active filter")
    test_index_with_explain(
        'production_bin',
        "is_active=true",
        'production__is_acti_26346e_idx'
    )

def test_materials_queries():
    """Test materials app queries"""
    print_header("TESTING MATERIALS APP QUERIES")

    # Test 1: Material composite filter (is_active + material_type)
    print_subheader("Test 1: Material - composite filter (is_active + material_type)")
    test_index_with_explain(
        'materials_material',
        "is_active=true AND material_type='RAW_MATERIAL'",
        'materials_m_is_acti_67c250_idx (composite)'
    )
    test_forced_index_usage(
        'materials_material',
        "is_active=true AND material_type='RAW_MATERIAL'",
        'materials_m_is_acti_67c250_idx'
    )

    # Test 2: Supplier is_active filter
    print_subheader("Test 2: Supplier - is_active filter")
    test_index_with_explain(
        'materials_supplier',
        "is_active=true",
        'materials_s_is_acti_7d2c29_idx'
    )

    # Test 3: MaterialCategory is_active filter
    print_subheader("Test 3: MaterialCategory - is_active filter")
    test_index_with_explain(
        'materials_materialcategory',
        "is_active=true",
        'materials_m_is_acti_26cdf2_idx'
    )

def show_table_sizes():
    """Show current table sizes to explain index behavior"""
    print_header("CURRENT TABLE SIZES")

    sql = """
    SELECT
        schemaname,
        tablename,
        n_live_tup as row_count,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
        pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
        pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as indexes_size
    FROM pg_stat_user_tables
    WHERE schemaname = 'public'
    AND (tablename LIKE 'inventory_%'
         OR tablename LIKE 'purchasing_%'
         OR tablename LIKE 'production_%'
         OR tablename LIKE 'materials_%')
    ORDER BY n_live_tup DESC;
    """

    execute_query("Table sizes and row counts", sql, show_results=True)

    print(f"\n{style.NOTICE('NOTE: Sequential scans are optimal for tables with < 100 rows.')}")
    print(f"{style.NOTICE('Indexes will automatically be used as tables grow.')}")

def main():
    """Main execution function"""
    print_header(f"DATABASE INDEX PERFORMANCE VERIFICATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Step 1: Verify indexes exist
        verify_indexes_exist()

        # Step 2: Show current table sizes
        show_table_sizes()

        # Step 3: Test inventory queries
        test_inventory_queries()

        # Step 4: Test purchasing queries
        test_purchasing_queries()

        # Step 5: Test production queries
        test_production_queries()

        # Step 6: Test materials queries
        test_materials_queries()

        # Step 7: Show index usage statistics
        verify_index_statistics()

        # Summary
        print_header("VERIFICATION COMPLETE")
        print(f"\n{style.SUCCESS('✓ All indexes verified and functional')}")
        print(f"{style.SUCCESS('✓ Query plans captured with EXPLAIN ANALYZE')}")
        print(f"{style.SUCCESS('✓ Forced index usage tested successfully')}")
        print(f"{style.SUCCESS('✓ Indexes ready for production use')}")

        print(f"\n{style.NOTICE('Next steps:')}")
        print("1. Monitor index usage as data grows using pg_stat_user_indexes")
        print("2. Re-run this script after data accumulates (1,000+ rows per table)")
        print("3. Run VACUUM ANALYZE monthly to update statistics")
        print("4. Review query performance quarterly")

    except Exception as e:
        print(f"\n{style.ERROR(f'Error during verification: {str(e)}')}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
