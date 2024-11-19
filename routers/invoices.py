from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import Warehouse,InventoryMovement,WarehouseProduct

from schemas import InventoryMovement  as InventoryMovementSchema  #   # Esquema para los movimientos de inventario
from typing import List



router = APIRouter()

@router.post("/invoices/", response_model=schemas.Invoice)
def create_invoice_endpoint(invoice_data: schemas.Invoice, db: Session = Depends(database.get_db)):
    try:
        # Llamada a la función del CRUD para crear la factura
        invoice = crud.create_invoice(db, invoice_data)
        return invoice
    except HTTPException as e:
        raise e  # Lanza el error si ocurre alguna excepción (como "Producto no encontrado", "Stock insuficiente", etc.)

@router.get("/invoices/{invoice_id}", response_model=schemas.Invoice)
def view_invoice_endpoint(invoice_id: int, db: Session = Depends(database.get_db)):
    return crud.view_invoice(db, invoice_id)

@router.put("/invoice/{invoice_id}", response_model=schemas.Invoice)
def edit_invoice_endpoint(invoice_id: int, invoice_data: schemas.Invoice, db: Session = Depends(database.get_db)):
    return crud.edit_invoice(db, invoice_id, invoice_data)


@router.delete("/invoices/{invoice_id}", response_model=dict)
def delete_invoice_endpoint(invoice_id: int, db: Session = Depends(database.get_db)):
    return crud.delete_invoice(db, invoice_id)

"""04c528cbf12f622c5f1fc046b3d15cee"""

"""https://api.currencylayer.com/convert?access_key=04c528cbf12f622c5f1fc046b3d15cee&from=USD&to=VES&amount=30"""

"""@router.post("/budgets/", response_model=schemas.Invoice)
def create_budget_endpoint(budget_data: schemas.InvoiceCreate, db: Session = Depends(database.get_db)):
    return crud.create_budget(db=db, budget_data=budget_data)

@router.put("/budgets/{budget_id}/confirm", response_model=schemas.Invoice)
def confirm_budget_endpoint(budget_id: int, db: Session = Depends(database.get_db)):
    return crud.confirm_budget(db=db, budget_id=budget_id)"""