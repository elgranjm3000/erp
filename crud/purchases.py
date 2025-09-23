# crud/purchases.py
"""
Funciones CRUD para gestión de compras
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException
from datetime import datetime
from typing import List, Optional
import models
import schemas
from .base import verify_company_ownership, paginate_query

# ================= FUNCIONES LEGACY (MANTENER COMPATIBILIDAD) =================

def create_purchase(db: Session, purchase_data: schemas.Purchase):
    """Legacy: crear compra sin empresa específica"""
    return create_purchase_for_company(db, purchase_data, 1)

# ================= FUNCIONES MULTIEMPRESA =================

def create_purchase_for_company(
    db: Session, 
    purchase_data: schemas.PurchaseCreate, 
    company_id: int
):
    """Crear compra para empresa específica"""
    
    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Verificar que el proveedor pertenezca a la empresa
    if hasattr(purchase_data, 'supplier_id') and purchase_data.supplier_id:
        supplier = verify_company_ownership(
            db=db,
            model_class=models.Supplier,
            item_id=purchase_data.supplier_id,
            company_id=company_id,
            error_message="Supplier not found in your company"
        )
    
    # Verificar que el almacén pertenezca a la empresa
    if hasattr(purchase_data, 'warehouse_id') and purchase_data.warehouse_id:
        warehouse = verify_company_ownership(
            db=db,
            model_class=models.Warehouse,
            item_id=purchase_data.warehouse_id,
            company_id=company_id,
            error_message="Warehouse not found in your company"
        )
    
    # Generar número de compra
    purchase_count = db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id
    ).count()
    purchase_number = f"PUR-{purchase_count + 1:06d}"
    
    try:
        # Crear compra
        purchase = models.Purchase(
            company_id=company_id,
            supplier_id=getattr(purchase_data, 'supplier_id', None),
            warehouse_id=getattr(purchase_data, 'warehouse_id', None),
            purchase_number=purchase_number,
            date=getattr(purchase_data, 'date', datetime.utcnow().date()),
            status=getattr(purchase_data, 'status', 'pending'),
            total_amount=0,
            notes=getattr(purchase_data, 'notes', None),
            reference=getattr(purchase_data, 'reference', None)
        )
        
        db.add(purchase)
        db.flush()  # Para obtener el ID
        
        total_amount = 0
        
        # Procesar items si existen
        if hasattr(purchase_data, 'items') and purchase_data.items:
            for item_data in purchase_data.items:
                # Verificar que el producto pertenezca a la empresa
                product = verify_company_ownership(
                    db=db,
                    model_class=models.Product,
                    item_id=item_data.product_id,
                    company_id=company_id,
                    error_message="Product not found in your company"
                )
                
                # Calcular precio
                unit_cost = getattr(item_data, 'unit_cost', product.price)
                line_total = unit_cost * item_data.quantity
                
                # Crear item de compra
                purchase_item = models.PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=product.id,
                    quantity=item_data.quantity,
                    unit_cost=unit_cost,
                    total_cost=line_total
                )
                
                db.add(purchase_item)
                total_amount += line_total
                
                # Si la compra está confirmada, actualizar stock
                if purchase.status == 'received':
                    product.quantity += item_data.quantity
                    
                    # Actualizar costo del producto si es diferente
                    if unit_cost != product.price:
                        product.price = unit_cost  # O usar promedio ponderado
                    
                    # Crear movimiento de inventario
                    movement = models.InventoryMovement(
                        product_id=product.id,
                        movement_type='purchase',
                        quantity=item_data.quantity,
                        timestamp=datetime.utcnow(),
                        description=f"Purchase - {purchase_number}",
                        purchase_id=purchase.id
                    )
                    db.add(movement)
                    
                    # Actualizar stock en almacén específico si se especifica
                    if purchase.warehouse_id:
                        warehouse_product = db.query(models.WarehouseProduct).filter(
                            models.WarehouseProduct.warehouse_id == purchase.warehouse_id,
                            models.WarehouseProduct.product_id == product.id
                        ).first()
                        
                        if warehouse_product:
                            warehouse_product.stock += item_data.quantity
                        else:
                            new_wp = models.WarehouseProduct(
                                warehouse_id=purchase.warehouse_id,
                                product_id=product.id,
                                stock=item_data.quantity
                            )
                            db.add(new_wp)
        
        # Aplicar descuento si existe
        if hasattr(purchase_data, 'discount') and purchase_data.discount > 0:
            discount_amount = (total_amount * purchase_data.discount) / 100
            total_amount -= discount_amount
        
        # Actualizar total
        purchase.total_amount = total_amount
        
        db.commit()
        db.refresh(purchase)
        
        return purchase
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating purchase: {str(e)}")

def get_purchases_by_company(
    db: Session, 
    company_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None
):
    """Obtener compras de una empresa"""
    query = db.query(models.Purchase).filter(models.Purchase.company_id == company_id)
    
    if status:
        query = query.filter(models.Purchase.status == status)
    
    return paginate_query(
        query.order_by(models.Purchase.date.desc()),
        skip=skip,
        limit=limit
    ).all()

def get_purchase_by_id_and_company(db: Session, purchase_id: int, company_id: int):
    """Obtener compra específica de una empresa"""
    return verify_company_ownership(
        db=db,
        model_class=models.Purchase,
        item_id=purchase_id,
        company_id=company_id,
        error_message="Purchase not found in your company"
    )

def update_purchase_for_company(
    db: Session, 
    purchase_id: int, 
    purchase_data: schemas.PurchaseUpdate, 
    company_id: int
):
    """Actualizar compra de una empresa"""
    purchase = verify_company_ownership(
        db=db,
        model_class=models.Purchase,
        item_id=purchase_id,
        company_id=company_id,
        error_message="Purchase not found in your company"
    )
    
    # Verificar si se puede editar
    if purchase.status == 'received':
        raise HTTPException(
            status_code=400,
            detail="Cannot edit received purchases"
        )
    
    # Actualizar campos
    for key, value in purchase_data.dict(exclude_unset=True).items():
        if hasattr(purchase, key):
            setattr(purchase, key, value)
    
    db.commit()
    db.refresh(purchase)
    return purchase

def delete_purchase_for_company(db: Session, purchase_id: int, company_id: int):
    """Eliminar compra de una empresa"""
    purchase = verify_company_ownership(
        db=db,
        model_class=models.Purchase,
        item_id=purchase_id,
        company_id=company_id,
        error_message="Purchase not found in your company"
    )
    
    # Verificar si se puede eliminar
    if purchase.status == 'received':
        raise HTTPException(
            status_code=400,
            detail="Cannot delete received purchases"
        )
    
    # Eliminar items primero
    db.query(models.PurchaseItem).filter(
        models.PurchaseItem.purchase_id == purchase_id
    ).delete()
    
    db.delete(purchase)
    db.commit()
    return {"message": "Purchase deleted successfully"}

def update_purchase_status_for_company(
    db: Session, 
    purchase_id: int, 
    status: str, 
    company_id: int
):
    """Actualizar estado de la compra"""
    purchase = verify_company_ownership(
        db=db,
        model_class=models.Purchase,
        item_id=purchase_id,
        company_id=company_id,
        error_message="Purchase not found in your company"
    )
    
    old_status = purchase.status
    purchase.status = status
    
    # Si cambió a 'received', actualizar inventario
    if old_status != 'received' and status == 'received':
        try:
            for item in purchase.purchase_items:
                product = db.query(models.Product).filter(
                    models.Product.id == item.product_id,
                    models.Product.company_id == company_id
                ).first()
                
                if product:
                    # Actualizar stock
                    product.quantity += item.quantity
                    
                    # Actualizar precio del producto
                    product.price = item.unit_cost
                    
                    # Crear movimiento de inventario
                    movement = models.InventoryMovement(
                        product_id=product.id,
                        movement_type='purchase',
                        quantity=item.quantity,
                        timestamp=datetime.utcnow(),
                        description=f"Purchase received - {purchase.purchase_number}",
                        purchase_id=purchase.id
                    )
                    db.add(movement)
                    
                    # Actualizar stock en almacén específico
                    if purchase.warehouse_id:
                        warehouse_product = db.query(models.WarehouseProduct).filter(
                            models.WarehouseProduct.warehouse_id == purchase.warehouse_id,
                            models.WarehouseProduct.product_id == product.id
                        ).first()
                        
                        if warehouse_product:
                            warehouse_product.stock += item.quantity
                        else:
                            new_wp = models.WarehouseProduct(
                                warehouse_id=purchase.warehouse_id,
                                product_id=product.id,
                                stock=item.quantity
                            )
                            db.add(new_wp)
            
            db.commit()
            db.refresh(purchase)
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Error updating purchase status: {str(e)}"
            )
    
    else:
        db.commit()
        db.refresh(purchase)
    
    return purchase

# ================= ESTADÍSTICAS Y REPORTES =================

def get_purchases_stats_by_company(db: Session, company_id: int):
    """Estadísticas de compras por empresa"""
    # Total de compras
    total_purchases = db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id
    ).count()
    
    # Compras recibidas
    received_purchases = db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.status == 'received'
    ).count()
    
    # Compras pendientes
    pending_purchases = db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.status == 'pending'
    ).count()
    
    # Monto total de compras
    total_amount = db.query(func.sum(models.Purchase.total_amount)).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.status == 'received'
    ).scalar() or 0
    
    # Compras del mes actual
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_purchases = db.query(func.sum(models.Purchase.total_amount)).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.status == 'received',
        models.Purchase.date >= start_of_month
    ).scalar() or 0
    
    # Promedio por compra
    avg_purchase_amount = total_amount / received_purchases if received_purchases > 0 else 0
    
    return {
        "total_purchases": total_purchases,
        "received_purchases": received_purchases,
        "pending_purchases": pending_purchases,
        "total_amount": float(total_amount),
        "monthly_purchases": float(monthly_purchases),
        "avg_purchase_amount": float(avg_purchase_amount)
    }

def get_purchases_by_supplier_and_company(
    db: Session,
    supplier_id: int,
    company_id: int
):
    """Obtener compras de un proveedor específico"""
    return db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.supplier_id == supplier_id
    ).order_by(models.Purchase.date.desc()).all()

def get_pending_purchases_by_company(db: Session, company_id: int):
    """Obtener compras pendientes de una empresa"""
    return db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.status == 'pending'
    ).order_by(models.Purchase.date.asc()).all()

def get_purchases_summary_by_period(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime
):
    """Resumen de compras por período"""
    purchases = db.query(
        func.sum(models.Purchase.total_amount).label('total_purchases'),
        func.count(models.Purchase.id).label('purchase_count'),
        func.avg(models.Purchase.total_amount).label('avg_purchase')
    ).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.status == 'received',
        models.Purchase.date >= start_date,
        models.Purchase.date <= end_date
    ).first()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_purchases": float(purchases.total_purchases or 0),
        "purchase_count": purchases.purchase_count or 0,
        "average_purchase": float(purchases.avg_purchase or 0)
    }

def get_top_purchased_products_by_company(
    db: Session,
    company_id: int,
    limit: int = 10
):
    """Obtener productos más comprados por empresa"""
    return db.query(
        models.Product.name,
        models.Product.sku,
        func.sum(models.PurchaseItem.quantity).label('total_purchased'),
        func.sum(models.PurchaseItem.total_cost).label('total_cost')
    ).join(
        models.PurchaseItem,
        models.Product.id == models.PurchaseItem.product_id
    ).join(
        models.Purchase,
        models.PurchaseItem.purchase_id == models.Purchase.id
    ).filter(
        models.Product.company_id == company_id,
        models.Purchase.status == 'received'
    ).group_by(
        models.Product.id
    ).order_by(
        func.sum(models.PurchaseItem.quantity).desc()
    ).limit(limit).all()

def get_purchase_orders_by_status(db: Session, company_id: int):
    """Obtener resumen de órdenes de compra por estado"""
    orders_by_status = db.query(
        models.Purchase.status,
        func.count(models.Purchase.id).label('count'),
        func.sum(models.Purchase.total_amount).label('total_amount')
    ).filter(
        models.Purchase.company_id == company_id
    ).group_by(
        models.Purchase.status
    ).all()
    
    return {
        status: {
            "count": count,
            "total_amount": float(total_amount or 0)
        }
        for status, count, total_amount in orders_by_status
    }

def create_purchase_from_low_stock(
    db: Session,
    company_id: int,
    threshold: int = 10
):
    """Crear orden de compra automática basada en productos con stock bajo"""
    # Obtener productos con stock bajo
    low_stock_products = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity <= threshold
    ).all()
    
    if not low_stock_products:
        return {"message": "No products with low stock found"}
    
    # Agrupar por proveedor principal (esto requiere una relación producto-proveedor)
    # Por ahora, crear una sola orden con todos los productos
    purchase_number = f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    try:
        purchase = models.Purchase(
            company_id=company_id,
            purchase_number=purchase_number,
            date=datetime.utcnow().date(),
            status='draft',
            total_amount=0,
            notes="Auto-generated purchase order for low stock items"
        )
        
        db.add(purchase)
        db.flush()
        
        total_amount = 0
        
        for product in low_stock_products:
            # Calcular cantidad sugerida (ejemplo: 3 veces el stock actual o mínimo 20)
            suggested_quantity = max(product.quantity * 3, 20)
            line_total = product.price * suggested_quantity
            
            purchase_item = models.PurchaseItem(
                purchase_id=purchase.id,
                product_id=product.id,
                quantity=suggested_quantity,
                unit_cost=product.price,
                total_cost=line_total
            )
            
            db.add(purchase_item)
            total_amount += line_total
        
        purchase.total_amount = total_amount
        
        db.commit()
        db.refresh(purchase)
        
        return {
            "message": f"Auto purchase order created with {len(low_stock_products)} products",
            "purchase_id": purchase.id,
            "purchase_number": purchase.purchase_number,
            "total_amount": float(total_amount),
            "products_count": len(low_stock_products)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating auto purchase order: {str(e)}"
        )

# ================= OPERACIONES ADICIONALES =================

def cancel_purchase_for_company(db: Session, purchase_id: int, company_id: int, reason: str):
    """Cancelar compra de una empresa"""
    purchase = verify_company_ownership(
        db=db,
        model_class=models.Purchase,
        item_id=purchase_id,
        company_id=company_id,
        error_message="Purchase not found in your company"
    )
    
    if purchase.status == 'received':
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel received purchases"
        )
    
    purchase.status = 'cancelled'
    purchase.notes = f"Cancelled: {reason}. Original notes: {purchase.notes or 'None'}"
    
    db.commit()
    db.refresh(purchase)
    
    return purchase

def duplicate_purchase_for_company(db: Session, purchase_id: int, company_id: int):
    """Duplicar una compra existente"""
    original_purchase = verify_company_ownership(
        db=db,
        model_class=models.Purchase,
        item_id=purchase_id,
        company_id=company_id,
        error_message="Purchase not found in your company"
    )
    
    # Generar nuevo número
    purchase_count = db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id
    ).count()
    new_purchase_number = f"PUR-{purchase_count + 1:06d}"
    
    try:
        # Crear nueva compra
        new_purchase = models.Purchase(
            company_id=company_id,
            supplier_id=original_purchase.supplier_id,
            warehouse_id=original_purchase.warehouse_id,
            purchase_number=new_purchase_number,
            date=datetime.utcnow().date(),
            status='draft',
            total_amount=original_purchase.total_amount,
            notes=f"Duplicated from {original_purchase.purchase_number}",
            reference=original_purchase.reference
        )
        
        db.add(new_purchase)
        db.flush()
        
        # Duplicar items
        for item in original_purchase.purchase_items:
            new_item = models.PurchaseItem(
                purchase_id=new_purchase.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                total_cost=item.total_cost
            )
            db.add(new_item)
        
        db.commit()
        db.refresh(new_purchase)
        
        return new_purchase
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error duplicating purchase: {str(e)}"
        )

def get_purchase_history_by_product(
    db: Session,
    product_id: int,
    company_id: int,
    limit: int = 10
):
    """Obtener historial de compras de un producto específico"""
    # Verificar que el producto pertenezca a la empresa
    verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    return db.query(
        models.Purchase.purchase_number,
        models.Purchase.date,
        models.Purchase.status,
        models.PurchaseItem.quantity,
        models.PurchaseItem.unit_cost,
        models.PurchaseItem.total_cost,
        models.Supplier.name.label('supplier_name')
    ).join(
        models.PurchaseItem,
        models.Purchase.id == models.PurchaseItem.purchase_id
    ).outerjoin(
        models.Supplier,
        models.Purchase.supplier_id == models.Supplier.id
    ).filter(
        models.Purchase.company_id == company_id,
        models.PurchaseItem.product_id == product_id
    ).order_by(
        models.Purchase.date.desc()
    ).limit(limit).all()