# Split large inventory views.py into domain-specific modules

## Overview

The file apps/inventory/views.py has grown to 1251 lines and handles multiple unrelated concerns: stock management, movements, warehouses, reservations, and inventory counts. This violates single responsibility and makes the code hard to navigate, test, and maintain.

## Rationale

Very large files increase cognitive load, make code reviews harder, and often lead to merge conflicts. The inventory app handles 5 distinct domains (stocks, movements, warehouses, reservations, counts) that each deserve their own view module. Smaller, focused modules are easier to test, maintain, and reason about.

---
*This spec was created from ideation and is pending detailed specification.*
