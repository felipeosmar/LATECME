# QA Fix Request

**Status**: ❌ REJECTED
**Date**: 2026-01-28 19:19 UTC
**QA Session**: 1

---

## Critical Issues to Fix

### 1. ValueError in material_list view - UUID to int() conversion

**Severity**: 🔴 CRITICAL - Blocks production deployment

**Problem**:
The material_list view attempts to convert a UUID category_id to int(), causing a ValueError when users filter materials by category.

**Location**: `apps/materials/views.py:56`

**Current Code (BROKEN)**:
```python
context = {
    'page_obj': result['page_obj'],
    'search': result['filter_values']['search'],
    'material_type': result['filter_values']['type'],
    'category_id': int(category_id) if category_id else '',  # ❌ BUG HERE
    'categories': categories,
    'material_types': material_types,
    'total_materials': result['paginator'].count,
}
```

**Error Message**:
```
ValueError: invalid literal for int() with base 10: '8e634106-fdf6-43fd-ba63-d539c5582c28'
```

**Root Cause**:
The `category_id` is a UUID string (from MaterialCategory model which uses UUIDs), not an integer. The refactoring incorrectly added an `int()` conversion that doesn't exist in the original code.

**Required Fix**:
Remove the `int()` conversion on line 56:

```python
context = {
    'page_obj': result['page_obj'],
    'search': result['filter_values']['search'],
    'material_type': result['filter_values']['type'],
    'category_id': category_id,  # ✅ FIXED - No int() conversion
    'categories': categories,
    'material_types': material_types,
    'total_materials': result['paginator'].count,
}
```

**Verification Steps**:
1. Edit `apps/materials/views.py` line 56
2. Change `int(category_id) if category_id else ''` to just `category_id`
3. Run the specific test:
   ```bash
   python manage.py test apps.materials.test_views.MaterialViewsTestCase.test_material_list_view_with_filters
   ```
   Expected: Test passes ✅

4. Manual verification (with Django server running):
   - Navigate to http://localhost:8000/materials/
   - Select any category from the category filter dropdown
   - Click filter button
   - Expected: Page loads successfully with filtered results
   - Expected: No 500 error or ValueError

5. Test with URL directly:
   ```bash
   curl "http://localhost:8000/materials/?category=<some-uuid>"
   ```
   Expected: HTTP 200 response

**Impact**:
- ❌ Materials list page crashes when filtering by category
- ❌ Test failure prevents CI/CD
- ❌ User-facing feature broken
- ✅ Other filters (search, type) still work
- ✅ 14 other refactored views unaffected

---

## After Fixes

Once the fix is complete:

1. **Commit the fix** with message:
   ```
   fix: Remove incorrect int() conversion for UUID category_id (qa-requested)
   ```

2. **Run the full test suite** for list views:
   ```bash
   python manage.py test tests.test_list_utils
   python manage.py test apps.materials.test_views.MaterialViewsTestCase.test_material_list_view_with_filters
   ```

3. **QA will automatically re-run** to verify the fix

---

## Context

This is a simple bug introduced during an otherwise successful refactoring. The refactoring consolidated 15 duplicate list views into a reusable utility pattern. All other aspects of the refactoring are working correctly:

✅ 33 unit tests pass
✅ 14/15 refactored views work perfectly
✅ Security review clean
✅ Pattern compliance verified
✅ Documentation comprehensive

Only this one line needs fixing.

---

## Estimated Fix Time

⏱️ **2-5 minutes** - This is a one-line fix

---

## Questions?

If anything is unclear about this fix request, refer to:
- Full QA report: `qa_report.md`
- Test file: `apps/materials/test_views.py` line 102-109
- Original view: `apps/materials/views.py` line 13-62
