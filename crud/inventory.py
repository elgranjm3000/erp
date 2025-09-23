# crud/inventory.py
"""
Funciones CRUD para gestión de inventario, almacenes y movimientos
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import List, Optional
import models
import schemas
from .base import verify_company_ownership, paginate_query

# ================= WAREHOUSE PRODUCTS =================

def create_or_update_warehouse_product(db: Session, wp_data: schemas.WarehouseProductCreate):
    """Legacy: crear o actualizar producto en almacén"""
    wp = db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == wp_data.warehouse_id,
        models.WarehouseProduct.product_id == wp_data.product_id,
    ).first()

    if wp:
        wp.stock = wp_data.stock
    else:
        wp = models.WarehouseProduct(**wp_data.dict())
        db.add(wp)

    db.commit()
    db.refresh(wp)
    return wp

def get_warehouse_products(db: Session, skip: int = 0, limit: int = 100):
    """Legacy: obtener productos de almacén"""
    return paginate_query(
        db.query(models.WarehouseProduct),
        skip=skip,
        limit=limit
    ).all()

def get_warehouse_product(db: Session, warehouse_id: int, product_id: int):
    """Obtener producto específico de almacén"""
    return db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id,
        models.WarehouseProduct.product_id == product_id,
    ).first()

def update_warehouse_product_stock(
    db: Session, 
    warehouse_id: int, 
    product_id: int, 
    stock: int
):
    """Actualizar stock de producto en almacén"""
    wp = get_warehouse_product(db, warehouse_id, product_id)
    
    if not wp:
        return None

    wp.stock = stock
    db.commit()
    db.refresh(wp)
    return wp

def delete_warehouse_product(db: Session, warehouse_id: int, product_id: int):
    """Eliminar producto de almacén"""
    wp = get_warehouse_product(db, warehouse_id, product_id)
    
    if not wp:
        return None

    db.delete(wp)
    db.commit()
    return wp

# ================= WAREHOUSE PRODUCTS CON EMPRESA =================

def create_or_update_warehouse_product_for_company(
    db: Session, 
    wp_data: schemas.WarehouseProductCreate, 
    company_id: int
):
    """Crear o actualizar producto en almacén de empresa específica"""
    # Verificar que el almacén pertenezca a la empresa
    warehouse = verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=wp_data.warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )
    
    # Verificar que el producto pertenezca a la empresa
    product = verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=wp_data.product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    return create_or_update_warehouse_product(db, wp_data)

def get_warehouse_products_by_company(
    db: Session, 
    company_id: int, 
    skip: int = 0, 
    limit: int = 100
):
    """Obtener productos de almacenes de una empresa"""
    return paginate_query(
        db.query(models.WarehouseProduct).join(
            models.Warehouse, 
            models.WarehouseProduct.warehouse_id == models.Warehouse.id
        ).filter(
            models.Warehouse.company_id == company_id
        ),
        skip=skip,
        limit=limit
    ).all()

def get_warehouse_product_by_company(
    db: Session, 
    warehouse_id: int, 
    product_id: int, 
    company_id: int
):
    """Obtener producto específico de almacén de empresa"""
    # Verificar pertenencia a empresa
    verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )
    
    verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    return get_warehouse_product(db, warehouse_id, product_id)

def update_warehouse_product_stock_for_company(
    db: Session, 
    warehouse_id: int, 
    product_id: int, 
    stock: int, 
    company_id: int
):
    """Actualizar stock de producto en almacén de empresa"""
    # Verificar pertenencia
    verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )
    
    verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    return update_warehouse_product_stock(db, warehouse_id, product_id, stock)

def delete_warehouse_product_for_company(
    db: Session, 
    warehouse_id: int, 
    product_id: int, 
    company_id: int
):
    """Eliminar producto de almacén de empresa"""
    # Verificar pertenencia
    verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )
    
    verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    return delete_warehouse_product(db, warehouse_id, product_id)

# ================= WAREHOUSES =================

def get_warehouses(db: Session, skip: int = 0, limit: int = 100):
    """Legacy: obtener almacenes"""
    return paginate_query(
        db.query(models.Warehouse),
        skip=skip,
        limit=limit
    ).all()

def create_warehouse(db: Session, warehouse: schemas.WarehouseCreate):
    """Legacy: crear almacén"""
    db_warehouse = models.Warehouse(**warehouse.dict())
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

def get_warehouses_by_company(
    db: Session, 
    company_id: int, 
    skip: int = 0, 
    limit: int = 100
):
    """Obtener almacenes de una empresa"""
    return paginate_query(
        db.query(models.Warehouse).filter(
            models.Warehouse.company_id == company_id
        ),
        skip=skip,
        limit=limit
    ).all()

def get_warehouse_by_id_and_company(db: Session, warehouse_id: int, company_id: int):
    """Obtener almacén específico de una empresa"""
    return verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )

def create_warehouse_for_company(
    db: Session, 
    warehouse: schemas.WarehouseCreate, 
    company_id: int
):
    """Crear almacén para empresa específica"""
    db_warehouse = models.Warehouse(
        company_id=company_id,
        **warehouse.dict()
    )
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

def update_warehouse_for_company(
    db: Session, 
    warehouse_id: int, 
    warehouse_data: schemas.WarehouseUpdate, 
    company_id: int
):
    """Actualizar almacén de empresa"""
    warehouse = verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )
    
    for key, value in warehouse_data.dict(exclude_unset=True).items():
        setattr(warehouse, key, value)
    
    db.commit()
    db.refresh(warehouse)
    return warehouse

def delete_warehouse_for_company(db: Session, warehouse_id: int, company_id: int):
    """Eliminar almacén de empresa"""
    warehouse = verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )
    
    # Verificar si tiene productos asignados
    products_count = db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id
    ).count()
    
    if products_count > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete warehouse with assigned products"
        )
    
    db.delete(warehouse)
    db.commit()
    return {"message": "Warehouse deleted successfully"}

# ================= MOVIMIENTOS DE INVENTARIO =================

def create_inventory_movement(db: Session, movement: schemas.InventoryMovementCreate):
    """Legacy: crear movimiento de inventario"""
    db_movement = models.InventoryMovement(**movement.dict())
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement

def create_inventory_movement_for_company(
    db: Session, 
    movement: schemas.InventoryMovementCreate, 
    company_id: int
):
    """Crear movimiento de inventario para empresa específica"""
    # Verificar que el producto pertenezca a la empresa
    verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=movement.product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    return create_inventory_movement(db, movement)

def get_inventory_movements_by_company(
    db: Session, 
    company_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    movement_type: Optional[str] = None, 
    product_id: Optional[int] = None
):
    """Obtener movimientos de inventario de una empresa"""
    query = db.query(models.InventoryMovement).join(
        models.Product, 
        models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.Product.company_id == company_id
    )
    
    if movement_type:
        query = query.filter(models.InventoryMovement.movement_type == movement_type)
    
    if product_id:
        query = query.filter(models.InventoryMovement.product_id == product_id)
    
    return paginate_query(query, skip=skip, limit=limit).all()

def get_inventory_movement_by_id_and_company(
    db: Session, 
    movement_id: int, 
    company_id: int
):
    """Obtener movimiento específico de empresa"""
    movement = db.query(models.InventoryMovement).join(
        models.Product, 
        models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.InventoryMovement.id == movement_id,
        models.Product.company_id == company_id
    ).first()
    
    if not movement:
        raise HTTPException(
            status_code=404, 
            detail="Movement not found in your company"
        )
    
    return movement

def get_inventory_movements_by_product_and_company(
    db: Session, 
    product_id: int, 
    company_id: int
):
    """Obtener movimientos de un producto específico de empresa"""
    verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    return db.query(models.InventoryMovement).filter(
        models.InventoryMovement.product_id == product_id
    ).all()

def get_inventory_movements_by_invoice(db: Session, invoice_id: int):
    """Obtener movimientos de una factura"""
    return db.query(models.InventoryMovement).filter(
        models.InventoryMovement.invoice_id == invoice_id
    ).all()

# ================= ESTADÍSTICAS DE INVENTARIO =================

def get_inventory_movements_stats_by_company(db: Session, company_id: int):
    """Estadísticas de movimientos por empresa"""
    total_movements = db.query(models.InventoryMovement).join(
        models.Product, 
        models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.Product.company_id == company_id
    ).count()
    
    return {"total_movements": total_movements}

def get_movements_stats_by_type_and_company(db: Session, company_id: int):
    """Estadísticas de movimientos por tipo"""
    movements_by_type = db.query(
        models.InventoryMovement.movement_type,
        func.count(models.InventoryMovement.id)
    ).join(
        models.Product, 
        models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.Product.company_id == company_id
    ).group_by(models.InventoryMovement.movement_type).all()
    
    return {movement_type: count for movement_type, count in movements_by_type}

def get_recent_inventory_movements_by_company(
    db: Session, 
    company_id: int, 
    days: int = 7, 
    limit: int = 50
):
    """Obtener movimientos recientes de empresa"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    return db.query(models.InventoryMovement).join(
        models.Product, 
        models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.Product.company_id == company_id,
        models.InventoryMovement.timestamp >= cutoff_date
    ).order_by(
        models.InventoryMovement.timestamp.desc()
    ).limit(limit).all()

