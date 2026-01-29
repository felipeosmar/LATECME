#!/usr/bin/env python3
"""
Verification script to ensure urls.py references match views package exports.
This verifies the refactored views package structure without needing Django runtime.
"""

import ast
import sys

def get_view_references_from_urls():
    """Extract all view references from urls.py"""
    with open('./apps/purchasing/urls.py', 'r') as f:
        content = f.read()

    tree = ast.parse(content)
    references = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == 'views':
                references.add(node.attr)

    return references

def get_exports_from_views_init():
    """Extract all exports from views/__init__.py"""
    with open('./apps/purchasing/views/__init__.py', 'r') as f:
        content = f.read()

    tree = ast.parse(content)
    exports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    if isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant):
                                exports.add(elt.value)

    return exports

def main():
    print("Verifying views package structure...")
    print()

    # Get references and exports
    url_references = get_view_references_from_urls()
    view_exports = get_exports_from_views_init()

    print(f"✓ Found {len(url_references)} view references in urls.py")
    print(f"✓ Found {len(view_exports)} view exports in views/__init__.py")
    print()

    # Check if all URL references are exported
    missing = url_references - view_exports
    extra = view_exports - url_references

    if missing:
        print(f"✗ ERROR: {len(missing)} views referenced in urls.py but not exported:")
        for view in sorted(missing):
            print(f"  - {view}")
        sys.exit(1)

    print("✓ All views referenced in urls.py are exported from views package")

    if extra:
        print(f"⚠ Note: {len(extra)} views exported but not used in urls.py:")
        for view in sorted(extra):
            print(f"  - {view}")

    print()
    print("✓ Views package structure verification PASSED")
    print()
    print("View references found:")
    for view in sorted(url_references):
        print(f"  - views.{view}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
