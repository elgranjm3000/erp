# crud/invoices.py
"""
Funciones CRUD para gestión de facturas y presupuestos
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException
from datetime import datetime
from typing import List, Optional
import models
import schemas
from .base import verify_company_ownership, paginate_query
import traceback

# ================= FUNCIONES LEGACY (MANTENER COMPATIBILIDAD) =================

def create_budget(db: Session, budget_data: schemas.Invoice):
    """Legacy: crear presupuesto sin empresa específica"""
    budget = models.Invoice(
        customer_id=budget_data.customer_id,
        status='presupuesto',
        total_amount=0,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    for item in budget_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        budget_item = models.InvoiceItem(
            invoice_id=budget.id,
            product_id=product.id,
            quantity=item.quantity,
            price_per_unit=product.price,
            total_price=product.price * item.quantity,
        )
        db.add(budget_item)

    db.commit()
    budget.total_amount = sum(item.total_price for item in budget.invoice_items)
    db.commit()
    return budget

def confirm_budget(db: Session, budget_id: int):
    """Legacy: confirmar presupuesto como factura"""
    budget = db.query(models.Invoice).filter(
        models.Invoice.id == budget_id, 
        models.Invoice.status == 'presupuesto'
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found or already confirmed")

    budget.status = 'factura'

    for item in budget.invoice_items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if product.quantity < item.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for product")
        product.quantity -= item.quantity

    db.commit()
    return budget

def create_invoice(db: Session, invoice_data: schemas.Invoice):
    """Legacy: crear factura sin empresa específica"""
    return create_invoice_for_company(db, invoice_data, 1)

def view_invoice(db: Session, invoice_id: int):
    """Legacy: ver factura sin validar empresa"""
    return view_invoice_by_company(db, invoice_id, 1)

def edit_invoice(db: Session, invoice_id: int, invoice_data: schemas.Invoice):
    """Legacy: editar factura sin validar empresa"""
    return edit_invoice_for_company(db, invoice_id, invoice_data, 1)

def delete_invoice(db: Session, invoice_id: int):
    """Legacy: eliminar factura sin validar empresa"""
    return delete_invoice_for_company(db, invoice_id, 1)

# ================= FUNCIONES MULTIEMPRESA =================

def create_invoice_for_company(
    db: Session, 
    invoice_data: schemas.InvoiceCreate, 
    company_id: int
):
    """Crear factura para empresa específica"""
    
    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Verificar que el cliente pertenezca a la empresa
    if hasattr(invoice_data, 'customer_id') and invoice_data.customer_id:
        customer = verify_company_ownership(
            db=db,
            model_class=models.Customer,
            item_id=invoice_data.customer_id,
            company_id=company_id,
            error_message="Customer not found in your company"
        )
    
    # Generar número de factura
    invoice_number = f"{company.invoice_prefix}-{company.next_invoice_number:06d}"
    
    try:
        # Crear factura
        invoice = models.Invoice(
            company_id=company_id,
            customer_id=getattr(invoice_data, 'customer_id', None),
            warehouse_id=getattr(invoice_data, 'warehouse_id', None),
            invoice_number=invoice_number,
            status=getattr(invoice_data, 'status', 'factura'),
            discount=getattr(invoice_data, 'discount', 0),
            total_amount=0,
            date=getattr(invoice_data, 'date', datetime.utcnow().date()),
            due_date=getattr(invoice_data, 'due_date', None),
            notes=getattr(invoice_data, 'notes', None)
        )
        
        db.add(invoice)
        db.flush()  # Para obtener el ID
        
        total_amount = 0
        
        # Procesar items si existen
        if hasattr(invoice_data, 'items') and invoice_data.items:
            for item_data in invoice_data.items:
                # Verificar que el producto pertenezca a la empresa
                product = verify_company_ownership(
                    db=db,
                    model_class=models.Product,
                    item_id=item_data.product_id,
                    company_id=company_id,
                    error_message="Product not found in your company"
                )
                
                # Verificar stock disponible
                if product.quantity < item_data.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for product {product.name}"
                    )
                
                # Calcular precio
                unit_price = getattr(item_data, 'price_per_unit', product.price)
                line_total = unit_price * item_data.quantity
                
                # Crear item de factura
                invoice_item = models.InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id,
                    quantity=item_data.quantity,
                    price_per_unit=unit_price,
                    total_price=line_total
                )
                
                db.add(invoice_item)
                total_amount += line_total
                
                # Actualizar stock si es factura confirmada
                if invoice.status == 'factura':
                    product.quantity -= item_data.quantity
                    
                    # Crear movimiento de inventario
                    movement = models.InventoryMovement(
                        product_id=product.id,
                        movement_type='sale',
                        quantity=item_data.quantity,
                        timestamp=datetime.utcnow(),
                        description=f"Sale - Invoice {invoice_number}",
                        invoice_id=invoice.id
                    )
                    db.add(movement)
        
        # Aplicar descuento
        if invoice.discount > 0:
            discount_amount = (total_amount * invoice.discount) / 100
            total_amount -= discount_amount
        
        # Actualizar totales
        invoice.total_amount = total_amount
        company.next_invoice_number += 1
        
        db.commit()
        db.refresh(invoice)
        
        return invoice
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
        status_code=400,
            detail={
                "error": "Error creating invoice",
                "message": str(e),                # mensaje legible
                "type": type(e).__name__,         # tipo de excepción
                "args": e.args,                   # argumentos originales
                "traceback": traceback.format_exc()  # stack trace completo
            }
        )

def view_invoice_by_company(db: Session, invoice_id: int, company_id: int):
    """Ver factura específica de empresa"""
    return verify_company_ownership(
        db=db,
        model_class=models.Invoice,
        item_id=invoice_id,
        company_id=company_id,
        error_message="Invoice not found in your company"
    )

def edit_invoice_for_company(
    db: Session, 
    invoice_id: int, 
    invoice_data: schemas.InvoiceUpdate, 
    company_id: int
):
    """Editar factura de empresa"""
    invoice = verify_company_ownership(
        db=db,
        model_class=models.Invoice,
        item_id=invoice_id,
        company_id=company_id,
        error_message="Invoice not found in your company"
    )
    
    # Solo permitir edición si es presupuesto
    if invoice.status == 'factura':
        raise HTTPException(
            status_code=400,
            detail="Cannot edit confirmed invoices"
        )
    
    # Actualizar campos
    for key, value in invoice_data.dict(exclude_unset=True).items():
        if hasattr(invoice, key):
            setattr(invoice, key, value)
    
    db.commit()
    db.refresh(invoice)
    return invoice

def delete_invoice_for_company(db: Session, invoice_id: int, company_id: int):
    """Eliminar factura de empresa"""
    invoice = verify_company_ownership(
        db=db,
        model_class=models.Invoice,
        item_id=invoice_id,
        company_id=company_id,
        error_message="Invoice not found in your company"
    )
    
    # Solo permitir eliminación si es presupuesto
    if invoice.status == 'factura':
        raise HTTPException(
            status_code=400,
            detail="Cannot delete confirmed invoices"
        )
    
    # Eliminar items primero
    db.query(models.InvoiceItem).filter(
        models.InvoiceItem.invoice_id == invoice_id
    ).delete()
    
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted successfully"}

def get_invoices_by_company(
    db: Session, 
    company_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None
):
    """Obtener facturas de una empresa"""
    query = db.query(models.Invoice).filter(models.Invoice.company_id == company_id)
    
    if status:
        query = query.filter(models.Invoice.status == status)
    
    return paginate_query(
        query.order_by(models.Invoice.date.desc()),
        skip=skip,
        limit=limit
    ).all()

def confirm_budget_for_company(db: Session, budget_id: int, company_id: int):
    """Confirmar presupuesto como factura en empresa específica"""
    budget = db.query(models.Invoice).filter(
        models.Invoice.id == budget_id,
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'presupuesto'
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=404, 
            detail="Budget not found or already confirmed"
        )
    
    try:
        # Cambiar status
        budget.status = 'factura'
        
        # Actualizar stock y crear movimientos
        for item in budget.invoice_items:
            product = db.query(models.Product).filter(
                models.Product.id == item.product_id,
                models.Product.company_id == company_id
            ).first()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            if product.quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product.name}"
                )
            
            # Actualizar stock
            product.quantity -= item.quantity
            
            # Crear movimiento de inventario
            movement = models.InventoryMovement(
                product_id=product.id,
                movement_type='sale',
                quantity=item.quantity,
                timestamp=datetime.utcnow(),
                description=f"Sale - Invoice {budget.invoice_number}",
                invoice_id=budget.id
            )
            db.add(movement)
        
        db.commit()
        db.refresh(budget)
        return budget
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error confirming budget: {str(e)}"
        )

# ================= MOVIMIENTOS DE CRÉDITO =================

def create_credit_movement_for_company(
    db: Session,
    invoice_id: int,
    movement_data: schemas.CreditMovementCreate,
    company_id: int
):
    """Crear movimiento de crédito (nota de crédito/devolución)"""
    # Verificar que la factura pertenezca a la empresa
    invoice = verify_company_ownership(
        db=db,
        model_class=models.Invoice,
        item_id=invoice_id,
        company_id=company_id,
        error_message="Invoice not found in your company"
    )
    
    if invoice.status != 'factura':
        raise HTTPException(
            status_code=400,
            detail="Can only create credit movements for confirmed invoices"
        )
    
    try:
        # Crear movimiento de crédito
        credit_movement = models.CreditMovement(
            invoice_id=invoice_id,
            movement_type=movement_data.movement_type,
            amount=movement_data.amount,
            reason=movement_data.reason,
            date=datetime.utcnow().date()
        )
        
        db.add(credit_movement)
        
        # Si es devolución, restaurar stock
        if movement_data.movement_type == 'return':
            for item in invoice.invoice_items:
                product = db.query(models.Product).filter(
                    models.Product.id == item.product_id
                ).first()
                
                if product:
                    # Calcular cantidad a devolver proporcionalmente
                    return_ratio = movement_data.amount / invoice.total_amount
                    return_quantity = int(item.quantity * return_ratio)
                    
                    if return_quantity > 0:
                        product.quantity += return_quantity
                        
                        # Crear movimiento de inventario
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            movement_type='return',
                            quantity=return_quantity,
                            timestamp=datetime.utcnow(),
                            description=f"Return - Credit Note #{credit_movement.id}",
                            invoice_id=invoice_id
                        )
                        db.add(movement)
        
        db.commit()
        db.refresh(credit_movement)
        return credit_movement
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating credit movement: {str(e)}"
        )

# ================= ESTADÍSTICAS Y REPORTES =================

def get_invoices_stats_by_company(db: Session, company_id: int):
    """Estadísticas de facturas por empresa"""
    # Total de facturas
    total_invoices = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id
    ).count()
    
    # Total confirmadas
    confirmed_invoices = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura'
    ).count()
    
    # Total presupuestos
    pending_budgets = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'presupuesto'
    ).count()
    
    # Monto total facturado
    total_amount = db.query(func.sum(models.Invoice.total_amount)).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura'
    ).scalar() or 0
    
    # Ventas del mes actual
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_sales = db.query(func.sum(models.Invoice.total_amount)).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura',
        models.Invoice.date >= start_of_month
    ).scalar() or 0
    
    # Promedio por factura
    avg_invoice_amount = total_amount / confirmed_invoices if confirmed_invoices > 0 else 0
    
    return {
        "total_invoices": total_invoices,
        "confirmed_invoices": confirmed_invoices,
        "pending_budgets": pending_budgets,
        "total_amount": float(total_amount),
        "monthly_sales": float(monthly_sales),
        "avg_invoice_amount": float(avg_invoice_amount)
    }

def get_invoices_by_customer_and_company(
    db: Session,
    customer_id: int,
    company_id: int
):
    """Obtener facturas de un cliente específico"""
    return db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.customer_id == customer_id
    ).order_by(models.Invoice.date.desc()).all()

def get_overdue_invoices_by_company(db: Session, company_id: int):
    """Obtener facturas vencidas de una empresa"""
    today = datetime.utcnow().date()
    
    return db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura',
        models.Invoice.due_date < today,
        models.Invoice.paid == False  # Asumiendo que existe este campo
    ).all()

def get_sales_summary_by_period(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime
):
    """Resumen de ventas por período"""
    sales = db.query(
        func.sum(models.Invoice.total_amount).label('total_sales'),
        func.count(models.Invoice.id).label('invoice_count'),
        func.avg(models.Invoice.total_amount).label('avg_sale')
    ).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura',
        models.Invoice.date >= start_date,
        models.Invoice.date <= end_date
    ).first()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_sales": float(sales.total_sales or 0),
        "invoice_count": sales.invoice_count or 0,
        "average_sale": float(sales.avg_sale or 0)
    }