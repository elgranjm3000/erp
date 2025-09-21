from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import User
from typing import List
from auth import verify_token, check_permission

router = APIRouter()

# ================= CATEGORÍAS CON FILTRO POR EMPRESA =================

@router.get("/categories", response_model=List[schemas.Category])
def read_categories(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Listar categorías de mi empresa"""
    return crud.get_categories_by_company(
        db=db, 
        company_id=current_user.company_id,
        skip=skip, 
        limit=limit
    )

@router.get("/categories/{category_id}", response_model=schemas.Category)
def read_category(
    category_id: int, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener categoría específica de mi empresa"""
    return crud.get_category_by_id_and_company(
        db=db, 
        category_id=category_id, 
        company_id=current_user.company_id
    )

@router.post("/categories", response_model=schemas.Category)
def create_category(
    category: schemas.CategoryCreate, 
    current_user: User = Depends(check_permission(role="user")),
    db: Session = Depends(database.get_db)
):
    """Crear categoría en mi empresa"""
    return crud.create_category_for_company(
        db=db, 
        category=category, 
        company_id=current_user.company_id
    )

@router.put("/categories/{category_id}", response_model=schemas.Category)
def update_category(
    category_id: int, 
    category_data: schemas.CategoryUpdate, 
    current_user: User = Depends(check_permission(role="user")),
    db: Session = Depends(database.get_db)
):
    """Actualizar categoría de mi empresa"""
    return crud.update_category_for_company(
        db=db, 
        category_id=category_id, 
        category_data=category_data,
        company_id=current_user.company_id
    )

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int, 
    current_user: User = Depends(check_permission(role="manager")),
    db: Session = Depends(database.get_db)
):
    """Eliminar categoría de mi empresa"""
    return crud.delete_category_for_company(
        db=db, 
        category_id=category_id,
        company_id=current_user.company_id
    )

# ================= ENDPOINTS ESPECÍFICOS =================

@router.get("/categories/{category_id}/products", response_model=List[schemas.Product])
def get_category_products(
    category_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener productos de una categoría específica"""
    # Verificar que la categoría pertenezca a la empresa
    category = crud.get_category_by_id_and_company(
        db=db, 
        category_id=category_id, 
        company_id=current_user.company_id
    )
    
    if not category:
        raise HTTPException(
            status_code=404, 
            detail="Category not found in your company"
        )
    
    return crud.get_products_by_category_and_company(
        db=db,
        company_id=current_user.company_id,
        category_id=category_id
    )

@router.get("/categories/stats/summary")
def get_categories_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Resumen estadístico de categorías de mi empresa"""
    return crud.get_categories_stats_by_company(
        db=db,
        company_id=current_user.company_id
    )