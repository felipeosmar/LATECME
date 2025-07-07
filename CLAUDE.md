# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LATECME is a Django-based manufacturing control system for additive manufacturing materials, specifically designed for metal alloys inventory management. The system provides comprehensive material tracking, stock movements, supplier management, and user authentication with approval workflows.

## Technology Stack

- **Framework**: Django 5.2.4+ (single-file settings configuration)
- **Database**: SQLite (development), PostgreSQL (production via Docker)
- **Python**: 3.10+ (managed via Poetry)
- **Frontend**: Bootstrap-based template (Color Admin)
- **Authentication**: Custom user model with role-based access control
- **Localization**: Portuguese (pt-br), São Paulo timezone

## Development Commands

### Environment Setup
```bash
# Using Poetry (recommended)
poetry install
poetry shell

# Database setup
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Static files
python manage.py collectstatic --noinput
```

### Daily Development
```bash
# Start development server
python manage.py runserver

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py shell

# Run tests
python manage.py test

# Check for issues
python manage.py check
```

### Initial Data Setup
```bash
# Create sample data
python create_initial_data.py
python create_materials_data.py
```

### Docker Database (Optional)
```bash
# Start PostgreSQL services
docker-compose -f docker-compose-dev.yml up -d

# Check service status
docker-compose -f docker-compose-dev.yml ps

# Stop services
docker-compose -f docker-compose-dev.yml down
```

## Project Architecture

### App Structure
```
apps/
├── core/           # Base models (BaseModel, TimeStampedModel) and shared utilities
├── accounts/       # Custom user authentication with approval workflow
├── materials/      # Material definitions, suppliers, and pricing management
└── inventory/      # Stock tracking, movements, reservations, and inventory counts
```

### Core Design Patterns

**Base Models**: All business models inherit from `BaseModel` which provides:
- UUID primary keys (`id = models.UUIDField`)
- Audit trail (`created_by`, `updated_by`, `created_at`, `updated_at`)
- Soft delete capability (`is_active = models.BooleanField`)
- User tracking for all changes

**Authentication System**: Custom user model with workflow:
- User registration requires approval (`status: pending → approved`)
- Role-based permissions via `UserRole` model
- Middleware blocks unapproved users (`UserApprovalMiddleware`)

**Material Management**: Hierarchical material system:
- `Material` → core material definitions with unique codes (AL7075, TI6AL4V pattern)
- `Supplier` → vendor information and contact details
- `MaterialSupplier` → junction table with pricing and lead times
- `MaterialCategory` → organizational groupings with visual colors

**Inventory Control**: Multi-warehouse stock management:
- `Warehouse` → physical storage locations
- `MaterialStock` → current quantities per material/warehouse
- `StockMovement` → complete audit trail of all movements
- `StockReservation` → temporary holds on inventory
- `InventoryCount` → physical count reconciliation

### Key Business Rules

1. **Material Codes**: Follow pattern `TYPE + alphanumeric` (e.g., AL7075, TI6AL4V)
2. **Stock Movements**: Automatically update `MaterialStock` quantities
3. **Reservations**: Automatically tracked in `reserved_quantity`
4. **Inventory Counts**: Generate automatic reference numbers
5. **User Access**: Requires approval workflow before system access

### URL Structure
- `/admin/` - Django admin interface
- `/accounts/` - User authentication and profile management
- `/dashboard/` - Main dashboard (from core app)
- `/materials/` - Material and supplier management
- `/inventory/` - Stock operations and reporting
- `/` - Redirects to login page

## Configuration Notes

### Settings Structure
Single file configuration at `config/settings.py`:
- SQLite database for development
- Custom user model: `accounts.CustomUser`
- Brazilian Portuguese localization
- Static files served from `color-admin/assets/`

### Database Models
- All models use UUID primary keys
- Extensive use of JSONField for flexible data storage
- Decimal fields for precise quantity/price calculations
- Proper foreign key relationships with CASCADE/PROTECT

### Template Integration
- Bootstrap-based frontend using Color Admin template
- Templates organized by app in `templates/` directory
- Static files collected from `color-admin/assets/`

## Development Best Practices

### Model Development
- Always inherit from `BaseModel` for audit trail
- Use `clean()` methods for validation
- Implement `__str__()` methods for admin interface
- Use `@property` decorators for computed fields

### Code Validation
- CNPJ validation in `Supplier` model
- Material code pattern validation
- Automatic quantity calculations in movements
- Reservation expiry tracking

### Testing
- No test files currently present in the codebase
- Use Django's built-in testing framework when adding tests
- Test command: `python manage.py test`

## Hardware Integration Notes

The system is designed for integration with:
- Barcode label printers (mentioned in documentation)
- Continuous barcode scanners (mentioned in documentation)
- Physical inventory tracking systems

## Important Implementation Details

- Uses PostgreSQL for production but SQLite for development
- Custom middleware for user approval workflow
- Extensive use of Django's admin interface
- Material composition stored as JSON for flexibility
- Automatic stock quantity updates via model save methods
- Reservation system with expiry date tracking

## Development Workflow

1. Models are defined with proper relationships and validation
2. Admin interface provides immediate CRUD operations
3. URL routing follows Django conventions
4. Templates use Bootstrap for consistent UI
5. All user actions are tracked via audit fields
6. System requires user approval before access