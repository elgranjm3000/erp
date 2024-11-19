from sqlalchemy.orm import Session
import models
import schemas
from passlib.context import CryptContext
from fastapi import HTTPException
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_budget(db: Session, budget_data: schemas.Invoice):
    # Crear un presupuesto (similar a una factura)
    budget = models.Invoice(
        customer_id=budget_data.customer_id,
        status='presupuesto',  # Estado del presupuesto
        total_amount=0,  # Calculado a partir de los items
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    # Agregar items al presupuesto
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

    # Calcular el total del presupuesto
    budget.total_amount = sum(item.total_price for item in budget.invoice_items)
    db.commit()

    return budget

def confirm_budget(db: Session, budget_id: int):
    # Buscar el presupuesto
    budget = db.query(models.Invoice).filter(models.Invoice.id == budget_id, models.Invoice.status == 'presupuesto').first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found or already confirmed")

    # Cambiar el estado a 'factura'
    budget.status = 'factura'

    # Actualizar el stock de los productos
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
    # Crear la factura
    invoice = models.Invoice(
        customer_id=invoice_data.customer_id,
        date=invoice_data.date,
        total_amount=0,  # Se calculará basado en los items
        status=invoice_data.status,
        warehouse_id=invoice_data.warehouse_id,
        discount=invoice_data.discount
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    invoice_items = []  # Lista para almacenar los ítems de la factura
    for item in invoice_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Buscar el producto en el almacén específico
        warehouse_product = db.query(models.WarehouseProduct).filter(
            models.WarehouseProduct.product_id == item.product_id,
            models.WarehouseProduct.warehouse_id == invoice_data.warehouse_id
        ).first()

        if not warehouse_product:
            raise HTTPException(status_code=404, detail="Product not found in the specified warehouse")
        
        # Verificar si hay suficiente stock en el almacén
        if warehouse_product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product {item.product_id} in warehouse {invoice_data.warehouse_id}"
            )
        
        # Restar el stock del producto en el almacén
        if invoice_data.status == "factura":
            product.quantity -= item.quantity
            warehouse_product.stock -= item.quantity
            # Registrar el movimiento de inventario
            movement = models.InventoryMovement(
                product_id=item.product_id,
                quantity=item.quantity,
                movement_type="salida",  # Salida de inventario
                invoice_id=invoice.id  # Relacionar con la factura
            )
            db.add(movement)

        # Crear el ítem de la factura
        invoice_item = models.InvoiceItem(
            invoice_id=invoice.id,
            product_id=product.id,
            quantity=item.quantity,
            price_per_unit=product.price,
            total_price=product.price * item.quantity,
        )
        db.add(invoice_item)
        invoice_items.append(invoice_item)  # Guardamos los ítems creados

        

    # Commit de las operaciones de los ítems y el movimiento de inventario
    db.commit()

    # Calcular el total de la factura
    subtotal = sum(item.total_price for item in invoice_items)
    discount_amount = subtotal * (invoice_data.discount / 100)  # Descuento en porcentaje
    invoice.total_amount =  subtotal - discount_amount
    db.commit()

    # Crear la respuesta para el cliente
    invoice_response = schemas.Invoice(
        customer_id=invoice.customer_id,
        total_amount=invoice.total_amount,
        date=invoice.date,
        status=invoice.status,
        warehouse_id=invoice.warehouse_id,
        discount=invoice.discount,
        items=[schemas.InvoiceItem(
            product_id=item.product_id,
            quantity=item.quantity,
            price_per_unit=item.price_per_unit,
            total_price=item.total_price
        ) for item in invoice_items]
    )
    return invoice_response

def view_invoice(db: Session, invoice_id: int):
    # Buscar la factura por su ID
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Crear la respuesta con la información de la factura
    invoice_response = schemas.Invoice(
        customer_id=invoice.customer_id,
        total_amount=invoice.total_amount,
        date=invoice.date,
        status=invoice.status,
        warehouse_id=invoice.warehouse_id,
        discount=invoice.discount,
        items=[
            schemas.InvoiceItem(
                product_id=item.product_id,
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                total_price=item.total_price
            ) for item in invoice.invoice_items
        ]
    )
    return invoice_response


def edit_invoice(db: Session, invoice_id: int, invoice_data: schemas.Invoice):
    # Buscar la factura existente
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Actualizar los datos principales de la factura
    invoice.customer_id = invoice_data.customer_id
    invoice.date = invoice_data.date
    invoice.status = invoice_data.status
    invoice.warehouse_id = invoice_data.warehouse_id
    invoice.discount = invoice_data.discount
    

    # Obtener los ítems originales para revertir stock si es necesario
    original_items = invoice.invoice_items

    # Revertir cambios en el inventario si es una "factura"
    if invoice.status == "factura":
        for original_item in original_items:
            warehouse_product = db.query(models.WarehouseProduct).filter(
                models.WarehouseProduct.product_id == original_item.product_id,
                models.WarehouseProduct.warehouse_id == invoice.warehouse_id
            ).first()
            if warehouse_product:
                warehouse_product.stock += original_item.quantity
                db.query(models.Product).filter(
                    models.Product.id == original_item.product_id
                ).update({"quantity": models.Product.quantity + original_item.quantity})
    
    # Eliminar los ítems antiguos
    db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id == invoice.id).delete()

    # Agregar los nuevos ítems
    new_items = []
    for item in invoice_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        warehouse_product = db.query(models.WarehouseProduct).filter(
            models.WarehouseProduct.product_id == item.product_id,
            models.WarehouseProduct.warehouse_id == invoice.warehouse_id
        ).first()

        if not warehouse_product:
            raise HTTPException(status_code=404, detail="Product not found in warehouse")

        if warehouse_product.stock < item.quantity and invoice.status == "factura":
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product {item.product_id} in warehouse {invoice.warehouse_id}"
            )

        if invoice.status == "factura":
            product.quantity -= item.quantity
            warehouse_product.stock -= item.quantity

        invoice_item = models.InvoiceItem(
            invoice_id=invoice.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_per_unit=product.price,
            total_price=product.price * item.quantity,
        )
        db.add(invoice_item)
        new_items.append(invoice_item)

    # Actualizar el monto total de la factura    
    subtotal = sum(item.total_price for item in new_items)
    discount_amount = subtotal * (invoice_data.discount / 100)  # Descuento en porcentaje
    invoice.total_amount =  subtotal - discount_amount
    db.commit()

    # Retornar la factura actualizada
    invoice_response = schemas.Invoice(
        customer_id=invoice.customer_id,
        total_amount=invoice.total_amount,
        date=invoice.date,
        status=invoice.status,
        warehouse_id=invoice.warehouse_id,
        items=[
            schemas.InvoiceItem(
                product_id=item.product_id,
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                total_price=item.total_price
            ) for item in new_items
        ]
    )
    return invoice_response


