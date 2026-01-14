from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import Warehouse, InventoryMovement, WarehouseProduct, User
from schemas import InventoryMovement as InventoryMovementSchema
from typing import List
from auth import verify_token, check_permission

router = APIRouter()

# ================= ALMACENES CON FILTRO POR EMPRESA =================

@router.get("/warehouses", response_model=List[schemas.Warehouse])
def read_warehouses(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Listar almacenes de mi empresa"""
    return crud.get_warehouses_by_company(
        db=db, 
        company_id=current_user.company_id,
        skip=skip, 
        limit=limit
    )

@router.get("/warehouses/{warehouse_id}", response_model=schemas.Warehouse)
def read_warehouse(
    warehouse_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener almacén específico de mi empresa"""
    return crud.get_warehouse_by_id_and_company(
        db=db,
        warehouse_id=warehouse_id,
        company_id=current_user.company_id
    )

@router.post("/warehouses", response_model=schemas.Warehouse)
def create_warehouse(
    warehouse: schemas.WarehouseCreate,     
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    """Crear almacén en mi empresa"""
    return crud.create_warehouse_for_company(
        db=db, 
        warehouse=warehouse,
        company_id=current_user.company_id
    )

@router.put("/warehouses/{warehouse_id}", response_model=schemas.Warehouse)
def update_warehouse(
    warehouse_id: int,
    warehouse_data: schemas.WarehouseUpdate,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    """Actualizar almacén de mi empresa"""
    return crud.update_warehouse_for_company(
        db=db,
        warehouse_id=warehouse_id,
        warehouse_data=warehouse_data,
        company_id=current_user.company_id
    )

@router.delete("/warehouses/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """Eliminar almacén de mi empresa"""
    return crud.delete_warehouse_for_company(
        db=db,
        warehouse_id=warehouse_id,
        company_id=current_user.company_id
    )

@router.get("/warehouses/{warehouse_id}/inventory_movements", response_model=List[InventoryMovementSchema])
def get_inventory_movements_by_warehouse(
    warehouse_id: int, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener movimientos de inventario de un almacén de mi empresa"""
    
    # Verificar que el almacén pertenezca a la empresa
    warehouse = crud.get_warehouse_by_id_and_company(
        db=db,
        warehouse_id=warehouse_id,
        company_id=current_user.company_id
    )
    
    if not warehouse:
        raise HTTPException(
            status_code=404, 
            detail="Warehouse not found in your company"
        )

    # Obtener movimientos del almacén específico
    inventory_movements = (
        db.query(InventoryMovement)
        .join(WarehouseProduct, WarehouseProduct.product_id == InventoryMovement.product_id)
        .filter(WarehouseProduct.warehouse_id == warehouse_id)
        .all()
    )

    return inventory_movements

# ================= ESTADÍSTICAS Y REPORTES =================

@router.get("/warehouses/stats/summary")
def get_warehouses_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Resumen estadístico de almacenes de mi empresa"""
    return crud.get_warehouses_stats_by_company(
        db=db,
        company_id=current_user.company_id
    )

@router.get("/warehouses/{warehouse_id}/products", response_model=List[schemas.WarehouseProductWithDetails])
def get_warehouse_products(
    warehouse_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener productos de un almacén específico con información completa del producto"""
    # Verificar que el almacén pertenezca a la empresa
    warehouse = crud.get_warehouse_by_id_and_company(
        db=db,
        warehouse_id=warehouse_id,
        company_id=current_user.company_id
    )

    if not warehouse:
        raise HTTPException(
            status_code=404,
            detail="Warehouse not found in your company"
        )

    return crud.get_warehouse_products_with_details(
        db=db,
        warehouse_id=warehouse_id
    )

@router.get("/warehouses/{warehouse_id}/low-stock")
def get_warehouse_low_stock(
    warehouse_id: int,
    threshold: int = 10,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener productos con stock bajo en un almacén específico"""
    # Verificar que el almacén pertenezca a la empresa
    warehouse = crud.get_warehouse_by_id_and_company(
        db=db,
        warehouse_id=warehouse_id,
        company_id=current_user.company_id
    )
    
    if not warehouse:
        raise HTTPException(
            status_code=404, 
            detail="Warehouse not found in your company"
        )
    
    return crud.get_low_stock_products_by_warehouse(
        db=db,
        warehouse_id=warehouse_id,
        threshold=threshold
    )