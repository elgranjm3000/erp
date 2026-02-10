"""
✅ SISTEMA ESCRITORIO: Router para Gestión de Impuestos e Historial de Monedas

Sistema de impuestos venezolano con dos niveles:
1. TaxType: Categorías de impuesto (General, Reducida, Exento, etc.)
2. Tax: Códigos de impuesto específicos (01=16%, 02=31%, 03=8%, EX=0%, 06=Percibido)

Historial de monedas (CoinHistory):
- Registro histórico de tasas de cambio (desktop ERP)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, time, datetime
import models
import schemas
import database
from models import User, TaxType, Tax, CoinHistory
from auth import verify_token, check_permission

router = APIRouter()


# ==================== ✅ TAX TYPES (Categorías) ====================

@router.get("/tax-types", response_model=List[schemas.TaxType])
def read_tax_types(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """
    Listar todos los tipos de impuesto de mi empresa.

    Tax Types (Categorías):
    - 1: General (IVA 16%)
    - 2: Reducida (IVA 8%)
    - 3: General + Adicional (IVA 31%)
    - 4: Exento
    - 5: Alicuota General + Adicional Decreto 3085
    - 6: Alicuota Reducida Decreto 3085
    - 7: Percibido
    """
    tax_types = db.query(TaxType).filter(
        TaxType.company_id == current_user.company_id
    ).order_by(TaxType.code).offset(skip).limit(limit).all()

    return tax_types


@router.get("/tax-types/{tax_type_id}", response_model=schemas.TaxType)
def read_tax_type(
    tax_type_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener un tipo de impuesto por ID"""
    tax_type = db.query(TaxType).filter(
        TaxType.id == tax_type_id,
        TaxType.company_id == current_user.company_id
    ).first()

    if not tax_type:
        raise HTTPException(status_code=404, detail="Tax type not found")

    return tax_type


