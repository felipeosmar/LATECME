# Extract duplicated list view pagination/filtering into reusable mixin or utility

## Overview

The codebase contains 14+ list views that all follow the same pattern: get filters from request.GET, apply filters to queryset, paginate results, and render template. This pattern is duplicated across inventory, purchasing, production, materials, and labels apps.

## Rationale

Code duplication leads to inconsistencies when fixes are applied unevenly and increases maintenance burden. A reusable mixin or utility function would ensure consistent behavior, reduce boilerplate, and make adding new list views faster and less error-prone.

---
*This spec was created from ideation and is pending detailed specification.*
