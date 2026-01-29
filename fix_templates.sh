#!/bin/bash

# inventory/movements_list.html
sed -i 's/selected_movement_type==type_code/selected_movement_type == type_code/g' templates/inventory/movements_list.html
sed -i 's/selected_warehouse==warehouse.id|stringformat:"s"/selected_warehouse == warehouse.id|stringformat:"s"/g' templates/inventory/movements_list.html

# inventory/inventory_count_list.html
sed -i 's/status_filter==status_code/status_filter == status_code/g' templates/inventory/inventory_count_list.html
sed -i 's/selected_warehouse==warehouse.id|stringformat:"s"/selected_warehouse == warehouse.id|stringformat:"s"/g' templates/inventory/inventory_count_list.html

# inventory/stock_list.html
sed -i 's/selected_warehouse==warehouse.id|stringformat:"s"/selected_warehouse == warehouse.id|stringformat:"s"/g' templates/inventory/stock_list.html
sed -i 's/selected_material_type==type_code/selected_material_type == type_code/g' templates/inventory/stock_list.html
sed -i "s/selected_stock_status=='normal'/selected_stock_status == 'normal'/g" templates/inventory/stock_list.html
sed -i "s/selected_stock_status=='low'/selected_stock_status == 'low'/g" templates/inventory/stock_list.html
sed -i "s/selected_stock_status=='out'/selected_stock_status == 'out'/g" templates/inventory/stock_list.html

# inventory/reservations_list.html
sed -i "s/status=='active'/status == 'active'/g" templates/inventory/reservations_list.html
sed -i "s/status=='expired'/status == 'expired'/g" templates/inventory/reservations_list.html

# production/production_order_list.html
sed -i "s/status_filter=='DRAFT'/status_filter == 'DRAFT'/g" templates/production/production_order_list.html
sed -i "s/status_filter=='PLANNED'/status_filter == 'PLANNED'/g" templates/production/production_order_list.html
sed -i "s/status_filter=='IN_PROGRESS'/status_filter == 'IN_PROGRESS'/g" templates/production/production_order_list.html
sed -i "s/status_filter=='COMPLETED'/status_filter == 'COMPLETED'/g" templates/production/production_order_list.html
sed -i "s/status_filter=='CANCELLED'/status_filter == 'CANCELLED'/g" templates/production/production_order_list.html

# production/batch_list.html
sed -i "s/status_filter=='PREPARATION'/status_filter == 'PREPARATION'/g" templates/production/batch_list.html
sed -i "s/status_filter=='READY'/status_filter == 'READY'/g" templates/production/batch_list.html
sed -i "s/status_filter=='IN_PRODUCTION'/status_filter == 'IN_PRODUCTION'/g" templates/production/batch_list.html
sed -i "s/status_filter=='COMPLETED'/status_filter == 'COMPLETED'/g" templates/production/batch_list.html
sed -i "s/status_filter=='CANCELLED'/status_filter == 'CANCELLED'/g" templates/production/batch_list.html
sed -i "s/order_filter==order.id|stringformat:'s'/order_filter == order.id|stringformat:'s'/g" templates/production/batch_list.html

# production/bin_list.html
sed -i "s/warehouse_filter==wh.id|stringformat:'s'/warehouse_filter == wh.id|stringformat:'s'/g" templates/production/bin_list.html
sed -i "s/status_filter=='EMPTY'/status_filter == 'EMPTY'/g" templates/production/bin_list.html
sed -i "s/status_filter=='LOADED'/status_filter == 'LOADED'/g" templates/production/bin_list.html
sed -i "s/status_filter=='IN_USE'/status_filter == 'IN_USE'/g" templates/production/bin_list.html
sed -i "s/status_filter=='MAINTENANCE'/status_filter == 'MAINTENANCE'/g" templates/production/bin_list.html

echo "Fixes applied."
