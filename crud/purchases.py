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
from . import venezuela_tax  # ✅ VENEZUELA: Funciones de cálculo de impuestos
import traceback

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
    """Crear compra para empresa específica con cálculos de impuestos SENIAT"""

    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Verificar que el proveedor pertenezca a la empresa
    supplier = None
    if hasattr(purchase_data, 'supplier_id') and purchase_data.supplier_id:
        supplier = verify_company_ownership(
            db=db,
            model_class=models.Supplier,
            item_id=purchase_data.supplier_id,
            company_id=company_id,
            error_message="Supplier not found in your company"
        )

    # Verificar que el almacén pertenezca a la empresa
    warehouse = None
    if hasattr(purchase_data, 'warehouse_id') and purchase_data.warehouse_id:
        warehouse = verify_company_ownership(
            db=db,
            model_class=models.Warehouse,
            item_id=purchase_data.warehouse_id,
            company_id=company_id,
            error_message="Warehouse not found in your company"
        )

    # Generar número de compra y número de control
    purchase_count = db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id
    ).count()
    purchase_number = f"PUR-{purchase_count + 1:06d}"
    control_number = f"PUR-{purchase_count + 1:08d}"  # ✅ VENEZUELA: Número de control

    try:
        # Crear compra con campos para Venezuela
        purchase = models.Purchase(
            company_id=company_id,
            supplier_id=purchase_data.supplier_id,
            warehouse_id=purchase_data.warehouse_id,
            purchase_number=purchase_number,
            invoice_number=getattr(purchase_data, 'invoice_number', None),  # ✅ Factura del proveedor
            control_number=control_number,  # ✅ VENEZUELA
            date=getattr(purchase_data, 'date', datetime.utcnow()),
            due_date=getattr(purchase_data, 'due_date', datetime.utcnow()),
            status=getattr(purchase_data, 'status', 'pending'),
            discount=getattr(purchase_data, 'discount', 0),
            notes=getattr(purchase_data, 'notes', None),
            # ✅ VENEZUELA: Información fiscal
            transaction_type=getattr(purchase_data, 'transaction_type', 'contado'),
            payment_method=getattr(purchase_data, 'payment_method', 'efectivo'),
            credit_days=getattr(purchase_data, 'credit_days', 0),
            iva_percentage=getattr(purchase_data, 'iva_percentage', 16.0),
            supplier_phone=getattr(purchase_data, 'supplier_phone', None),
            supplier_address=getattr(purchase_data, 'supplier_address', None)
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
                price_per_unit = getattr(item_data, 'price_per_unit', item_data.price_per_unit)
                line_total = price_per_unit * item_data.quantity

                # ✅ VENEZUELA: Calcular impuestos del item
                tax_rate = getattr(item_data, 'tax_rate', purchase.iva_percentage)
                is_exempt = getattr(item_data, 'is_exempt', False)
                tax_amount = 0.0

                if not is_exempt and tax_rate > 0:
                    tax_amount = venezuela_tax.calculate_iva(line_total, tax_rate)

                # Crear item de compra con impuestos
                purchase_item = models.PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=product.id,
                    quantity=item_data.quantity,
                    price_per_unit=price_per_unit,
                    total_price=line_total,
                    # ✅ VENEZUELA: Información fiscal del item
                    tax_rate=tax_rate,
                    tax_amount=tax_amount,
                    is_exempt=is_exempt
                )

                db.add(purchase_item)
                total_amount += line_total

                # Si la compra está recibida/confirmada, actualizar stock
                if purchase.status in ['received', 'recibida']:
                    # Actualizar stock global del producto
                    product.quantity += item_data.quantity

                    # Actualizar costo del producto si es diferente
                    if price_per_unit != product.price:
                        product.price = price_per_unit

                    # Actualizar stock en almacén específico si se especifica
                    if warehouse:
                        warehouse_product = db.query(models.WarehouseProduct).filter(
                            models.WarehouseProduct.warehouse_id == warehouse.id,
                            models.WarehouseProduct.product_id == product.id
                        ).first()

                        if warehouse_product:
                            warehouse_product.stock += item_data.quantity

                            # Crear movimiento de inventario con referencia al almacén
                            movement = models.InventoryMovement(
                                product_id=product.id,
                                warehouse_id=warehouse.id,
                                movement_type='purchase',
                                quantity=item_data.quantity,
                                timestamp=datetime.utcnow(),
                                description=f"Purchase - {purchase_number}",
                                invoice_id=purchase.id
                            )
                            db.add(movement)
                        else:
                            # Crear nuevo registro en warehouse_products
                            new_wp = models.WarehouseProduct(
                                warehouse_id=warehouse.id,
                                product_id=product.id,
                                stock=item_data.quantity
                            )
                            db.add(new_wp)

                            # Crear movimiento de inventario
                            movement = models.InventoryMovement(
                                product_id=product.id,
                                warehouse_id=warehouse.id,
                                movement_type='purchase',
                                quantity=item_data.quantity,
                                timestamp=datetime.utcnow(),
                                description=f"Purchase - {purchase_number}",
                                invoice_id=purchase.id
                            )
                            db.add(movement)
                    else:
                        # Crear movimiento de inventario sin almacén específico
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            movement_type='purchase',
                            quantity=item_data.quantity,
                            timestamp=datetime.utcnow(),
                            description=f"Purchase - {purchase_number}",
                            invoice_id=purchase.id
                        )
                        db.add(movement)

        # ✅ VENEZUELA: Calcular totales con impuestos
        # Preparar datos para cálculo
        items_data = []
        for item_data in purchase_data.items:
            product = db.query(models.Product).filter(
                models.Product.id == item_data.product_id
            ).first()
            price_per_unit = getattr(item_data, 'price_per_unit', product.price)
            line_total = price_per_unit * item_data.quantity

            items_data.append({
                'price': price_per_unit,
                'quantity': item_data.quantity,
                'tax_rate': getattr(item_data, 'tax_rate', purchase.iva_percentage),
                'is_exempt': getattr(item_data, 'is_exempt', False)
            })

        # Calcular todos los impuestos usando la función auxiliar
        tax_calculations = venezuela_tax.calculate_invoice_totals(
            items=items_data,
            discount=purchase.discount,
            iva_percentage=purchase.iva_percentage,
            company=company,
            currency=company.currency
        )

        # Actualizar totales de la compra
        purchase.subtotal = tax_calculations['subtotal']
        purchase.taxable_base = tax_calculations['taxable_base']
        purchase.exempt_amount = tax_calculations['exempt_amount']
        purchase.iva_amount = tax_calculations['iva_amount']
        purchase.iva_retention = tax_calculations['iva_retention']
        purchase.iva_retention_percentage = tax_calculations['iva_retention_percentage']
        purchase.islr_retention = tax_calculations['islr_retention']
        purchase.islr_retention_percentage = tax_calculations['islr_retention_percentage']
        purchase.stamp_tax = tax_calculations['stamp_tax']
        purchase.total_with_taxes = tax_calculations['total_with_taxes']
        purchase.total_amount = tax_calculations['total_with_taxes']

        db.commit()
        db.refresh(purchase)

        return purchase

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Error creating purchase",
                "message": str(e),
                "type": type(e).__name__,
                "args": e.args,
                "traceback": traceback.format_exc()
            }
        )

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

    # Si cambió a 'received', actualizar inventario (agregar stock)
    if old_status != 'received' and status == 'received':
        try:
            # Obtener almacén si existe
            warehouse = None
            if purchase.warehouse_id:
                warehouse = db.query(models.Warehouse).filter(
                    models.Warehouse.id == purchase.warehouse_id,
                    models.Warehouse.company_id == company_id
                ).first()

            for item in purchase.purchase_items:
                product = db.query(models.Product).filter(
                    models.Product.id == item.product_id,
                    models.Product.company_id == company_id
                ).first()

                if product:
                    # Actualizar stock global
                    product.quantity += item.quantity

                    # Actualizar precio del producto
                    product.price = item.price_per_unit

                    # Actualizar stock en almacén específico
                    if warehouse:
                        warehouse_product = db.query(models.WarehouseProduct).filter(
                            models.WarehouseProduct.warehouse_id == warehouse.id,
                            models.WarehouseProduct.product_id == product.id
                        ).first()

                        if warehouse_product:
                            warehouse_product.stock += item.quantity
                        else:
                            new_wp = models.WarehouseProduct(
                                warehouse_id=warehouse.id,
                                product_id=product.id,
                                stock=item.quantity
                            )
                            db.add(new_wp)

                        # Crear movimiento de inventario con referencia al almacén
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            warehouse_id=warehouse.id,
                            movement_type='purchase',
                            quantity=item.quantity,
                            timestamp=datetime.utcnow(),
                            description=f"Purchase received - {purchase.purchase_number}",
                        )
                        db.add(movement)
                    else:
                        # Crear movimiento de inventario sin almacén específico
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            movement_type='purchase',
                            quantity=item.quantity,
                            timestamp=datetime.utcnow(),
                            description=f"Purchase received - {purchase.purchase_number}",
                        )
                        db.add(movement)

            db.commit()
            db.refresh(purchase)

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Error updating purchase status: {str(e)}"
            )
    # Si cambió de 'received' a otro estado, revertir inventario (quitar stock)
    elif old_status == 'received' and status != 'received':
        try:
            # Obtener almacén si existe
            warehouse = None
            if purchase.warehouse_id:
                warehouse = db.query(models.Warehouse).filter(
                    models.Warehouse.id == purchase.warehouse_id,
                    models.Warehouse.company_id == company_id
                ).first()

            for item in purchase.purchase_items:
                product = db.query(models.Product).filter(
                    models.Product.id == item.product_id,
                    models.Product.company_id == company_id
                ).first()

                if product:
                    # Revertir stock global (verificar que no quede en negativo)
                    if product.quantity >= item.quantity:
                        product.quantity -= item.quantity

                    # Revertir stock en almacén específico
                    if warehouse:
                        warehouse_product = db.query(models.WarehouseProduct).filter(
                            models.WarehouseProduct.warehouse_id == warehouse.id,
                            models.WarehouseProduct.product_id == product.id
                        ).first()

                        if warehouse_product and warehouse_product.stock >= item.quantity:
                            warehouse_product.stock -= item.quantity

                            # Crear movimiento de inventario de reversión
                            movement = models.InventoryMovement(
                                product_id=product.id,
                                warehouse_id=warehouse.id,
                                movement_type='purchase_reversal',
                                quantity=item.quantity,
                                timestamp=datetime.utcnow(),
                                description=f"Purchase status reverted - {purchase.purchase_number}",
                            )
                            db.add(movement)
                    else:
                        # Crear movimiento de inventario de reversión sin almacén
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            movement_type='purchase_reversal',
                            quantity=item.quantity,
                            timestamp=datetime.utcnow(),
                            description=f"Purchase status reverted - {purchase.purchase_number}",
                        )
                        db.add(movement)

            db.commit()
            db.refresh(purchase)

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Error reverting purchase status: {str(e)}"
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
                price_per_unit=product.price,
                total_price=line_total
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
                price_per_unit=item.price_per_unit,
                total_price=item.total_price
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

