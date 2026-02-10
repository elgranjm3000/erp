"""
✅ SISTEMA ESCRITORIO: Router para Operaciones de Venta

Sistema unificado de documentos de venta que soporta:
- Presupuestos (BUDGET)
- Pedidos (ORDER)
- Órdenes de Entrega (DELIVERYNOTE)
- Facturas (BILL)
- Notas de Crédito (CREDITNOTE)
- Notas de Débito (DEBITNOTE)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
import database
from models import User, SalesOperation, SalesOperationCoin, SalesOperationDetail, SalesOperationDetailCoin, SalesOperationTax, SalesOperationTaxCoin
from auth import verify_token, check_permission
from datetime import datetime

router = APIRouter()


# ==================== ✅ OPERACIONES DE VENTA - CRUD BÁSICO ====================

@router.get("/sales-operations", response_model=List[schemas.SalesOperation])
def read_sales_operations(
    skip: int = 0,
    limit: int = 100,
    operation_type: Optional[str] = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """
    Listar operaciones de venta de mi empresa.

    Puede filtrar por tipo de operación:
    - BUDGET: Presupuesto
    - ORDER: Pedido
    - DELIVERYNOTE: Orden de Entrega
    - BILL: Factura
    - CREDITNOTE: Nota de Crédito
    - DEBITNOTE: Nota de Débito
    """
    query = db.query(SalesOperation).filter(
        SalesOperation.company_id == current_user.company_id
    )

    if operation_type:
        query = query.filter(SalesOperation.operation_type == operation_type.upper())

    return query.order_by(SalesOperation.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/sales-operations/{operation_id}", response_model=schemas.SalesOperationWithDetails)
def read_sales_operation(
    operation_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener operación de venta con todos sus detalles"""
    operation = db.query(SalesOperation).filter(
        SalesOperation.id == operation_id,
        SalesOperation.company_id == current_user.company_id
    ).first()

    if not operation:
        raise HTTPException(status_code=404, detail="Sales operation not found")

    return operation


