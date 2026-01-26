.PHONY: help build up down logs shell migrate collectstatic createsuperuser clean rebuild prod-build prod-up prod-down prod-logs

# Development commands
help:
	@echo "LATECME - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev-up        - Start development services (postgres, redis)"
	@echo "  make dev-down      - Stop development services"
	@echo "  make dev-logs      - Show development logs"
	@echo ""
	@echo "Production:"
	@echo "  make prod-build    - Build production images"
	@echo "  make prod-up       - Start production stack"
	@echo "  make prod-down     - Stop production stack"
	@echo "  make prod-logs     - Show production logs"
	@echo "  make prod-shell    - Open shell in Django container"
	@echo "  make prod-migrate  - Run migrations in production"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         - Remove containers, volumes, and images"
	@echo "  make rebuild       - Clean and rebuild production stack"

# Development
dev-up:
	docker-compose -f docker-compose-dev.yml up -d

dev-down:
	docker-compose -f docker-compose-dev.yml down

dev-logs:
	docker-compose -f docker-compose-dev.yml logs -f

# Production
prod-build:
	docker-compose -f docker-compose.yml build

prod-up:
	docker-compose -f docker-compose.yml up -d

prod-down:
	docker-compose -f docker-compose.yml down

prod-logs:
	docker-compose -f docker-compose.yml logs -f

prod-logs-django:
	docker-compose -f docker-compose.yml logs -f django

prod-logs-nginx:
	docker-compose -f docker-compose.yml logs -f nginx

prod-shell:
	docker-compose -f docker-compose.yml exec django /bin/bash

prod-migrate:
	docker-compose -f docker-compose.yml exec django python manage.py migrate

prod-collectstatic:
	docker-compose -f docker-compose.yml exec django python manage.py collectstatic --noinput

prod-createsuperuser:
	docker-compose -f docker-compose.yml exec django python manage.py createsuperuser

# Maintenance
clean:
	docker-compose -f docker-compose.yml down -v --rmi local
	docker-compose -f docker-compose-dev.yml down -v --rmi local

rebuild: clean prod-build prod-up

# Status
status:
	docker-compose -f docker-compose.yml ps

# Backup database
backup-db:
	@mkdir -p backups
	docker-compose -f docker-compose.yml exec postgres pg_dump -U $${DJANGO_DB_USER} $${DJANGO_DB_NAME} > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup saved to backups/"

# Restore database
restore-db:
	@echo "Usage: cat backup.sql | docker-compose -f docker-compose.yml exec -T postgres psql -U \$$DJANGO_DB_USER \$$DJANGO_DB_NAME"
