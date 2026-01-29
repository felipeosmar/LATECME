# QA Fix Request

**Status**: REJECTED
**Date**: 2026-01-27T14:30:00Z
**QA Session**: 1

## Critical Issues to Fix

### 1. Missing Active Supplier Filter in best_price Calculation

**Severity**: CRITICAL - Blocks Sign-off
**Priority**: P0 - Data Correctness Issue

**Problem**:
The optimized query does NOT filter by `supplier__is_active=True`, but the original `get_best_price()` method does. This means the API can return prices from inactive suppliers, which is incorrect behavior.

**Location**: `apps/materials/views.py:290-291`

**Current Code**:
```python
materials = Material.objects.filter(
    Q(code__icontains=query) | Q(name__icontains=query),
    is_active=True
).annotate(
    best_price=Min('materialsupplier__price_per_kg')  # ← NO FILTER!
)[:10]
```

**Required Fix**:
```python
materials = Material.objects.filter(
    Q(code__icontains=query) | Q(name__icontains=query),
    is_active=True
).annotate(
    best_price=Min(
        'materialsupplier__price_per_kg',
        filter=Q(materialsupplier__supplier__is_active=True)
    )
)[:10]
```

**Why This is Critical**:
1. The original `get_best_price()` method (models.py:154-159) filters by `supplier__is_active=True`
2. Your optimization removed this filter, changing the API behavior
3. If an inactive supplier has the lowest price, the API will incorrectly return that price
4. Users will see prices that are not actually available

**Evidence**:
- Original method: `supplier__is_active=True` filter on line 157 of models.py
- Implementation plan explicitly mentioned this filter should be included
- Codebase has 20+ other locations that filter by `is_active`

**Implementation Steps**:
1. Open `apps/materials/views.py`
2. Locate the `material_search_api` function (around line 281)
3. Find the `.annotate(best_price=Min('materialsupplier__price_per_kg'))` line (line 290-291)
4. Add the `filter` parameter to the `Min()` function as shown above
5. Ensure `Q` is imported (it already is, on line 4)

**Verification**:
After making the fix, verify:
1. Run the specific test: `python manage.py test apps.materials.test_views.MaterialViewsTestCase.test_material_search_api_view --keepdb`
2. Expected: Test should still pass
3. Create a manual test to verify inactive suppliers are excluded:
   - Create a material with two suppliers (one active, one inactive)
   - Inactive supplier has lower price
   - API should return active supplier's price (higher), not inactive supplier's price (lower)

**Django Documentation**:
The `filter` parameter is supported in Django's aggregate functions since Django 2.0:
```python
# Django documentation example:
from django.db.models import Min, Q

queryset.annotate(
    filtered_min=Min('related__field', filter=Q(related__status='active'))
)
```

This is the standard Django pattern for conditional aggregation.

---

## After Fixes

Once the fix is complete:

1. **Test your changes**:
   ```bash
   source .venv/bin/activate
   python manage.py test apps.materials.test_views.MaterialViewsTestCase.test_material_search_api_view --keepdb
   ```

2. **Commit with the following format**:
   ```bash
   git add apps/materials/views.py
   git commit -m "fix: add active supplier filter to best_price calculation (qa-requested)

   Add filter=Q(materialsupplier__supplier__is_active=True) parameter to Min()
   aggregate function to exclude inactive suppliers from best_price calculation.
   This restores the original logic from get_best_price() method.

   Fixes critical data correctness issue where API could return prices from
   inactive suppliers.

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

3. **QA will automatically re-run** to verify the fix

4. **Loop continues until approved** (maximum 50 iterations)

---

## Optional Improvements (Not Blocking)

### Improve Test Coverage

The current test `test_material_search_api_view` doesn't validate:
- If `best_price` field is present
- If `best_price` value is correct
- If inactive suppliers are excluded

Consider adding a comprehensive test case that creates:
- Materials with multiple suppliers
- Mix of active and inactive suppliers
- Verifies best_price comes from active suppliers only

**This is OPTIONAL** and should only be done if time permits. The critical fix above is the blocker.

---

## Summary

**What to fix**: Add `filter=Q(materialsupplier__supplier__is_active=True)` to the `Min()` function
**Where**: `apps/materials/views.py:290-291`
**Why**: Restore original filtering logic to exclude inactive suppliers
**Priority**: CRITICAL - Blocks sign-off

**Estimated fix time**: 2 minutes (single line change)

---

**QA Agent**: Autonomous Quality Assurance
**Next QA Session**: Will run automatically after your commit