# ================= FUNCIONES PARA NOTAS DE CRÉDITO DE COMPRAS =================

def create_purchase_credit_movement_for_company(
    db: Session,
    purchase_id: int,
    movement_data: schemas.PurchaseCreditMovementCreate,
    company_id: int
):
    """Crear nota de crédito de compra con reversión de stock"""
    
    # Verificar que la compra pertenezca a la empresa
    purchase = verify_company_ownership(
        db=db,
        model_class=models.Purchase,
        item_id=purchase_id,
        company_id=company_id,
        error_message="Purchase not found in your company"
    )
    
    if purchase.status != "received":
        raise HTTPException(
            status_code=400,
            detail="Can only create credit notes for received purchases"
        )
    
    try:
        # Crear movimiento de crédito de compra
        credit_movement = models.PurchaseCreditMovement(
            purchase_id=purchase_id,
            amount=movement_data.amount,
            movement_type=movement_data.movement_type,
            reason=movement_data.reason,
            reference_purchase_number=getattr(movement_data, "reference_purchase_number", None) or purchase.purchase_number,
            reference_control_number=getattr(movement_data, "reference_control_number", None) or purchase.control_number,
            warehouse_id=getattr(movement_data, "warehouse_id", None) or purchase.warehouse_id,
            stock_reverted=False
        )
        
        db.add(credit_movement)
        
        # Si es devolución, restaurar stock
        if movement_data.movement_type == "devolucion":
            for item in purchase.purchase_items:
                product = db.query(models.Product).filter(
                    models.Product.id == item.product_id
                ).first()
                
                if product:
                    # Calcular cantidad a devolver proporcionalmente
                    return_ratio = movement_data.amount / purchase.total_amount
                    return_quantity = int(item.quantity * return_ratio)
                    
                    if return_quantity > 0:
                        # Revertir stock global
                        product.quantity -= return_quantity
                        
                        # Revertir stock en almacén
                        warehouse_id = getattr(movement_data, "warehouse_id", None) or purchase.warehouse_id
                        if warehouse_id:
                            warehouse_product = db.query(models.WarehouseProduct).filter(
                                models.WarehouseProduct.warehouse_id == warehouse_id,
                                models.WarehouseProduct.product_id == product.id
                            ).first()
                            
                            if warehouse_product:
                                warehouse_product.stock -= return_quantity
                        
                        # Crear movimiento de inventario
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            warehouse_id=warehouse_id,
                            movement_type="purchase_return",
                            quantity=return_quantity,
                            timestamp=datetime.utcnow(),
                            description=f"Purchase Return - Credit Note #{credit_movement.id}",
                            invoice_id=purchase_id
                        )
                        db.add(movement)
            
            # Marcar que se revirtió el stock
            credit_movement.stock_reverted = True
        
        db.commit()
        db.refresh(credit_movement)
        return credit_movement
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating purchase credit movement: {str(e)}"
        )

def get_purchase_credit_movements_by_company(
    db: Session,
    company_id: int,
    skip: int = 0,
    limit: int = 100
):
    """Obtener notas de crédito de compras de una empresa"""
    
    # Obtener IDs de compras de la empresa
    purchase_ids = db.query(models.Purchase.id).filter(
        models.Purchase.company_id == company_id
    ).subquery()
    
    # Obtener movimientos de crédito de esas compras
    query = db.query(models.PurchaseCreditMovement).filter(
        models.PurchaseCreditMovement.purchase_id.in_(purchase_ids)
    )
    
    return paginate_query(
        query.order_by(models.PurchaseCreditMovement.date.desc()),
        skip=skip,
        limit=limit
    ).all()

