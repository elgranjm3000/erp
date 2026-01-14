# crud/reports.py
"""
Funciones CRUD para reportes fiscales SENIAT Venezuela
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import models
import schemas
from .base import verify_company_ownership, paginate_query


# ================= LIBRO DE VENTAS (SENIAT) =================

def get_sales_book(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime,
    invoice_type: Optional[str] = None  # 'factura', 'nota_credito', None
):
    """
    Generar Libro de Ventas según formato SENIAT Venezuela

    Contiene:
    - Número de factura
    - Número de control
    - Fecha
    - RIF del cliente
    - Nombre del cliente
    - Total ventas gravadas (base imponible)
    - Total ventas exentas
    - Total IVA retenido
    - Total IVA percibido
    - Ventas totales
    """

    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Construir query base
    query = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.date >= start_date,
        models.Invoice.date <= end_date,
        models.Invoice.status.in_(['factura', 'nota_credito', 'nota_debito'])
    )

    # Filtrar por tipo si se especifica
    if invoice_type:
        if invoice_type == 'factura':
            query = query.filter(models.Invoice.status == 'factura')
        elif invoice_type == 'nota_credito':
            query = query.filter(models.Invoice.status == 'nota_credito')

    # Ordenar por fecha
    invoices = query.order_by(models.Invoice.date.asc()).all()

    # Construir reporte
    report_data = []

    total_taxable_base = 0.0
    total_exempt_amount = 0.0
    total_iva_retention = 0.0
    total_iva_amount = 0.0
    total_sales = 0.0

    for invoice in invoices:
        # Obtener cliente
        customer = db.query(models.Customer).filter(
            models.Customer.id == invoice.customer_id
        ).first()

        # Calcular signo para notas de crédito (negativo)
        sign = -1 if invoice.status == 'nota_credito' else 1

        row = {
            "invoice_number": invoice.invoice_number,
            "control_number": invoice.control_number,
            "date": invoice.date.strftime("%d-%m-%Y"),
            "customer_tax_id": customer.tax_id if customer else "",
            "customer_name": customer.name if customer else "",
            "invoice_type": invoice.status,
            # Montos con signo
            "taxable_base": invoice.taxable_base * sign,
            "exempt_amount": invoice.exempt_amount * sign,
            "iva_percentage": invoice.iva_percentage,
            "iva_amount": invoice.iva_amount * sign,
            "iva_retention": invoice.iva_retention * sign,
            "iva_retention_percentage": invoice.iva_retention_percentage,
            "islr_retention": invoice.islr_retention * sign,
            "islr_retention_percentage": invoice.islr_retention_percentage,
            "stamp_tax": invoice.stamp_tax * sign,
            "subtotal": invoice.subtotal * sign,
            "total_with_taxes": invoice.total_with_taxes * sign,
            "transaction_type": invoice.transaction_type,
            "payment_method": invoice.payment_method
        }

        report_data.append(row)

        # Acumular totales
        total_taxable_base += invoice.taxable_base * sign
        total_exempt_amount += invoice.exempt_amount * sign
        total_iva_retention += invoice.iva_retention * sign
        total_iva_amount += invoice.iva_amount * sign
        total_sales += invoice.total_with_taxes * sign

    # Resumen del reporte
    summary = {
        "period_start": start_date.strftime("%d-%m-%Y"),
        "period_end": end_date.strftime("%d-%m-%Y"),
        "company": {
            "name": company.name,
            "tax_id": company.tax_id,
            "fiscal_address": company.fiscal_address
        },
        "totals": {
            "taxable_base": total_taxable_base,
            "exempt_amount": total_exempt_amount,
            "iva_retention": total_iva_retention,
            "iva_amount": total_iva_amount,
            "total_sales": total_sales
        },
        "invoices": report_data,
        "total_invoices": len(report_data)
    }

    return summary


# ================= LIBRO DE COMPRAS (SENIAT) =================

def get_purchase_book(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime,
    purchase_type: Optional[str] = None  # 'factura', 'nota_credito', None
):
    """
    Generar Libro de Compras según formato SENIAT Venezuela

    Contiene:
    - Número de factura del proveedor
    - Número de control
    - Fecha
    - RIF del proveedor
    - Nombre del proveedor
    - Total compras gravadas (base imponible)
    - Total compras exentas
    - Total IVA retenido
    - Total IVA percibido
    - Compras totales
    """

    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Construir query base - solo compras recibidas
    query = db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.date >= start_date,
        models.Purchase.date <= end_date,
        models.Purchase.status == 'received'
    )

    # Filtrar por tipo si se especifica
    if purchase_type:
        if purchase_type == 'factura':
            query = query.filter(models.Purchase.refund_reason == None)
        elif purchase_type == 'nota_credito':
            query = query.filter(models.Purchase.refund_reason != None)

    # Ordenar por fecha
    purchases = query.order_by(models.Purchase.date.asc()).all()

    # Construir reporte
    report_data = []

    total_taxable_base = 0.0
    total_exempt_amount = 0.0
    total_iva_retention = 0.0
    total_iva_amount = 0.0
    total_purchases = 0.0

    for purchase in purchases:
        # Obtener proveedor
        supplier = db.query(models.Supplier).filter(
            models.Supplier.id == purchase.supplier_id
        ).first()

        # Calcular signo para notas de crédito (negativo)
        is_credit_note = purchase.refund_reason is not None
        sign = -1 if is_credit_note else 1

        row = {
            "invoice_number": purchase.invoice_number or purchase.purchase_number,
            "control_number": purchase.control_number,
            "date": purchase.date.strftime("%d-%m-%Y"),
            "supplier_tax_id": supplier.tax_id if supplier else "",
            "supplier_name": supplier.name if supplier else "",
            "purchase_type": "nota_credito" if is_credit_note else "factura",
            # Montos con signo
            "taxable_base": purchase.taxable_base * sign if purchase.taxable_base else 0,
            "exempt_amount": purchase.exempt_amount * sign if purchase.exempt_amount else 0,
            "iva_percentage": purchase.iva_percentage,
            "iva_amount": purchase.iva_amount * sign if purchase.iva_amount else 0,
            "iva_retention": purchase.iva_retention * sign if purchase.iva_retention else 0,
            "iva_retention_percentage": purchase.iva_retention_percentage,
            "islr_retention": purchase.islr_retention * sign if purchase.islr_retention else 0,
            "islr_retention_percentage": purchase.islr_retention_percentage,
            "stamp_tax": purchase.stamp_tax * sign if purchase.stamp_tax else 0,
            "subtotal": purchase.subtotal * sign if purchase.subtotal else 0,
            "total_with_taxes": purchase.total_with_taxes * sign if purchase.total_with_taxes else 0,
            "transaction_type": purchase.transaction_type,
            "payment_method": purchase.payment_method
        }

        report_data.append(row)

        # Acumular totales
        if purchase.taxable_base:
            total_taxable_base += purchase.taxable_base * sign
        if purchase.exempt_amount:
            total_exempt_amount += purchase.exempt_amount * sign
        if purchase.iva_retention:
            total_iva_retention += purchase.iva_retention * sign
        if purchase.iva_amount:
            total_iva_amount += purchase.iva_amount * sign
        if purchase.total_with_taxes:
            total_purchases += purchase.total_with_taxes * sign

    # Resumen del reporte
    summary = {
        "period_start": start_date.strftime("%d-%m-%Y"),
        "period_end": end_date.strftime("%d-%m-%Y"),
        "company": {
            "name": company.name,
            "tax_id": company.tax_id,
            "fiscal_address": company.fiscal_address
        },
        "totals": {
            "taxable_base": total_taxable_base,
            "exempt_amount": total_exempt_amount,
            "iva_retention": total_iva_retention,
            "iva_amount": total_iva_amount,
            "total_purchases": total_purchases
        },
        "purchases": report_data,
        "total_purchases_count": len(report_data)
    }

    return summary


# ================= RELACIÓN DE VENTAS (RESUMEN GERENCIAL) =================

def get_sales_summary(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime,
    group_by: Optional[str] = "day"  # 'day', 'week', 'month', 'payment_method'
):
    """
    Generar Relación de Ventas (Resumen Gerencial)

    Agrupa ventas por período o método de pago
    """

    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Query base
    query = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.date >= start_date,
        models.Invoice.date <= end_date,
        models.Invoice.status == 'factura'
    )

    invoices = query.all()

    # Agrupar según el parámetro
    if group_by == "payment_method":
        groups = {}
        for invoice in invoices:
            key = invoice.payment_method or "sin_definir"
            if key not in groups:
                groups[key] = {
                    "payment_method": key,
                    "total_invoices": 0,
                    "total_amount": 0.0,
                    "total_iva": 0.0,
                    "total_retention": 0.0
                }

            groups[key]["total_invoices"] += 1
            groups[key]["total_amount"] += invoice.total_with_taxes
            groups[key]["total_iva"] += invoice.iva_amount
            groups[key]["total_retention"] += invoice.iva_retention + invoice.islr_retention

        report_data = list(groups.values())

    else:  # day, week, month
        # Agrupar por fecha (implementación básica por día)
        groups = {}
        for invoice in invoices:
            # Determinar clave de agrupación según group_by
            if group_by == "day":
                key = invoice.date.strftime("%Y-%m-%d")
            elif group_by == "week":
                key = invoice.date.strftime("%Y-W%U")
            else:  # month
                key = invoice.date.strftime("%Y-%m")

            if key not in groups:
                groups[key] = {
                    "period": key,
                    "total_invoices": 0,
                    "total_amount": 0.0,
                    "total_iva": 0.0,
                    "total_retention": 0.0
                }

            groups[key]["total_invoices"] += 1
            groups[key]["total_amount"] += invoice.total_with_taxes
            groups[key]["total_iva"] += invoice.iva_amount
            groups[key]["total_retention"] += invoice.iva_retention + invoice.islr_retention

        report_data = list(groups.values())
        report_data.sort(key=lambda x: x["period"])

    # Calcular totales generales
    total_invoices = sum(item["total_invoices"] for item in report_data)
    total_amount = sum(item["total_amount"] for item in report_data)
    total_iva = sum(item["total_iva"] for item in report_data)
    total_retention = sum(item["total_retention"] for item in report_data)

    return {
        "period_start": start_date.strftime("%d-%m-%Y"),
        "period_end": end_date.strftime("%d-%m-%Y"),
        "group_by": group_by,
        "company": {
            "name": company.name,
            "tax_id": company.tax_id
        },
        "data": report_data,
        "totals": {
            "total_invoices": total_invoices,
            "total_amount": total_amount,
            "total_iva": total_iva,
            "total_retention": total_retention,
            "net_total": total_amount - total_retention
        }
    }


# ================= FLUJO DE CAJA (POR FORMA DE PAGO) =================

def get_cash_flow(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime
):
    """
    Generar reporte de Flujo de Caja por forma de pago

    Muestra entradas y salidas agrupadas por método de pago
    """

    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Obtener facturas de ventas (entradas)
    sales_query = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.date >= start_date,
        models.Invoice.date <= end_date,
        models.Invoice.status == 'factura'
    )

    sales = sales_query.all()

    # Obtener compras (salidas)
    purchases_query = db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id,
        models.Purchase.date >= start_date,
        models.Purchase.date <= end_date,
        models.Purchase.status == 'received'
    )

    purchases = purchases_query.all()

    # Agrupar por método de pago
    cash_flow = {}

    # Procesar ventas (entradas)
    for sale in sales:
        key = sale.payment_method or "sin_definir"
        if key not in cash_flow:
            cash_flow[key] = {
                "payment_method": key,
                "total_in": 0.0,
                "total_out": 0.0,
                "balance": 0.0,
                "transactions": 0
            }

        cash_flow[key]["total_in"] += sale.total_with_taxes
        cash_flow[key]["transactions"] += 1

    # Procesar compras (salidas)
    for purchase in purchases:
        key = purchase.payment_method or "sin_definir"
        if key not in cash_flow:
            cash_flow[key] = {
                "payment_method": key,
                "total_in": 0.0,
                "total_out": 0.0,
                "balance": 0.0,
                "transactions": 0
            }

        cash_flow[key]["total_out"] += purchase.total_with_taxes if purchase.total_with_taxes else 0
        cash_flow[key]["transactions"] += 1

    # Calcular balances
    total_balance = 0.0
    for key in cash_flow:
        cash_flow[key]["balance"] = cash_flow[key]["total_in"] - cash_flow[key]["total_out"]
        total_balance += cash_flow[key]["balance"]

    # Convertir a lista
    report_data = list(cash_flow.values())
    report_data.sort(key=lambda x: x["balance"], reverse=True)

    # Calcular totales generales
    total_in = sum(item["total_in"] for item in report_data)
    total_out = sum(item["total_out"] for item in report_data)

    return {
        "period_start": start_date.strftime("%d-%m-%Y"),
        "period_end": end_date.strftime("%d-%m-%Y"),
        "company": {
            "name": company.name,
            "tax_id": company.tax_id
        },
        "cash_flow": report_data,
        "totals": {
            "total_in": total_in,
            "total_out": total_out,
            "net_balance": total_balance
        }
    }
