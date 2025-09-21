from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import models
import schemas
from passlib.context import CryptContext
from fastapi import HTTPException
from datetime import datetime, timedelta
from auth import hash_password, create_access_token
from config import ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ================= FUNCIONES LEGACY (MANTENER PARA COMPATIBILIDAD) =================

def create_budget(db: Session, budget_data: schemas.Invoice):
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
    budget = db.query(models.Invoice).filter(models.Invoice.id == budget_id, models.Invoice.status == 'presupuesto').first()
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
    return create_invoice_for_company(db, invoice_data, 1)

def view_invoice(db: Session, invoice_id: int):
    return view_invoice_by_company(db, invoice_id, 1)

def edit_invoice(db: Session, invoice_id: int, invoice_data: schemas.Invoice):
    return edit_invoice_for_company(db, invoice_id, invoice_data, 1)

def delete_invoice(db: Session, invoice_id: int):
    return delete_invoice_for_company(db, invoice_id, 1)

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

def create_or_update_warehouse_product(db: Session, wp_data: schemas.WarehouseProductCreate):
    wp = db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == wp_data.warehouse_id,
        models.WarehouseProduct.product_id == wp_data.product_id,
    ).first()

    if wp:
        wp.stock = wp_data.stock
    else:
        wp = models.WarehouseProduct(**wp_data.dict())
        db.add(wp)

    db.commit()
    db.refresh(wp)
    return wp

def get_warehouse_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.WarehouseProduct).offset(skip).limit(limit).all()

def get_warehouse_product(db: Session, warehouse_id: int, product_id: int):
    return db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id,
        models.WarehouseProduct.product_id == product_id,
    ).first()

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

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def create_inventory_movement(db: Session, movement: schemas.InventoryMovementCreate):
    db_movement = models.InventoryMovement(**movement.dict())
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement

def get_warehouses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Warehouse).offset(skip).limit(limit).all()

def create_warehouse(db: Session, warehouse: schemas.WarehouseCreate):
    db_warehouse = models.Warehouse(**warehouse.dict())
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

def create_purchase(db: Session, purchase_data: schemas.Purchase):
    return create_purchase_for_company(db, purchase_data, 1)

