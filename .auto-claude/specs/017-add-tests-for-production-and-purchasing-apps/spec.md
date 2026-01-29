# Add tests for production and purchasing apps

## Overview

The production (869 lines in views.py) and purchasing (1084 lines in views.py) apps have no test files, while other apps like inventory, materials, and accounts have comprehensive test coverage. This leaves critical business logic untested.

## Rationale

Production orders and purchasing workflows are core business functionality that should have thorough test coverage. Without tests, refactoring becomes risky, bugs may go undetected, and there's no documentation of expected behavior. The existing test patterns in apps/inventory/tests.py and apps/materials/tests.py can serve as templates.

---
*This spec was created from ideation and is pending detailed specification.*
