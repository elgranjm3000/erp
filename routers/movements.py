from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import crud
import schemas
import database

router = APIRouter()

@router.post("/inventory/movements", response_model=schemas.InventoryMovement)
def create_inventory_movement(movement: schemas.InventoryMovementCreate, db: Session = Depends(database.get_db)):
    return crud.create_inventory_movement(db=db, movement=movement)
