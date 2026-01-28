# Fix N+1 Query in Material Search API

## Overview

The `material_search_api()` endpoint iterates through materials and calls `material.get_best_price()` for each one, triggering a separate database query per material. This creates an N+1 query pattern where 10 search results generate 11 queries (1 main + 10 per-material).

## Rationale

This API endpoint is called on every keystroke for material autocomplete searches. With typical usage patterns of 2-3 searches per form interaction, this could generate 30+ database queries per user action. The fix is straightforward with `Prefetch` and annotation.

---
*This spec was created from ideation and is pending detailed specification.*
