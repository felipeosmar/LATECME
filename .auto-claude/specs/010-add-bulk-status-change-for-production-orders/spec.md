# Add Bulk Status Change for Production Orders

## Overview

Add bulk operations capability to change status of multiple production orders at once (start multiple, complete multiple) - extending the existing bulk operations pattern from bin batch printing.

## Rationale

The code reveals this opportunity because: 1) Bulk operations pattern exists in production/views.py bin_batch_create() and bin_batch_print() with transaction.atomic(), 2) ProductionOrder has start() and complete() methods that can be called in a loop, 3) AJAX endpoint pattern with JsonResponse for bulk ops is established, 4) The list view already shows multiple orders that could be selected.

---
*This spec was created from ideation and is pending detailed specification.*
