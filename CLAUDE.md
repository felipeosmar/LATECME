# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LATECME is a Django-based manufacturing control system for additive manufacturing materials, primarily focused on metal alloys inventory management. The system handles material tracking, barcode generation, stock movements, and hardware integration with printers and scanners.

## Technology Stack

- **Framework**: Django 5.2+ with Django REST Framework (DRF)
- **Database**: PostgreSQL (as specified in documentation)
- **Task Queue**: Celery with Redis broker
- **Cache**: Redis
- **Authentication**: JWT tokens (djangorestframework-simplejwt)
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Frontend**: Template mentions color-admin Bootstrap template

## Project Structure

The project follows Django best practices with a multi-app architecture:

```
apps/
├── core/           # Base models and shared utilities
├── materials/      # Material and supplier management
├── inventory/      # Stock items and movements
├── identification/  # Unique code generation and barcode handling
├── purchasing/     # Purchase orders and supplier management
├── hardware/       # Printer and scanner integration
```

## Development Commands

### Setup and Installation
```bash
# Install dependencies (Poetry-based project)
poetry install

# OR if using pip
pip install django>=5.2.4

# Database setup (PostgreSQL expected)
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Database Management
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Access Django shell
python manage.py shell
```

### Background Tasks
```bash
# Start Redis (required for Celery)
redis-server

# Start Celery worker
celery -A config worker -l info

# Start Celery beat scheduler
celery -A config beat -l info

# Monitor tasks with Flower
celery -A config flower
```

## Core Business Logic

### Material Management
- Materials are identified by unique codes following pattern: `TYPE + 4 digits` (e.g., AL7075, TI6AL4)
- Supported material types: Aluminum (AL), Titanium (TI), Stainless Steel (SS), Inconel (IN), Cobalt-Chrome (CO)
- Each material has composition, density, and certification requirements
- Multiple suppliers per material with pricing and lead times

### Inventory Control
- Each stock item gets a unique barcode identifier
- Tracks weight, supplier batch, location, and status
- Status flow: `Registered → Available → Reserved → Consumed`
- Supports quarantine and disposal workflows

### Hardware Integration
- Barcode label printing via Celery tasks
- Continuous barcode scanning support
- Error handling and retry logic for hardware failures

## Key Models and Relationships

- **Material**: Core material definitions with specifications
- **Supplier**: Vendor information and contact details
- **MaterialSupplier**: Junction table with pricing and terms
- **StockItem**: Individual material instances with unique codes
- **StockMovement**: Audit trail of all stock transactions
- **PurchaseOrder**: Procurement tracking

## API Architecture

All business logic exposed via REST API:
- JWT authentication required
- Pagination on all list endpoints
- Filtering and search capabilities
- Async task status tracking
- OpenAPI/Swagger documentation at `/api/docs/`

## Testing

Look for test files in `tests/` directory or `test_*.py` files in each app. Run tests with:
```bash
python manage.py test
```

## Important Patterns

1. **UUID Primary Keys**: All models use UUID instead of integer IDs
2. **Audit Trail**: All models track `created_by`, `updated_by`, `created_at`, `updated_at`
3. **Soft Delete**: Use `is_active` field instead of hard deletes
4. **Async Processing**: Hardware operations run via Celery tasks
5. **Cache Strategy**: Frequent queries cached in Redis
6. **Security**: All operations require authentication and user tracking

## Hardware Components

- **Label Printer**: ESC/POS compatible, USB/Serial connection
- **Barcode Scanner**: Continuous reading mode, WebSocket integration
- **Error Handling**: Automatic retry with exponential backoff

## Configuration

Settings are split by environment:
- `config/settings/base.py` - Common settings
- `config/settings/development.py` - Development overrides
- `config/settings/production.py` - Production configuration

Environment variables expected:
- `SECRET_KEY` - Django secret key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - Database connection
- `REDIS_URL` - Redis connection string

## Development Notes

- The project is currently in planning phase with detailed documentation
- Core Django structure is defined but may not be fully implemented
- Focus on manufacturing domain with metal alloys and precision tracking
- Integration with physical hardware is a key requirement
- Multi-user system with role-based access (Operator, Administrator, Buyer)