#!/usr/bin/env python3
"""
Verify URL Patterns Resolution
===============================
This script verifies that all URL patterns in apps/purchasing/urls.py
correctly resolve to views that exist in the new views package structure.
"""

import ast
import re
from pathlib import Path


def extract_url_patterns_from_file(urls_file):
    """Extract view references from urls.py file."""
    with open(urls_file, 'r') as f:
        content = f.read()

    # Find all view references in path() calls (e.g., views.dashboard, views.request_list)
    view_pattern = re.compile(r"views\.(\w+)")
    view_references = view_pattern.findall(content)

    return sorted(set(view_references))


def extract_exports_from_init(init_file):
    """Extract all exports from views/__init__.py."""
    with open(init_file, 'r') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return None, f"Syntax error: {e}"

    exports = []

    # Find all imports
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                exports.append(alias.name)

    return sorted(set(exports)), None


def verify_view_exists_in_module(view_name, views_dir):
    """Verify that a view function exists in its corresponding module."""
    module_mapping = {
        'dashboard': 'dashboard.py',
        'request_list': 'purchase_requests.py',
        'request_detail': 'purchase_requests.py',
        'request_create': 'purchase_requests.py',
        'request_update': 'purchase_requests.py',
        'request_submit': 'purchase_requests.py',
        'request_approve': 'purchase_requests.py',
        'request_reject': 'purchase_requests.py',
        'request_item_add': 'purchase_requests.py',
        'request_item_remove': 'purchase_requests.py',
        'order_list': 'purchase_orders.py',
        'order_detail': 'purchase_orders.py',
        'order_create': 'purchase_orders.py',
        'order_send': 'purchase_orders.py',
        'order_confirm': 'purchase_orders.py',
        'order_item_add': 'purchase_orders.py',
        'order_item_remove': 'purchase_orders.py',
        'receiving_list': 'receiving.py',
        'receiving_detail': 'receiving.py',
        'receiving_create': 'receiving.py',
        'receiving_item_add': 'receiving.py',
        'receiving_approve': 'receiving.py',
        'receiving_reject': 'receiving.py',
        'api_approved_requests': 'api.py',
        'api_order_items': 'api.py',
    }

    module_file = module_mapping.get(view_name)
    if not module_file:
        return False, f"Unknown view: {view_name}"

    module_path = views_dir / module_file
    if not module_path.exists():
        return False, f"Module file not found: {module_file}"

    # Parse the module file and check for function definition
    try:
        with open(module_path, 'r') as f:
            content = f.read()
        tree = ast.parse(content)
    except SyntaxError as e:
        return False, f"Syntax error in {module_file}: {e}"

    # Find function definitions
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    if view_name in functions:
        return True, f"Found in {module_file}"
    else:
        return False, f"Function {view_name} not found in {module_file}"


def main():
    """Main verification function."""
    base_dir = Path(__file__).parent
    urls_file = base_dir / 'apps' / 'purchasing' / 'urls.py'
    views_dir = base_dir / 'apps' / 'purchasing' / 'views'
    init_file = views_dir / '__init__.py'

    print("=" * 70)
    print("URL Pattern Resolution Verification")
    print("=" * 70)
    print()

    # Step 1: Verify files exist
    print("Step 1: Verifying file structure...")
    if not urls_file.exists():
        print(f"❌ FAILED: urls.py not found at {urls_file}")
        return False
    if not views_dir.exists():
        print(f"❌ FAILED: views directory not found at {views_dir}")
        return False
    if not init_file.exists():
        print(f"❌ FAILED: __init__.py not found at {init_file}")
        return False
    print("✓ File structure OK")
    print()

    # Step 2: Extract URL patterns
    print("Step 2: Extracting URL patterns from urls.py...")
    url_views = extract_url_patterns_from_file(urls_file)
    print(f"✓ Found {len(url_views)} unique view references")
    print()

    # Step 3: Extract exports from __init__.py
    print("Step 3: Extracting exports from views/__init__.py...")
    exported_views, error = extract_exports_from_init(init_file)
    if error:
        print(f"❌ FAILED: {error}")
        return False
    print(f"✓ Found {len(exported_views)} exported views")
    print()

    # Step 4: Verify all URL views are exported
    print("Step 4: Verifying all URL views are exported...")
    missing_exports = []
    for view in url_views:
        if view not in exported_views:
            missing_exports.append(view)

    if missing_exports:
        print(f"❌ FAILED: {len(missing_exports)} views not exported:")
        for view in missing_exports:
            print(f"   - {view}")
        return False
    print(f"✓ All {len(url_views)} URL views are properly exported")
    print()

    # Step 5: Verify each view exists in its module
    print("Step 5: Verifying views exist in their modules...")
    view_errors = []
    for view in url_views:
        exists, message = verify_view_exists_in_module(view, views_dir)
        if not exists:
            view_errors.append((view, message))
        else:
            print(f"   ✓ {view}: {message}")

    if view_errors:
        print()
        print(f"❌ FAILED: {len(view_errors)} views have issues:")
        for view, error in view_errors:
            print(f"   - {view}: {error}")
        return False
    print()

    # Step 6: Count URL patterns
    print("Step 6: Counting URL patterns...")
    with open(urls_file, 'r') as f:
        urls_content = f.read()

    # Count path() calls
    path_pattern = re.compile(r"path\(")
    total_paths = len(path_pattern.findall(urls_content))

    # Count purchasing-specific patterns
    purchasing_pattern = re.compile(r"path\(['\"](?:requests|orders|receivings)/")
    purchasing_paths = len(purchasing_pattern.findall(urls_content))

    print(f"   Total URL patterns: {total_paths}")
    print(f"   Purchasing-specific patterns (requests/orders/receivings): {purchasing_paths}")
    print()

    # Final summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"✓ URLs file structure: OK")
    print(f"✓ Views package structure: OK")
    print(f"✓ Total URL patterns: {total_paths}")
    print(f"✓ Purchasing patterns: {purchasing_paths}")
    print(f"✓ View references in urls.py: {len(url_views)}")
    print(f"✓ Views exported from package: {len(exported_views)}")
    print(f"✓ All URL views properly exported: YES")
    print(f"✓ All views exist in modules: YES")
    print()
    print("=" * 70)
    print("✅ ALL VERIFICATIONS PASSED")
    print("=" * 70)

    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
