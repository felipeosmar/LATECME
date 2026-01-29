# Add Redis Caching for Dashboard Statistics

## Overview

Dashboard views (materials/dashboard, inventory/dashboard, production stats) compute aggregate statistics on every page load using COUNT, SUM, and other aggregations. These queries run on potentially large tables without any caching.

## Rationale

Redis is already configured in docker-compose but not utilized in Django. Dashboard statistics rarely change and are perfect candidates for caching. Multiple users viewing dashboards amplify the database load unnecessarily.

---
*This spec was created from ideation and is pending detailed specification.*
