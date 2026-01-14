# crud/suppliers.py
"""
Funciones CRUD para gestión de proveedores
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

def get_suppliers_by_company(
    db: Session, 
    company_id: int, 
    skip: int = 0, 
    limit: int = 100
):
    """Obtener proveedores de una empresa específica"""
    return paginate_query(
        db.query(models.Supplier).filter(
            models.Supplier.company_id == company_id,
        ).order_by(models.Supplier.name),
        skip=skip,
        limit=limit
    ).all()

def get_supplier_by_id_and_company(db: Session, supplier_id: int, company_id: int):
    """Obtener proveedor específico de una empresa"""
    return verify_company_ownership(
        db=db,
        model_class=models.Supplier,
        item_id=supplier_id,
        company_id=company_id,
        error_message="Supplier not found in your company"
    )

def create_supplier_for_company(
    db: Session, 
    supplier_data: schemas.SupplierCreate, 
    company_id: int
):
    """Crear proveedor para empresa específica"""
    
    # Verificar que el email no exista en la empresa (si se proporciona)
    if hasattr(supplier_data, 'email') and supplier_data.email:
        existing_supplier = db.query(models.Supplier).filter(
            models.Supplier.company_id == company_id,
            models.Supplier.email == supplier_data.email
        ).first()
        
        if existing_supplier:
            raise HTTPException(
                status_code=400,
                detail="Supplier with this email already exists in your company"
            )
    
    # Verificar que el tax_id no exista en la empresa (si se proporciona)
    if hasattr(supplier_data, 'tax_id') and supplier_data.tax_id:
        existing_tax_id = db.query(models.Supplier).filter(
            models.Supplier.company_id == company_id,
            models.Supplier.tax_id == supplier_data.tax_id.upper()
        ).first()
        
        if existing_tax_id:
            raise HTTPException(
                status_code=400,
                detail="Supplier with this tax ID already exists in your company"
            )
    
    try:
        # Generar código de proveedor si no se proporciona
        supplier_code = None
        if hasattr(supplier_data, 'supplier_code') and supplier_data.supplier_code:
            supplier_code = supplier_data.supplier_code
        else:
            # Generar código automático
            count = db.query(models.Supplier).filter(
                models.Supplier.company_id == company_id
            ).count()
            supplier_code = f"SUP-{count + 1:06d}"
        
        # Crear proveedor
        db_supplier = models.Supplier(
            company_id=company_id,
            name=supplier_data.name,
            address=getattr(supplier_data, 'address', None),
            tax_id=getattr(supplier_data, 'tax_id', '').upper() if getattr(supplier_data, 'tax_id', None) else None,
            contact=getattr(supplier_data, 'contact', None),
        )
        
 
        
        db.add(db_supplier)
        db.commit()
        db.refresh(db_supplier)
        
        return db_supplier
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating supplier: {str(e)}"
        )

def update_supplier_for_company(
    db: Session, 
    supplier_id: int, 
    supplier_data: schemas.SupplierUpdate, 
    company_id: int
):
    """Actualizar proveedor de una empresa"""
    supplier = verify_company_ownership(
        db=db,
        model_class=models.Supplier,
        item_id=supplier_id,
        company_id=company_id,
        error_message="Supplier not found in your company"
    )
    
    # Verificar email único si se actualiza
    if hasattr(supplier_data, 'email') and supplier_data.email and supplier_data.email != supplier.email:
        existing_email = db.query(models.Supplier).filter(
            models.Supplier.company_id == company_id,
            models.Supplier.email == supplier_data.email,
            models.Supplier.id != supplier_id
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already exists for another supplier"
            )
    
    # Verificar tax_id único si se actualiza
    if hasattr(supplier_data, 'tax_id') and supplier_data.tax_id:
        tax_id_upper = supplier_data.tax_id.upper()
        if tax_id_upper != supplier.tax_id:
            existing_tax_id = db.query(models.Supplier).filter(
                models.Supplier.company_id == company_id,
                models.Supplier.tax_id == tax_id_upper,
                models.Supplier.id != supplier_id
            ).first()
            
            if existing_tax_id:
                raise HTTPException(
                    status_code=400,
                    detail="Tax ID already exists for another supplier"
                )
    
    # Actualizar campos
    for key, value in supplier_data.dict(exclude_unset=True).items():
        if key == 'tax_id' and value:
            setattr(supplier, key, value.upper())
        else:
            setattr(supplier, key, value)
    
    supplier.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(supplier)
    
    return supplier

def delete_supplier_for_company(db: Session, supplier_id: int, company_id: int):
    """Eliminar (desactivar) proveedor de una empresa"""
    supplier = verify_company_ownership(
        db=db,
        model_class=models.Supplier,
        item_id=supplier_id,
        company_id=company_id,
        error_message="Supplier not found in your company"
    )
    
    # Verificar si tiene compras asociadas
    has_purchases = db.query(models.Purchase).filter(
        models.Purchase.supplier_id == supplier_id,
        models.Purchase.company_id == company_id
    ).first()
    
    if has_purchases:
        # Soft delete - solo desactivar
        supplier.is_active = False
        supplier.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Supplier deactivated successfully (has related purchases)"}
    else:
        # Hard delete si no tiene compras
        db.delete(supplier)
        db.commit()
        return {"message": "Supplier deleted successfully"}

# ================= FUNCIONES DE BÚSQUEDA Y FILTROS =================

def search_suppliers_by_company(db: Session, company_id: int, search_term: str):
    """Buscar proveedores por nombre, email o tax_id en una empresa"""
    return db.query(models.Supplier).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.is_active == True,
        or_(
            models.Supplier.name.ilike(f"%{search_term}%"),
            models.Supplier.email.ilike(f"%{search_term}%"),
            models.Supplier.tax_id.ilike(f"%{search_term}%"),
            models.Supplier.supplier_code.ilike(f"%{search_term}%"),
            models.Supplier.contact_person.ilike(f"%{search_term}%")
        )
    ).order_by(models.Supplier.name).all()

def get_suppliers_by_type_and_company(
    db: Session,
    company_id: int,
    supplier_type: str
):
    """Obtener proveedores por tipo en una empresa"""
    return db.query(models.Supplier).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.supplier_type == supplier_type,
        models.Supplier.is_active == True
    ).order_by(models.Supplier.name).all()

def get_suppliers_by_credit_rating(
    db: Session,
    company_id: int,
    credit_rating: str
):
    """Obtener proveedores por calificación crediticia"""
    return db.query(models.Supplier).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.credit_rating == credit_rating,
        models.Supplier.is_active == True
    ).order_by(models.Supplier.name).all()

# ================= ESTADÍSTICAS Y REPORTES =================

def get_suppliers_stats_by_company(db: Session, company_id: int):
    """Estadísticas de proveedores por empresa"""
    # Total proveedores activos
    total_suppliers = db.query(models.Supplier).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.is_active == True
    ).count()
    
    # Proveedores inactivos
    inactive_suppliers = db.query(models.Supplier).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.is_active == False
    ).count()
    
    # Proveedores por tipo
    suppliers_by_type = db.query(
        models.Supplier.supplier_type,
        func.count(models.Supplier.id).label('count')
    ).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.is_active == True
    ).group_by(models.Supplier.supplier_type).all()
    
    # Proveedores por calificación crediticia
    suppliers_by_rating = db.query(
        models.Supplier.credit_rating,
        func.count(models.Supplier.id).label('count')
    ).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.is_active == True
    ).group_by(models.Supplier.credit_rating).all()
    
    # Proveedores con compras recientes (últimos 90 días)
    recent_date = datetime.utcnow().date() - timedelta(days=90)
    active_suppliers = db.query(models.Supplier.id).join(
        models.Purchase,
        models.Supplier.id == models.Purchase.supplier_id
    ).filter(
        models.Supplier.company_id == company_id,
        models.Purchase.date >= recent_date,
        models.Purchase.status == 'received'
    ).distinct().count()
    
    return {
        "total_suppliers": total_suppliers,
        "inactive_suppliers": inactive_suppliers,
        "active_suppliers_90_days": active_suppliers,
        "suppliers_by_type": {
            supplier_type: count for supplier_type, count in suppliers_by_type
        },
        "suppliers_by_credit_rating": {
            rating: count for rating, count in suppliers_by_rating
        }
    }

def get_top_suppliers_by_purchases(
    db: Session,
    company_id: int,
    limit: int = 10
):
    """Obtener top proveedores por volumen de compras"""
    return db.query(
        models.Supplier.name,
        models.Supplier.supplier_code,
        models.Supplier.email,
        models.Supplier.contact_person,
        func.sum(models.Purchase.total_amount).label('total_purchases'),
        func.count(models.Purchase.id).label('purchase_count'),
        func.avg(models.Purchase.total_amount).label('avg_purchase')
    ).join(
        models.Purchase,
        models.Supplier.id == models.Purchase.supplier_id
    ).filter(
        models.Supplier.company_id == company_id,
        models.Purchase.status == 'received'
    ).group_by(
        models.Supplier.id
    ).order_by(
        func.sum(models.Purchase.total_amount).desc()
    ).limit(limit).all()

def get_purchases_by_supplier_and_company(
    db: Session,
    supplier_id: int,
    company_id: int,
    skip: int = 0,
    limit: int = 100
):
    """Obtener compras de un proveedor específico"""
    # Verificar que el proveedor pertenezca a la empresa
    verify_company_ownership(
        db=db,
        model_class=models.Supplier,
        item_id=supplier_id,
        company_id=company_id,
        error_message="Supplier not found in your company"
    )
    
    return paginate_query(
        db.query(models.Purchase).filter(
            models.Purchase.supplier_id == supplier_id,
            models.Purchase.company_id == company_id
        ).order_by(models.Purchase.date.desc()),
        skip=skip,
        limit=limit
    ).all()

def get_supplier_performance_report(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime
):
    """Reporte de performance de proveedores en un período"""
    return db.query(
        models.Supplier.name,
        models.Supplier.supplier_code,
        models.Supplier.credit_rating,
        func.count(models.Purchase.id).label('purchase_count'),
        func.sum(models.Purchase.total_amount).label('total_purchases'),
        func.avg(models.Purchase.total_amount).label('avg_purchase'),
        func.min(models.Purchase.date).label('first_purchase'),
        func.max(models.Purchase.date).label('last_purchase')
    ).outerjoin(
        models.Purchase,
        and_(
            models.Supplier.id == models.Purchase.supplier_id,
            models.Purchase.status == 'received',
            models.Purchase.date >= start_date,
            models.Purchase.date <= end_date
        )
    ).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.is_active == True
    ).group_by(
        models.Supplier.id
    ).order_by(
        func.sum(models.Purchase.total_amount).desc().nullslast()
    ).all()

def get_suppliers_payment_terms_report(db: Session, company_id: int):
    """Reporte de términos de pago de proveedores"""
    return db.query(
        models.Supplier.payment_terms,
        func.count(models.Supplier.id).label('supplier_count'),
        func.sum(models.Purchase.total_amount).label('total_purchases')
    ).outerjoin(
        models.Purchase,
        and_(
            models.Supplier.id == models.Purchase.supplier_id,
            models.Purchase.status == 'received'
        )
    ).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.is_active == True
    ).group_by(
        models.Supplier.payment_terms
    ).order_by(
        models.Supplier.payment_terms.asc()
    ).all()

def get_inactive_suppliers_report(
    db: Session,
    company_id: int,
    days_inactive: int = 180
):
    """Reporte de proveedores inactivos (sin compras en X días)"""
    cutoff_date = datetime.utcnow().date() - timedelta(days=days_inactive)
    
    # Subquery para obtener la última fecha de compra de cada proveedor
    last_purchase_subquery = db.query(
        models.Purchase.supplier_id,
        func.max(models.Purchase.date).label('last_purchase_date')
    ).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.status == 'received'
    ).group_by(models.Purchase.supplier_id).subquery()
    
    return db.query(
        models.Supplier.name,
        models.Supplier.supplier_code,
        models.Supplier.email,
        models.Supplier.contact_person,
        models.Supplier.phone,
        last_purchase_subquery.c.last_purchase_date
    ).outerjoin(
        last_purchase_subquery,
        models.Supplier.id == last_purchase_subquery.c.supplier_id
    ).filter(
        models.Supplier.company_id == company_id,
        models.Supplier.is_active == True,
        or_(
            last_purchase_subquery.c.last_purchase_date < cutoff_date,
            last_purchase_subquery.c.last_purchase_date.is_(None)
        )
    ).order_by(
        last_purchase_subquery.c.last_purchase_date.desc().nullslast()
    ).all()

# ================= OPERACIONES ADICIONALES =================

def reactivate_supplier_for_company(db: Session, supplier_id: int, company_id: int):
    """Reactivar proveedor desactivado"""
    supplier = verify_company_ownership(
        db=db,
        model_class=models.Supplier,
        item_id=supplier_id,
        company_id=company_id,
        error_message="Supplier not found in your company"
    )
    
    if supplier.is_active:
        raise HTTPException(
            status_code=400,
            detail="Supplier is already active"
        )
    
    supplier.is_active = True
    supplier.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(supplier)
    
    return supplier

def bulk_update_suppliers_for_company(
    db: Session,
    company_id: int,
    updates
):
    """Actualización masiva de proveedores"""
    results = []
    errors = []
    
    try:
        for update in updates:
            try:
                supplier = verify_company_ownership(
                    db=db,
                    model_class=models.Supplier,
                    item_id=update.supplier_id,
                    company_id=company_id,
                    error_message=f"Supplier {update.supplier_id} not found"
                )
                
                # Actualizar campos especificados
                if hasattr(update, 'supplier_type') and update.supplier_type:
                    supplier.supplier_type = update.supplier_type
                if hasattr(update, 'credit_rating') and update.credit_rating:
                    supplier.credit_rating = update.credit_rating
                if hasattr(update, 'payment_terms') and update.payment_terms is not None:
                    supplier.payment_terms = update.payment_terms
                if hasattr(update, 'is_active') and update.is_active is not None:
                    supplier.is_active = update.is_active
                
                supplier.updated_at = datetime.utcnow()
                results.append(supplier)
                
            except HTTPException as e:
                errors.append({
                    "supplier_id": update.supplier_id,
                    "error": e.detail
                })
        
        if results and not errors:
            db.commit()
            return {
                "updated_suppliers": len(results),
                "message": "Bulk update completed successfully",
                "errors": []
            }
        elif errors:
            db.rollback()
            return {
                "updated_suppliers": 0,
                "message": "Bulk update failed",
                "errors": errors
            }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Bulk update failed: {str(e)}"
        )

def export_suppliers_for_company(db: Session, company_id: int, active_only: bool = True):
    """Exportar proveedores para descarga"""
    query = db.query(models.Supplier).filter(
        models.Supplier.company_id == company_id
    )
    
    if active_only:
        query = query.filter(models.Supplier.is_active == True)
    
    suppliers = query.order_by(models.Supplier.name).all()
    
    return [
        {
            "supplier_code": s.supplier_code,
            "name": s.name,
            "email": s.email,
            "phone": s.phone,
            "address": s.address,
            "tax_id": s.tax_id,
            "supplier_type": s.supplier_type,
            "payment_terms": s.payment_terms,
            "credit_rating": s.credit_rating,
            "contact_person": s.contact_person,
            "website": s.website,
            "is_active": s.is_active,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "notes": s.notes
        }
        for s in suppliers
    ]

def import_suppliers_for_company(
    db: Session,
    company_id: int,
    suppliers_data
):
    """Importación masiva de proveedores"""
    created_suppliers = []
    errors = []
    
    try:
        for i, supplier_data in enumerate(suppliers_data):
            try:
                # Verificar duplicados por email
                if supplier_data.email:
                    existing_email = db.query(models.Supplier).filter(
                        models.Supplier.company_id == company_id,
                        models.Supplier.email == supplier_data.email
                    ).first()
                    
                    if existing_email:
                        errors.append({
                            "row": i + 1,
                            "email": supplier_data.email,
                            "error": "Email already exists"
                        })
                        continue
                
                # Verificar duplicados por tax_id
                if supplier_data.tax_id:
                    existing_tax_id = db.query(models.Supplier).filter(
                        models.Supplier.company_id == company_id,
                        models.Supplier.tax_id == supplier_data.tax_id.upper()
                    ).first()
                    
                    if existing_tax_id:
                        errors.append({
                            "row": i + 1,
                            "tax_id": supplier_data.tax_id,
                            "error": "Tax ID already exists"
                        })
                        continue
                
                # Generar código de proveedor si no se proporciona
                if not supplier_data.supplier_code:
                    count = db.query(models.Supplier).filter(
                        models.Supplier.company_id == company_id
                    ).count()
                    supplier_data.supplier_code = f"SUP-{count + len(created_suppliers) + 1:06d}"
                
                # Crear proveedor
                db_supplier = models.Supplier(
                    company_id=company_id,
                    supplier_code=supplier_data.supplier_code,
                    name=supplier_data.name,
                    email=supplier_data.email,
                    phone=supplier_data.phone,
                    address=supplier_data.address,
                    tax_id=supplier_data.tax_id.upper() if supplier_data.tax_id else None,
                    supplier_type=supplier_data.supplier_type or 'regular',
                    payment_terms=supplier_data.payment_terms or 0,
                    credit_rating=supplier_data.credit_rating or 'A',
                    contact_person=supplier_data.contact_person,
                    website=supplier_data.website,
                    notes=supplier_data.notes,
                    is_active=True
                )
                
                db.add(db_supplier)
                created_suppliers.append(db_supplier)
                
            except Exception as e:
                errors.append({
                    "row": i + 1,
                    "error": str(e)
                })
        
        if created_suppliers and not errors:
            db.commit()
            return {
                "imported_suppliers": len(created_suppliers),
                "message": "Import completed successfully",
                "errors": []
            }
        elif errors:
            db.rollback()
            return {
                "imported_suppliers": 0,
                "message": "Import failed",
                "errors": errors
            }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )

def create_supplier_evaluation(
    db: Session,
    supplier_id: int,
    company_id: int,
    evaluation_data
):
    """Crear evaluación de proveedor"""
    # Verificar que el proveedor pertenezca a la empresa
    supplier = verify_company_ownership(
        db=db,
        model_class=models.Supplier,
        item_id=supplier_id,
        company_id=company_id,
        error_message="Supplier not found in your company"
    )
    
    try:
        evaluation = models.SupplierEvaluation(
            supplier_id=supplier_id,
            evaluation_date=evaluation_data.evaluation_date or datetime.utcnow().date(),
            quality_rating=evaluation_data.quality_rating,
            delivery_rating=evaluation_data.delivery_rating,
            price_rating=evaluation_data.price_rating,
            service_rating=evaluation_data.service_rating,
            overall_rating=(
                evaluation_data.quality_rating + 
                evaluation_data.delivery_rating + 
                evaluation_data.price_rating + 
                evaluation_data.service_rating
            ) / 4,
            comments=evaluation_data.comments,
            evaluator=evaluation_data.evaluator
        )
        
        db.add(evaluation)
        
        # Actualizar calificación del proveedor basada en la evaluación
        if evaluation.overall_rating >= 4.5:
            supplier.credit_rating = 'A+'
        elif evaluation.overall_rating >= 4.0:
            supplier.credit_rating = 'A'
        elif evaluation.overall_rating >= 3.5:
            supplier.credit_rating = 'B+'
        elif evaluation.overall_rating >= 3.0:
            supplier.credit_rating = 'B'
        elif evaluation.overall_rating >= 2.5:
            supplier.credit_rating = 'C'
        else:
            supplier.credit_rating = 'D'
        
        supplier.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(evaluation)
        
        return evaluation
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating supplier evaluation: {str(e)}"
        )

def get_supplier_evaluations(
    db: Session,
    supplier_id: int,
    company_id: int,
    limit: int = 10
):
    """Obtener evaluaciones de un proveedor"""
    # Verificar que el proveedor pertenezca a la empresa
    verify_company_ownership(
        db=db,
        model_class=models.Supplier,
        item_id=supplier_id,
        company_id=company_id,
        error_message="Supplier not found in your company"
    )
    
    return db.query(models.SupplierEvaluation).filter(
        models.SupplierEvaluation.supplier_id == supplier_id
    ).order_by(
        models.SupplierEvaluation.evaluation_date.desc()
    ).limit(limit).all()

def get_suppliers_by_product_category(
    db: Session,
    company_id: int,
    category_id: int
):
    """Obtener proveedores que suministran productos de una categoría específica"""
    return db.query(models.Supplier).join(
        models.Purchase,
        models.Supplier.id == models.Purchase.supplier_id
    ).join(
        models.PurchaseItem,
        models.Purchase.id == models.PurchaseItem.purchase_id
    ).join(
        models.Product,
        models.PurchaseItem.product_id == models.Product.id
    ).filter(
        models.Supplier.company_id == company_id,
        models.Product.category_id == category_id,
        models.Supplier.is_active == True
    ).distinct().order_by(models.Supplier.name).all()

def get_supplier_product_catalog(
    db: Session,
    supplier_id: int,
    company_id: int
):
    """Obtener catálogo de productos de un proveedor (productos que hemos comprado)"""
    # Verificar que el proveedor pertenezca a la empresa
    verify_company_ownership(
        db=db,
        model_class=models.Supplier,
        item_id=supplier_id,
        company_id=company_id,
        error_message="Supplier not found in your company"
    )
    
    return db.query(
        models.Product.name,
        models.Product.sku,
        models.Product.category_id,
        func.avg(models.PurchaseItem.unit_cost).label('avg_cost'),
        func.min(models.PurchaseItem.unit_cost).label('min_cost'),
        func.max(models.PurchaseItem.unit_cost).label('max_cost'),
        func.sum(models.PurchaseItem.quantity).label('total_purchased'),
        func.count(models.PurchaseItem.id).label('purchase_frequency'),
        func.max(models.Purchase.date).label('last_purchase_date')
    ).join(
        models.PurchaseItem,
        models.Product.id == models.PurchaseItem.product_id
    ).join(
        models.Purchase,
        models.PurchaseItem.purchase_id == models.Purchase.id
    ).filter(
        models.Purchase.supplier_id == supplier_id,
        models.Purchase.company_id == company_id,
        models.Purchase.status == 'received'
    ).group_by(
        models.Product.id
    ).order_by(
        func.sum(models.PurchaseItem.quantity).desc()
    ).all()

def suggest_alternative_suppliers(
    db: Session,
    product_id: int,
    current_supplier_id: int,
    company_id: int
):
    """Sugerir proveedores alternativos para un producto específico"""
    # Verificar que el producto pertenezca a la empresa
    verify_company_ownership(
        db=db,
        model_class=models.Product,
        item_id=product_id,
        company_id=company_id,
        error_message="Product not found in your company"
    )
    
    # Buscar otros proveedores que han suministrado este producto
    alternative_suppliers = db.query(
        models.Supplier.name,
        models.Supplier.supplier_code,
        models.Supplier.credit_rating,
        models.Supplier.contact_person,
        func.avg(models.PurchaseItem.unit_cost).label('avg_cost'),
        func.count(models.Purchase.id).label('purchase_count'),
        func.max(models.Purchase.date).label('last_purchase_date')
    ).join(
        models.Purchase,
        models.Supplier.id == models.Purchase.supplier_id
    ).join(
        models.PurchaseItem,
        models.Purchase.id == models.PurchaseItem.purchase_id
    ).filter(
        models.PurchaseItem.product_id == product_id,
        models.Purchase.company_id == company_id,
        models.Purchase.status == 'received',
        models.Supplier.id != current_supplier_id,
        models.Supplier.is_active == True
    ).group_by(
        models.Supplier.id
    ).order_by(
        func.avg(models.PurchaseItem.unit_cost).asc()
    ).all()
    
    return alternative_suppliers