def get_warehouses_stats_by_company(db: Session, company_id: int):
    """Estadísticas de almacenes por empresa"""
    total_warehouses = db.query(models.Warehouse).filter(
        models.Warehouse.company_id == company_id
    ).count()
    
    return {"total_warehouses": total_warehouses}

# ================= FUNCIONES ADICIONALES DE WAREHOUSE PRODUCTS =================

def get_warehouse_products_by_warehouse_and_company(
    db: Session,
    warehouse_id: int,
    company_id: int
):
    """Obtener productos de un almacén específico de una empresa"""
    verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )
    
    return db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id
    ).all()

def get_warehouse_products_by_product_and_company(
    db: Session,
    product_id: int,
    company_id: int
):
    """Obtener almacenes donde está un producto específico"""
    verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    return db.query(models.WarehouseProduct).join(
        models.Warehouse,
        models.WarehouseProduct.warehouse_id == models.Warehouse.id
    ).filter(
        models.WarehouseProduct.product_id == product_id,
        models.Warehouse.company_id == company_id
    ).all()

def get_low_stock_warehouse_products_by_company(
    db: Session,
    company_id: int,
    threshold: int = 10
):
    """Obtener productos con stock bajo en todos los almacenes de una empresa"""
    return db.query(models.WarehouseProduct).join(
        models.Warehouse,
        models.WarehouseProduct.warehouse_id == models.Warehouse.id
    ).filter(
        models.Warehouse.company_id == company_id,
        models.WarehouseProduct.stock <= threshold
    ).all()

