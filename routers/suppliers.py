from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import User
from typing import List
from auth import verify_token, check_permission

router = APIRouter()

# ================= PROVEEDORES CON FILTRO POR EMPRESA =================

@router.get("/suppliers", response_model=List[schemas.Supplier])
def read_suppliers(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Listar proveedores de mi empresa"""
    return crud.get_suppliers_by_company(
        db=db, 
        company_id=current_user.company_id,
        skip=skip, 
        limit=limit
    )

@router.get("/suppliers/{supplier_id}", response_model=schemas.Supplier)
def read_supplier(
    supplier_id: int, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener proveedor específico de mi empresa"""
    return crud.get_supplier_by_id_and_company(
        db=db, 
        supplier_id=supplier_id, 
        company_id=current_user.company_id
    )

@router.post("/suppliers", response_model=schemas.Supplier)
def create_supplier(
    supplier_data: schemas.SupplierCreate, 
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """Crear proveedor en mi empresa"""
    return crud.create_supplier_for_company(
        db=db, 
        supplier_data=supplier_data, 
        company_id=current_user.company_id
    )

@router.put("/suppliers/{supplier_id}", response_model=schemas.Supplier)
def update_supplier(
    supplier_id: int, 
    supplier_data: schemas.SupplierUpdate, 
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """Actualizar proveedor de mi empresa"""
    return crud.update_supplier_for_company(
        db=db, 
        supplier_id=supplier_id, 
        supplier_data=supplier_data,
        company_id=current_user.company_id
    )

@router.delete("/suppliers/{supplier_id}")
def delete_supplier(
    supplier_id: int, 
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    """Eliminar proveedor de mi empresa"""
    return crud.delete_supplier_for_company(
        db=db, 
        supplier_id=supplier_id,
        company_id=current_user.company_id
    )

# ================= ENDPOINTS ESPECÍFICOS =================

@router.get("/suppliers/{supplier_id}/purchases", response_model=List[schemas.Purchase])
def get_supplier_purchases(
    supplier_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener compras de un proveedor específico"""
    # Verificar que el proveedor pertenezca a la empresa
    supplier = crud.get_supplier_by_id_and_company(
        db=db, 
        supplier_id=supplier_id, 
        company_id=current_user.company_id
    )
    
    if not supplier:
        raise HTTPException(
            status_code=404, 
            detail="Supplier not found in your company"
        )
    
    return crud.get_purchases_by_supplier_and_company(
        db=db,
        supplier_id=supplier_id,
        company_id=current_user.company_id
    )

@router.get("/suppliers/search", response_model=List[schemas.Supplier])
def search_suppliers(
    q: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Buscar proveedores por nombre en mi empresa"""
    return crud.search_suppliers_by_company(
        db=db,
        company_id=current_user.company_id,
        search_term=q
    )

@router.get("/suppliers/stats/summary")
def get_suppliers_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Resumen estadístico de proveedores de mi empresa"""
    return crud.get_suppliers_stats_by_company(
        db=db,
        company_id=current_user.company_id
    )

@router.get("/suppliers/top-by-purchases")
def get_top_suppliers(
    limit: int = 10,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener top proveedores por volumen de compras"""
    return crud.get_top_suppliers_by_purchases(
        db=db,
        company_id=current_user.company_id,
        limit=limit
    )