def delete_invoice(db: Session, invoice_id: int):
    # Buscar la factura existente
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Revertir cambios en el inventario si es una "factura"
    if invoice.status == "factura":
        for item in invoice.invoice_items:
            warehouse_product = db.query(models.WarehouseProduct).filter(
                models.WarehouseProduct.product_id == item.product_id,
                models.WarehouseProduct.warehouse_id == invoice.warehouse_id
            ).first()
            if warehouse_product:
                warehouse_product.stock += item.quantity
                db.query(models.Product).filter(
                    models.Product.id == item.product_id
                ).update({"quantity": models.Product.quantity + item.quantity})
    
    # Eliminar los ítems de la factura
    db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id == invoice_id).delete()
    
    # Eliminar la factura
    db.delete(invoice)
    db.commit()
    
    return {"message": "Invoice deleted successfully"}


def create_credit_movement(db: Session, invoice_id: int, amount: float, movement_type: str):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if movement_type not in ["nota_credito", "devolucion"]:
        raise HTTPException(status_code=400, detail="Invalid movement type")

    credit_movement = models.CreditMovement(
        invoice_id=invoice_id,
        amount=amount,
        movement_type=movement_type,
    )
    db.add(credit_movement)

    if movement_type == "devolucion":
        # Revertir el stock de los productos involucrados
        for item in invoice.invoice_items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            product.quantity += item.quantity

    db.commit()
    return credit_movement


# Funciones de productos
def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_product_by_id(db: Session, product_id: int):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

def delete_product(db: Session, product_id: int):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted successfully"}

def update_product(db: Session, product_id: int, product_data: schemas.ProductUpdate):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# Crear o actualizar un registro warehouse-product
def create_or_update_warehouse_product(db: Session, wp_data: schemas.WarehouseProductCreate):
    wp = db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == wp_data.warehouse_id,
        models.WarehouseProduct.product_id == wp_data.product_id,
    ).first()

    if wp:
        wp.stock = wp_data.stock  # Actualiza el stock si ya existe
    else:
        wp = models.WarehouseProduct(**wp_data.dict())  # Crea un nuevo registro
        db.add(wp)

    db.commit()
    db.refresh(wp)
    return wp

