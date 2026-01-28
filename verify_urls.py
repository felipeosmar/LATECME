#!/usr/bin/env python
"""Verification script to test URL resolution after refactoring."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import resolve, reverse

# Test key URLs
urls_to_test = [
    ('inventory:dashboard', 'dashboard'),
    ('inventory:stock_list', 'stock_list'),
    ('inventory:warehouse_list', 'warehouse_list'),
    ('inventory:reservations_list', 'reservations_list'),
    ('inventory:inventory_count_list', 'inventory_count_list'),
    ('inventory:movements_list', 'movements_list'),
]

print("Testing URL resolution after refactoring...\n")

all_passed = True
for url_name, expected_view in urls_to_test:
    try:
        url = reverse(url_name)
        resolved = resolve(url)
        view_name = resolved.func.__name__
        status = "✅" if view_name == expected_view else "❌"
        print(f"{status} {url_name} -> {url} -> {view_name}")
        if view_name != expected_view:
            all_passed = False
            print(f"   Expected: {expected_view}, Got: {view_name}")
    except Exception as e:
        print(f"❌ {url_name} -> ERROR: {e}")
        all_passed = False

if all_passed:
    print("\n✅ VERIFICATION PASSED: All URLs resolve correctly after refactoring")
else:
    print("\n❌ VERIFICATION FAILED: Some URLs did not resolve correctly")
    exit(1)
