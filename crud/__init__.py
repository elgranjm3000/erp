# crud/__init__.py
"""
Módulo CRUD refactorizado para mejor organización y escalabilidad
"""

# Funciones de autenticación y usuarios
from .auth import (
    create_user,
    verify_password,
    authenticate_user,
    create_user_for_company,
    authenticate_multicompany,
    register_company_and_login,
    get_company_users,
    update_company_user,
    deactivate_company_user,
    update_user_profile,
    create_user_with_company
)

# Funciones de empresas
from .companies import (
    create_company_with_admin,
    get_company_dashboard,
    get_company_settings,
    update_company_settings,
    update_company
)

# Funciones de productos
from .products import (
    get_products,
    get_product_by_id,
    create_product,
    update_product,
    delete_product,
    get_products_by_company,
    get_product_by_id_and_company,
    create_product_for_company,
    update_product_for_company,
    delete_product_for_company,
    search_products_by_company,
    get_low_stock_products,
    get_products_by_category_and_company,
    get_products_stats_by_company,
    bulk_update_products_for_company
)

# Funciones de inventario
from .inventory import (
    create_or_update_warehouse_product,
    get_warehouse_products,
    get_warehouse_product,
    update_warehouse_product_stock,
    delete_warehouse_product,
    create_inventory_movement,
    create_inventory_movement_for_company,
    get_inventory_movements_by_company,
    get_inventory_movement_by_id_and_company,
    get_inventory_movements_by_product_and_company,
    get_inventory_movements_by_invoice,
    get_inventory_movements_stats_by_company,
    get_movements_stats_by_type_and_company,
    get_recent_inventory_movements_by_company,
    # Warehouse products
    create_or_update_warehouse_product_for_company,
    get_warehouse_products_by_company,
    get_warehouse_product_by_company,
    update_warehouse_product_stock_for_company,
    delete_warehouse_product_for_company,
    # Warehouses
    get_warehouses,
    create_warehouse,
    get_warehouses_by_company,
    get_warehouse_by_id_and_company,
    create_warehouse_for_company,
    get_warehouses_stats_by_company,
    update_warehouse_for_company,
    delete_warehouse_for_company
)

# Funciones de facturas
from .invoices import (
    create_invoice,
    view_invoice,
    edit_invoice,
    delete_invoice,
    create_budget,
    confirm_budget,
    create_invoice_for_company,
    view_invoice_by_company,
    edit_invoice_for_company,
    delete_invoice_for_company,
    get_invoices_by_company,
    get_invoices_stats_by_company,
    confirm_budget_for_company,
    create_credit_movement_for_company,
    get_invoices_by_customer_and_company,
    get_overdue_invoices_by_company,
    get_sales_summary_by_period
)

# Funciones de compras
from .purchases import (
    create_purchase,
    create_purchase_for_company,
    get_purchases_by_company,
    get_purchase_by_id_and_company,
    update_purchase_for_company,
    delete_purchase_for_company,
    update_purchase_status_for_company,
    get_purchases_stats_by_company,
    get_purchases_by_supplier_and_company,
    get_pending_purchases_by_company,
    get_purchases_summary_by_period,
    get_top_purchased_products_by_company,
    cancel_purchase_for_company,
    duplicate_purchase_for_company,
    create_purchase_from_low_stock,
    get_purchase_history_by_product
)

# Funciones de clientes (versión simplificada)
from .customers import (
    get_customers_by_company,
    get_customer_by_id_and_company,
    create_customer_for_company,
    update_customer_for_company,
    delete_customer_for_company,
    search_customers_by_company,
    get_customers_stats_by_company,
    get_top_customers_by_sales,
    get_customer_balance,
    get_invoices_by_customer_and_company,
    get_customers_by_type_and_company,
    get_customers_with_credit_limit,
    get_customers_activity_report,
    get_inactive_customers_report,
    get_customer_credit_status_report,
    reactivate_customer_for_company,
    merge_customers_for_company,
    bulk_update_customers_for_company,
    export_customers_for_company,
    import_customers_for_company
)

