from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import InventoryMovement, User
from typing import List
from schemas import InventoryMovement as InventoryMovementSchema
from auth import verify_token, check_permission

router = APIRouter()

# ================= PRODUCTOS CON FILTRO POR EMPRESA =================

@router.get("/products", response_model=List[schemas.Product])
def read_products(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Listar productos de mi empresa"""
    return crud.get_products_by_company(
        db=db, 
        company_id=current_user.company_id,
        skip=skip, 
        limit=limit
    )

@router.get("/products/{product_id}", response_model=schemas.Product)
def read_product(
    product_id: int, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener producto específico de mi empresa"""
    return crud.get_product_by_id_and_company(
        db=db, 
        product_id=product_id, 
        company_id=current_user.company_id
    )

@router.post("/products", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,     
    current_user: User = Depends(check_permission(required_role="user")),

    db: Session = Depends(database.get_db)
):
    """Crear producto en mi empresa"""
    return crud.create_product_for_company(
        db=db, 
        product=product, 
        company_id=current_user.company_id
    )

@router.put("/products/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int, 
    product_data: schemas.ProductUpdate,     
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """Actualizar producto de mi empresa"""
    return crud.update_product_for_company(
        db=db, 
        product_id=product_id, 
        product_data=product_data,
        company_id=current_user.company_id
    )

@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,     
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    """Eliminar producto de mi empresa"""
    return crud.delete_product_for_company(
        db=db, 
        product_id=product_id,
        company_id=current_user.company_id
    )

@router.get("/products/{product_id}/inventory_movements", response_model=List[InventoryMovementSchema])
def get_inventory_movements_by_product(
    product_id: int, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener movimientos de inventario de un producto de mi empresa"""
    
    # Verificar que el producto pertenezca a la empresa
    product = crud.get_product_by_id_and_company(
        db=db, 
        product_id=product_id, 
        company_id=current_user.company_id
    )
    
    if not product:
        raise HTTPException(
            status_code=404, 
            detail="Product not found in your company"
        )
    
    movements = db.query(InventoryMovement).filter(
        InventoryMovement.product_id == product_id
    ).all()

    return movements

# ================= ENDPOINTS ESPECÍFICOS DE EMPRESA =================

@router.get("/products/low-stock", response_model=List[schemas.Product])
def get_low_stock_products(
    threshold: int = 10,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener productos con stock bajo en mi empresa"""
    return crud.get_low_stock_products(
        db=db,
        company_id=current_user.company_id,
        threshold=threshold
    )

@router.get("/products/search", response_model=List[schemas.Product])
def search_products(
    q: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Buscar productos por nombre o SKU en mi empresa"""
    return crud.search_products_by_company(
        db=db,
        company_id=current_user.company_id,
        search_term=q
    )

@router.get("/products/category/{category_id}", response_model=List[schemas.Product])
def get_products_by_category(
    category_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener productos por categoría en mi empresa"""
    return crud.get_products_by_category_and_company(
        db=db,
        company_id=current_user.company_id,
        category_id=category_id
    )

@router.post("/products/bulk-update")
def bulk_update_products(
    updates: List[schemas.ProductBulkUpdate],    
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    """Actualización masiva de productos"""
    return crud.bulk_update_products_for_company(
        db=db,
        company_id=current_user.company_id,
        updates=updates
    )

@router.get("/products/stats/summary")
def get_products_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Resumen estadístico de productos de mi empresa"""
    return crud.get_products_stats_by_company(
        db=db,
        company_id=current_user.company_id
    )