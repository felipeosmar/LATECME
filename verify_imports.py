#!/usr/bin/env python
"""Verification script to test all view imports after refactoring."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Test all view imports from the new structure
try:
    from apps.inventory.views import (
        # Stock views
        dashboard, stock_list, stock_detail, reports,
        # Movement views
        movements_list, create_movement,
        # Warehouse views
        warehouse_list, warehouse_detail, warehouse_create,
        warehouse_update, api_warehouses,
        # Reservation views
        reservations_list, reservation_detail, reservation_create,
        reservation_update, reservation_cancel, api_materials_with_stock,
        api_stock_info,
        # Count views
        inventory_count_list, inventory_count_detail, inventory_count_create,
        inventory_count_start, inventory_count_save_items, inventory_count_complete,
        inventory_count_cancel, inventory_count_generate_adjustments,
    )

    print("✅ All 25 view functions import successfully")
    print("\nStock views (4):", dashboard.__name__, stock_list.__name__, stock_detail.__name__, reports.__name__)
    print("Movement views (2):", movements_list.__name__, create_movement.__name__)
    print("Warehouse views (5):", warehouse_list.__name__, warehouse_detail.__name__, warehouse_create.__name__, warehouse_update.__name__, api_warehouses.__name__)
    print("Reservation views (7):", reservations_list.__name__, reservation_detail.__name__, reservation_create.__name__, reservation_update.__name__, reservation_cancel.__name__, api_materials_with_stock.__name__, api_stock_info.__name__)
    print("Count views (8):", inventory_count_list.__name__, inventory_count_detail.__name__, inventory_count_create.__name__, inventory_count_start.__name__, inventory_count_save_items.__name__, inventory_count_complete.__name__, inventory_count_cancel.__name__, inventory_count_generate_adjustments.__name__)
    print("\n✅ VERIFICATION PASSED: All view imports working correctly after refactoring")

except ImportError as e:
    print(f"❌ VERIFICATION FAILED: Import error - {e}")
    exit(1)
except Exception as e:
    print(f"❌ VERIFICATION FAILED: {e}")
    exit(1)