def get_warehouse_products_by_warehouse(db: Session, warehouse_id: int):
    """Obtener productos de un almacén específico"""
    return db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id
    ).all()

def get_low_stock_products_by_warehouse(
    db: Session,
    warehouse_id: int,
    threshold: int = 10
):
    """Obtener productos con stock bajo en un almacén específico"""
    return db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id,
        models.WarehouseProduct.stock <= threshold
    ).all()

# ================= OPERACIONES AVANZADAS DE INVENTARIO =================

def transfer_stock_between_warehouses(
    db: Session,
    from_warehouse_id: int,
    to_warehouse_id: int,
    product_id: int,
    quantity: int,
    company_id: int
):
    """Transferir stock entre almacenes de la misma empresa"""
    # Verificar que ambos almacenes pertenezcan a la empresa
    from_warehouse = verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=from_warehouse_id,
        company_id=company_id,
        error_message="Source warehouse not found in your company"
    )
    
    to_warehouse = verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=to_warehouse_id,
        company_id=company_id,
        error_message="Destination warehouse not found in your company"
    )
    
    # Verificar que el producto pertenezca a la empresa
    product = verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    # Verificar stock disponible en almacén origen
    from_wp = get_warehouse_product(db, from_warehouse_id, product_id)
    if not from_wp or from_wp.stock < quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock in source warehouse"
        )
    
    # Obtener o crear registro en almacén destino
    to_wp = get_warehouse_product(db, to_warehouse_id, product_id)
    if not to_wp:
        to_wp = models.WarehouseProduct(
            warehouse_id=to_warehouse_id,
            product_id=product_id,
            stock=0
        )
        db.add(to_wp)
    
    try:
        # Realizar transferencia
        from_wp.stock -= quantity
        to_wp.stock += quantity
        
        # Crear movimientos de inventario
        # Salida del almacén origen
        out_movement = models.InventoryMovement(
            product_id=product_id,
            movement_type="transfer_out",
            quantity=quantity,
            timestamp=datetime.utcnow(),
            description=f"Transfer to warehouse {to_warehouse.name}",
            warehouse_id=from_warehouse_id
        )
        
        # Entrada al almacén destino
        in_movement = models.InventoryMovement(
            product_id=product_id,
            movement_type="transfer_in",
            quantity=quantity,
            timestamp=datetime.utcnow(),
            description=f"Transfer from warehouse {from_warehouse.name}",
            warehouse_id=to_warehouse_id
        )
        
        db.add(out_movement)
        db.add(in_movement)
        db.commit()
        
        return {
            "message": "Stock transferred successfully",
            "from_warehouse": from_warehouse.name,
            "to_warehouse": to_warehouse.name,
            "product": product.name,
            "quantity": quantity,
            "from_remaining_stock": from_wp.stock,
            "to_new_stock": to_wp.stock
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Transfer failed: {str(e)}"
        )