@router.post("/sales-operations", response_model=schemas.SalesOperation)
def create_sales_operation(
    operation_data: schemas.SalesOperationCreate,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """
    Crear nueva operación de venta con soporte multi-moneda completo.

    Campos requeridos:
    - operation_type: Tipo de documento (BUDGET, ORDER, DELIVERYNOTE, BILL, CREDITNOTE, DEBITNOTE)
    - client_id: ID del cliente
    - emission_date: Fecha de emisión
    - register_date: Fecha de registro
    - details: Lista opcional de items/productos
    """
    # ✅ Verificar que el cliente existe y pertenece a la empresa
    from models import Customer, Currency
    customer = db.query(Customer).filter(
        Customer.id == operation_data.client_id,
        Customer.company_id == current_user.company_id
    ).first()

    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found in your company")

    # ✅ Crear operación de venta
    db_operation = SalesOperation(
        company_id=current_user.company_id,
        **operation_data.dict(exclude={'details'})
    )

    # ✅ Duplicar información del cliente para historial
    db_operation.client_name = customer.name
    db_operation.client_tax_id = customer.tax_id
    db_operation.client_address = customer.address
    db_operation.client_phone = customer.phone
    db_operation.client_name_fiscal = customer.name_fiscal

    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)

    # ✅ SISTEMA ESCRITORIO: Obtener todas las monedas de la empresa
    currencies = db.query(Currency).filter(
        Currency.company_id == current_user.company_id,
        Currency.is_active == True
    ).all()

    # ✅ SISTEMA ESCRITORIO: Procesar detalles (items) si se proporcionan
    details_data = operation_data.details or []

    # Diccionario para agrupar impuestos por tipo
    taxes_by_code = {}  # {tax_code: {taxable, tax, aliquot}}

    for detail_data in details_data:
        # Crear el detalle del item
        db_detail = SalesOperationDetail(
            company_id=current_user.company_id,
            sales_operation_id=db_operation.id,
            main_correlative=db_operation.correlative,
            **detail_data.dict()
        )
        db.add(db_detail)
        db.flush()  # Para obtener el ID si es necesario

        # ✅ Acumular impuestos para agrupar después
        tax_code = detail_data.sale_tax
        if tax_code not in taxes_by_code:
            taxes_by_code[tax_code] = {
                'taxable': 0,
                'tax': 0,
                'aliquot': detail_data.sale_aliquot
            }
        taxes_by_code[tax_code]['taxable'] += detail_data.total_net
        taxes_by_code[tax_code]['tax'] += detail_data.total_tax

        # ✅ Crear multi-moneda para este item (sales_operation_detail_coins)
        for currency in currencies:
            if currency.code == operation_data.coin_code:
                rate = 1.0
            else:
                rate = float(currency.exchange_rate) if currency.exchange_rate else 1.0

            detail_coin = SalesOperationDetailCoin(
                company_id=current_user.company_id,
                main_correlative=db_operation.correlative,
                main_line=detail_data.line,
                coin_code=currency.code,
                unitary_cost=detail_data.unitary_cost * rate if detail_data.unitary_cost else 0,
                total_net_cost=detail_data.total_net * rate if detail_data.total_net else 0,
                total_tax_cost=detail_data.total_tax * rate if detail_data.total_tax else 0,
                total_cost=detail_data.total * rate if detail_data.total else 0,
                total_net_gross=detail_data.total_net * rate if detail_data.total_net else 0,
                total_tax_gross=detail_data.total_tax * rate if detail_data.total_tax else 0,
                total_gross=detail_data.total * rate if detail_data.total else 0,
                discount=0,
                total_net=detail_data.total_net * rate if detail_data.total_net else 0,
                total_tax=detail_data.total_tax * rate if detail_data.total_tax else 0,
                total=detail_data.total * rate if detail_data.total else 0,
            )
            db.add(detail_coin)

    # ✅ SISTEMA ESCRITORIO: Crear impuestos agrupados (sales_operation_taxes)
    tax_line = 1
    for tax_code, tax_info in taxes_by_code.items():
        db_tax = SalesOperationTax(
            company_id=current_user.company_id,
            sales_operation_id=db_operation.id,
            main_correlative=db_operation.correlative,
            line=tax_line,
            taxe_code=tax_code,
            aliquot=tax_info['aliquot'],
            taxable=tax_info['taxable'],
            tax=tax_info['tax'],
            tax_type=0  # 0 = IVA estándar (puede variar según el sistema)
        )
        db.add(db_tax)
        tax_line += 1

    db.flush()  # Para que los taxes tengan IDs

    # ✅ SISTEMA ESCRITORIO: Crear registro en sales_operation_coins por cada moneda
    for currency in currencies:
        # Si es la misma moneda de la operación, usar los montos directamente
        if currency.code == operation_data.coin_code:
            total_net = operation_data.total_net
            total_tax = operation_data.total_tax
            total = operation_data.total
            buy_aliquot = 1.0
            sales_aliquot = 1.0
            factor_type = 0  # Moneda principal
        else:
            # Convertir montos según la tasa de cambio
            if currency.exchange_rate and currency.exchange_rate > 0:
                rate = float(currency.exchange_rate)
                total_net = operation_data.total_net * rate
                total_tax = operation_data.total_tax * rate
                total = operation_data.total * rate
                buy_aliquot = rate
                sales_aliquot = rate
                factor_type = 1  # Moneda convertida
            else:
                # Si no hay tasa, guardar 0
                total_net = 0
                total_tax = 0
                total = 0
                buy_aliquot = 0
                sales_aliquot = 0
                factor_type = 1

        operation_coin = SalesOperationCoin(
            company_id=current_user.company_id,
            sales_operation_id=db_operation.id,
            main_correlative=db_operation.correlative,
            coin_code=currency.code,
            factor_type=factor_type,
            buy_aliquot=buy_aliquot,
            sales_aliquot=sales_aliquot,
            total_net_details=operation_data.total_net,
            total_tax_details=operation_data.total_tax,
            total_details=operation_data.total,
            discount=operation_data.percent_discount,
            freight=operation_data.freight,
            total_net=total_net,
            total_tax=total_tax,
            total=total
        )
        db.add(operation_coin)

        # ✅ SISTEMA ESCRITORIO: Crear multi-moneda para impuestos (sales_operation_tax_coins)
        tax_line_counter = 1
        for tax_code, tax_info in taxes_by_code.items():
            if currency.code == operation_data.coin_code:
                rate = 1.0
            else:
                rate = float(currency.exchange_rate) if currency.exchange_rate else 1.0

            tax_coin = SalesOperationTaxCoin(
                company_id=current_user.company_id,
                main_correlative=db_operation.correlative,
                main_taxe_code=tax_code,
                main_line=tax_line_counter,
                coin_code=currency.code,
                taxable=tax_info['taxable'] * rate,
                tax=tax_info['tax'] * rate
            )
            db.add(tax_coin)
            tax_line_counter += 1

    db.commit()
    db.refresh(db_operation)

    return db_operation


