# Quick Spec: Create Codebase Memories

## Overview
Analyze LATECME codebase and create useful memories in graphiti-memory for future reference. This task captures domain knowledge about the manufacturing control system to provide context for future development sessions without re-analyzing the codebase.

## Workflow Type
Feature - Creating new memory entries in the graphiti-memory system.

## Task Scope
- Create 10 memories covering all major domains of the LATECME system
- Use graphiti-memory MCP tools (add_memory, search_nodes, search_memory_facts)
- Group all memories under `latecme-project` group ID
- No code modifications required - this is a documentation/knowledge capture task

## Success Criteria
- [ ] All 10 memories created successfully in graphiti-memory
- [ ] Memories retrievable via search_nodes or search_memory_facts
- [ ] Each memory covers a distinct domain/aspect of the system
- [ ] Group ID `latecme-project` used consistently for filtering

## Project Summary
LATECME is a Django-based Manufacturing Control System for additive manufacturing of metallic materials. Key features: inventory management, material tracking, production orders, purchasing workflows.

## Memories to Create

### 1. Project Overview
- **Name**: LATECME Project Overview
- **Content**: Django 5.2.4 manufacturing system for metallic alloys, PostgreSQL database, Portuguese locale (pt-br), Docker support

### 2. Django Apps Structure
- **Name**: LATECME Django Apps Structure
- **Content**: 7 apps (core, accounts, materials, inventory, production, purchasing, labels), all use BaseModel pattern

### 3. BaseModel Pattern
- **Name**: LATECME BaseModel Pattern
- **Content**: UUID primary keys, audit fields (created_by/updated_by), timestamps, Sequence for ID generation

### 4. Materials Domain
- **Name**: LATECME Materials Domain
- **Content**: Material types (AL, TI, SS, IN, CO, CU, NI), Supplier with CNPJ, MaterialComposition for chemical elements

### 5. Inventory Management
- **Name**: LATECME Inventory Management
- **Content**: Warehouse, MaterialStock, StockMovement (IN/OUT/TRANSFER/ADJUSTMENT), StockReservation, InventoryCount

### 6. Production System
- **Name**: LATECME Production System
- **Content**: ProductionOrder workflow, Bin containers, Batch for material collection, full traceability

### 7. Purchasing Workflow
- **Name**: LATECME Purchasing Workflow
- **Content**: PurchaseRequest → PurchaseOrder → Receiving inspection flow

### 8. User Authentication
- **Name**: LATECME User Authentication
- **Content**: CustomUser with approval workflow, UserRole with JSON permissions, roles (Operator, Admin, Buyer)

### 9. Reference Number Patterns
- **Name**: LATECME Reference Number Patterns
- **Content**: SC (purchase request), PC (order), RB (receiving), OP (production), BAT (batch), INV (inventory count)

### 10. Project Structure
- **Name**: LATECME Project Structure
- **Content**: Root structure, config/, apps/, templates/, static/ with Tabler+HTMX+Alpine.js

## Notes
- Group ID: `latecme-project` for all memories
- Source type: `text`
- Each memory provides context for future development sessions