def adjust_warehouse_product_stock(
    db: Session,
    warehouse_id: int,
    product_id: int,
    adjustment: int,
    reason: str,
    company_id: int
):
    """Ajustar stock por diferencias de inventario"""
    # Verificar pertenencia a empresa
    warehouse = verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )
    
    product = verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    # Obtener o crear registro de warehouse product
    wp = get_warehouse_product(db, warehouse_id, product_id)
    if not wp:
        if adjustment < 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot make negative adjustment to non-existent stock"
            )
        wp = models.WarehouseProduct(
            warehouse_id=warehouse_id,
            product_id=product_id,
            stock=0
        )
        db.add(wp)
    
    old_stock = wp.stock
    new_stock = old_stock + adjustment
    
    if new_stock < 0:
        raise HTTPException(
            status_code=400,
            detail="Stock cannot be negative"
        )
    
    try:
        # Actualizar stock
        wp.stock = new_stock
        
        # Crear movimiento de inventario
        movement_type = "adjustment_in" if adjustment > 0 else "adjustment_out"
        movement = models.InventoryMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=abs(adjustment),
            timestamp=datetime.utcnow(),
            description=f"Stock adjustment: {reason}",
            warehouse_id=warehouse_id
        )
        
        db.add(movement)
        db.commit()
        
        return {
            "message": "Stock adjusted successfully",
            "warehouse": warehouse.name,
            "product": product.name,
            "old_stock": old_stock,
            "adjustment": adjustment,
            "new_stock": new_stock,
            "reason": reason
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Stock adjustment failed: {str(e)}"
        )

def get_inventory_valuation_by_warehouse(
    db: Session,
    warehouse_id: int,
    company_id: int
):
    """Obtener valorización del inventario de un almacén"""
    verify_company_ownership(
        db=db,
        model_class=models.Warehouse,
        item_id=warehouse_id,
        company_id=company_id,
        error_message="Warehouse not found in your company"
    )
    
    valuation = db.query(
        models.Product.name,
        models.Product.sku,
        models.Product.price,
        models.WarehouseProduct.stock,
        (models.Product.price * models.WarehouseProduct.stock).label('total_value')
    ).join(
        models.WarehouseProduct,
        models.Product.id == models.WarehouseProduct.product_id
    ).filter(
        models.Product.company_id == company_id,
        models.WarehouseProduct.warehouse_id == warehouse_id
    ).all()
    
    total_value = sum(item.total_value for item in valuation)
    
    return {
        "warehouse_id": warehouse_id,
        "products": valuation,
        "total_value": total_value,
        "products_count": len(valuation)
    }

def get_stock_movements_summary(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime
):
    """Resumen de movimientos de stock en un período"""
    movements = db.query(
        models.InventoryMovement.movement_type,
        func.sum(models.InventoryMovement.quantity).label('total_quantity'),
        func.count(models.InventoryMovement.id).label('movements_count')
    ).join(
        models.Product,
        models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.Product.company_id == company_id,
        models.InventoryMovement.timestamp >= start_date,
        models.InventoryMovement.timestamp <= end_date
    ).group_by(
        models.InventoryMovement.movement_type
    ).all()
    
    return {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "movements_by_type": {
            movement.movement_type: {
                "total_quantity": movement.total_quantity,
                "movements_count": movement.movements_count
            }
            for movement in movements
        }
    }