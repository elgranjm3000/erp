# crud/base.py
"""
Funciones base y utilidades comunes para todos los módulos CRUD
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from typing import Optional, List, Type, TypeVar
import models
import sys
import os
# Importar schemas.py directamente para evitar importar el package schemas/
spec = sys.modules.get('schemas_file') or __import__('importlib').util.spec_from_file_location("schemas_file", "/home/erp/schemas.py")
if 'schemas_file' not in sys.modules:
    schemas_file = __import__('importlib').util.module_from_spec(spec)
    sys.modules['schemas_file'] = schemas_file
    spec.loader.exec_module(schemas_file)
schemas = sys.modules['schemas_file']
from passlib.context import CryptContext

# Type variable para funciones genéricas
ModelType = TypeVar("ModelType", bound=models.Base)

# Context para password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ================= FUNCIONES UTILITARIAS =================

def verify_company_ownership(
    db: Session, 
    model_class: Type[ModelType], 
    item_id: int, 
    company_id: int, 
    error_message: str = "Item not found in your company"
) -> ModelType:
    """
    Verifica que un elemento pertenezca a la empresa especificada
    """
    item = db.query(model_class).filter(
        model_class.id == item_id,
        model_class.company_id == company_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail=error_message)
    
    return item

def get_next_sequence_number(
    db: Session, 
    company_id: int, 
    prefix: str, 
    table_name: str
) -> str:
    """
    Genera el siguiente número de secuencia para una empresa
    """
    # Esto es un ejemplo, ajustar según tu lógica específica
    count = db.query(func.count()).filter_by(company_id=company_id).scalar()
    return f"{prefix}-{count + 1:06d}"

def paginate_query(query, skip: int = 0, limit: int = 100):
    """
    Aplica paginación a una query
    """
    return query.offset(skip).limit(limit)

def apply_search_filter(query, model_class, search_term: str, fields: List[str]):
    """
    Aplica filtros de búsqueda a múltiples campos
    """
    if not search_term:
        return query
    
    search_conditions = []
    for field in fields:
        if hasattr(model_class, field):
            attr = getattr(model_class, field)
            search_conditions.append(attr.ilike(f"%{search_term}%"))
    
    if search_conditions:
        from sqlalchemy import or_
        query = query.filter(or_(*search_conditions))
    
    return query

# ================= FUNCIONES LEGACY (MANTENER PARA COMPATIBILIDAD) =================

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    """Legacy: obtener categorías sin filtro de empresa"""
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    """Legacy: crear categoría sin empresa específica"""
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# ================= FUNCIONES CATEGORÍAS CON EMPRESA =================

def get_categories_by_company(db: Session, company_id: int, skip: int = 0, limit: int = 100):
    """Obtener categorías de una empresa específica"""
    return db.query(models.Category).filter(
        models.Category.company_id == company_id
    ).offset(skip).limit(limit).all()

def get_category_by_id_and_company(db: Session, category_id: int, company_id: int):
    """Obtener categoría específica de una empresa"""
    return verify_company_ownership(
        db=db,
        model_class=models.Category,
        item_id=category_id,
        company_id=company_id,
        error_message="Category not found in your company"
    )

def create_category_for_company(db: Session, category: schemas.CategoryCreate, company_id: int):
    """Crear categoría para una empresa específica"""
    db_category = models.Category(
        company_id=company_id,
        **category.dict()
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category_for_company(
    db: Session, 
    category_id: int, 
    category_data: schemas.CategoryUpdate, 
    company_id: int
):
    """Actualizar categoría de una empresa"""
    category = verify_company_ownership(
        db=db,
        model_class=models.Category,
        item_id=category_id,
        company_id=company_id,
        error_message="Category not found in your company"
    )
    
    for key, value in category_data.dict(exclude_unset=True).items():
        setattr(category, key, value)
    
    db.commit()
    db.refresh(category)
    return category

def delete_category_for_company(db: Session, category_id: int, company_id: int):
    """Eliminar categoría de una empresa"""
    category = verify_company_ownership(
        db=db,
        model_class=models.Category,
        item_id=category_id,
        company_id=company_id,
        error_message="Category not found in your company"
    )
    
    # Verificar si hay productos usando esta categoría
    products_count = db.query(models.Product).filter(
        models.Product.category_id == category_id,
        models.Product.company_id == company_id
    ).count()
    
    if products_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete category with assigned products"
        )
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}

def get_categories_stats_by_company(db: Session, company_id: int):
    """Estadísticas de categorías por empresa"""
    total_categories = db.query(models.Category).filter(
        models.Category.company_id == company_id
    ).count()
    
    categories_with_products = db.query(models.Category).join(
        models.Product,
        models.Category.id == models.Product.category_id
    ).filter(
        models.Category.company_id == company_id
    ).distinct().count()
    
    return {
        "total_categories": total_categories,
        "categories_with_products": categories_with_products,
        "empty_categories": total_categories - categories_with_products
    }