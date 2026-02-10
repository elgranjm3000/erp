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

@router.post("/budgets/", response_model=schemas.Invoice)
def create_budget_endpoint(
    budget_data: schemas.InvoiceCreate, 
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """Crear presupuesto en mi empresa"""
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
    """Confirmar presupuesto como factura"""
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
    """Crear movimiento de crédito (nota de crédito/devolución)"""
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
    """Resumen estadístico de facturas de mi empresa"""
    return crud.get_invoices_stats_by_company(
        db=db,
        company_id=current_user.company_id
    )

@router.get("/invoices/pending", response_model=List[schemas.Invoice])
def get_pending_invoices(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener facturas pendientes de mi empresa"""
    return crud.get_invoices_by_company(
        db=db,
        company_id=current_user.company_id,
        status="presupuesto"
    )

# ================= MULTI-MONEDA: PREVIEW DE FACTURAS =================

from pydantic import BaseModel
from typing import Optional, List

class InvoicePreviewItem(BaseModel):
    product_id: int
    quantity: int

class InvoicePreviewRequest(BaseModel):
    items: List[InvoicePreviewItem]
    customer_id: int
    payment_method: str
    manual_exchange_rate: Optional[float] = None
    igtf_exempt: bool = False
    iva_percentage: float = 16.0
    reference_currency_code: str = "USD"
    payment_currency_code: str = "VES"

@router.post("/invoices/preview")
def preview_invoice_with_conversion(
    request: InvoicePreviewRequest,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """
    Preview de factura con conversión automática USD→VES.

    Calcula todos los totales de una factura con la tasa de cambio del día.
    Útil para mostrar al cliente el preview antes de crear la factura.

    Args:
        request: InvoicePreviewRequest con todos los parámetros

    Returns:
        Dict con el cálculo completo de la factura:
        - items: Lista de items con precios en ambas monedas
        - exchange_rate: Tasa utilizada
        - totals: Subtotal, IVA, IGTF, Total final
    """
    from services.invoice_calculation_service import InvoiceCalculationService

    try:
        service = InvoiceCalculationService(db, current_user.company_id)

        # Convertir items a dict
        items_dict = [item.dict() for item in request.items]

        preview = service.calculate_invoice_preview(
            items=items_dict,
            customer_id=request.customer_id,
            payment_method=request.payment_method,
            manual_exchange_rate=request.manual_exchange_rate,
            igtf_exempt=request.igtf_exempt,
            iva_percentage=request.iva_percentage,
            reference_currency_code=request.reference_currency_code,
            payment_currency_code=request.payment_currency_code
        )

        return preview

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating invoice preview: {str(e)}")