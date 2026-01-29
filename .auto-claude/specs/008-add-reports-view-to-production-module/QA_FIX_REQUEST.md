# QA Fix Request

**Status**: REJECTED
**Date**: 2026-01-27
**QA Session**: 1

---

## Summary

The production reports implementation is **structurally correct** but has **critical data mismatches** between the view function and the template. The template expects data fields that the view doesn't provide, which will cause the page to display zeros or missing data.

**Issues Found**: 3 critical, 1 major
**Estimated Fix Time**: 15-20 minutes
**Complexity**: Low (straightforward aggregation additions)

---

## Critical Issues to Fix

### 1. Add Missing `bin_utilization` Data ⚠️ CRITICAL

**Problem**: Template extensively uses `bin_utilization` but view doesn't calculate or pass it.

**Location**: `apps/production/views.py` lines 833-849

**Current Code**:
```python
# Utilização de contentores
bin_movements = BinHistory.objects.filter(
    created_at__date__range=[date_from, date_to]
).values('movement_type').annotate(
    count=Count('id'),
    total_quantity=Sum('quantity_change')
).order_by('movement_type')

context = {
    'date_from': date_from,
    'date_to': date_to,
    'orders_by_status': orders_by_status,
    'batches_by_status': batches_by_status,
    'top_materials': top_materials,
    'bin_movements': bin_movements,
    # Missing: bin_utilization
}

return render(request, 'production/reports.html', context)
```

**Required Fix**: Add bin utilization query AFTER bin_movements and BEFORE context dict:

```python
# Utilização de contentores
bin_movements = BinHistory.objects.filter(
    created_at__date__range=[date_from, date_to]
).values('movement_type').annotate(
    count=Count('id'),
    total_quantity=Sum('quantity_change')
).order_by('movement_type')

# Estatísticas de utilização de bins
bin_utilization = Bin.objects.aggregate(
    total_bins=Count('id'),
    loaded_bins=Count('id', filter=Q(status='LOADED')),
    empty_bins=Count('id', filter=Q(status='EMPTY')),
    total_capacity=Sum('capacity'),
    total_current=Sum('current_quantity')
)

context = {
    'date_from': date_from,
    'date_to': date_to,
    'orders_by_status': orders_by_status,
    'batches_by_status': batches_by_status,
    'top_materials': top_materials,
    'bin_movements': bin_movements,
    'bin_utilization': bin_utilization,  # ADD THIS LINE
}
```

**Note**: Q is already imported at line 4: `from django.db.models import Q, Sum, Count`

**Verification Steps**:
1. Start dev server: `python manage.py runserver 9000`
2. Navigate to: http://localhost:9000/production/reports/
3. Check that "Utilizacao de Bins" summary card shows a percentage (not 0%)
4. Scroll to "Bin Utilization Statistics" card
5. Verify all fields show actual data:
   - Total de Bins
   - Bins Carregados
   - Bins Vazios
   - Capacidade Total (kg)
   - Quantidade Atual (kg)
   - Progress bar with utilization %

---

### 2. Add Missing Aggregations to `orders_by_status` ⚠️ CRITICAL

**Problem**: Template expects `total_planned` and `total_produced` but view only provides `count`.

**Location**: `apps/production/views.py` lines 809-813

**Current Code**:
```python
# Ordens de produção por status
orders_by_status = ProductionOrder.objects.filter(
    created_at__date__range=[date_from, date_to]
).values('status').annotate(
    count=Count('id')
).order_by('status')
```

**Required Fix**: Add Sum aggregations for planned_quantity and produced_quantity:

```python
# Ordens de produção por status
orders_by_status = ProductionOrder.objects.filter(
    created_at__date__range=[date_from, date_to]
).values('status').annotate(
    count=Count('id'),
    total_planned=Sum('planned_quantity'),
    total_produced=Sum('produced_quantity')
).order_by('status')
```

**Verification Steps**:
1. Navigate to http://localhost:9000/production/reports/
2. Scroll to "Ordens por Status" table
3. Verify the table has 4 columns:
   - Status (with colored badges)
   - Qtd. Ordens (count)
   - Planejado (kg) - should show actual kg values, not 0.00
   - Produzido (kg) - should show actual kg values, not 0.00

---

### 3. Fix Field Name Mismatch in `batches_by_status` ⚠️ CRITICAL

**Problem**: View provides `total_target` and `total_actual` but template expects `total_quantity`.

**Location**: `apps/production/views.py` lines 816-822

**Current Code**:
```python
# Bateladas por status
batches_by_status = Batch.objects.filter(
    created_at__date__range=[date_from, date_to]
).values('status').annotate(
    count=Count('id'),
    total_target=Sum('target_quantity'),
    total_actual=Sum('actual_quantity')
).order_by('status')
```

**Required Fix**: Change to match template expectation (use actual_quantity as total_quantity):

```python
# Bateladas por status
batches_by_status = Batch.objects.filter(
    created_at__date__range=[date_from, date_to]
).values('status').annotate(
    count=Count('id'),
    total_quantity=Sum('actual_quantity')
).order_by('status')
```

**Why actual_quantity?**: This follows the inventory reports pattern and represents the actual produced quantity, which is what we want to report on.

**Verification Steps**:
1. Navigate to http://localhost:9000/production/reports/
2. Scroll to "Lotes por Status" table
3. Verify the "Quantidade (kg)" column shows actual kg values, not 0.00

---

## Major Issue (Verification Needed)

### 4. Verify `quantity_change` Field in BinHistory Model ⚠️ MAJOR

