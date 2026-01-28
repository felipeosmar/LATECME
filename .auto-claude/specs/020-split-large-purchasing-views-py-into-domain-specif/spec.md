# Split large purchasing views.py into domain-specific modules

## Overview

The file apps/purchasing/views.py has grown to 1084 lines and handles three distinct domains: Purchase Requests (solicitations), Purchase Orders, and Receiving. Each domain has its own set of CRUD operations, status transitions, and business logic.

## Rationale

Like the inventory views, this file has grown too large to maintain effectively. The purchasing workflow has clear domain boundaries that map well to separate modules. This split would also make it easier to add the planned 'Supplier Search API Endpoint' feature without further bloating the file.

---
*This spec was created from ideation and is pending detailed specification.*