def create_user(db: Session, username: str, password: str):
    hashed_password = hash_password(password)
    
    default_company = db.query(models.Company).filter(models.Company.id == 1).first()
    if not default_company:
        default_company = models.Company(
            name="Empresa Principal",
            legal_name="Empresa Principal C.A.",
            tax_id="DEFAULT-001",
            currency="USD",
            timezone="UTC",
            invoice_prefix="INV"
        )
        db.add(default_company)
        db.commit()
        db.refresh(default_company)
    
    db_user = models.User(
        username=username, 
        hashed_password=hashed_password,
        company_id=1,
        email=f"{username}@empresa.local",
        role="admin",
        is_company_admin=True,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

# ================= FUNCIONES MULTIEMPRESA =================

def create_company_with_admin(db: Session, company_data: schemas.CompanyCreate):
    existing_company = db.query(models.Company).filter(
        models.Company.tax_id == company_data.tax_id.upper()
    ).first()
    
    if existing_company:
        raise HTTPException(
            status_code=400,
            detail="Company with this tax ID already exists"
        )
    
    try:
        db_company = models.Company(
            name=company_data.name,
            legal_name=company_data.legal_name,
            tax_id=company_data.tax_id.upper(),
            email=company_data.email,
            phone=company_data.phone,
            address=company_data.address,
            currency=company_data.currency,
            timezone=company_data.timezone,
            invoice_prefix=company_data.invoice_prefix
        )
        
        db.add(db_company)
        db.flush()
        
        admin_user = models.User(
            username=company_data.admin_username,
            email=company_data.admin_email,
            hashed_password=hash_password(company_data.admin_password),
            company_id=db_company.id,
            role="admin",
            is_company_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(db_company)
        
        return db_company
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

def get_company_dashboard(db: Session, company_id: int):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    
    total_products = db.query(models.Product).filter(models.Product.company_id == company_id).count()
    total_customers = db.query(models.Customer).filter(models.Customer.company_id == company_id).count()
    total_warehouses = db.query(models.Warehouse).filter(models.Warehouse.company_id == company_id).count()
    
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_sales = db.query(func.sum(models.Invoice.total_amount)).filter(
        and_(
            models.Invoice.company_id == company_id,
            models.Invoice.status == "factura",
            models.Invoice.date >= start_of_month
        )
    ).scalar() or 0.0
    
    pending_invoices = db.query(models.Invoice).filter(
        and_(
            models.Invoice.company_id == company_id,
            models.Invoice.status == "presupuesto"
        )
    ).count()
    
    low_stock_products = db.query(models.Product).filter(
        and_(
            models.Product.company_id == company_id,
            models.Product.quantity <= 10
        )
    ).count()
    
    return schemas.CompanyDashboard(
        company=company,
        total_products=total_products,
        total_customers=total_customers,
        total_warehouses=total_warehouses,
        monthly_sales=monthly_sales,
        pending_invoices=pending_invoices,
        low_stock_products=low_stock_products
    )

def get_products_by_company(db: Session, company_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Product).filter(
        models.Product.company_id == company_id
    ).offset(skip).limit(limit).all()

def get_product_by_id_and_company(db: Session, product_id: int, company_id: int):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.company_id == company_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in your company")
    return product

def create_product_for_company(db: Session, product: schemas.ProductCreate, company_id: int):
    if not product.sku:
        count = db.query(models.Product).filter(models.Product.company_id == company_id).count()
        product.sku = f"PRD-{count + 1:06d}"
    
    existing_sku = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.sku == product.sku
    ).first()
    
    if existing_sku:
        raise HTTPException(status_code=400, detail="SKU already exists in this company")
    
    db_product = models.Product(
        company_id=company_id,
        **product.dict()
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product_for_company(db: Session, product_id: int, product_data: schemas.ProductUpdate, company_id: int):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.company_id == company_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in your company")
    
    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

def delete_product_for_company(db: Session, product_id: int, company_id: int):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.company_id == company_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in your company")
    
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted successfully"}

def create_invoice_for_company(db: Session, invoice_data, company_id: int):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    invoice_number = f"{company.invoice_prefix}-{company.next_invoice_number:06d}"
    
    try:
        invoice = models.Invoice(
            company_id=company_id,
            customer_id=invoice_data.customer_id,
            warehouse_id=invoice_data.warehouse_id,
            invoice_number=invoice_number,
            status=invoice_data.status,
            discount=invoice_data.discount,
            total_amount=0
        )
        
        db.add(invoice)
        db.flush()
        
        total_amount = 0
        company.next_invoice_number += 1
        
        invoice.total_amount = total_amount
        db.commit()
        db.refresh(invoice)
        
        return invoice
        
    except Exception as e:
        db.rollback()
        raise

def view_invoice_by_company(db: Session, invoice_id: int, company_id: int):
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.company_id == company_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found in your company")
    
    return invoice

def edit_invoice_for_company(db: Session, invoice_id: int, invoice_data, company_id: int):
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.company_id == company_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found in your company")
    
    for key, value in invoice_data.dict(exclude_unset=True).items():
        if hasattr(invoice, key):
            setattr(invoice, key, value)
    
    db.commit()
    db.refresh(invoice)
    return invoice

def delete_invoice_for_company(db: Session, invoice_id: int, company_id: int):
    invoice = db.query(models.Invoice).filter(
        models.Invoice.id == invoice_id,
        models.Invoice.company_id == company_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found in your company")
    
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted successfully"}

def create_purchase_for_company(db: Session, purchase_data, company_id: int):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    purchase_count = db.query(models.Purchase).filter(models.Purchase.company_id == company_id).count()
    purchase_number = f"PUR-{purchase_count + 1:06d}"
    
    try:
        purchase = models.Purchase(
            company_id=company_id,
            supplier_id=purchase_data.supplier_id,
            warehouse_id=purchase_data.warehouse_id,
            purchase_number=purchase_number,
            date=purchase_data.date,
            total_amount=0
        )
        
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        
        return purchase
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

def get_warehouses_by_company(db: Session, company_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Warehouse).filter(
        models.Warehouse.company_id == company_id
    ).offset(skip).limit(limit).all()

def get_warehouse_by_id_and_company(db: Session, warehouse_id: int, company_id: int):
    warehouse = db.query(models.Warehouse).filter(
        models.Warehouse.id == warehouse_id,
        models.Warehouse.company_id == company_id
    ).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found in your company")
    return warehouse

def create_warehouse_for_company(db: Session, warehouse: schemas.WarehouseCreate, company_id: int):
    db_warehouse = models.Warehouse(
        company_id=company_id,
        **warehouse.dict()
    )
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

def create_or_update_warehouse_product_for_company(db: Session, wp_data: schemas.WarehouseProductCreate, company_id: int):
    warehouse = get_warehouse_by_id_and_company(db, wp_data.warehouse_id, company_id)
    product = get_product_by_id_and_company(db, wp_data.product_id, company_id)
    
    return create_or_update_warehouse_product(db, wp_data)

def get_warehouse_products_by_company(db: Session, company_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.WarehouseProduct).join(
        models.Warehouse, models.WarehouseProduct.warehouse_id == models.Warehouse.id
    ).filter(
        models.Warehouse.company_id == company_id
    ).offset(skip).limit(limit).all()

def get_warehouse_product_by_company(db: Session, warehouse_id: int, product_id: int, company_id: int):
    get_warehouse_by_id_and_company(db, warehouse_id, company_id)
    get_product_by_id_and_company(db, product_id, company_id)
    
    return get_warehouse_product(db, warehouse_id, product_id)

def update_warehouse_product_stock_for_company(db: Session, warehouse_id: int, product_id: int, stock: int, company_id: int):
    get_warehouse_by_id_and_company(db, warehouse_id, company_id)
    get_product_by_id_and_company(db, product_id, company_id)
    
    return update_warehouse_product_stock(db, warehouse_id, product_id, stock)

def delete_warehouse_product_for_company(db: Session, warehouse_id: int, product_id: int, company_id: int):
    get_warehouse_by_id_and_company(db, warehouse_id, company_id)
    get_product_by_id_and_company(db, product_id, company_id)
    
    return delete_warehouse_product(db, warehouse_id, product_id)

def get_company_users(db: Session, company_id: int):
    return db.query(models.User).filter(
        models.User.company_id == company_id
    ).all()

def create_user_for_company(db: Session, user_data: schemas.UserCreateForCompany, company_id: int):
    existing_user = db.query(models.User).filter(
        models.User.username == user_data.username,
        models.User.company_id == company_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists in this company"
        )
    
    hashed_password = hash_password(user_data.password)
    
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        company_id=company_id,
        role=user_data.role,
        is_company_admin=user_data.is_company_admin
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_company_user(db: Session, user_id: int, company_id: int, user_update: schemas.UserUpdate):
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.company_id == company_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found in this company")
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

def deactivate_company_user(db: Session, user_id: int, company_id: int):
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.company_id == company_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found in this company")
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}

def authenticate_multicompany(db: Session, login_data: schemas.LoginRequest):
    if not login_data.company_tax_id:
        user = db.query(models.User).filter(
            models.User.username == login_data.username,
            models.User.is_active == True
        ).first()
    else:
        user = db.query(models.User).join(models.Company).filter(
            models.User.username == login_data.username,
            models.Company.tax_id == login_data.company_tax_id.upper(),
            models.User.is_active == True
        ).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials or company",
        )
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "company_id": user.company_id,
            "role": user.role,
            "is_company_admin": user.is_company_admin
        },
        expires_delta=access_token_expires
    )
    
    return schemas.LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserWithCompany(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            company_id=user.company_id,
            is_active=user.is_active,
            is_company_admin=user.is_company_admin,
            created_at=user.created_at,
            last_login=user.last_login,
            company=user.company
        )
    )