**Problem**: The view uses `quantity_change` field but we need to verify this field exists in the BinHistory model.

**Location**: `apps/production/views.py` line 837

**Required Verification**:
```bash
# Run this command to check BinHistory model fields:
python manage.py shell -c "from apps.production.models import BinHistory; print([f.name for f in BinHistory._meta.get_fields()])"
```

**If `quantity_change` field doesn't exist**, find the correct field name and update line 837:
```python
total_quantity=Sum('CORRECT_FIELD_NAME')  # Replace with actual field name
```

**Likely alternatives** if quantity_change doesn't exist:
- `quantity`
- `amount`
- `quantity_delta`

---

## Implementation Checklist

Use this checklist to ensure all fixes are complete:

- [ ] **Fix 1**: Added bin_utilization query with all 5 fields
- [ ] **Fix 1**: Added bin_utilization to context dict
- [ ] **Fix 2**: Added total_planned to orders_by_status annotation
- [ ] **Fix 2**: Added total_produced to orders_by_status annotation
- [ ] **Fix 3**: Changed batches_by_status to use total_quantity=Sum('actual_quantity')
- [ ] **Fix 3**: Removed total_target and total_actual from batches annotation
- [ ] **Fix 4**: Verified BinHistory field name (quantity_change or alternative)
- [ ] **Verification**: Ran `python manage.py check` (should pass)
- [ ] **Verification**: Started dev server on port 9000
- [ ] **Verification**: Navigated to /production/reports/ (no 500 errors)
- [ ] **Verification**: All summary cards show data
- [ ] **Verification**: All tables show data in all columns
- [ ] **Verification**: Bin utilization card shows statistics
- [ ] **Verification**: No JavaScript console errors

---

## Complete Fixed Code

For reference, here's what the complete `reports()` function should look like after all fixes:

```python
@login_required
def reports(request):
    """Relatórios de produção"""
    from datetime import timedelta

    # Período
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()

    if not date_to:
        date_to = timezone.now().date()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

    # Ordens de produção por status
    orders_by_status = ProductionOrder.objects.filter(
        created_at__date__range=[date_from, date_to]
    ).values('status').annotate(
        count=Count('id'),
        total_planned=Sum('planned_quantity'),      # ADDED
        total_produced=Sum('produced_quantity')     # ADDED
    ).order_by('status')

    # Bateladas por status
    batches_by_status = Batch.objects.filter(
        created_at__date__range=[date_from, date_to]
    ).values('status').annotate(
        count=Count('id'),
        total_quantity=Sum('actual_quantity')       # CHANGED from total_target/total_actual
    ).order_by('status')

    # Materiais mais produzidos
    top_materials = Batch.objects.filter(
        created_at__date__range=[date_from, date_to]
    ).values('material__code', 'material__name').annotate(
        total_batches=Count('id'),
        total_quantity=Sum('actual_quantity')
    ).order_by('-total_batches')[:10]

    # Utilização de contentores
    bin_movements = BinHistory.objects.filter(
        created_at__date__range=[date_from, date_to]
    ).values('movement_type').annotate(
        count=Count('id'),
        total_quantity=Sum('quantity_change')       # VERIFY field name
    ).order_by('movement_type')

    # Estatísticas de utilização de bins
    bin_utilization = Bin.objects.aggregate(         # ADDED
        total_bins=Count('id'),                      # ADDED
        loaded_bins=Count('id', filter=Q(status='LOADED')),  # ADDED
        empty_bins=Count('id', filter=Q(status='EMPTY')),    # ADDED
        total_capacity=Sum('capacity'),              # ADDED
        total_current=Sum('current_quantity')        # ADDED
    )                                                # ADDED

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'orders_by_status': orders_by_status,
        'batches_by_status': batches_by_status,
        'top_materials': top_materials,
        'bin_movements': bin_movements,
        'bin_utilization': bin_utilization,          # ADDED
    }

    return render(request, 'production/reports.html', context)
```

---

## After Fixes

Once all fixes are complete:

1. **Test the implementation**:
   ```bash
   python manage.py check
   python manage.py runserver 9000
   # Navigate to http://localhost:9000/production/reports/
   # Verify all sections display data correctly
   ```

2. **Commit with QA-requested message**:
   ```bash
   git add apps/production/views.py
   git commit -m "fix: add missing aggregations and bin utilization to production reports (qa-requested)

   - Added bin_utilization statistics (total, loaded, empty bins + capacity)
   - Added total_planned and total_produced to orders_by_status
   - Fixed field name mismatch in batches_by_status (now uses total_quantity)
   - All template data requirements now satisfied

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

3. **QA will automatically re-run** and verify:
   - All data fields present and displaying correctly
   - No template rendering errors
   - Summary cards show accurate percentages and counts
   - Tables display all columns with data
   - Date range filtering works correctly

---

## Questions or Issues?

If you encounter any problems while implementing these fixes:

1. **Check imports**: Make sure `Q, Sum, Count` are imported (line 4)
2. **Check field names**: If aggregation fails, verify model field names with:
   ```bash
   python manage.py shell -c "from apps.production.models import Bin, ProductionOrder, Batch; print(Bin._meta.get_fields())"
   ```
3. **Check Django syntax**: Filter with Q() requires Q import
4. **Test queries separately**: You can test aggregation queries in Django shell before adding to view

---

**Fix Priority**: HIGH - Blocking feature functionality
**Estimated Time**: 15-20 minutes
**Difficulty**: Low (copy-paste with minor adjustments)

**Next**: Implement fixes → Commit → QA re-validation → Approval ✓
