from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import User
from typing import List
from auth import verify_token, check_permission

router = APIRouter()

# ================= FACTURAS CON FILTRO POR EMPRESA =================

@router.post("/invoices/", response_model=schemas.Invoice)
def create_invoice_endpoint(
    invoice_data: schemas.InvoiceCreate, 
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """Crear factura en mi empresa"""
    try:
        invoice = crud.create_invoice_for_company(
            db=db, 
            invoice_data=invoice_data, 
            company_id=current_user.company_id
        )
        return invoice
    except HTTPException as e:
        raise e

@router.get("/invoices/", response_model=List[schemas.Invoice])
def list_invoices(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Listar facturas de mi empresa"""
    return crud.get_invoices_by_company(
        db=db,
        company_id=current_user.company_id,
        skip=skip,
        limit=limit,
        status=status
    )

@router.get("/invoices/{invoice_id}", response_model=schemas.Invoice)
def view_invoice_endpoint(
    invoice_id: int, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Ver factura específica de mi empresa"""
    return crud.view_invoice_by_company(
        db=db, 
        invoice_id=invoice_id, 
        company_id=current_user.company_id
    )

@router.put("/invoices/{invoice_id}", response_model=schemas.Invoice)
def edit_invoice_endpoint(
    invoice_id: int, 
    invoice_data: schemas.InvoiceUpdate, 
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """Editar factura de mi empresa"""
    return crud.edit_invoice_for_company(
        db=db, 
        invoice_id=invoice_id, 
        invoice_data=invoice_data,
        company_id=current_user.company_id
    )

@router.delete("/invoices/{invoice_id}")
def delete_invoice_endpoint(
    invoice_id: int, 
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    """Eliminar factura de mi empresa"""
    return crud.delete_invoice_for_company(
        db=db, 
        invoice_id=invoice_id,
        company_id=current_user.company_id
    )

# ================= PRESUPUESTOS =================

"""@router.post("/budgets/", response_model=schemas.Invoice)
def create_budget_endpoint(
    budget_data: schemas.InvoiceCreate, 
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    # Forzar status a presupuesto
    budget_data.status = "presupuesto"
    return crud.create_invoice_for_company(
        db=db, 
        invoice_data=budget_data, 
        company_id=current_user.company_id
    )

@router.put("/budgets/{budget_id}/confirm", response_model=schemas.Invoice)
def confirm_budget_endpoint(
    budget_id: int, 
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    return crud.confirm_budget_for_company(
        db=db, 
        budget_id=budget_id,
        company_id=current_user.company_id
    )

# ================= MOVIMIENTOS DE CRÉDITO =================

@router.post("/invoices/{invoice_id}/credit-movements", response_model=schemas.CreditMovement)
def create_credit_movement(
    invoice_id: int,
    movement_data: schemas.CreditMovementCreate,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    return crud.create_credit_movement_for_company(
        db=db,
        invoice_id=invoice_id,
        movement_data=movement_data,
        company_id=current_user.company_id
    )

# ================= ESTADÍSTICAS Y REPORTES =================

@router.get("/invoices/stats/summary")
def get_invoices_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    return crud.get_invoices_stats_by_company(
        db=db,
        company_id=current_user.company_id
    )

@router.get("/invoices/pending", response_model=List[schemas.Invoice])
def get_pending_invoices(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    return crud.get_invoices_by_company(
        db=db,
        company_id=current_user.company_id,
        status="presupuesto"
    )"""