@router.post("/tax-types", response_model=schemas.TaxType)
def create_tax_type(
    tax_type_data: schemas.TaxTypeCreate,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """
    Crear un nuevo tipo de impuesto (categoría).

    Ejemplo:
    {
        "code": 1,
        "description": "General",
        "fiscal_printer_position": 1
    }
    """
    # Verificar que el código no existe en la empresa
    existing = db.query(TaxType).filter(
        TaxType.company_id == current_user.company_id,
        TaxType.code == tax_type_data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tax type with code {tax_type_data.code} already exists"
        )

    db_tax_type = TaxType(
        company_id=current_user.company_id,
        **tax_type_data.dict()
    )

    db.add(db_tax_type)
    db.commit()
    db.refresh(db_tax_type)

    return db_tax_type


@router.put("/tax-types/{tax_type_id}", response_model=schemas.TaxType)
def update_tax_type(
    tax_type_id: int,
    tax_type_data: schemas.TaxTypeUpdate,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """Actualizar un tipo de impuesto"""
    db_tax_type = db.query(TaxType).filter(
        TaxType.id == tax_type_id,
        TaxType.company_id == current_user.company_id
    ).first()

    if not db_tax_type:
        raise HTTPException(status_code=404, detail="Tax type not found")

    update_data = tax_type_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tax_type, field, value)

    db.commit()
    db.refresh(db_tax_type)

    return db_tax_type


@router.delete("/tax-types/{tax_type_id}")
def delete_tax_type(
    tax_type_id: int,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """
    Eliminar un tipo de impuesto (solo admin).

    Precaución: No eliminar si hay impuestos (Tax) asociados.
    """
    db_tax_type = db.query(TaxType).filter(
        TaxType.id == tax_type_id,
        TaxType.company_id == current_user.company_id
    ).first()

    if not db_tax_type:
        raise HTTPException(status_code=404, detail="Tax type not found")

    # Verificar que no hay impuestos asociados
    associated_taxes = db.query(Tax).filter(
        Tax.tax_type_id == tax_type_id,
        Tax.company_id == current_user.company_id
    ).count()

    if associated_taxes > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete tax type with {associated_taxes} associated taxes"
        )

    db.delete(db_tax_type)
    db.commit()

    return {"message": "Tax type deleted successfully"}


# ==================== ✅ TAXES (Códigos específicos) ====================

@router.get("/taxes", response_model=List[schemas.Tax])
def read_taxes(
    skip: int = 0,
    limit: int = 100,
    tax_type_id: int = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """
    Listar todos los códigos de impuesto de mi empresa.

    Códigos de impuesto venezolanos:
    - 01: Alicuota General (16%)
    - 02: Alicuota General + Adicional (31%)
    - 03: Alicuota Reducida (8%)
    - EX: Exento (0%)
    - 06: Percibido (0%)
    """
    query = db.query(Tax).filter(
        Tax.company_id == current_user.company_id
    )

    if tax_type_id:
        query = query.filter(Tax.tax_type_id == tax_type_id)

    return query.order_by(Tax.code).offset(skip).limit(limit).all()


@router.get("/taxes/{tax_id}", response_model=schemas.Tax)
def read_tax(
    tax_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener un código de impuesto por ID"""
    tax = db.query(Tax).filter(
        Tax.id == tax_id,
        Tax.company_id == current_user.company_id
    ).first()

    if not tax:
        raise HTTPException(status_code=404, detail="Tax not found")

    return tax


@router.post("/taxes", response_model=schemas.Tax)
def create_tax(
    tax_data: schemas.TaxCreate,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """
    Crear un nuevo código de impuesto.

    Ejemplo para IVA General 16%:
    {
        "code": "01",
        "description": "Alicuota General",
        "short_description": "16%",
        "aliquot": 16,
        "tax_type_id": 1,
        "status": true
    }

    Ejemplo para Exento:
    {
        "code": "EX",
        "description": "Exento",
        "short_description": "Exento",
        "aliquot": 0,
        "tax_type_id": 4,
        "status": true
    }
    """
    # Verificar que el código no existe en la empresa
    existing = db.query(Tax).filter(
        Tax.company_id == current_user.company_id,
        Tax.code == tax_data.code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tax with code {tax_data.code} already exists"
        )

    # Verificar que el tax_type_id existe y pertenece a la empresa
    tax_type = db.query(TaxType).filter(
        TaxType.id == tax_data.tax_type_id,
        TaxType.company_id == current_user.company_id
    ).first()

    if not tax_type:
        raise HTTPException(
            status_code=400,
            detail="Tax type not found in your company"
        )

    db_tax = Tax(
        company_id=current_user.company_id,
        **tax_data.dict()
    )

    db.add(db_tax)
    db.commit()
    db.refresh(db_tax)

    return db_tax


@router.put("/taxes/{tax_id}", response_model=schemas.Tax)
def update_tax(
    tax_id: int,
    tax_data: schemas.TaxUpdate,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """Actualizar un código de impuesto"""
    db_tax = db.query(Tax).filter(
        Tax.id == tax_id,
        Tax.company_id == current_user.company_id
    ).first()

    if not db_tax:
        raise HTTPException(status_code=404, detail="Tax not found")

    # Si se está actualizando tax_type_id, verificar que existe
    if tax_data.tax_type_id is not None:
        tax_type = db.query(TaxType).filter(
            TaxType.id == tax_data.tax_type_id,
            TaxType.company_id == current_user.company_id
        ).first()

        if not tax_type:
            raise HTTPException(
                status_code=400,
                detail="Tax type not found in your company"
            )

    update_data = tax_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tax, field, value)

    db.commit()
    db.refresh(db_tax)

    return db_tax


@router.delete("/taxes/{tax_id}")
def delete_tax(
    tax_id: int,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """
    Eliminar un código de impuesto (solo admin).

    Precaución: Verificar que no esté siendo usado en productos o facturas.
    """
    db_tax = db.query(Tax).filter(
        Tax.id == tax_id,
        Tax.company_id == current_user.company_id
    ).first()

    if not db_tax:
        raise HTTPException(status_code=404, detail="Tax not found")

    db.delete(db_tax)
    db.commit()

    return {"message": "Tax deleted successfully"}


# ==================== ✅ COIN HISTORY (Historial de Monedas) ====================

@router.get("/coin-history", response_model=List[schemas.CoinHistory])
def read_coin_history(
    currency_id: int = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """
    Listar historial de tasas de cambio de monedas de mi empresa.

    Puede filtrar por moneda específica con currency_id.
    """
    query = db.query(CoinHistory).filter(
        CoinHistory.company_id == current_user.company_id
    )

    if currency_id:
        query = query.filter(CoinHistory.currency_id == currency_id)

    return query.order_by(
        CoinHistory.register_date.desc(),
        CoinHistory.register_hour.desc()
    ).offset(skip).limit(limit).all()


@router.get("/coin-history/{history_id}", response_model=schemas.CoinHistory)
def read_coin_history_entry(
    history_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener un registro de historial por ID"""
    history = db.query(CoinHistory).filter(
        CoinHistory.id == history_id,
        CoinHistory.company_id == current_user.company_id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="Coin history entry not found")

    return history


@router.post("/coin-history", response_model=schemas.CoinHistory)
def create_coin_history(
    history_data: schemas.CoinHistoryCreate,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """
    Crear nuevo registro de historial de tasas de cambio.

    Ejemplo:
    {
        "currency_id": 1,
        "sales_aliquot": 165.41,
        "buy_aliquot": 165.41,
        "register_date": "2026-01-18",
        "register_hour": "10:30:00",
        "user_id": 1
    }
    """
    # Verificar que la moneda existe y pertenece a la empresa
    from models.currency_config import Currency
    currency = db.query(Currency).filter(
        Currency.id == history_data.currency_id,
        Currency.company_id == current_user.company_id
    ).first()

    if not currency:
        raise HTTPException(status_code=400, detail="Currency not found in your company")

    # Crear registro de historial
    db_history = CoinHistory(
        company_id=current_user.company_id,
        user_id=current_user.id,  # Usuario que está registrando
        **history_data.dict()
    )

    db.add(db_history)
    db.commit()
    db.refresh(db_history)

    return db_history


@router.post("/coin-history/batch", response_model=List[schemas.CoinHistory])
def create_coin_history_batch(
    history_data: List[schemas.CoinHistoryCreate],
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """
    Crear múltiples registros de historial en una sola petición.

    Útil para importar historial desde el sistema desktop.
    """
    from models.currency_config import Currency

    # Verificar que todas las monedas existen
    currency_ids = [h.currency_id for h in history_data]
    currencies = db.query(Currency).filter(
        Currency.id.in_(currency_ids),
        Currency.company_id == current_user.company_id
    ).all()

    if len(currencies) != len(set(currency_ids)):
        raise HTTPException(status_code=400, detail="One or more currencies not found")

    # Crear registros
    db_histories = []
    for h_data in history_data:
        db_history = CoinHistory(
            company_id=current_user.company_id,
            user_id=current_user.id,
            **h_data.dict()
        )
        db.add(db_history)
        db_histories.append(db_history)

    db.commit()

    for h in db_histories:
        db.refresh(h)

    return db_histories


@router.get("/coin-history/currency/{currency_id}/latest")
def get_latest_coin_history(
    currency_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """
    Obtener el registro más reciente de una moneda.

    Útil para mostrar la última tasa registrada.
    """
    history = db.query(CoinHistory).filter(
        CoinHistory.company_id == current_user.company_id,
        CoinHistory.currency_id == currency_id
    ).order_by(
        CoinHistory.register_date.desc(),
        CoinHistory.register_hour.desc()
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="No history found for this currency")

    return history