@router.put("/sales-operations/{operation_id}", response_model=schemas.SalesOperation)
def update_sales_operation(
    operation_id: int,
    operation_data: schemas.SalesOperationUpdate,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """Actualizar operación de venta"""
    db_operation = db.query(SalesOperation).filter(
        SalesOperation.id == operation_id,
        SalesOperation.company_id == current_user.company_id
    ).first()

    if not db_operation:
        raise HTTPException(status_code=404, detail="Sales operation not found")

    # ✅ Actualizar campos
    update_data = operation_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_operation, field, value)

    db_operation.updated_at = datetime.now()
    db.commit()
    db.refresh(db_operation)

    return db_operation


@router.delete("/sales-operations/{operation_id}")
def delete_sales_operation(
    operation_id: int,
    current_user: User = Depends(check_permission(required_role="admin")),
    db: Session = Depends(database.get_db)
):
    """Eliminar operación de venta (solo admin)"""
    db_operation = db.query(SalesOperation).filter(
        SalesOperation.id == operation_id,
        SalesOperation.company_id == current_user.company_id
    ).first()

    if not db_operation:
        raise HTTPException(status_code=404, detail="Sales operation not found")

    db.delete(db_operation)
    db.commit()

    return {"message": "Sales operation deleted successfully"}


# ==================== ✅ CONVERSIÓN DE DOCUMENTOS ====================

