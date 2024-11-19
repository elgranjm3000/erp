from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import models
import schemas
from database import get_db  # Asegúrate de tener tu función `get_db` para obtener la sesión de DB
import crud

router = APIRouter()

# Endpoint para crear una compra
@router.post("/purchases", response_model=schemas.Purchase)
def create_purchase_endpoint(purchase: schemas.Purchase, db: Session = Depends(get_db)):
    try:
        # Llamar a la función create_purchase
        created_purchase = crud.create_purchase(db, purchase)        
        return created_purchase
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
