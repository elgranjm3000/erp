from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import User
from typing import List
from auth import verify_token, check_permission

router = APIRouter()

# ================= MOVIMIENTOS DE INVENTARIO CON FILTRO POR EMPRESA =================

@router.post("/inventory/movements", response_model=schemas.InventoryMovement)
def create_inventory_movement(
    movement: schemas.InventoryMovementCreate,     
    current_user: User = Depends(check_permission(required_role="user")),

    db: Session = Depends(database.get_db)
):
    """Crear movimiento de inventario en mi empresa"""
    return crud.create_inventory_movement_for_company(
        db=db, 
        movement=movement,
        company_id=current_user.company_id
    )

@router.get("/inventory/movements", response_model=List[schemas.InventoryMovement])
def list_inventory_movements(
    skip: int = 0,
    limit: int = 100,
    movement_type: str = None,
    product_id: int = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Listar movimientos de inventario de mi empresa"""
    return crud.get_inventory_movements_by_company(
        db=db,
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        movement_type=movement_type,
        product_id=product_id
    )

@router.get("/inventory/movements/{movement_id}", response_model=schemas.InventoryMovement)
def get_inventory_movement(
    movement_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener movimiento específico de mi empresa"""
    return crud.get_inventory_movement_by_id_and_company(
        db=db,
        movement_id=movement_id,
        company_id=current_user.company_id
    )

@router.get("/inventory/movements/product/{product_id}", response_model=List[schemas.InventoryMovement])
def get_movements_by_product(
    product_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener movimientos de un producto específico de mi empresa"""
    # Verificar que el producto pertenezca a la empresa
    product = crud.get_product_by_id_and_company(
        db=db,
        product_id=product_id,
        company_id=current_user.company_id
    )
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found in your company"
        )
    
    return crud.get_inventory_movements_by_product_and_company(
        db=db,
        product_id=product_id,
        company_id=current_user.company_id
    )

@router.get("/inventory/movements/invoice/{invoice_id}", response_model=List[schemas.InventoryMovement])
def get_movements_by_invoice(
    invoice_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener movimientos de una factura específica de mi empresa"""
    # Verificar que la factura pertenezca a la empresa
    invoice = crud.view_invoice_by_company(
        db=db,
        invoice_id=invoice_id,
        company_id=current_user.company_id
    )
    
    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found in your company"
        )
    
    return crud.get_inventory_movements_by_invoice(
        db=db,
        invoice_id=invoice_id
    )

# ================= ESTADÍSTICAS Y REPORTES =================

@router.get("/inventory/movements/stats/summary")
def get_movements_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Resumen estadístico de movimientos de mi empresa"""
    return crud.get_inventory_movements_stats_by_company(
        db=db,
        company_id=current_user.company_id
    )

@router.get("/inventory/movements/stats/by-type")
def get_movements_by_type(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Estadísticas de movimientos por tipo de mi empresa"""
    return crud.get_movements_stats_by_type_and_company(
        db=db,
        company_id=current_user.company_id
    )

@router.get("/inventory/movements/recent", response_model=List[schemas.InventoryMovement])
def get_recent_movements(
    days: int = 7,
    limit: int = 50,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener movimientos recientes de mi empresa"""
    return crud.get_recent_inventory_movements_by_company(
        db=db,
        company_id=current_user.company_id,
        days=days,
        limit=limit
    )