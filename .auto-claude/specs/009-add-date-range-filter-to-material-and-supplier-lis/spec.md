# Add Date Range Filter to Material and Supplier Lists

## Overview

Add date range filtering (date_from, date_to) to material_list and supplier_list views, allowing users to filter by creation date - extending the existing date filter pattern from inventory movements.

## Rationale

The code reveals this opportunity because: 1) Date range filter pattern exists in inventory/views.py movements_list() and production/views.py bin_list(), 2) Material and Supplier models have created_at field from BaseModel, 3) The filter UI pattern is established in the codebase, 4) material_list and supplier_list already have search and type filters, just missing date range.

---
*This spec was created from ideation and is pending detailed specification.*