# Leer todos los registros warehouse-product
def get_warehouse_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.WarehouseProduct).offset(skip).limit(limit).all()

# Leer un registro específico por warehouse_id y product_id
def get_warehouse_product(db: Session, warehouse_id: int, product_id: int):
    return db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id,
        models.WarehouseProduct.product_id == product_id,
    ).first()

# Actualizar el stock de un producto en un almacén
def update_warehouse_product_stock(db: Session, warehouse_id: int, product_id: int, stock: int):
    wp = db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id,
        models.WarehouseProduct.product_id == product_id,
    ).first()

    if not wp:
        return None

    wp.stock = stock
    db.commit()
    db.refresh(wp)
    return wp

# Eliminar un registro warehouse-product
def delete_warehouse_product(db: Session, warehouse_id: int, product_id: int):
    wp = db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id,
        models.WarehouseProduct.product_id == product_id,
    ).first()

    if not wp:
        return None

    db.delete(wp)
    db.commit()
    return wp

# Funciones de categorías
def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Funciones de movimientos de inventario
def create_inventory_movement(db: Session, movement: schemas.InventoryMovementCreate):
    db_movement = models.InventoryMovement(**movement.dict())
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement

# Funciones de almacenes
def get_warehouses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Warehouse).offset(skip).limit(limit).all()

def create_warehouse(db: Session, warehouse: schemas.WarehouseCreate):
    db_warehouse = models.Warehouse(**warehouse.dict())
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse




# Crear una compra
def create_purchase(db: Session, purchase_data: schemas.Purchase):
    # Crear la compra
    purchase = models.Purchase(
        supplier_id=purchase_data.supplier_id,
        date=purchase_data.date,
        total_amount=0,  # Se calculará basado en los ítems
        warehouse_id=purchase_data.warehouse_id
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    purchase_items = []  # Lista para almacenar los ítems de la compra
    for item in purchase_data.items:
        # Verificar si el producto existe
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Buscar o crear el producto en el almacén específico
        warehouse_product = db.query(models.WarehouseProduct).filter(
            models.WarehouseProduct.product_id == item.product_id,
            models.WarehouseProduct.warehouse_id == purchase_data.warehouse_id
        ).first()

        if warehouse_product:
            # Actualizar el stock del producto en el almacén
            warehouse_product.stock += item.quantity
        else:
            # Crear un nuevo registro si no existe en el almacén
            warehouse_product = models.WarehouseProduct(
                product_id=item.product_id,
                warehouse_id=purchase_data.warehouse_id,
                stock=item.quantity
            )
            db.add(warehouse_product)

        # Actualizar la cantidad total del producto
        product.quantity += item.quantity

        # Crear el ítem de la compra
        purchase_item = models.PurchaseItem(
            purchase_id=purchase.id,
            product_id=product.id,
            quantity=item.quantity,
            price_per_unit=product.price,
            total_price=product.price * item.quantity
        )
        db.add(purchase_item)
        purchase_items.append(purchase_item)  # Guardar los ítems creados

        # Registrar el movimiento de inventario
        movement = models.InventoryMovement(
            product_id=product.id,
            quantity=item.quantity,
            movement_type="entrada",  # Entrada de inventario            
        )
        db.add(movement)

    # Commit de las operaciones de los ítems y el movimiento de inventario
    db.commit()

    # Calcular el total de la compra
    total_amount = sum(item.total_price for item in purchase_items)
    purchase.total_amount = total_amount
    db.commit()

    # Crear la respuesta para el cliente
    purchase_response = schemas.Purchase(
        supplier_id=purchase.supplier_id,
        total_amount=purchase.total_amount,
        date=purchase.date,
        warehouse_id=purchase.warehouse_id,
        items=[schemas.PurchaseItem(
            product_id=item.product_id,
            quantity=item.quantity,
            price_per_unit=item.price_per_unit,
            total_price=item.total_price
        ) for item in purchase_items]
    )
    return purchase_response



# Hashear la contraseña
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Crear un nuevo usuario
def create_user(db: Session, username: str, password: str):
    hashed_password = hash_password(password)
    db_user = models.User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Autenticar usuario (verificar si existe y si la contraseña es correcta)
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user