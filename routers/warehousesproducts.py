from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import Warehouse,InventoryMovement,WarehouseProduct

from schemas import InventoryMovement  as InventoryMovementSchema  #   # Esquema para los movimientos de inventario
from typing import List



router = APIRouter()


# Crear o actualizar warehouse-product
@router.post("/warehouse-products/", response_model=schemas.WarehouseProduct)
def create_or_update_wp(wp: schemas.WarehouseProductCreate, db: Session = Depends(database.get_db)):
    return crud.create_or_update_warehouse_product(db, wp)

# Leer todos los registros
@router.get("/warehouse-products/", response_model=list[schemas.WarehouseProduct])
def read_all_wp(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_warehouse_products(db, skip, limit)

# Leer un registro específico
@router.get("/warehouse-products/{warehouse_id}/{product_id}", response_model=schemas.WarehouseProduct)
def read_wp(warehouse_id: int, product_id: int, db: Session = Depends(database.get_db)):
    wp = crud.get_warehouse_product(db, warehouse_id, product_id)
    if not wp:
        raise HTTPException(status_code=404, detail="WarehouseProduct not found")
    return wp

# Actualizar el stock de un registro
@router.put("/warehouse-products/{warehouse_id}/{product_id}", response_model=schemas.WarehouseProduct)
def update_wp_stock(warehouse_id: int, product_id: int, stock: int, db: Session = Depends(database.get_db)):
    wp = crud.update_warehouse_product_stock(db, warehouse_id, product_id, stock)
    if not wp:
        raise HTTPException(status_code=404, detail="WarehouseProduct not found")
    return wp

# Eliminar un registro
@router.delete("/warehouse-products/{warehouse_id}/{product_id}", response_model=schemas.WarehouseProduct)
def delete_wp(warehouse_id: int, product_id: int, db: Session = Depends(database.get_db)):
    wp = crud.delete_warehouse_product(db, warehouse_id, product_id)
    if not wp:
        raise HTTPException(status_code=404, detail="WarehouseProduct not found")
    return wp