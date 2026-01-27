# Views package for inventory app
# This package contains domain-specific view modules

# Import from stock_views
from .stock_views import (
    dashboard,
    stock_list,
    stock_detail,
    reports,
)

# Import from warehouse_views
from .warehouse_views import (
    warehouse_list,
    warehouse_detail,
    warehouse_create,
    warehouse_update,
    api_warehouses,
)

# Import from reservation_views
from .reservation_views import (
    reservations_list,
    reservation_detail,
    reservation_create,
    reservation_update,
    reservation_cancel,
    api_materials_with_stock,
    api_stock_info,
)

# Import from movement_views
from .movement_views import (
    movements_list,
    create_movement,
)

# Import from count_views
from .count_views import (
    inventory_count_list,
    inventory_count_detail,
    inventory_count_create,
    inventory_count_start,
    inventory_count_save_items,
    inventory_count_complete,
    inventory_count_cancel,
    inventory_count_generate_adjustments,
)

# Export all view functions for backward compatibility
__all__ = [
    # Stock views
    'dashboard',
    'stock_list',
    'stock_detail',
    'reports',
    # Warehouse views
    'warehouse_list',
    'warehouse_detail',
    'warehouse_create',
    'warehouse_update',
    'api_warehouses',
    # Reservation views
    'reservations_list',
    'reservation_detail',
    'reservation_create',
    'reservation_update',
    'reservation_cancel',
    'api_materials_with_stock',
    'api_stock_info',
    # Movement views
    'movements_list',
    'create_movement',
    # Count views
    'inventory_count_list',
    'inventory_count_detail',
    'inventory_count_create',
    'inventory_count_start',
    'inventory_count_save_items',
    'inventory_count_complete',
    'inventory_count_cancel',
    'inventory_count_generate_adjustments',
]
