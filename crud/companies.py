# crud/companies.py
"""
Funciones CRUD para gestión de empresas
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException
from datetime import datetime
from typing import Optional
import models
import schemas
from auth import hash_password

# ================= GESTIÓN DE EMPRESAS =================

def create_company_with_admin(db: Session, company_data: schemas.CompanyCreate):
    """Crear empresa nueva con usuario administrador"""
    
    # Verificar que el tax_id no exista
    existing_company = db.query(models.Company).filter(
        models.Company.tax_id == company_data.tax_id.upper()
    ).first()
    
    if existing_company:
        raise HTTPException(
            status_code=400,
            detail="Company with this tax ID already exists"
        )
    
    try:
        # Crear empresa
        db_company = models.Company(
            name=company_data.name,
            legal_name=company_data.legal_name,
            tax_id=company_data.tax_id.upper(),
            email=company_data.email,
            phone=company_data.phone,
            address=company_data.address,
            currency=company_data.currency,
            timezone=company_data.timezone,
            invoice_prefix=company_data.invoice_prefix,
            next_invoice_number=1,
            date_format="YYYY-MM-DD",
            is_active=True
        )
        
        db.add(db_company)
        db.flush()  # Para obtener el ID
        
        # Crear usuario administrador
        admin_user = models.User(
            username=company_data.admin_username,
            email=company_data.admin_email,
            hashed_password=hash_password(company_data.admin_password),
            company_id=db_company.id,
            role="admin",
            is_company_admin=True,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(db_company)
        
        return db_company
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

def get_company_dashboard(db: Session, company_id: int):
    """Obtener dashboard con métricas de la empresa"""
    company = db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Métricas básicas
    total_products = db.query(models.Product).filter(
        models.Product.company_id == company_id
    ).count()
    
    total_customers = db.query(models.Customer).filter(
        models.Customer.company_id == company_id
    ).count()
    
    total_warehouses = db.query(models.Warehouse).filter(
        models.Warehouse.company_id == company_id
    ).count()
    
    # Ventas del mes actual
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_sales = db.query(func.sum(models.Invoice.total_amount)).filter(
        and_(
            models.Invoice.company_id == company_id,
            models.Invoice.status == "factura",
            models.Invoice.date >= start_of_month
        )
    ).scalar() or 0.0
    
    # Facturas pendientes (presupuestos)
    pending_invoices = db.query(models.Invoice).filter(
        and_(
            models.Invoice.company_id == company_id,
            models.Invoice.status == "presupuesto"
        )
    ).count()
    
    # Productos con stock bajo
    low_stock_products = db.query(models.Product).filter(
        and_(
            models.Product.company_id == company_id,
            models.Product.quantity <= 10
        )
    ).count()
    
    # Usuarios activos
    active_users = db.query(models.User).filter(
        and_(
            models.User.company_id == company_id,
            models.User.is_active == True
        )
    ).count()
    
    # Valor total del inventario
    inventory_value = db.query(
        func.sum(models.Product.price * models.Product.quantity)
    ).filter(
        models.Product.company_id == company_id
    ).scalar() or 0.0
    
    return schemas.CompanyDashboard(
        company=company,
        total_products=total_products,
        total_customers=total_customers,
        total_warehouses=total_warehouses,
        monthly_sales=float(monthly_sales),
        pending_invoices=pending_invoices,
        low_stock_products=low_stock_products,
        active_users=active_users,
        inventory_value=float(inventory_value)
    )

def update_company(db: Session, company_id: int, company_update: schemas.CompanyUpdate):
    """Actualizar información de empresa"""
    company = db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Actualizar campos
    update_data = company_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'tax_id' and value:
            # Verificar que el nuevo tax_id no exista
            existing = db.query(models.Company).filter(
                models.Company.tax_id == value.upper(),
                models.Company.id != company_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Tax ID already exists"
                )
            setattr(company, field, value.upper())
        else:
            setattr(company, field, value)
    
    company.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(company)
    
    return company

# ================= CONFIGURACIONES DE EMPRESA =================

def get_company_settings(db: Session, company_id: int):
    """Obtener configuraciones de la empresa"""
    company = db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return schemas.CompanySettings(
        currency=company.currency,
        timezone=company.timezone,
        date_format=company.date_format or "YYYY-MM-DD",
        invoice_prefix=company.invoice_prefix,
        next_invoice_number=company.next_invoice_number,
        low_stock_threshold=10,  # Valor por defecto
        auto_increment_invoice=True,  # Valor por defecto
        require_customer_tax_id=False  # Valor por defecto
    )

def update_company_settings(
    db: Session, 
    company_id: int, 
    settings: schemas.CompanySettings
):
    """Actualizar configuraciones de la empresa"""
    company = db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Actualizar configuraciones
    company.currency = settings.currency
    company.timezone = settings.timezone
    company.date_format = settings.date_format
    company.invoice_prefix = settings.invoice_prefix
    company.next_invoice_number = settings.next_invoice_number
    company.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(company)
    
    return settings

# ================= ESTADÍSTICAS AVANZADAS =================

def get_company_financial_summary(db: Session, company_id: int, months: int = 12):
    """Obtener resumen financiero de la empresa por meses"""
    # Calcular fecha de inicio
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    # Ventas por mes
    monthly_sales = db.query(
        func.date_format(models.Invoice.date, '%Y-%m').label('month'),
        func.sum(models.Invoice.total_amount).label('total_sales'),
        func.count(models.Invoice.id).label('invoice_count')
    ).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura',
        models.Invoice.date >= start_date
    ).group_by(
        func.date_format(models.Invoice.date, '%Y-%m')
    ).all()
    
    # Compras por mes
    monthly_purchases = db.query(
        func.date_format(models.Purchase.date, '%Y-%m').label('month'),
        func.sum(models.Purchase.total_amount).label('total_purchases'),
        func.count(models.Purchase.id).label('purchase_count')
    ).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.date >= start_date
    ).group_by(
        func.date_format(models.Purchase.date, '%Y-%m')
    ).all()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "months": months
        },
        "monthly_sales": [
            {
                "month": sale.month,
                "total_sales": float(sale.total_sales),
                "invoice_count": sale.invoice_count
            }
            for sale in monthly_sales
        ],
        "monthly_purchases": [
            {
                "month": purchase.month,
                "total_purchases": float(purchase.total_purchases),
                "purchase_count": purchase.purchase_count
            }
            for purchase in monthly_purchases
        ]
    }

def get_company_top_products(db: Session, company_id: int, limit: int = 10):
    """Obtener productos más vendidos de la empresa"""
    return db.query(
        models.Product.name,
        models.Product.sku,
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

def get_company_inventory_alert(db: Session, company_id: int):
    """Obtener alertas de inventario de la empresa"""
    low_stock = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity <= 10,
        models.Product.quantity > 0
    ).all()
    
    out_of_stock = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity == 0
    ).all()
    
    overstock = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity >= 1000  # Configurable
    ).all()
    
    return {
        "low_stock": [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "current_stock": p.quantity,
                "price": float(p.price)
            }
            for p in low_stock
        ],
        "out_of_stock": [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "price": float(p.price)
            }
            for p in out_of_stock
        ],
        "overstock": [
            {
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "current_stock": p.quantity,
                "price": float(p.price)
            }
            for p in overstock
        ]
    }

def get_company_user_activity(db: Session, company_id: int):
    """Obtener estadísticas de actividad de usuarios"""
    users = db.query(models.User).filter(
        models.User.company_id == company_id
    ).all()
    
    total_users = len(users)
    active_users = len([u for u in users if u.is_active])
    admin_users = len([u for u in users if u.is_company_admin])
    
    # Últimos logins
    recent_logins = db.query(models.User).filter(
        models.User.company_id == company_id,
        models.User.last_login.isnot(None)
    ).order_by(
        models.User.last_login.desc()
    ).limit(10).all()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "admin_users": admin_users,
        "recent_logins": [
            {
                "username": u.username,
                "last_login": u.last_login,
                "role": u.role
            }
            for u in recent_logins
        ]
    }

def deactivate_company(db: Session, company_id: int):
    """Desactivar empresa (soft delete)"""
    company = db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.is_active = False
    company.updated_at = datetime.utcnow()
    
    # También desactivar todos los usuarios
    db.query(models.User).filter(
        models.User.company_id == company_id
    ).update({"is_active": False})
    
    db.commit()
    
    return {"message": "Company deactivated successfully"}

def reactivate_company(db: Session, company_id: int):
    """Reactivar empresa"""
    company = db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.is_active = True
    company.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Company reactivated successfully"}