def register_company_and_login(db: Session, company_data: schemas.CompanyCreate):
    company = create_company_with_admin(db, company_data)
    
    admin_user = db.query(models.User).filter(
        models.User.company_id == company.id,
        models.User.is_company_admin == True
    ).first()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": admin_user.username,
            "company_id": admin_user.company_id,
            "role": admin_user.role,
            "is_company_admin": admin_user.is_company_admin
        },
        expires_delta=access_token_expires
    )
    
    return schemas.LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserWithCompany(
            id=admin_user.id,
            username=admin_user.username,
            email=admin_user.email,
            role=admin_user.role,
            company_id=admin_user.company_id,
            is_active=admin_user.is_active,
            is_company_admin=admin_user.is_company_admin,
            created_at=admin_user.created_at,
            last_login=admin_user.last_login,
            company=company
        )
    )

def get_company_settings(db: Session, company_id: int):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return schemas.CompanySettings(
        currency=company.currency,
        timezone=company.timezone,
        date_format=company.date_format,
        invoice_prefix=company.invoice_prefix,
        next_invoice_number=company.next_invoice_number,
        low_stock_threshold=10,
        auto_increment_invoice=True,
        require_customer_tax_id=False
    )

def update_company_settings(db: Session, company_id: int, settings: schemas.CompanySettings):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.currency = settings.currency
    company.timezone = settings.timezone
    company.date_format = settings.date_format
    company.invoice_prefix = settings.invoice_prefix
    company.next_invoice_number = settings.next_invoice_number
    
    db.commit()
    db.refresh(company)
    
    return settings

