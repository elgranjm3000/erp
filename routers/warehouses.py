from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import Warehouse,InventoryMovement,WarehouseProduct

from schemas import InventoryMovement  as InventoryMovementSchema  #   # Esquema para los movimientos de inventario
from typing import List



router = APIRouter()

@router.get("/warehouses", response_model=list[schemas.Warehouse])
def read_warehouses(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_warehouses(db=db, skip=skip, limit=limit)

@router.post("/warehouses", response_model=schemas.Warehouse)
def create_warehouse(warehouse: schemas.WarehouseCreate, db: Session = Depends(database.get_db)):
    return crud.create_warehouse(db=db, warehouse=warehouse)

@router.get("/warehouses/{warehouse_id}/inventory_movements", response_model=List[InventoryMovementSchema])
def get_inventory_movements_by_warehouse(warehouse_id: int, db: Session = Depends(database.get_db)):
    # Verifica que el almacén existe
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    # Une las tablas `InventoryMovement` y `WarehouseProduct` para obtener los movimientos del almacén específico
    inventory_movements = (
        db.query(InventoryMovement)
        .join(WarehouseProduct, WarehouseProduct.product_id == InventoryMovement.product_id)
        .filter(WarehouseProduct.warehouse_id == warehouse_id)
        .all()
    )

    return inventory_movements


