# Purchasing views package
# This package contains domain-specific view modules split from the original monolithic views.py
#
# Modules:
# - dashboard.py: Dashboard view
# - purchase_requests.py: Purchase request CRUD and workflow views
# - purchase_orders.py: Purchase order CRUD and workflow views
# - receiving.py: Receiving CRUD and workflow views
# - api.py: API endpoint views

# Dashboard views
from .dashboard import dashboard

# Purchase request views
from .purchase_requests import (
    request_list,
    request_detail,
    request_create,
    request_update,
    request_submit,
    request_approve,
    request_reject,
    request_item_add,
    request_item_remove,
)

# Purchase order views
from .purchase_orders import (
    order_list,
    order_detail,
    order_create,
    order_send,
    order_confirm,
    order_item_add,
    order_item_remove,
)

# Receiving views
from .receiving import (
    receiving_list,
    receiving_detail,
    receiving_create,
    receiving_item_add,
    receiving_approve,
    receiving_reject,
)

# API views
from .api import (
    api_approved_requests,
    api_order_items,
)

__all__ = [
    # Dashboard
    'dashboard',
    # Purchase requests
    'request_list',
    'request_detail',
    'request_create',
    'request_update',
    'request_submit',
    'request_approve',
    'request_reject',
    'request_item_add',
    'request_item_remove',
    # Purchase orders
    'order_list',
    'order_detail',
    'order_create',
    'order_send',
    'order_confirm',
    'order_item_add',
    'order_item_remove',
    # Receiving
    'receiving_list',
    'receiving_detail',
    'receiving_create',
    'receiving_item_add',
    'receiving_approve',
    'receiving_reject',
    # API
    'api_approved_requests',
    'api_order_items',
]
