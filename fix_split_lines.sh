#!/bin/bash

# movements_list.html lines 64-65
sed -i '64,65c\                    <option value="{{ warehouse.id }}" {% if selected_warehouse == warehouse.id|stringformat:"s" %}selected{% endif %}>{{ warehouse.code }} - {{ warehouse.name }}</option>' templates/inventory/movements_list.html

# inventory_count_list.html lines 149-150
sed -i '149,150c\                            <option value="{{ warehouse.id }}" {% if selected_warehouse == warehouse.id|stringformat:"s" %}selected{% endif %}>{{ warehouse.code }}</option>' templates/inventory/inventory_count_list.html

# stock_list.html lines 48-49
sed -i '48,49c\                    <option value="{{ warehouse.id }}" {% if selected_warehouse == warehouse.id|stringformat:"s" %}selected{% endif %}>' templates/inventory/stock_list.html

# batch_list.html lines 66-67
sed -i "66,67c\                            <option value=\"{{ order.id }}\" {% if order_filter == order.id|stringformat:'s' %}selected{% endif %}>{{ order.order_number }}</option>" templates/production/batch_list.html

# bin_list.html lines 68-69
sed -i "68,69c\                            <option value=\"{{ wh.id }}\" {% if warehouse_filter == wh.id|stringformat:'s' %}selected{% endif %}>" templates/production/bin_list.html

echo "Split line fixes applied."