@router.post("/sales-operations/{operation_id}/convert", response_model=schemas.SalesOperation)
def convert_sales_operation(
    operation_id: int,
    target_type: str = Query(..., description="Target operation type: ORDER, DELIVERYNOTE, BILL, CREDITNOTE, DEBITNOTE"),
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """
    Convertir operación de venta a otro tipo de documento.

    Workflow típico:
    1. BUDGET (Presupuesto) → ORDER (Pedido)
    2. ORDER (Pedido) → DELIVERYNOTE (Orden de Entrega)
    3. DELIVERYNOTE (Orden de Entrega) → BILL (Factura)
    4. BILL (Factura) → CREDITNOTE/DEBITNOTE (Notas de crédito/débito)
    """
    valid_types = ['ORDER', 'DELIVERYNOTE', 'BILL', 'CREDITNOTE', 'DEBITNOTE']
    if target_type.upper() not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Target type must be one of: {valid_types}"
        )

    # ✅ Obtener operación origen
    source_operation = db.query(SalesOperation).filter(
        SalesOperation.id == operation_id,
        SalesOperation.company_id == current_user.company_id
    ).first()

    if not source_operation:
        raise HTTPException(status_code=404, detail="Source operation not found")

    # ✅ Crear nueva operación basada en la origen
    new_operation = SalesOperation(
        company_id=current_user.company_id,
        operation_type=target_type.upper(),
        correlative=source_operation.correlative,  # ✅ Mantener correlativo
        client_id=source_operation.client_id,
        client_name=source_operation.client_name,
        client_tax_id=source_operation.client_tax_id,
        client_address=source_operation.client_address,
        client_phone=source_operation.client_phone,
        client_name_fiscal=source_operation.client_name_fiscal,
        emission_date=datetime.now(),
        register_date=datetime.now(),
        seller=source_operation.seller,
        store=source_operation.store,
        locations=source_operation.locations,
        user_code=current_user.username,
        station=source_operation.station,

        # ✅ Copiar montos
        total_amount=source_operation.total_amount,
        total_net_details=source_operation.total_net_details,
        total_tax_details=source_operation.total_tax_details,
        total_details=source_operation.total_details,
        percent_discount=source_operation.percent_discount,
        discount=source_operation.discount,
        percent_freight=source_operation.percent_freight,
        freight=source_operation.freight,
        total_net=source_operation.total_net,
        total_tax=source_operation.total_tax,
        total=source_operation.total,
        credit=source_operation.credit,
        cash=source_operation.cash,

        # ✅ Configuración
        type_price=source_operation.type_price,
        total_count_details=source_operation.total_count_details,
        freight_tax=source_operation.freight_tax,
        freight_aliquot=source_operation.freight_aliquot,

        # ✅ Retenciones
        total_retention_tax=source_operation.total_retention_tax,
        total_retention_municipal=source_operation.total_retention_municipal,
        total_retention_islr=source_operation.total_retention_islr,

        # ✅ IGTF
        free_tax=source_operation.free_tax,
        total_exempt=source_operation.total_exempt,
        base_igtf=source_operation.base_igtf,
        percent_igtf=source_operation.percent_igtf,
        igtf=source_operation.igtf,

        # ✅ Estado inicial
        wait=False,
        pending=True,
        canceled=False,
        delivered=False,
        begin_used=True,

        # ✅ Moneda
        coin_code=source_operation.coin_code,
        sale_point=source_operation.sale_point,
        restorant=source_operation.restorant,

        # ✅ Envío
        address_send=source_operation.address_send,
        contact_send=source_operation.contact_send,
        phone_send=source_operation.phone_send,
        total_weight=source_operation.total_weight,

        # ✅ Referencia a documento origen
        shopping_order_document_no=source_operation.document_no,
        shopping_order_date=source_operation.emission_date,
    )

    db.add(new_operation)
    db.commit()
    db.refresh(new_operation)

    # ✅ Copiar detalles
    source_details = db.query(SalesOperationDetail).filter(
        SalesOperationDetail.sales_operation_id == operation_id
    ).all()

    for source_detail in source_details:
        new_detail = SalesOperationDetail(
            sales_operation_id=new_operation.id,
            company_id=current_user.company_id,
            main_correlative=new_operation.correlative,
            line=source_detail.line,

            # ✅ Producto
            code_product=source_detail.code_product,
            description_product=source_detail.description_product,
            referenc=source_detail.referenc,
            mark=source_detail.mark,
            model=source_detail.model,

            # ✅ Ubicación
            store=source_detail.store,
            locations=source_detail.locations,

            # ✅ Unidad
            unit=source_detail.unit,
            conversion_factor=source_detail.conversion_factor,
            unit_type=source_detail.unit_type,

            # ✅ Cantidades y Precios
            amount=source_detail.amount,
            unitary_cost=source_detail.unitary_cost,
            sale_tax=source_detail.sale_tax,
            sale_aliquot=source_detail.sale_aliquot,
            price=source_detail.price,
            type_price=source_detail.type_price,

            # ✅ Costos
            total_net_cost=source_detail.total_net_cost,
            total_tax_cost=source_detail.total_tax_cost,
            total_cost=source_detail.total_cost,

            # ✅ Precios Brutos
            total_net_gross=source_detail.total_net_gross,
            total_tax_gross=source_detail.total_tax_gross,
            total_gross=source_detail.total_gross,

            # ✅ Descuentos
            percent_discount=source_detail.percent_discount,
            discount=source_detail.discount,

            # ✅ Totales
            total_net=source_detail.total_net,
            total_tax=source_detail.total_tax,
            total=source_detail.total,

            # ✅ Inventario
            pending_amount=source_detail.amount,  # ✅ Reiniciar pendiente
            buy_tax=source_detail.buy_tax,
            buy_aliquot=source_detail.buy_aliquot,
            update_inventory=source_detail.update_inventory,

            # ✅ Adicionales
            product_type=source_detail.product_type,
            description=source_detail.description,
            technician=source_detail.technician,
            coin_code=source_detail.coin_code,
            total_weight=source_detail.total_weight,
        )

        db.add(new_detail)

    # ✅ Copiar impuestos
    source_taxes = db.query(SalesOperationTax).filter(
        SalesOperationTax.sales_operation_id == operation_id
    ).all()

    for source_tax in source_taxes:
        new_tax = SalesOperationTax(
            sales_operation_id=new_operation.id,
            company_id=current_user.company_id,
            main_correlative=new_operation.correlative,
            line=source_tax.line,
            taxe_code=source_tax.taxe_code,
            aliquot=source_tax.aliquot,
            taxable=source_tax.taxable,
            tax=source_tax.tax,
            tax_type=source_tax.tax_type,
        )

        db.add(new_tax)

    db.commit()

    return new_operation


