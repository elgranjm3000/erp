from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import crud
import models
import schemas
from database import get_db
from models import User
from auth import verify_token, check_permission

router = APIRouter()


# ================= LIBRO DE VENTAS (SENIAT) =================

@router.get("/reports/sales-book")
def get_sales_book_report(
    start_date: str = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    invoice_type: str = Query(None, description="Tipo: factura, nota_credito"),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Generar Libro de Ventas según formato SENIAT Venezuela

    Incluye todas las facturas con desglose de impuestos.
    Formato completo según normativa SENIAT.
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        return crud.get_sales_book(
            db=db,
            company_id=current_user.company_id,
            start_date=start_dt,
            end_date=end_dt,
            invoice_type=invoice_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


# ================= LIBRO DE COMPRAS (SENIAT) =================

@router.get("/reports/purchase-book")
def get_purchase_book_report(
    start_date: str = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    purchase_type: str = Query(None, description="Tipo: factura, nota_credito"),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Generar Libro de Compras según formato SENIAT Venezuela

    Incluye todas las compras recibidas con desglose de impuestos.
    Formato completo según normativa SENIAT.
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        return crud.get_purchase_book(
            db=db,
            company_id=current_user.company_id,
            start_date=start_dt,
            end_date=end_dt,
            purchase_type=purchase_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


# ================= RELACIÓN DE VENTAS (RESUMEN GERENCIAL) =================

@router.get("/reports/sales-summary")
def get_sales_summary_report(
    start_date: str = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    group_by: str = Query("day", description="Agrupar por: day, week, month, payment_method"),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Generar Relación de Ventas (Resumen Gerencial)

    Permite agrupar ventas por diferentes criterios.
    Útil para análisis gerencial.
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if group_by not in ['day', 'week', 'month', 'payment_method']:
            raise HTTPException(
                status_code=400,
                detail="group_by must be one of: day, week, month, payment_method"
            )

        return crud.get_sales_summary(
            db=db,
            company_id=current_user.company_id,
            start_date=start_dt,
            end_date=end_dt,
            group_by=group_by
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


# ================= FLUJO DE CAJA (POR FORMA DE PAGO) =================

@router.get("/reports/cash-flow")
def get_cash_flow_report(
    start_date: str = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Generar reporte de Flujo de Caja por forma de pago

    Muestra entradas (ventas) y salidas (compras) agrupadas por método de pago.
    Incluye balance neto por cada método de pago.
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        return crud.get_cash_flow(
            db=db,
            company_id=current_user.company_id,
            start_date=start_dt,
            end_date=end_dt
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")
