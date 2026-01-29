# Add Reports View to Production Module

## Overview

Create a reports view for the Production module showing production order statistics, batch throughput, bin utilization, and material consumption over configurable time periods - following the existing inventory reports pattern.

## Rationale

The code reveals this opportunity because: 1) Reports view pattern exists in inventory/views.py reports() with date range filtering, 2) Production models have all necessary data fields (status, dates, quantities) for meaningful reports, 3) Aggregation queries using Sum, Count, values() are well-established, 4) templates/inventory/reports.html provides the template structure to follow.

---
*This spec was created from ideation and is pending detailed specification.*