def update_company(db: Session, company_id: int, company_update: schemas.CompanyUpdate):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = company_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    company.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(company)
    
    return company

def search_products_by_company(db: Session, company_id: int, search_term: str):
    return db.query(models.Product).filter(
        models.Product.company_id == company_id,
        (models.Product.name.ilike(f"%{search_term}%") | 
         models.Product.sku.ilike(f"%{search_term}%"))
    ).all()

def get_low_stock_products(db: Session, company_id: int, threshold: int = 10):
    return db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity <= threshold
    ).all()

def get_products_by_category_and_company(db: Session, company_id: int, category_id: int):
    return db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.category_id == category_id
    ).all()

def get_products_stats_by_company(db: Session, company_id: int):
    total_products = db.query(models.Product).filter(models.Product.company_id == company_id).count()
    
    total_value = db.query(func.sum(models.Product.price * models.Product.quantity)).filter(
        models.Product.company_id == company_id
    ).scalar() or 0
    
    low_stock_count = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity <= 10
    ).count()
    
    out_of_stock_count = db.query(models.Product).filter(
        models.Product.company_id == company_id,
        models.Product.quantity == 0
    ).count()
    
    categories_count = db.query(models.Category).filter(
        models.Category.company_id == company_id
    ).count()
    
    return {
        "total_products": total_products,
        "total_value": total_value,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "categories_count": categories_count
    }

def bulk_update_products_for_company(db: Session, company_id: int, updates):
    results = []
    
    for update in updates:
        product = db.query(models.Product).filter(
            models.Product.id == update.product_id,
            models.Product.company_id == company_id
        ).first()
        
        if product:
            if update.price is not None:
                product.price = update.price
            if update.quantity is not None:
                product.quantity = update.quantity
            results.append(product)
    
    db.commit()
    return {"updated_products": len(results), "message": "Bulk update completed"}

def get_warehouses_stats_by_company(db: Session, company_id: int):
    total_warehouses = db.query(models.Warehouse).filter(
        models.Warehouse.company_id == company_id
    ).count()
    
    return {"total_warehouses": total_warehouses}

def update_warehouse_for_company(db: Session, warehouse_id: int, warehouse_data, company_id: int):
    warehouse = get_warehouse_by_id_and_company(db, warehouse_id, company_id)
    
    for key, value in warehouse_data.dict(exclude_unset=True).items():
        setattr(warehouse, key, value)
    
    db.commit()
    db.refresh(warehouse)
    return warehouse

def delete_warehouse_for_company(db: Session, warehouse_id: int, company_id: int):
    warehouse = get_warehouse_by_id_and_company(db, warehouse_id, company_id)
    
    products_count = db.query(models.WarehouseProduct).filter(
        models.WarehouseProduct.warehouse_id == warehouse_id
    ).count()
    
    if products_count > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete warehouse with assigned products"
        )
    
    db.delete(warehouse)
    db.commit()
    return {"message": "Warehouse deleted successfully"}

def create_inventory_movement_for_company(db: Session, movement, company_id: int):
    get_product_by_id_and_company(db, movement.product_id, company_id)
    return create_inventory_movement(db, movement)

def get_inventory_movements_by_company(db: Session, company_id: int, skip: int = 0, limit: int = 100, movement_type: str = None, product_id: int = None):
    query = db.query(models.InventoryMovement).join(
        models.Product, models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.Product.company_id == company_id
    )
    
    if movement_type:
        query = query.filter(models.InventoryMovement.movement_type == movement_type)
    
    if product_id:
        query = query.filter(models.InventoryMovement.product_id == product_id)
    
    return query.offset(skip).limit(limit).all()

def get_inventory_movement_by_id_and_company(db: Session, movement_id: int, company_id: int):
    movement = db.query(models.InventoryMovement).join(
        models.Product, models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.InventoryMovement.id == movement_id,
        models.Product.company_id == company_id
    ).first()
    
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found in your company")
    
    return movement

