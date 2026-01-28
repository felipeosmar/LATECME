# Add Database Indexes for Frequently Filtered Fields

## Overview

Several Django models filter on fields that lack explicit database indexes. Fields like `status`, `movement_type`, `is_active`, and date fields are used in WHERE clauses and ordering but rely on implicit indexing or full table scans.

## Rationale

List views filter by status (DRAFT, IN_PROGRESS, COMPLETED), movement_type (IN, OUT, TRANSFER), and date ranges. As data grows, these queries will become slower without proper indexes. PostgreSQL's query planner needs hints for optimal paths.

---
*This spec was created from ideation and is pending detailed specification.*
