# crud/invoices.py
"""
Funciones CRUD para gestión de facturas y presupuestos
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException
from datetime import datetime
from typing import List, Optional
import models
import schemas
from .base import verify_company_ownership, paginate_query
from . import venezuela_tax  # ✅ VENEZUELA: Funciones de cálculo de impuestos
import traceback

# ================= FUNCIONES LEGACY (MANTENER COMPATIBILIDAD) =================

def create_budget(db: Session, budget_data: schemas.Invoice):
    """Legacy: crear presupuesto sin empresa específica"""
    budget = models.Invoice(
        customer_id=budget_data.customer_id,
        status='presupuesto',
        total_amount=0,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    for item in budget_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        budget_item = models.InvoiceItem(
            invoice_id=budget.id,
            product_id=product.id,
            quantity=item.quantity,
            price_per_unit=product.price,
            total_price=product.price * item.quantity,
        )
        db.add(budget_item)

    db.commit()
    budget.total_amount = sum(item.total_price for item in budget.invoice_items)
    db.commit()
    return budget

def confirm_budget(db: Session, budget_id: int):
    """Legacy: confirmar presupuesto como factura"""
    budget = db.query(models.Invoice).filter(
        models.Invoice.id == budget_id, 
        models.Invoice.status == 'presupuesto'
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found or already confirmed")

    budget.status = 'factura'

    for item in budget.invoice_items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if product.quantity < item.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for product")
        product.quantity -= item.quantity

    db.commit()
    return budget

def create_invoice(db: Session, invoice_data: schemas.Invoice):
    """Legacy: crear factura sin empresa específica"""
    return create_invoice_for_company(db, invoice_data, 1)

def view_invoice(db: Session, invoice_id: int):
    """Legacy: ver factura sin validar empresa"""
    return view_invoice_by_company(db, invoice_id, 1)

def edit_invoice(db: Session, invoice_id: int, invoice_data: schemas.Invoice):
    """Legacy: editar factura sin validar empresa"""
    return edit_invoice_for_company(db, invoice_id, invoice_data, 1)

def delete_invoice(db: Session, invoice_id: int):
    """Legacy: eliminar factura sin validar empresa"""
    return delete_invoice_for_company(db, invoice_id, 1)

# ================= FUNCIONES MULTIEMPRESA =================

def create_invoice_for_company(
    db: Session, 
    invoice_data: schemas.InvoiceCreate, 
    company_id: int
):
    """Crear factura para empresa específica"""

    # Verificar que la empresa exista
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Verificar que el cliente pertenezca a la empresa
    customer = None
    if hasattr(invoice_data, 'customer_id') and invoice_data.customer_id:
        customer = verify_company_ownership(
            db=db,
            model_class=models.Customer,
            item_id=invoice_data.customer_id,
            company_id=company_id,
            error_message="Customer not found in your company"
        )

        # ✅ VENEZUELA: Validar que el cliente tenga RIF si el monto lo requiere
        # Calcular subtotal aproximado para validar
        estimated_total = 0
        if hasattr(invoice_data, 'items') and invoice_data.items:
            for item in invoice_data.items:
                product = db.query(models.Product).filter(
                    models.Product.id == item.product_id,
                    models.Product.company_id == company_id
                ).first()
                if product:
                    unit_price = getattr(item, 'price_per_unit', product.price)
                    estimated_total += unit_price * item.quantity

        # Verificar si se supera el umbral para requerir RIF
        threshold = company.require_customer_tax_id_threshold or 0.0
        if estimated_total > threshold and not customer.tax_id:
            raise HTTPException(
                status_code=400,
                detail=f"Customer tax ID (RIF/CI) is required for invoices over {threshold} {company.currency}. "
                       f"Please update the customer's tax information before creating this invoice."
            )

    # Verificar que el almacén pertenezca a la empresa (si se especifica)
    warehouse = None
    if hasattr(invoice_data, 'warehouse_id') and invoice_data.warehouse_id:
        warehouse = verify_company_ownership(
            db=db,
            model_class=models.Warehouse,
            item_id=invoice_data.warehouse_id,
            company_id=company_id,
            error_message="Warehouse not found in your company"
        )

    # Generar número de factura
    invoice_number = f"{company.invoice_prefix}-{company.next_invoice_number:06d}"

    # ✅ VENEZUELA: Generar número de control
    control_number = f"{company.invoice_prefix}-{company.next_control_number:08d}"

    try:
        # Crear factura con campos para Venezuela
        invoice = models.Invoice(
            company_id=company_id,
            customer_id=getattr(invoice_data, 'customer_id', None),
            warehouse_id=getattr(invoice_data, 'warehouse_id', None),
            invoice_number=invoice_number,
            control_number=control_number,  # ✅ VENEZUELA
            status=getattr(invoice_data, 'status', 'factura'),
            discount=getattr(invoice_data, 'discount', 0),
            total_amount=0,
            date=getattr(invoice_data, 'date', datetime.utcnow().date()),
            due_date=getattr(invoice_data, 'due_date', None),
            notes=getattr(invoice_data, 'notes', None),
            # ✅ VENEZUELA: Información fiscal
            transaction_type=getattr(invoice_data, 'transaction_type', 'contado'),
            payment_method=getattr(invoice_data, 'payment_method', 'efectivo'),
            credit_days=getattr(invoice_data, 'credit_days', 0),
            iva_percentage=getattr(invoice_data, 'iva_percentage', 16.0),
            customer_phone=getattr(invoice_data, 'customer_phone', None),
            customer_address=getattr(invoice_data, 'customer_address', None)
        )

        db.add(invoice)
        db.flush()  # Para obtener el ID

        total_amount = 0

        # Procesar items si existen
        if hasattr(invoice_data, 'items') and invoice_data.items:
            for item_data in invoice_data.items:
                # Verificar que el producto pertenezca a la empresa
                product = verify_company_ownership(
                    db=db,
                    model_class=models.Product,
                    item_id=item_data.product_id,
                    company_id=company_id,
                    error_message="Product not found in your company"
                )

                # Verificar stock disponible en el almacén si está especificado
                if warehouse:
                    warehouse_product = db.query(models.WarehouseProduct).filter(
                        models.WarehouseProduct.warehouse_id == warehouse.id,
                        models.WarehouseProduct.product_id == product.id
                    ).first()

                    if not warehouse_product or warehouse_product.stock < item_data.quantity:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Insufficient stock for product {product.name} in warehouse {warehouse.name}"
                        )
                elif product.quantity < item_data.quantity:
                    # Si no hay almacén especificado, verificar stock global
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for product {product.name}"
                    )

                # Calcular precio
                unit_price = getattr(item_data, 'price_per_unit', product.price)
                line_total = unit_price * item_data.quantity

                # ✅ VENEZUELA: Calcular impuestos del item
                tax_rate = getattr(item_data, 'tax_rate', invoice.iva_percentage)
                is_exempt = getattr(item_data, 'is_exempt', False)
                tax_amount = 0.0

                if not is_exempt and tax_rate > 0:
                    tax_amount = venezuela_tax.calculate_iva(line_total, tax_rate)

                # Crear item de factura con impuestos
                invoice_item = models.InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id,
                    quantity=item_data.quantity,
                    price_per_unit=unit_price,
                    total_price=line_total,
                    # ✅ VENEZUELA: Información fiscal del item
                    tax_rate=tax_rate,
                    tax_amount=tax_amount,
                    is_exempt=is_exempt
                )

                db.add(invoice_item)
                total_amount += line_total

                # Actualizar stock si es factura confirmada
                if invoice.status == 'factura':
                    # Actualizar stock global del producto
                    product.quantity -= item_data.quantity

                    # Actualizar stock en el almacén si está especificado
                    if warehouse:
                        warehouse_product = db.query(models.WarehouseProduct).filter(
                            models.WarehouseProduct.warehouse_id == warehouse.id,
                            models.WarehouseProduct.product_id == product.id
                        ).first()

                        if warehouse_product:
                            warehouse_product.stock -= item_data.quantity

                            # Crear movimiento de inventario con referencia al almacén
                            movement = models.InventoryMovement(
                                product_id=product.id,
                                warehouse_id=warehouse.id,
                                movement_type='sale',
                                quantity=item_data.quantity,
                                timestamp=datetime.utcnow(),
                                description=f"Sale - Invoice {invoice_number}",
                                invoice_id=invoice.id
                            )
                            db.add(movement)
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Warehouse product not found for {product.name}"
                            )
                    else:
                        # Crear movimiento de inventario sin almacén específico
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            movement_type='sale',
                            quantity=item_data.quantity,
                            timestamp=datetime.utcnow(),
                            description=f"Sale - Invoice {invoice_number}",
                            invoice_id=invoice.id
                        )
                        db.add(movement)

        # ✅ VENEZUELA: Calcular totales con impuestos
        # Preparar datos para cálculo
        items_data = []
        for item_data in invoice_data.items:
            product = db.query(models.Product).filter(
                models.Product.id == item_data.product_id
            ).first()
            unit_price = getattr(item_data, 'price_per_unit', product.price)
            line_total = unit_price * item_data.quantity

            items_data.append({
                'price': unit_price,
                'quantity': item_data.quantity,
                'tax_rate': getattr(item_data, 'tax_rate', invoice.iva_percentage),
                'is_exempt': getattr(item_data, 'is_exempt', False)
            })

        # Calcular todos los impuestos usando la función auxiliar
        # ✅ VENEZUELA: Pasar moneda de la empresa para conversión correcta de umbrales
        tax_calculations = venezuela_tax.calculate_invoice_totals(
            items=items_data,
            discount=invoice.discount,
            iva_percentage=invoice.iva_percentage,
            company=company,
            currency=company.currency  # USD o VES
        )

        # Actualizar totales de la factura
        invoice.subtotal = tax_calculations['subtotal']
        invoice.taxable_base = tax_calculations['taxable_base']
        invoice.exempt_amount = tax_calculations['exempt_amount']
        invoice.iva_amount = tax_calculations['iva_amount']
        invoice.iva_retention = tax_calculations['iva_retention']
        invoice.iva_retention_percentage = tax_calculations['iva_retention_percentage']
        invoice.islr_retention = tax_calculations['islr_retention']
        invoice.islr_retention_percentage = tax_calculations['islr_retention_percentage']
        invoice.stamp_tax = tax_calculations['stamp_tax']
        invoice.total_with_taxes = tax_calculations['total_with_taxes']
        invoice.total_amount = tax_calculations['total_with_taxes']

        # Actualizar contadores de empresa
        company.next_invoice_number += 1
        company.next_control_number += 1  # ✅ VENEZUELA: Actualizar número de control

        db.commit()
        db.refresh(invoice)

        return invoice
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
        status_code=400,
            detail={
                "error": "Error creating invoice",
                "message": str(e),                # mensaje legible
                "type": type(e).__name__,         # tipo de excepción
                "args": e.args,                   # argumentos originales
                "traceback": traceback.format_exc()  # stack trace completo
            }
        )

def view_invoice_by_company(db: Session, invoice_id: int, company_id: int):
    """Ver factura específica de empresa con detalles de productos"""
    invoice = verify_company_ownership(
        db=db,
        model_class=models.Invoice,
        item_id=invoice_id,
        company_id=company_id,
        error_message="Invoice not found in your company"
    )

    # Convertir a diccionario y agregar detalles de productos
    invoice_dict = {
        "id": invoice.id,
        "company_id": invoice.company_id,
        "customer_id": invoice.customer_id,
        "warehouse_id": invoice.warehouse_id,
        "invoice_number": invoice.invoice_number,
        "control_number": invoice.control_number,
        "date": invoice.date,
        "total_amount": invoice.total_amount,
        "status": invoice.status,
        "discount": invoice.discount,
        "notes": invoice.notes,
        "transaction_type": invoice.transaction_type,
        "payment_method": invoice.payment_method,
        "credit_days": invoice.credit_days,
        "iva_percentage": invoice.iva_percentage,
        "iva_amount": invoice.iva_amount,
        "taxable_base": invoice.taxable_base,
        "exempt_amount": invoice.exempt_amount,
        "iva_retention": invoice.iva_retention,
        "iva_retention_percentage": invoice.iva_retention_percentage,
        "islr_retention": invoice.islr_retention,
        "islr_retention_percentage": invoice.islr_retention_percentage,
        "stamp_tax": invoice.stamp_tax,
        "subtotal": invoice.subtotal,
        "total_with_taxes": invoice.total_with_taxes,
        "customer_phone": invoice.customer_phone,
        "customer_address": invoice.customer_address,
        "items": []
    }

    # Agregar items con detalles de productos
    for item in invoice.invoice_items:
        # Obtener detalles del producto
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id
        ).first()

        item_dict = {
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price_per_unit": item.price_per_unit,
            "total_price": item.total_price,
            "tax_rate": item.tax_rate,
            "tax_amount": item.tax_amount,
            "is_exempt": item.is_exempt,
            "product_name": product.name if product else None,
            "product_description": product.description if product else None,
            "product_sku": product.sku if product else None
        }
        invoice_dict["items"].append(item_dict)

    return invoice_dict

def edit_invoice_for_company(
    db: Session,
    invoice_id: int,
    invoice_data: schemas.InvoiceUpdate,
    company_id: int
):
    """Editar factura de empresa"""
    invoice = verify_company_ownership(
        db=db,
        model_class=models.Invoice,
        item_id=invoice_id,
        company_id=company_id,
        error_message="Invoice not found in your company"
    )

    # Guardar el almacén original
    original_warehouse_id = invoice.warehouse_id
    new_warehouse_id = getattr(invoice_data, 'warehouse_id', original_warehouse_id)

    # Verificar nuevo almacén si se está cambiando
    new_warehouse = None
    if hasattr(invoice_data, 'warehouse_id') and new_warehouse_id:
        if new_warehouse_id != original_warehouse_id:
            new_warehouse = verify_company_ownership(
                db=db,
                model_class=models.Warehouse,
                item_id=new_warehouse_id,
                company_id=company_id,
                error_message="New warehouse not found in your company"
            )

    try:
        # Si hay nuevos items y la factura está confirmada, revertir stock anterior
        if hasattr(invoice_data, 'items') and invoice_data.items and invoice.status == 'factura':
            # Revertir stock de los items anteriores
            for old_item in invoice.invoice_items:
                product = db.query(models.Product).filter(
                    models.Product.id == old_item.product_id
                ).first()

                if product:
                    # Revertir stock global
                    product.quantity += old_item.quantity

                    # Revertir stock en almacén original
                    if original_warehouse_id:
                        warehouse_product = db.query(models.WarehouseProduct).filter(
                            models.WarehouseProduct.warehouse_id == original_warehouse_id,
                            models.WarehouseProduct.product_id == old_item.product_id
                        ).first()

                        if warehouse_product:
                            warehouse_product.stock += old_item.quantity

            # Eliminar items antiguos
            db.query(models.InvoiceItem).filter(
                models.InvoiceItem.invoice_id == invoice_id
            ).delete()

            # Calcular nuevo total
            total_amount = 0

            # Agregar nuevos items y actualizar stock
            for item_data in invoice_data.items:
                product = verify_company_ownership(
                    db=db,
                    model_class=models.Product,
                    item_id=item_data.product_id,
                    company_id=company_id,
                    error_message="Product not found in your company"
                )

                # Verificar stock disponible
                if new_warehouse:
                    warehouse_product = db.query(models.WarehouseProduct).filter(
                        models.WarehouseProduct.warehouse_id == new_warehouse.id,
                        models.WarehouseProduct.product_id == product.id
                    ).first()

                    if not warehouse_product or warehouse_product.stock < item_data.quantity:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Insufficient stock for product {product.name} in warehouse {new_warehouse.name}"
                        )
                elif product.quantity < item_data.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for product {product.name}"
                    )

                # Calcular precio
                unit_price = getattr(item_data, 'price_per_unit', product.price)
                line_total = unit_price * item_data.quantity

                # Crear nuevo item
                new_item = models.InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id,
                    quantity=item_data.quantity,
                    price_per_unit=unit_price,
                    total_price=line_total
                )

                db.add(new_item)
                total_amount += line_total

                # Actualizar stock
                product.quantity -= item_data.quantity

                if new_warehouse:
                    warehouse_product = db.query(models.WarehouseProduct).filter(
                        models.WarehouseProduct.warehouse_id == new_warehouse.id,
                        models.WarehouseProduct.product_id == product.id
                    ).first()

                    if warehouse_product:
                        warehouse_product.stock -= item_data.quantity

                        # Crear movimiento de inventario
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            warehouse_id=new_warehouse.id,
                            movement_type='sale',
                            quantity=item_data.quantity,
                            timestamp=datetime.utcnow(),
                            description=f"Updated sale - Invoice {invoice.invoice_number}",
                            invoice_id=invoice.id
                        )
                        db.add(movement)

            # Actualizar total
            invoice.total_amount = total_amount

        # Actualizar otros campos
        update_data = invoice_data.dict(exclude_unset=True)
        if 'items' in update_data:
            del update_data['items']

        for key, value in update_data.items():
            if hasattr(invoice, key) and key != 'warehouse_id':
                setattr(invoice, key, value)

        # Actualizar warehouse_id por separado si cambió
        if hasattr(invoice_data, 'warehouse_id') and new_warehouse_id is not None:
            invoice.warehouse_id = new_warehouse_id

        db.commit()
        db.refresh(invoice)
        return invoice

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating invoice: {str(e)}"
        )

def delete_invoice_for_company(db: Session, invoice_id: int, company_id: int):
    """Eliminar factura de empresa"""
    invoice = verify_company_ownership(
        db=db,
        model_class=models.Invoice,
        item_id=invoice_id,
        company_id=company_id,
        error_message="Invoice not found in your company"
    )
    
    # Solo permitir eliminación si es presupuesto
    if invoice.status == 'factura':
        raise HTTPException(
            status_code=400,
            detail="Cannot delete confirmed invoices"
        )
    
    # Eliminar items primero
    db.query(models.InvoiceItem).filter(
        models.InvoiceItem.invoice_id == invoice_id
    ).delete()
    
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted successfully"}

def get_invoices_by_company(
    db: Session,
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """Obtener facturas de una empresa con detalles de productos"""
    query = db.query(models.Invoice).filter(models.Invoice.company_id == company_id)

    if status:
        query = query.filter(models.Invoice.status == status)

    invoices = paginate_query(
        query.order_by(models.Invoice.date.desc()),
        skip=skip,
        limit=limit
    ).all()

    # Construir respuesta con detalles de productos
    result = []
    for invoice in invoices:
        invoice_dict = {
            "id": invoice.id,
            "company_id": invoice.company_id,
            "customer_id": invoice.customer_id,
            "warehouse_id": invoice.warehouse_id,
            "invoice_number": invoice.invoice_number,
            "control_number": invoice.control_number,
            "date": invoice.date,
            "total_amount": invoice.total_amount,
            "status": invoice.status,
            "discount": invoice.discount,
            "notes": invoice.notes,
            "transaction_type": invoice.transaction_type,
            "payment_method": invoice.payment_method,
            "credit_days": invoice.credit_days,
            "iva_percentage": invoice.iva_percentage,
            "iva_amount": invoice.iva_amount,
            "taxable_base": invoice.taxable_base,
            "exempt_amount": invoice.exempt_amount,
            "iva_retention": invoice.iva_retention,
            "iva_retention_percentage": invoice.iva_retention_percentage,
            "islr_retention": invoice.islr_retention,
            "islr_retention_percentage": invoice.islr_retention_percentage,
            "stamp_tax": invoice.stamp_tax,
            "subtotal": invoice.subtotal,
            "total_with_taxes": invoice.total_with_taxes,
            "customer_phone": invoice.customer_phone,
            "customer_address": invoice.customer_address,
            "items": []
        }

        # Agregar items con detalles de productos
        for item in invoice.invoice_items:
            product = db.query(models.Product).filter(
                models.Product.id == item.product_id
            ).first()

            item_dict = {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price_per_unit": item.price_per_unit,
                "total_price": item.total_price,
                "tax_rate": item.tax_rate,
                "tax_amount": item.tax_amount,
                "is_exempt": item.is_exempt,
                "product_name": product.name if product else None,
                "product_description": product.description if product else None,
                "product_sku": product.sku if product else None
            }
            invoice_dict["items"].append(item_dict)

        result.append(invoice_dict)

    return result

def confirm_budget_for_company(db: Session, budget_id: int, company_id: int):
    """Confirmar presupuesto como factura en empresa específica"""
    budget = db.query(models.Invoice).filter(
        models.Invoice.id == budget_id,
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'presupuesto'
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=404, 
            detail="Budget not found or already confirmed"
        )
    
    try:
        # Cambiar status
        budget.status = 'factura'
        
        # Actualizar stock y crear movimientos
        for item in budget.invoice_items:
            product = db.query(models.Product).filter(
                models.Product.id == item.product_id,
                models.Product.company_id == company_id
            ).first()
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            if product.quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product.name}"
                )
            
            # Actualizar stock
            product.quantity -= item.quantity
            
            # Crear movimiento de inventario
            movement = models.InventoryMovement(
                product_id=product.id,
                movement_type='sale',
                quantity=item.quantity,
                timestamp=datetime.utcnow(),
                description=f"Sale - Invoice {budget.invoice_number}",
                invoice_id=budget.id
            )
            db.add(movement)
        
        db.commit()
        db.refresh(budget)
        return budget
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error confirming budget: {str(e)}"
        )

# ================= MOVIMIENTOS DE CRÉDITO =================

def create_credit_movement_for_company(
    db: Session,
    invoice_id: int,
    movement_data: schemas.CreditMovementCreate,
    company_id: int
):
    """Crear movimiento de crédito (nota de crédito/devolución)"""
    # Verificar que la factura pertenezca a la empresa
    invoice = verify_company_ownership(
        db=db,
        model_class=models.Invoice,
        item_id=invoice_id,
        company_id=company_id,
        error_message="Invoice not found in your company"
    )
    
    if invoice.status != 'factura':
        raise HTTPException(
            status_code=400,
            detail="Can only create credit movements for confirmed invoices"
        )
    
    try:
        # Crear movimiento de crédito
        credit_movement = models.CreditMovement(
            invoice_id=invoice_id,
            movement_type=movement_data.movement_type,
            amount=movement_data.amount,
            reason=movement_data.reason,
            date=datetime.utcnow().date()
        )
        
        db.add(credit_movement)
        
        # Si es devolución, restaurar stock
        if movement_data.movement_type == 'return':
            for item in invoice.invoice_items:
                product = db.query(models.Product).filter(
                    models.Product.id == item.product_id
                ).first()
                
                if product:
                    # Calcular cantidad a devolver proporcionalmente
                    return_ratio = movement_data.amount / invoice.total_amount
                    return_quantity = int(item.quantity * return_ratio)
                    
                    if return_quantity > 0:
                        product.quantity += return_quantity
                        
                        # Crear movimiento de inventario
                        movement = models.InventoryMovement(
                            product_id=product.id,
                            movement_type='return',
                            quantity=return_quantity,
                            timestamp=datetime.utcnow(),
                            description=f"Return - Credit Note #{credit_movement.id}",
                            invoice_id=invoice_id
                        )
                        db.add(movement)
        
        db.commit()
        db.refresh(credit_movement)
        return credit_movement
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating credit movement: {str(e)}"
        )

# ================= ESTADÍSTICAS Y REPORTES =================

def get_invoices_stats_by_company(db: Session, company_id: int):
    """Estadísticas de facturas por empresa"""
    # Total de facturas
    total_invoices = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id
    ).count()
    
    # Total confirmadas
    confirmed_invoices = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura'
    ).count()
    
    # Total presupuestos
    pending_budgets = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'presupuesto'
    ).count()
    
    # Monto total facturado
    total_amount = db.query(func.sum(models.Invoice.total_amount)).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura'
    ).scalar() or 0
    
    # Ventas del mes actual
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_sales = db.query(func.sum(models.Invoice.total_amount)).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura',
        models.Invoice.date >= start_of_month
    ).scalar() or 0
    
    # Promedio por factura
    avg_invoice_amount = total_amount / confirmed_invoices if confirmed_invoices > 0 else 0
    
    return {
        "total_invoices": total_invoices,
        "confirmed_invoices": confirmed_invoices,
        "pending_budgets": pending_budgets,
        "total_amount": float(total_amount),
        "monthly_sales": float(monthly_sales),
        "avg_invoice_amount": float(avg_invoice_amount)
    }

def get_invoices_by_customer_and_company(
    db: Session,
    customer_id: int,
    company_id: int
):
    """Obtener facturas de un cliente específico"""
    return db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.customer_id == customer_id
    ).order_by(models.Invoice.date.desc()).all()

def get_overdue_invoices_by_company(db: Session, company_id: int):
    """Obtener facturas vencidas de una empresa"""
    today = datetime.utcnow().date()
    
    return db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura',
        models.Invoice.due_date < today,
        models.Invoice.paid == False  # Asumiendo que existe este campo
    ).all()

def get_sales_summary_by_period(
    db: Session,
    company_id: int,
    start_date: datetime,
    end_date: datetime
):
    """Resumen de ventas por período"""
    sales = db.query(
        func.sum(models.Invoice.total_amount).label('total_sales'),
        func.count(models.Invoice.id).label('invoice_count'),
        func.avg(models.Invoice.total_amount).label('avg_sale')
    ).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == 'factura',
        models.Invoice.date >= start_date,
        models.Invoice.date <= end_date
    ).first()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_sales": float(sales.total_sales or 0),
        "invoice_count": sales.invoice_count or 0,
        "average_sale": float(sales.avg_sale or 0)
    }