def get_inventory_movements_by_product_and_company(db: Session, product_id: int, company_id: int):
    return db.query(models.InventoryMovement).join(
        models.Product, models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.InventoryMovement.product_id == product_id,
        models.Product.company_id == company_id
    ).all()

def get_inventory_movements_by_invoice(db: Session, invoice_id: int):
    return db.query(models.InventoryMovement).filter(
        models.InventoryMovement.invoice_id == invoice_id
    ).all()

def get_inventory_movements_stats_by_company(db: Session, company_id: int):
    total_movements = db.query(models.InventoryMovement).join(
        models.Product, models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.Product.company_id == company_id
    ).count()
    
    return {"total_movements": total_movements}

def get_movements_stats_by_type_and_company(db: Session, company_id: int):
    movements_by_type = db.query(
        models.InventoryMovement.movement_type,
        func.count(models.InventoryMovement.id)
    ).join(
        models.Product, models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.Product.company_id == company_id
    ).group_by(models.InventoryMovement.movement_type).all()
    
    return {movement_type: count for movement_type, count in movements_by_type}

def get_recent_inventory_movements_by_company(db: Session, company_id: int, days: int = 7, limit: int = 50):
    cutoff_date = datetime.now() - timedelta(days=days)
    
    return db.query(models.InventoryMovement).join(
        models.Product, models.InventoryMovement.product_id == models.Product.id
    ).filter(
        models.Product.company_id == company_id,
        models.InventoryMovement.timestamp >= cutoff_date
    ).order_by(models.InventoryMovement.timestamp.desc()).limit(limit).all()

# Funciones adicionales que pueden ser necesarias para los routers

def get_invoices_by_company(db: Session, company_id: int, skip: int = 0, limit: int = 100, status: str = None):
    query = db.query(models.Invoice).filter(models.Invoice.company_id == company_id)
    
    if status:
        query = query.filter(models.Invoice.status == status)
    
    return query.offset(skip).limit(limit).all()

def get_purchases_by_company(db: Session, company_id: int, skip: int = 0, limit: int = 100, status: str = None):
    query = db.query(models.Purchase).filter(models.Purchase.company_id == company_id)
    
    if status:
        query = query.filter(models.Purchase.status == status)
    
    return query.offset(skip).limit(limit).all()

def get_purchase_by_id_and_company(db: Session, purchase_id: int, company_id: int):
    purchase = db.query(models.Purchase).filter(
        models.Purchase.id == purchase_id,
        models.Purchase.company_id == company_id
    ).first()
    
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found in your company")
    
    return purchase

def update_purchase_for_company(db: Session, purchase_id: int, purchase_data, company_id: int):
    purchase = get_purchase_by_id_and_company(db, purchase_id, company_id)
    
    for key, value in purchase_data.dict(exclude_unset=True).items():
        if hasattr(purchase, key):
            setattr(purchase, key, value)
    
    db.commit()
    db.refresh(purchase)
    return purchase

def delete_purchase_for_company(db: Session, purchase_id: int, company_id: int):
    purchase = get_purchase_by_id_and_company(db, purchase_id, company_id)
    
    db.delete(purchase)
    db.commit()
    return {"message": "Purchase deleted successfully"}

def update_purchase_status_for_company(db: Session, purchase_id: int, status: str, company_id: int):
    purchase = get_purchase_by_id_and_company(db, purchase_id, company_id)
    
    purchase.status = status
    db.commit()
    db.refresh(purchase)
    
    return purchase

def get_purchases_stats_by_company(db: Session, company_id: int):
    total_purchases = db.query(models.Purchase).filter(
        models.Purchase.company_id == company_id
    ).count()
    
    total_amount = db.query(func.sum(models.Purchase.total_amount)).filter(
        models.Purchase.company_id == company_id
    ).scalar() or 0
    
    return {
        "total_purchases": total_purchases,
        "total_amount": total_amount
    }

def get_invoices_stats_by_company(db: Session, company_id: int):
    total_invoices = db.query(models.Invoice).filter(
        models.Invoice.company_id == company_id
    ).count()
    
    total_amount = db.query(func.sum(models.Invoice.total_amount)).filter(
        models.Invoice.company_id == company_id,
        models.Invoice.status == "factura"
    ).scalar() or 0
    
    return {
        "total_invoices": total_invoices,
        "total_amount": total_amount
    }

def update_user_profile(db: Session, user_id: int, user_update: schemas.UserUpdate, company_id: int):
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.company_id == company_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user