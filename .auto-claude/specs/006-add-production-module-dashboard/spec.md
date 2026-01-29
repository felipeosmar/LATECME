# Add Production Module Dashboard

## Overview

Create a dashboard view for the Production module with statistics about production orders, batches, bins, and recent activity - similar to the existing inventory and purchasing dashboards.

## Rationale

The code reveals this opportunity because: 1) Dashboard pattern already exists in inventory/views.py dashboard() and purchasing/views.py dashboard(), 2) Production module has all the necessary models (ProductionOrder, Batch, Bin) with status fields and timestamps, 3) Statistics queries using Count, Sum, and aggregations are well-established patterns in the codebase, 4) Template structure exists (templates/dashboard/index.html, templates/inventory/dashboard.html) that can be followed.

---
*This spec was created from ideation and is pending detailed specification.*
