from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import crud
import models
import schemas
from database import get_db
from models import User
from auth import verify_token, check_permission

router = APIRouter()


@router.post("/units", response_model=schemas.Unit)
def create_unit(
    unit: schemas.UnitCreate,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(get_db)
):
    """Crear unidad de medida para mi empresa"""
    return crud.create_unit_for_company(
        db=db,
        unit_data=unit,
        company_id=current_user.company_id
    )


@router.get("/units", response_model=List[schemas.Unit])
def list_units(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Listar unidades de medida de mi empresa"""
    return crud.get_units_by_company(
        db=db,
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        active_only=active_only
    )


@router.get("/units/{unit_id}", response_model=schemas.Unit)
def get_unit(
    unit_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obtener unidad de medida específica de mi empresa"""
    return crud.get_unit_by_id_and_company(
        db=db,
        unit_id=unit_id,
        company_id=current_user.company_id
    )


@router.put("/units/{unit_id}", response_model=schemas.Unit)
def update_unit(
    unit_id: int,
    unit_data: schemas.UnitUpdate,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(get_db)
):
    """Actualizar unidad de medida de mi empresa"""
    return crud.update_unit_for_company(
        db=db,
        unit_id=unit_id,
        unit_data=unit_data,
        company_id=current_user.company_id
    )


@router.delete("/units/{unit_id}")
def delete_unit(
    unit_id: int,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(get_db)
):
    """Eliminar (desactivar) unidad de medida de mi empresa"""
    return crud.delete_unit_for_company(
        db=db,
        unit_id=unit_id,
        company_id=current_user.company_id
    )
