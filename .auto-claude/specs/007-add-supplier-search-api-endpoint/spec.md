# Add Supplier Search API Endpoint

## Overview

Create an AJAX search API endpoint for suppliers, allowing typeahead/autocomplete functionality when selecting suppliers in forms - similar to the existing material_search_api.

## Rationale

The code reveals this opportunity because: 1) material_search_api() exists in materials/views.py and returns JSON for autocomplete, 2) Supplier model is fully defined with searchable fields (name, code, cnpj), 3) api_materials_with_stock() and api_warehouses() show the API endpoint pattern is well-established, 4) Several forms require supplier selection (purchase requests, purchase orders) that would benefit from search.

---
*This spec was created from ideation and is pending detailed specification.*
