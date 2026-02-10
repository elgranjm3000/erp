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


# ==================== REPORTE IGTF ====================

@router.get("/reports/igtf")
def get_igtf_report_endpoint(
    start_date: str,
    end_date: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Generar reporte de IGTF para declaraciones SENIAT.

    Incluye:
    - Total IGTF cobrado por moneda
    - Total IGTF convertido a VES
    - Lista de facturas con IGTF
    """
    try:
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Obtener moneda base VES
        base_currency = db.query(models.Currency).filter(
            models.Currency.company_id == current_user.company_id,
            models.Currency.is_base_currency == True
        ).first()

        if not base_currency:
            raise HTTPException(status_code=400, detail="Base currency not configured")

        # Obtener facturas con IGTF en el periodo
        invoices = db.query(models.Invoice).filter(
            models.Invoice.company_id == current_user.company_id,
            models.Invoice.date >= start_dt,
            models.Invoice.date <= end_dt,
            models.Invoice.status == 'factura',
            models.Invoice.igtf_amount > 0
        ).order_by(models.Invoice.date).all()

        # Agrupar por moneda
        igtf_by_currency = {}
        total_igtf_in_ves = 0.0

        for invoice in invoices:
            currency = invoice.currency.code if invoice.currency else "VES"

            if currency not in igtf_by_currency:
                igtf_by_currency[currency] = {
                    "currency_id": invoice.currency_id,
                    "currency_code": currency,
                    "total_igtf": 0.0,
                    "total_invoices": 0,
                    "invoices": []
                }

            # Calcular IGTF en VES
            igtf_ves = invoice.igtf_amount
            if invoice.currency_id != base_currency.id and invoice.exchange_rate:
                igtf_ves = invoice.igtf_amount * invoice.exchange_rate

            igtf_by_currency[currency]["total_igtf"] += igtf_ves
            igtf_by_currency[currency]["total_invoices"] += 1
            total_igtf_in_ves += igtf_ves

            igtf_by_currency[currency]["invoices"].append({
                "invoice_number": invoice.invoice_number,
                "date": invoice.date.strftime("%Y-%m-%d"),
                "customer_name": invoice.customer.name if invoice.customer else None,
                "subtotal": float(invoice.subtotal),
                "igtf_percentage": float(invoice.igtf_percentage),
                "igtf_amount": float(invoice.igtf_amount),
                "exchange_rate": float(invoice.exchange_rate) if invoice.exchange_rate else None,
                "igtf_in_ves": float(igtf_ves)
            })

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "igtf_by_currency": list(igtf_by_currency.values()),
            "total_igtf_in_ves": total_igtf_in_ves,
            "total_invoices_with_igtf": sum(c["total_invoices"] for c in igtf_by_currency.values())
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


# ================= REPORTES BIMONETARIOS (SISTEMA REF) =================

@router.get("/reports/bicurrency-sales")
def get_bicurrency_sales_report(
    start_date: str = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Reporte de ventas en USD y VES (Sistema REF).

    Retorna las ventas desglosadas en ambas monedas:
    - USD: Monto de referencia (precio estable)
    - VES: Monto convertido con tasa BCV del día

    Útil para:
    - Ver ganancias reales en USD
    - Ver inflación en VES
    - Análisis de tendencias
    """
    try:
        from sqlalchemy import func

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Obtener facturas con REF creadas en el período
        invoices = db.query(models.Invoice).filter(
            models.Invoice.company_id == current_user.company_id,
            models.Invoice.date >= start_dt,
            models.Invoice.date <= end_dt,
            models.Invoice.subtotal_reference.isnot(None),  # Solo facturas con REF
            models.Invoice.status == 'factura'
        ).all()

        # Calcular totales
        total_usd = 0.0
        total_ves = 0.0
        total_iva_ves = 0.0
        total_igtf_ves = 0.0

        invoice_details = []

        for invoice in invoices:
            usd_amount = invoice.subtotal_reference or 0
            ves_amount = invoice.subtotal_target or invoice.subtotal or 0

            total_usd += usd_amount
            total_ves += ves_amount
            total_iva_ves += invoice.iva_amount or 0
            total_igtf_ves += invoice.igtf_amount or 0

            invoice_details.append({
                "invoice_number": invoice.invoice_number,
                "date": invoice.date.strftime("%Y-%m-%d"),
                "customer": invoice.customer.name if invoice.customer else None,
                "subtotal_usd": float(usd_amount),
                "subtotal_ves": float(ves_amount),
                "exchange_rate": float(invoice.exchange_rate) if invoice.exchange_rate else None,
                "iva_ves": float(invoice.iva_amount or 0),
                "igtf_ves": float(invoice.igtf_amount or 0),
                "total_ves": float(invoice.total_amount)
            })

        # Calcular promedio de tasas
        avg_exchange_rate = None
        if invoices:
            rates = [i.exchange_rate for i in invoices if i.exchange_rate]
            if rates:
                avg_exchange_rate = sum(rates) / len(rates)

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "summary": {
                "total_invoices": len(invoices),
                "total_sales_usd": float(round(total_usd, 2)),
                "total_sales_ves": float(round(total_ves, 2)),
                "total_iva_ves": float(round(total_iva_ves, 2)),
                "total_igtf_ves": float(round(total_igtf_ves, 2)),
                "total_collected_ves": float(round(total_ves + total_iva_ves + total_igtf_ves, 2)),
                "average_exchange_rate": float(round(avg_exchange_rate, 2)) if avg_exchange_rate else None
            },
            "invoices": invoice_details
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/reports/rate-history")
def get_rate_history_report(
    start_date: str = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Historial de tasas de cambio usadas en facturas.

    Muestra todas las tasas BCV utilizadas en un período,
    con auditoría completa de qué factura usó qué tasa.
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Obtener historial de tasas
        rate_history = db.query(models.InvoiceRateHistory).filter(
            models.InvoiceRateHistory.company_id == current_user.company_id,
            models.InvoiceRateHistory.rate_date >= start_dt,
            models.InvoiceRateHistory.rate_date <= end_dt
        ).order_by(models.InvoiceRateHistory.rate_date.desc()).all()

        history_details = []
        for rate in rate_history:
            history_details.append({
                "id": rate.id,
                "invoice_id": rate.invoice_id,
                "invoice_number": rate.invoice.invoice_number if rate.invoice else None,
                "from_currency": rate.from_currency.code if rate.from_currency else None,
                "to_currency": rate.to_currency.code if rate.to_currency else None,
                "exchange_rate": float(rate.exchange_rate),
                "rate_source": rate.rate_source,
                "rate_date": rate.rate_date.strftime("%Y-%m-%d %H:%M:%S") if rate.rate_date else None,
                "recorded_at": rate.recorded_at.strftime("%Y-%m-%d %H:%M:%S") if rate.recorded_at else None
            })

        # Agrupar por tasa para ver estadísticas
        rate_stats = {}
        for rate in rate_history:
            key = rate.exchange_rate
            if key not in rate_stats:
                rate_stats[key] = {
                    "exchange_rate": float(key),
                    "count": 0,
                    "first_used": None,
                    "last_used": None
                }
            rate_stats[key]["count"] += 1
            if not rate_stats[key]["first_used"] or rate.rate_date < rate_stats[key]["first_used"]:
                rate_stats[key]["first_used"] = rate.rate_date
            if not rate_stats[key]["last_used"] or rate.rate_date > rate_stats[key]["last_used"]:
                rate_stats[key]["last_used"] = rate.rate_date

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "summary": {
                "total_records": len(rate_history),
                "unique_rates": len(rate_stats),
                "rate_statistics": sorted(rate_stats.values(), key=lambda x: x["exchange_rate"], reverse=True)
            },
            "history": history_details
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")
