# crud/units.py
"""
Funciones CRUD para gestión de unidades de medida (Unit)
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from typing import List, Optional
import models
import schemas
from .base import verify_company_ownership, paginate_query


def create_unit_for_company(
    db: Session,
    unit_data: schemas.UnitCreate,
    company_id: int
):
    """Crear unidad de medida para empresa específica"""

    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        unit = models.Unit(
            company_id=company_id,
            name=unit_data.name,
            abbreviation=unit_data.abbreviation.upper(),
            description=unit_data.description,
            is_active=True
        )

        db.add(unit)
        db.commit()
        db.refresh(unit)

        return unit

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating unit: {str(e)}")


def get_units_by_company(
    db: Session,
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
):
    """Obtener unidades de medida de una empresa"""
    query = db.query(models.Unit).filter(
        models.Unit.company_id == company_id
    )

    if active_only:
        query = query.filter(models.Unit.is_active == True)

    return paginate_query(
        query.order_by(models.Unit.abbreviation.asc()),
        skip=skip,
        limit=limit
    ).all()


def get_unit_by_id_and_company(
    db: Session,
    unit_id: int,
    company_id: int
):
    """Obtener unidad de medida específica de una empresa"""
    return verify_company_ownership(
        db=db,
        model_class=models.Unit,
        item_id=unit_id,
        company_id=company_id,
        error_message="Unit not found in your company"
    )


def update_unit_for_company(
    db: Session,
    unit_id: int,
    unit_data: schemas.UnitUpdate,
    company_id: int
):
    """Actualizar unidad de medida de una empresa"""
    unit = verify_company_ownership(
        db=db,
        model_class=models.Unit,
        item_id=unit_id,
        company_id=company_id,
        error_message="Unit not found in your company"
    )

    # Actualizar campos
    update_data = unit_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(unit, key):
            if key == "abbreviation" and value:
                setattr(unit, key, value.upper())
            else:
                setattr(unit, key, value)

    db.commit()
    db.refresh(unit)
    return unit


def delete_unit_for_company(
    db: Session,
    unit_id: int,
    company_id: int
):
    """Eliminar (desactivar) unidad de medida de una empresa"""
    unit = verify_company_ownership(
        db=db,
        model_class=models.Unit,
        item_id=unit_id,
        company_id=company_id,
        error_message="Unit not found in your company"
    )

    # Verificar que no esté en uso
    products_count = db.query(models.Product).filter(
        models.Product.company_id == company_id
    ).count()

    if products_count > 0:
        # TODO: Podríamos verificar más específicamente si esta unidad está en uso
        pass

    # Soft delete
    unit.is_active = False
    db.commit()

    return {"message": "Unit deactivated successfully"}
