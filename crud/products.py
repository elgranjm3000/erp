# crud/products.py
"""
Funciones CRUD para gestión de productos
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException
from typing import List, Optional
import models
import schemas
from .base import verify_company_ownership, apply_search_filter, paginate_query

# ================= FUNCIONES LEGACY (MANTENER COMPATIBILIDAD) =================

def get_products(db: Session, skip: int = 0, limit: int = 100):
    """Legacy: obtener productos sin filtro de empresa"""
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_product_by_id(db: Session, product_id: int):
    """Legacy: obtener producto por ID sin validar empresa"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

def create_product(db: Session, product: schemas.ProductCreate):
    """Legacy: crear producto sin empresa específica"""
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_data: schemas.ProductUpdate):
    """Legacy: actualizar producto sin validar empresa"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    """Legacy: eliminar producto sin validar empresa"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted successfully"}

# ================= FUNCIONES MULTIEMPRESA =================

def get_products_by_company(
    db: Session,
    company_id: int,
    skip: int = 0,
    limit: int = 100
):
    """Obtener productos de una empresa específica"""
    from sqlalchemy.orm import joinedload
    return paginate_query(
        db.query(models.Product)
        .options(
            joinedload(models.Product.category),
            joinedload(models.Product.currency),
            joinedload(models.Product.warehouse)
        )
        .filter(models.Product.company_id == company_id),
        skip=skip,
        limit=limit
    ).all()

def get_product_by_id_and_company(db: Session, product_id: int, company_id: int):
    """Obtener producto específico de una empresa"""
    return verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )

def get_product_with_warehouses_by_company(db: Session, product_id: int, company_id: int):
    """Obtener producto con información de stock en todos los almacenes"""
    # Obtener el producto con eager loading de relaciones
    from sqlalchemy.orm import joinedload
    product = db.query(models.Product).options(
        joinedload(models.Product.category),
        joinedload(models.Product.warehouse)
    ).filter(
        models.Product.id == product_id,
        models.Product.company_id == company_id
    ).first()

    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found in your company")

    # Obtener stock en todos los almacenes
    warehouse_stocks = db.query(
        models.WarehouseProduct.warehouse_id,
        models.WarehouseProduct.stock,
        models.Warehouse.name,
        models.Warehouse.location
    ).join(
        models.Warehouse,
        models.WarehouseProduct.warehouse_id == models.Warehouse.id
    ).filter(
        models.WarehouseProduct.product_id == product_id,
        models.Warehouse.company_id == company_id
    ).all()

    # Convertir a lista de diccionarios
    warehouses_info = [
        {
            'warehouse_id': ws.warehouse_id,
            'warehouse_name': ws.name,
            'warehouse_location': ws.location,
            'stock': ws.stock
        }
        for ws in warehouse_stocks
    ]

    # Construir resultado
    product_dict = {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'quantity': product.quantity,
        'category_id': product.category_id,
        'sku': product.sku,
        'company_id': product.company_id,
        'warehouse_id': product.warehouse_id,  # ✅ Agregado: Depósito/Almacén del producto
        'warehouse': {
            'id': product.warehouse.id,
            'name': product.warehouse.name,
            'location': product.warehouse.location
        } if product.warehouse else None,  # ✅ Datos completos del warehouse
        'category': {
            'id': product.category.id,
            'name': product.category.name,
            'description': product.category.description
        } if product.category else None,
        'warehouses': warehouses_info
    }

    return product_dict

def create_product_for_company(
    db: Session, 
    product: schemas.ProductCreate, 
    company_id: int
):
    """Crear producto para empresa específica"""
    
    # Generar SKU automático si no se proporciona
    if not product.sku:
        count = db.query(models.Product).filter(
            models.Product.company_id == company_id
        ).count()
        product.sku = f"PRD-{count + 1:06d}"
    
    # Verificar que el SKU no exista en la empresa
    existing_sku = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.sku == product.sku
    ).first()
    
    if existing_sku:
        raise HTTPException(
            status_code=400, 
            detail="SKU already exists in this company"
        )
    
    # Crear producto (excluir currency_id ya que está en ProductPrice, no en Product)
    product_data_dict = product.dict()
    product_data_dict.pop('currency_id', None)  # Remover currency_id si existe

    db_product = models.Product(
        company_id=company_id,
        **product_data_dict
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product_for_company(
    db: Session, 
    product_id: int, 
    product_data: schemas.ProductUpdate, 
    company_id: int
):
    """Actualizar producto de una empresa"""
    product = verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    # Si se actualiza el SKU, verificar que no exista
    if hasattr(product_data, 'sku') and product_data.sku:
        existing_sku = db.query(models.Product).filter(
            models.Product.company_id == company_id,
            models.Product.sku == product_data.sku,
            models.Product.id != product_id  # Excluir el producto actual
        ).first()
        
        if existing_sku:
            raise HTTPException(
                status_code=400,
                detail="SKU already exists in this company"
            )
    
    # Actualizar campos
    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

def delete_product_for_company(db: Session, product_id: int, company_id: int):
    """Eliminar producto de una empresa"""
    product = verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    # Verificar si el producto tiene movimientos de inventario
    has_movements = db.query(models.InventoryMovement).filter(
        models.InventoryMovement.product_id == product_id
    ).first()
    
    if has_movements:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product with inventory movements"
        )
    
    # Verificar si está en facturas
    has_invoices = db.query(models.InvoiceItem).filter(
        models.InvoiceItem.product_id == product_id
    ).first()
    
    if has_invoices:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product used in invoices"
        )
    
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted successfully"}

# ================= FUNCIONES DE BÚSQUEDA Y FILTROS =================

