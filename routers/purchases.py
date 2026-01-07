from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import models
import schemas
from database import get_db
import crud
from models import User
from typing import List
from auth import verify_token, check_permission

router = APIRouter()

# ================= COMPRAS CON FILTRO POR EMPRESA =================

@router.post("/purchases", response_model=schemas.PurchaseResponse)
def create_purchase_endpoint(
    purchase: schemas.PurchaseCreate,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(get_db)
):
    """Crear compra en mi empresa"""
    try:
        created_purchase = crud.create_purchase_for_company(
            db=db,
            purchase_data=purchase,
            company_id=current_user.company_id
        )

        return created_purchase
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/purchases", response_model=List[schemas.PurchaseResponse])
def list_purchases(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Listar compras de mi empresa"""
    return crud.get_purchases_by_company(
        db=db,
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        status=status
    )

@router.get("/purchases/{purchase_id}", response_model=schemas.PurchaseResponse)
def get_purchase(
    purchase_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obtener compra específica de mi empresa"""
    return crud.get_purchase_by_id_and_company(
        db=db,
        purchase_id=purchase_id,
        company_id=current_user.company_id
    )

@router.put("/purchases/{purchase_id}", response_model=schemas.PurchaseResponse)
def update_purchase(
    purchase_id: int,
    purchase_data: schemas.PurchaseUpdate,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(get_db)
):
    """Actualizar compra de mi empresa"""
    return crud.update_purchase_for_company(
        db=db,
        purchase_id=purchase_id,
        purchase_data=purchase_data,
        company_id=current_user.company_id
    )

@router.delete("/purchases/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(get_db)
):
    """Eliminar compra de mi empresa"""
    return crud.delete_purchase_for_company(
        db=db,
        purchase_id=purchase_id,
        company_id=current_user.company_id
    )

@router.put("/purchases/{purchase_id}/status")
def update_purchase_status(
    purchase_id: int,
    status: str,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(get_db)
):
    """Actualizar estado de la compra"""
    return crud.update_purchase_status_for_company(
        db=db,
        purchase_id=purchase_id,
        status=status,
        company_id=current_user.company_id
    )

# ================= ESTADÍSTICAS Y REPORTES =================

@router.get("/purchases/stats/summary")
def get_purchases_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Resumen estadístico de compras de mi empresa"""
    return crud.get_purchases_stats_by_company(
        db=db,
        company_id=current_user.company_id
    )

@router.get("/purchases/pending", response_model=List[schemas.PurchaseResponse])
def get_pending_purchases(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obtener compras pendientes de mi empresa"""
    return crud.get_purchases_by_company(
        db=db,
        company_id=current_user.company_id,
        status="pending"
    )