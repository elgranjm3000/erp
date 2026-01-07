from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import User
from typing import List
from auth import verify_token, check_permission

router = APIRouter()

# ================= WAREHOUSE-PRODUCTS CON FILTRO POR EMPRESA =================

@router.post("/warehouse-products/", response_model=schemas.WarehouseProduct)
def create_or_update_wp(
    wp: schemas.WarehouseProductCreate,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """Crear o actualizar stock de producto en almacén de mi empresa"""
    return crud.create_or_update_warehouse_product_for_company(
        db=db,
        wp_data=wp,
        company_id=current_user.company_id
    )

@router.get("/warehouse-products/", response_model=List[schemas.WarehouseProduct])
def read_all_wp(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Listar todos los registros warehouse-product de mi empresa"""
    return crud.get_warehouse_products_by_company(
        db=db, 
        company_id=current_user.company_id,
        skip=skip, 
        limit=limit
    )

@router.get("/warehouse-products/{warehouse_id}/{product_id}", response_model=schemas.WarehouseProduct)
def read_wp(
    warehouse_id: int, 
    product_id: int, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener stock específico de producto en almacén de mi empresa"""
    wp = crud.get_warehouse_product_by_company(
        db=db, 
        warehouse_id=warehouse_id, 
        product_id=product_id,
        company_id=current_user.company_id
    )
    if not wp:
        raise HTTPException(
            status_code=404, 
            detail="WarehouseProduct not found in your company"
        )
    return wp

@router.put("/warehouse-products/{warehouse_id}/{product_id}", response_model=schemas.WarehouseProduct)
def update_wp_stock(
    warehouse_id: int, 
    product_id: int, 
    stock_update: schemas.WarehouseProductUpdate,
    current_user: User = Depends(check_permission(required_role="user")),
    db: Session = Depends(database.get_db)
):
    """Actualizar stock de producto en almacén de mi empresa"""
    wp = crud.update_warehouse_product_stock_for_company(
        db=db, 
        warehouse_id=warehouse_id, 
        product_id=product_id, 
        stock=stock_update.stock,
        company_id=current_user.company_id
    )
    if not wp:
        raise HTTPException(
            status_code=404, 
            detail="WarehouseProduct not found in your company"
        )
    return wp

@router.delete("/warehouse-products/{warehouse_id}/{product_id}", response_model=schemas.WarehouseProduct)
def delete_wp(
    warehouse_id: int, 
    product_id: int, 
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    """Eliminar registro warehouse-product de mi empresa"""
    wp = crud.delete_warehouse_product_for_company(
        db=db, 
        warehouse_id=warehouse_id, 
        product_id=product_id,
        company_id=current_user.company_id
    )
    if not wp:
        raise HTTPException(
            status_code=404, 
            detail="WarehouseProduct not found in your company"
        )
    return wp

# ================= ENDPOINTS ESPECÍFICOS =================

@router.get("/warehouse-products/warehouse/{warehouse_id}", response_model=List[schemas.WarehouseProduct])
def get_products_by_warehouse(
    warehouse_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener todos los productos de un almacén específico de mi empresa"""
    return crud.get_warehouse_products_by_warehouse_and_company(
        db=db,
        warehouse_id=warehouse_id,
        company_id=current_user.company_id
    )

@router.get("/warehouse-products/product/{product_id}", response_model=List[schemas.WarehouseProduct])
def get_warehouses_by_product(
    product_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener stock de un producto en todos los almacenes de mi empresa"""
    return crud.get_warehouse_products_by_product_and_company(
        db=db,
        product_id=product_id,
        company_id=current_user.company_id
    )

@router.get("/warehouse-products/low-stock")
def get_low_stock_all_warehouses(
    threshold: int = 10,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener productos con stock bajo en todos los almacenes de mi empresa"""
    return crud.get_low_stock_warehouse_products_by_company(
        db=db,
        company_id=current_user.company_id,
        threshold=threshold
    )

@router.post("/warehouse-products/transfer")
def transfer_stock(
    transfer: schemas.StockTransferCreate,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    """Transferir stock entre almacenes de mi empresa"""
    return crud.transfer_stock_between_warehouses(
        db=db,
        from_warehouse_id=transfer.from_warehouse_id,
        to_warehouse_id=transfer.to_warehouse_id,
        product_id=transfer.product_id,
        quantity=transfer.quantity,
        company_id=current_user.company_id
    )

@router.post("/warehouse-products/adjust-stock")
def adjust_stock(
    adjustment: schemas.StockAdjustmentCreate,
    current_user: User = Depends(check_permission(required_role="manager")),
    db: Session = Depends(database.get_db)
):
    """Ajustar stock por diferencias de inventario"""
    return crud.adjust_warehouse_product_stock(
        db=db,
        warehouse_id=adjustment.warehouse_id,
        product_id=adjustment.product_id,
        adjustment=adjustment.adjustment,
        reason=adjustment.reason,
        company_id=current_user.company_id
    )