# ==================== ✅ ESTADÍSTICAS Y REPORTES ====================

@router.get("/sales-operations/stats/summary")
def get_sales_operations_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Resumen estadístico de operaciones de venta"""
    from sqlalchemy import func

    # ✅ Total por tipo de operación
    totals_by_type = db.query(
        SalesOperation.operation_type,
        func.count(SalesOperation.id).label('count'),
        func.sum(SalesOperation.total).label('total_amount')
    ).filter(
        SalesOperation.company_id == current_user.company_id
    ).group_by(SalesOperation.operation_type).all()

    # ✅ Operaciones pendientes
    pending_count = db.query(func.count(SalesOperation.id)).filter(
        SalesOperation.company_id == current_user.company_id,
        SalesOperation.pending == True
    ).scalar()

    # ✅ Operaciones entregadas
    delivered_count = db.query(func.count(SalesOperation.id)).filter(
        SalesOperation.company_id == current_user.company_id,
        SalesOperation.delivered == True
    ).scalar()

    return {
        "totals_by_type": [
            {
                "operation_type": row.operation_type,
                "count": row.count,
                "total_amount": float(row.total_amount or 0)
            }
            for row in totals_by_type
        ],
        "pending_count": pending_count or 0,
        "delivered_count": delivered_count or 0,
    }


@router.get("/sales-operations/by-customer/{customer_id}")
def get_sales_operations_by_customer(
    customer_id: int,
    operation_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener todas las operaciones de venta de un cliente"""
    query = db.query(SalesOperation).filter(
        SalesOperation.company_id == current_user.company_id,
        SalesOperation.client_id == customer_id
    )

    if operation_type:
        query = query.filter(SalesOperation.operation_type == operation_type.upper())

    return query.order_by(SalesOperation.created_at.desc()).offset(skip).limit(limit).all()


@router.put("/sales-operations/{operation_id}/status")
def update_sales_operation_status(
    operation_id: int,
    wait: Optional[bool] = None,
    pending: Optional[bool] = None,
    canceled: Optional[bool] = None,
    delivered: Optional[bool] = None,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """
    Actualizar estado de operación de venta.

    Estados disponibles:
    - wait: En espera (para presupuestos)
    - pending: Pendiente (no aplicado completamente)
    - canceled: Cancelado/anulado
    - delivered: Entregado
    """
    db_operation = db.query(SalesOperation).filter(
        SalesOperation.id == operation_id,
        SalesOperation.company_id == current_user.company_id
    ).first()

    if not db_operation:
        raise HTTPException(status_code=404, detail="Sales operation not found")

    if wait is not None:
        db_operation.wait = wait
    if pending is not None:
        db_operation.pending = pending
    if canceled is not None:
        db_operation.canceled = canceled
    if delivered is not None:
        db_operation.delivered = delivered

    db_operation.updated_at = datetime.now()
    db.commit()
    db.refresh(db_operation)

    return db_operation
