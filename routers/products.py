from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import InventoryMovement
from typing import List
from schemas import InventoryMovement  as InventoryMovementSchema  #   # Esquema para los movimientos de inventario
from auth import verify_token  # Función para verificar el token

router = APIRouter()

@router.get("/products", response_model=list[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), token: str = Depends(verify_token)):
    return crud.get_products(db=db, skip=skip, limit=limit)

@router.post("/products", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(database.get_db)):    
    return crud.create_product(db=db, product=product)

@router.get("/products/{product_id}/inventory_movements", response_model=List[InventoryMovementSchema])
def get_inventory_movements_by_product(product_id: int, db: Session = Depends(database.get_db)):
    # Obtener los movimientos de inventario de un producto
    movements = db.query(InventoryMovement).filter(InventoryMovement.product_id == product_id).all()

    if not movements:
        raise HTTPException(status_code=404, detail="Movimientos de inventario no encontrados para este producto")

    return movements