# Funciones de proveedores (versión simplificada)
from .suppliers import (
    get_suppliers_by_company,
    get_supplier_by_id_and_company,
    create_supplier_for_company,
    update_supplier_for_company,
    delete_supplier_for_company,
    search_suppliers_by_company,
    get_suppliers_stats_by_company,
    get_top_suppliers_by_purchases,
    get_purchases_by_supplier_and_company,
    get_suppliers_by_type_and_company,
    get_suppliers_by_credit_rating,
    get_supplier_performance_report,
    get_suppliers_payment_terms_report,
    get_inactive_suppliers_report,
    reactivate_supplier_for_company,
    bulk_update_suppliers_for_company,
    export_suppliers_for_company,
    import_suppliers_for_company,
    create_supplier_evaluation,
    get_supplier_evaluations,
    get_suppliers_by_product_category,
    get_supplier_product_catalog,
    suggest_alternative_suppliers
)

# Funciones legacy (mantener para compatibilidad)
from .base import (
    get_categories,
    create_category,
    get_categories_by_company,
    get_category_by_id_and_company,
    create_category_for_company,
    update_category_for_company,
    delete_category_for_company,
    get_categories_stats_by_company
)

# Exportar todo lo que antes estaba en crud.py
__all__ = [
    # Auth
    'create_user', 'verify_password', 'authenticate_user', 
    'authenticate_multicompany', 'register_company_and_login',
    'get_company_users', 'create_user_for_company', 'update_company_user',
    'deactivate_company_user', 'update_user_profile', 'create_user_with_company',
    
    # Companies
    'create_company_with_admin', 'get_company_dashboard', 'get_company_settings',
    'update_company_settings', 'update_company',
    
    # Products
    'get_products', 'get_product_by_id', 'create_product', 'update_product', 
    'delete_product', 'get_products_by_company', 'get_product_by_id_and_company',
    'create_product_for_company', 'update_product_for_company', 'delete_product_for_company',
    'search_products_by_company', 'get_low_stock_products', 'get_products_by_category_and_company',
    'get_products_stats_by_company', 'bulk_update_products_for_company',
    
    # Inventory
    'create_or_update_warehouse_product', 'get_warehouse_products', 'get_warehouse_product',
    'update_warehouse_product_stock', 'delete_warehouse_product', 'create_inventory_movement',
    'get_warehouses', 'create_warehouse', 'create_inventory_movement_for_company',
    'get_inventory_movements_by_company', 'get_inventory_movement_by_id_and_company',
    'get_inventory_movements_by_product_and_company', 'get_inventory_movements_by_invoice',
    'get_warehouses_by_company', 'get_warehouse_by_id_and_company', 'create_warehouse_for_company',
    
    # Invoices
    'create_invoice', 'view_invoice', 'edit_invoice', 'delete_invoice',
    'create_budget', 'confirm_budget', 'create_invoice_for_company',
    'view_invoice_by_company', 'edit_invoice_for_company', 'delete_invoice_for_company',
    'get_invoices_by_company', 'get_invoices_stats_by_company', 'confirm_budget_for_company',
    
    # Purchases
    'create_purchase', 'create_purchase_for_company', 'get_purchases_by_company',
    'get_purchase_by_id_and_company', 'update_purchase_for_company', 'delete_purchase_for_company',
    'update_purchase_status_for_company', 'get_purchases_stats_by_company',
    
    # Customers
    'get_customers_by_company', 'get_customer_by_id_and_company', 'create_customer_for_company',
    'update_customer_for_company', 'delete_customer_for_company', 'search_customers_by_company',
    'get_customers_stats_by_company', 'get_top_customers_by_sales', 'get_customer_balance',
    'get_invoices_by_customer_and_company',
    
    # Suppliers  
    'get_suppliers_by_company', 'get_supplier_by_id_and_company', 'create_supplier_for_company',
    'update_supplier_for_company', 'delete_supplier_for_company', 'search_suppliers_by_company',
    'get_suppliers_stats_by_company', 'get_top_suppliers_by_purchases',
    'get_purchases_by_supplier_and_company',
    
    # Base/Categories
    'get_categories', 'create_category', 'get_categories_by_company'
]