def search_products_by_company(db: Session, company_id: int, search_term: str):
    """Buscar productos por nombre o SKU en una empresa"""
    query = db.query(models.Product).filter(
        models.Product.company_id == company_id
    )
    
    return apply_search_filter(
        query=query,
        model_class=models.Product,
        search_term=search_term,
        fields=['name', 'sku', 'description']
    ).all()

def get_low_stock_products(db: Session, company_id: int, threshold: int = 10):
    """Obtener productos con stock bajo"""
    return db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity <= threshold
    ).all()

def get_products_by_category_and_company(
    db: Session, 
    company_id: int, 
    category_id: int
):
    """Obtener productos de una categoría específica"""
    return db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.category_id == category_id
    ).all()

def get_products_by_warehouse_and_company(
    db: Session,
    company_id: int,
    warehouse_id: int
):
    """Obtener productos disponibles en un almacén específico"""
    return db.query(models.Product).join(
        models.WarehouseProduct,
        models.Product.id == models.WarehouseProduct.product_id
    ).filter(
        models.Product.company_id == company_id,
        models.WarehouseProduct.warehouse_id == warehouse_id,
        models.WarehouseProduct.stock > 0
    ).all()

# ================= ESTADÍSTICAS Y REPORTES =================

def get_products_stats_by_company(db: Session, company_id: int):
    """Estadísticas de productos por empresa"""
    total_products = db.query(models.Product).filter(
        models.Product.company_id == company_id
    ).count()
    
    total_value = db.query(
        func.sum(models.Product.price * models.Product.quantity)
    ).filter(
        models.Product.company_id == company_id
    ).scalar() or 0
    
    low_stock_count = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity <= 10
    ).count()
    
    out_of_stock_count = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity == 0
    ).count()
    
    categories_count = db.query(models.Category).filter(
        models.Category.company_id == company_id
    ).count()
    
    return {
        "total_products": total_products,
        "total_value": float(total_value),
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "categories_count": categories_count,
        "average_price": float(total_value / total_products) if total_products > 0 else 0
    }

def get_top_products_by_sales(
    db: Session, 
    company_id: int, 
    limit: int = 10
):
    """Top productos por volumen de ventas"""
    return db.query(
        models.Product,
        func.sum(models.InvoiceItem.quantity).label('total_sold'),
        func.sum(models.InvoiceItem.total_price).label('total_revenue')
    ).join(
        models.InvoiceItem,
        models.Product.id == models.InvoiceItem.product_id
    ).join(
        models.Invoice,
        models.InvoiceItem.invoice_id == models.Invoice.id
    ).filter(
        models.Product.company_id == company_id,
        models.Invoice.status == 'factura'
    ).group_by(
        models.Product.id
    ).order_by(
        func.sum(models.InvoiceItem.quantity).desc()
    ).limit(limit).all()

def get_products_valuation_by_company(db: Session, company_id: int):
    """Valorización del inventario por empresa"""
    products = db.query(
        models.Product.name,
        models.Product.sku,
        models.Product.quantity,
        models.Product.price,
        (models.Product.quantity * models.Product.price).label('total_value')
    ).filter(
        models.Product.company_id == company_id
    ).all()
    
    total_inventory_value = sum(p.total_value for p in products)
    
    return {
        "products": products,
        "total_inventory_value": total_inventory_value,
        "products_count": len(products)
    }

# ================= OPERACIONES MASIVAS =================

def bulk_update_products_for_company(
    db: Session, 
    company_id: int, 
    updates: List[schemas.ProductBulkUpdate]
):
    """Actualización masiva de productos"""
    results = []
    errors = []
    
    try:
        for update in updates:
            try:
                product = verify_company_ownership(
                    db=db,
                    model_class=models.Product,
                    item_id=update.product_id,
                    company_id=company_id,
                    error_message=f"Product {update.product_id} not found"
                )
                
                if update.price is not None:
                    product.price = update.price
                if update.quantity is not None:
                    product.quantity = update.quantity
                if update.name is not None:
                    product.name = update.name
                
                results.append(product)
                
            except HTTPException as e:
                errors.append({
                    "product_id": update.product_id,
                    "error": e.detail
                })
        
        if results and not errors:
            db.commit()
            return {
                "updated_products": len(results),
                "message": "Bulk update completed successfully",
                "errors": errors
            }
        elif errors:
            db.rollback()
            return {
                "updated_products": 0,
                "message": "Bulk update failed",
                "errors": errors
            }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Bulk update failed: {str(e)}"
        )

def bulk_import_products_for_company(
    db: Session,
    company_id: int,
    products_data: List[schemas.ProductCreate]
):
    """Importación masiva de productos"""
    created_products = []
    errors = []
    
    try:
        for i, product_data in enumerate(products_data):
            try:
                # Generar SKU si no existe
                if not product_data.sku:
                    count = db.query(models.Product).filter(
                        models.Product.company_id == company_id
                    ).count()
                    product_data.sku = f"PRD-{count + len(created_products) + 1:06d}"
                
                # Verificar SKU único
                existing = db.query(models.Product).filter(
                    models.Product.company_id == company_id,
                    models.Product.sku == product_data.sku
                ).first()
                
                if existing:
                    errors.append({
                        "row": i + 1,
                        "sku": product_data.sku,
                        "error": "SKU already exists"
                    })
                    continue
                
                # Crear producto
                db_product = models.Product(
                    company_id=company_id,
                    **product_data.dict()
                )
                
                db.add(db_product)
                created_products.append(db_product)
                
            except Exception as e:
                errors.append({
                    "row": i + 1,
                    "error": str(e)
                })
        
        if created_products and not errors:
            db.commit()
            return {
                "imported_products": len(created_products),
                "message": "Import completed successfully",
                "errors": []
            }
        elif errors:
            db.rollback()
            return {
                "imported_products": 0,
                "message": "Import failed",
                "errors": errors
            }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )