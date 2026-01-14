# crud/customers.py
"""
Funciones CRUD para gestión de clientes
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import List, Optional
import models
import schemas
from .base import verify_company_ownership, apply_search_filter, paginate_query

# ================= FUNCIONES MULTIEMPRESA =================

def get_customers_by_company(
    db: Session, 
    company_id: int, 
    skip: int = 0, 
    limit: int = 100
):
    """Obtener clientes de una empresa específica"""
    return paginate_query(
        db.query(models.Customer).filter(
            models.Customer.company_id == company_id,
        ).order_by(models.Customer.name),
        skip=skip,
        limit=limit
    ).all()

def get_customer_by_id_and_company(db: Session, customer_id: int, company_id: int):
    """Obtener cliente específico de una empresa"""
    return verify_company_ownership(
        db=db,
        model_class=models.Customer,
        item_id=customer_id,
        company_id=company_id,
        error_message="Customer not found in your company"
    )

def create_customer_for_company(
    db: Session, 
    customer_data: schemas.CustomerCreate, 
    company_id: int
):
    """Crear cliente para empresa específica"""
    
    # Verificar que el email no exista en la empresa (si se proporciona)
    if hasattr(customer_data, 'email') and customer_data.email:
        existing_customer = db.query(models.Customer).filter(
            models.Customer.company_id == company_id,
            models.Customer.email == customer_data.email
        ).first()
        
        if existing_customer:
            raise HTTPException(
                status_code=400,
                detail="Customer with this email already exists in your company"
            )
    
    # Verificar que el tax_id no exista en la empresa (si se proporciona)
    if hasattr(customer_data, 'tax_id') and customer_data.tax_id:
        existing_tax_id = db.query(models.Customer).filter(
            models.Customer.company_id == company_id,
            models.Customer.tax_id == customer_data.tax_id.upper()
        ).first()
        
        if existing_tax_id:
            raise HTTPException(
                status_code=400,
                detail="Customer with this tax ID already exists in your company"
            )
    
    try:
        # Generar código de cliente si no se proporciona
        customer_code = None
        if hasattr(customer_data, 'customer_code') and customer_data.customer_code:
            customer_code = customer_data.customer_code
        else:
            # Generar código automático
            count = db.query(models.Customer).filter(
                models.Customer.company_id == company_id
            ).count()
            customer_code = f"CUS-{count + 1:06d}"
        
        # Crear cliente
        db_customer = models.Customer(
            company_id=company_id,
            name=customer_data.name,
            email=getattr(customer_data, 'email', None),
            phone=getattr(customer_data, 'phone', None),
            address=getattr(customer_data, 'address', None),
            tax_id=getattr(customer_data, 'tax_id', '').upper() if getattr(customer_data, 'tax_id', None) else None,
            latitude=getattr(customer_data, 'latitude', None),
            longitude=getattr(customer_data, 'longitude', None),
        )
        
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        
        return db_customer
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating customer: {str(e)}"
        )

def update_customer_for_company(
    db: Session, 
    customer_id: int, 
    customer_data: schemas.CustomerUpdate, 
    company_id: int
):
    """Actualizar cliente de una empresa"""
    customer = verify_company_ownership(
        db=db,
        model_class=models.Customer,
        item_id=customer_id,
        company_id=company_id,
        error_message="Customer not found in your company"
    )
    
    # Verificar email único si se actualiza
    if hasattr(customer_data, 'email') and customer_data.email and customer_data.email != customer.email:
        existing_email = db.query(models.Customer).filter(
            models.Customer.company_id == company_id,
            models.Customer.email == customer_data.email,
            models.Customer.id != customer_id
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already exists for another customer"
            )
    
    # Verificar tax_id único si se actualiza
    if hasattr(customer_data, 'tax_id') and customer_data.tax_id:
        tax_id_upper = customer_data.tax_id.upper()
        if tax_id_upper != customer.tax_id:
            existing_tax_id = db.query(models.Customer).filter(
                models.Customer.company_id == company_id,
                models.Customer.tax_id == tax_id_upper,
                models.Customer.id != customer_id
            ).first()
            
            if existing_tax_id:
                raise HTTPException(
                    status_code=400,
                    detail="Tax ID already exists for another customer"
                )
    
    # Actualizar campos
    for key, value in customer_data.dict(exclude_unset=True).items():
        if key == 'tax_id' and value:
            setattr(customer, key, value.upper())
        else:
            setattr(customer, key, value)
    
    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)
    
    return customer

def delete_customer_for_company(db: Session, customer_id: int, company_id: int):
    """Eliminar (desactivar) cliente de una empresa"""
    customer = verify_company_ownership(
        db=db,
        model_class=models.Customer,
        item_id=customer_id,
        company_id=company_id,
        error_message="Customer not found in your company"
    )
    
    # Verificar si tiene facturas asociadas
    has_invoices = db.query(models.Invoice).filter(
        models.Invoice.customer_id == customer_id,
        models.Invoice.company_id == company_id
    ).first()
    
    if has_invoices:
        # Soft delete - solo desactivar
        customer.is_active = False
        customer.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Customer deactivated successfully (has related invoices)"}
    else:
        # Hard delete si no tiene facturas
        db.delete(customer)
        db.commit()
        return {"message": "Customer deleted successfully"}

# ================= FUNCIONES DE BÚSQUEDA Y FILTROS =================

def search_customers_by_company(db: Session, company_id: int, search_term: str):
    """Buscar clientes por nombre, email o tax_id en una empresa"""
    return db.query(models.Customer).filter(
        models.Customer.company_id == company_id,
        models.Customer.is_active == True,
        or_(
            models.Customer.name.ilike(f"%{search_term}%"),
            models.Customer.email.ilike(f"%{search_term}%"),
            models.Customer.tax_id.ilike(f"%{search_term}%"),
            models.Customer.customer_code.ilike(f"%{search_term}%")
        )
    ).order_by(models.Customer.name).all()

def get_customers_by_type_and_company(
    db: Session,
    company_id: int,
    customer_type: str
):
    """Obtener clientes por tipo en una empresa"""
    return db.query(models.Customer).filter(
        models.Customer.company_id == company_id,
        models.Customer.customer_type == customer_type,
        models.Customer.is_active == True
    ).order_by(models.Customer.name).all()

def get_customers_with_credit_limit(db: Session, company_id: int):
    """Obtener clientes con límite de crédito"""
    return db.query(models.Customer).filter(
        models.Customer.company_id == company_id,
        models.Customer.credit_limit > 0,
        models.Customer.is_active == True
    ).order_by(models.Customer.credit_limit.desc()).all()

# ================= ESTADÍSTICAS Y REPORTES =================

def get_customers_stats_by_company(db: Session, company_id: int):
    """Estadísticas de clientes por empresa"""
    # Total clientes activos
    total_customers = db.query(models.Customer).filter(
        models.Customer.company_id == company_id,
        models.Customer.is_active == True
    ).count()
    
    # Clientes inactivos
    inactive_customers = db.query(models.Customer).filter(
        models.Customer.company_id == company_id,
        models.Customer.is_active == False
    ).count()
    
    # Clientes por tipo
    customers_by_type = db.query(
        models.Customer.customer_type,
        func.count(models.Customer.id).label('count')
    ).filter(
        models.Customer.company_id == company_id,
        models.Customer.is_active == True
    ).group_by(models.Customer.customer_type).all()
    
    # Clientes con crédito
    customers_with_credit = db.query(models.Customer).filter(
        models.Customer.company_id == company_id,
        models.Customer.credit_limit > 0,
        models.Customer.is_active == True
    ).count()
    
    # Límite de crédito total
    total_credit_limit = db.query(
        func.sum(models.Customer.credit_limit)
    ).filter(
        models.Customer.company_id == company_id,
        models.Customer.is_active == True
    ).scalar() or 0
    
    return {
        "total_customers": total_customers,
        "inactive_customers": inactive_customers,
        "customers_with_credit": customers_with_credit,
        "total_credit_limit": float(total_credit_limit),
        "customers_by_type": {
            customer_type: count for customer_type, count in customers_by_type
        }
    }

def get_top_customers_by_sales(
    db: Session,
    company_id: int,
    limit: int = 10
):
    """Obtener top clientes por volumen de ventas"""
    return db.query(
        models.Customer.name,
        models.Customer.customer_code,
        models.Customer.email,
        func.sum(models.Invoice.total_amount).label('total_sales'),
        func.count(models.Invoice.id).label('invoice_count'),
        func.avg(models.Invoice.total_amount).label('avg_sale')
    ).join(
        models.Invoice,
        models.Customer.id == models.Invoice.customer_id
    ).filter(
        models.Customer.company_id == company_id,
        models.Invoice.status == 'factura'
    ).group_by(
        models.Customer.id
    ).order_by(
        func.sum(models.Invoice.total_amount).desc()
    ).limit(limit).all()

def get_customer_balance(db: Session, customer_id: int, company_id: int):
    """Obtener balance de cuenta de un cliente"""
    # Verificar que el cliente pertenezca a la empresa
    customer = verify_company_ownership(
        db=db,
        model_class=models.Customer,
        item_id=customer_id,
        company_id=company_id,
        error_message="Customer not found in your company"
    )
    
    # Calcular total facturado
    total_invoiced = db.query(
        func.sum(models.Invoice.total_amount)
    ).filter(
        models.Invoice.customer_id == customer_id,
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura'
    ).scalar() or 0
    
    # Calcular total pagado (esto requiere una tabla de pagos)
    # Por ahora asumimos que hay un campo 'paid_amount' en Invoice
    total_paid = db.query(
        func.sum(models.Invoice.paid_amount)
    ).filter(
        models.Invoice.customer_id == customer_id,
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura'
    ).scalar() or 0
    
    # Calcular balance pendiente
    balance = total_invoiced - total_paid
    
    # Facturas vencidas
    today = datetime.utcnow().date()
    overdue_amount = db.query(
        func.sum(models.Invoice.total_amount - models.Invoice.paid_amount)
    ).filter(
        models.Invoice.customer_id == customer_id,
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura',
        models.Invoice.due_date < today,
        models.Invoice.paid_amount < models.Invoice.total_amount
    ).scalar() or 0
    
    return {
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "customer_code": customer.customer_code,
            "credit_limit": float(customer.credit_limit)
        },
        "total_invoiced": float(total_invoiced),
        "total_paid": float(total_paid),
        "balance": float(balance),
        "overdue_amount": float(overdue_amount),
        "credit_available": float(customer.credit_limit - balance) if customer.credit_limit > 0 else None
    }

def get_invoices_by_customer_and_company(
    db: Session,
    customer_id: int,
    company_id: int,
    skip: int = 0,
    limit: int = 100
):
    """Obtener facturas de un cliente específico"""
    # Verificar que el cliente pertenezca a la empresa
    verify_company_ownership(
        db=db,
        model_class=models.Customer,
        item_id=customer_id,
        company_id=company_id,
        error_message="Customer not found in your company"
    )
    
    return paginate_query(
        db.query(models.Invoice).filter(
            models.Invoice.customer_id == customer_id,
            models.Invoice.company_id == company_id
        ).order_by(models.Invoice.date.desc()),
        skip=skip,
        limit=limit
    ).all()

def get_customers_activity_report(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime
):
    """Reporte de actividad de clientes en un período"""
    return db.query(
        models.Customer.name,
        models.Customer.customer_code,
        func.count(models.Invoice.id).label('invoice_count'),
        func.sum(models.Invoice.total_amount).label('total_sales'),
        func.max(models.Invoice.date).label('last_sale_date')
    ).outerjoin(
        models.Invoice,
        and_(
            models.Customer.id == models.Invoice.customer_id,
            models.Invoice.status == 'factura',
            models.Invoice.date >= start_date,
            models.Invoice.date <= end_date
        )
    ).filter(
        models.Customer.company_id == company_id,
        models.Customer.is_active == True
    ).group_by(
        models.Customer.id
    ).order_by(
        func.sum(models.Invoice.total_amount).desc().nullslast()
    ).all()

def get_inactive_customers_report(
    db: Session,
    company_id: int,
    days_inactive: int = 90
):
    """Reporte de clientes inactivos (sin compras en X días)"""
    cutoff_date = datetime.utcnow().date() - timedelta(days=days_inactive)
    
    # Subquery para obtener la última fecha de compra de cada cliente
    last_sale_subquery = db.query(
        models.Invoice.customer_id,
        func.max(models.Invoice.date).label('last_sale_date')
    ).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura'
    ).group_by(models.Invoice.customer_id).subquery()
    
    return db.query(
        models.Customer.name,
        models.Customer.customer_code,
        models.Customer.email,
        models.Customer.phone,
        last_sale_subquery.c.last_sale_date
    ).outerjoin(
        last_sale_subquery,
        models.Customer.id == last_sale_subquery.c.customer_id
    ).filter(
        models.Customer.company_id == company_id,
        models.Customer.is_active == True,
        or_(
            last_sale_subquery.c.last_sale_date < cutoff_date,
            last_sale_subquery.c.last_sale_date.is_(None)
        )
    ).order_by(
        last_sale_subquery.c.last_sale_date.desc().nullslast()
    ).all()

def get_customer_credit_status_report(db: Session, company_id: int):
    """Reporte de estado de crédito de clientes"""
    return db.query(
        models.Customer.name,
        models.Customer.customer_code,
        models.Customer.credit_limit,
        func.sum(
            models.Invoice.total_amount - func.coalesce(models.Invoice.paid_amount, 0)
        ).label('outstanding_balance')
    ).outerjoin(
        models.Invoice,
        and_(
            models.Customer.id == models.Invoice.customer_id,
            models.Invoice.status == 'factura'
        )
    ).filter(
        models.Customer.company_id == company_id,
        models.Customer.is_active == True,
        models.Customer.credit_limit > 0
    ).group_by(
        models.Customer.id
    ).having(
        func.sum(
            models.Invoice.total_amount - func.coalesce(models.Invoice.paid_amount, 0)
        ) > 0
    ).order_by(
        models.Customer.credit_limit.desc()
    ).all()

# ================= OPERACIONES ADICIONALES =================

def reactivate_customer_for_company(db: Session, customer_id: int, company_id: int):
    """Reactivar cliente desactivado"""
    customer = verify_company_ownership(
        db=db,
        model_class=models.Customer,
        item_id=customer_id,
        company_id=company_id,
        error_message="Customer not found in your company"
    )
    
    if customer.is_active:
        raise HTTPException(
            status_code=400,
            detail="Customer is already active"
        )
    
    customer.is_active = True
    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)
    
    return customer

def merge_customers_for_company(
    db: Session,
    primary_customer_id: int,
    secondary_customer_id: int,
    company_id: int
):
    """Fusionar dos clientes (mover todas las facturas del secundario al primario)"""
    # Verificar que ambos clientes pertenezcan a la empresa
    primary_customer = verify_company_ownership(
        db=db,
        model_class=models.Customer,
        item_id=primary_customer_id,
        company_id=company_id,
        error_message="Primary customer not found in your company"
    )
    
    secondary_customer = verify_company_ownership(
        db=db,
        model_class=models.Customer,
        item_id=secondary_customer_id,
        company_id=company_id,
        error_message="Secondary customer not found in your company"
    )
    
    if primary_customer_id == secondary_customer_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot merge a customer with itself"
        )
    
    try:
        # Mover todas las facturas del cliente secundario al primario
        db.query(models.Invoice).filter(
            models.Invoice.customer_id == secondary_customer_id,
            models.Invoice.company_id == company_id
        ).update({"customer_id": primary_customer_id})
        
        # Combinar notas si es necesario
        if secondary_customer.notes:
            combined_notes = f"{primary_customer.notes or ''}\n---\nMerged from {secondary_customer.name}: {secondary_customer.notes}".strip()
            primary_customer.notes = combined_notes
        
        # Actualizar límite de crédito si el secundario tiene mayor
        if secondary_customer.credit_limit > primary_customer.credit_limit:
            primary_customer.credit_limit = secondary_customer.credit_limit
        
        # Desactivar cliente secundario
        secondary_customer.is_active = False
        secondary_customer.notes = f"Merged into {primary_customer.name} ({primary_customer.customer_code})"
        
        primary_customer.updated_at = datetime.utcnow()
        secondary_customer.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Customers merged successfully",
            "primary_customer": {
                "id": primary_customer.id,
                "name": primary_customer.name,
                "customer_code": primary_customer.customer_code
            },
            "merged_customer": {
                "id": secondary_customer.id,
                "name": secondary_customer.name,
                "customer_code": secondary_customer.customer_code
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error merging customers: {str(e)}"
        )

def bulk_update_customers_for_company(
    db: Session,
    company_id: int,
    updates
):
    """Actualización masiva de clientes"""
    results = []
    errors = []
    
    try:
        for update in updates:
            try:
                customer = verify_company_ownership(
                    db=db,
                    model_class=models.Customer,
                    item_id=update.customer_id,
                    company_id=company_id,
                    error_message=f"Customer {update.customer_id} not found"
                )
                
                # Actualizar campos especificados
                if hasattr(update, 'customer_type') and update.customer_type:
                    customer.customer_type = update.customer_type
                if hasattr(update, 'credit_limit') and update.credit_limit is not None:
                    customer.credit_limit = update.credit_limit
                if hasattr(update, 'payment_terms') and update.payment_terms is not None:
                    customer.payment_terms = update.payment_terms
                if hasattr(update, 'is_active') and update.is_active is not None:
                    customer.is_active = update.is_active
                
                customer.updated_at = datetime.utcnow()
                results.append(customer)
                
            except HTTPException as e:
                errors.append({
                    "customer_id": update.customer_id,
                    "error": e.detail
                })
        
        if results and not errors:
            db.commit()
            return {
                "updated_customers": len(results),
                "message": "Bulk update completed successfully",
                "errors": []
            }
        elif errors:
            db.rollback()
            return {
                "updated_customers": 0,
                "message": "Bulk update failed",
                "errors": errors
            }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Bulk update failed: {str(e)}"
        )

def export_customers_for_company(db: Session, company_id: int, active_only: bool = True):
    """Exportar clientes para descarga"""
    query = db.query(models.Customer).filter(
        models.Customer.company_id == company_id
    )
    
    if active_only:
        query = query.filter(models.Customer.is_active == True)
    
    customers = query.order_by(models.Customer.name).all()
    
    return [
        {
            "customer_code": c.customer_code,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "tax_id": c.tax_id,
            "customer_type": c.customer_type,
            "credit_limit": float(c.credit_limit),
            "payment_terms": c.payment_terms,
            "is_active": c.is_active,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "notes": c.notes
        }
        for c in customers
    ]

def import_customers_for_company(
    db: Session,
    company_id: int,
    customers_data
):
    """Importación masiva de clientes"""
    created_customers = []
    errors = []
    
    try:
        for i, customer_data in enumerate(customers_data):
            try:
                # Verificar duplicados por email
                if customer_data.email:
                    existing_email = db.query(models.Customer).filter(
                        models.Customer.company_id == company_id,
                        models.Customer.email == customer_data.email
                    ).first()
                    
                    if existing_email:
                        errors.append({
                            "row": i + 1,
                            "email": customer_data.email,
                            "error": "Email already exists"
                        })
                        continue
                
                # Verificar duplicados por tax_id
                if customer_data.tax_id:
                    existing_tax_id = db.query(models.Customer).filter(
                        models.Customer.company_id == company_id,
                        models.Customer.tax_id == customer_data.tax_id.upper()
                    ).first()
                    
                    if existing_tax_id:
                        errors.append({
                            "row": i + 1,
                            "tax_id": customer_data.tax_id,
                            "error": "Tax ID already exists"
                        })
                        continue
                
                # Generar código de cliente si no se proporciona
                if not customer_data.customer_code:
                    count = db.query(models.Customer).filter(
                        models.Customer.company_id == company_id
                    ).count()
                    customer_data.customer_code = f"CUS-{count + len(created_customers) + 1:06d}"
                
                # Crear cliente
                db_customer = models.Customer(
                    company_id=company_id,
                    customer_code=customer_data.customer_code,
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone,
                    address=customer_data.address,
                    tax_id=customer_data.tax_id.upper() if customer_data.tax_id else None,
                    customer_type=customer_data.customer_type or 'regular',
                    credit_limit=customer_data.credit_limit or 0,
                    payment_terms=customer_data.payment_terms or 0,
                    notes=customer_data.notes,
                    is_active=True
                )
                
                db.add(db_customer)
                created_customers.append(db_customer)
                
            except Exception as e:
                errors.append({
                    "row": i + 1,
                    "error": str(e)
                })
        
        if created_customers and not errors:
            db.commit()
            return {
                "imported_customers": len(created_customers),
                "message": "Import completed successfully",
                "errors": []
            }
        elif errors:
            db.rollback()
            return {
                "imported_customers": 0,
                "message": "Import failed",
                "errors": errors
            }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )