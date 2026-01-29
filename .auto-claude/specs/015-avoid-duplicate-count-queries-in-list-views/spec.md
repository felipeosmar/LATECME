# Avoid Duplicate .count() Queries in List Views

## Overview

List views like `material_list()`, `supplier_list()`, and `stock_list()` call `.count()` on filtered querysets and also pass the same queryset to Paginator. Django's Paginator internally calls `.count()` again, resulting in duplicate COUNT queries.

## Rationale

Each duplicate COUNT query adds 50-100ms on large tables. This pattern appears in at least 5 list views. The fix is simple: use paginator.count instead of calling queryset.count() separately.

---
*This spec was created from ideation and is pending detailed specification.*
