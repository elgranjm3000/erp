from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import database
from models import User
from typing import List
from auth import verify_token, check_permission

router = APIRouter()

# ================= CLIENTES CON FILTRO POR EMPRESA =================

@router.get("/customers", response_model=List[schemas.Customer])
def read_customers(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Listar clientes de mi empresa"""
    return crud.get_customers_by_company(
        db=db, 
        company_id=current_user.company_id,
        skip=skip, 
        limit=limit
    )

@router.get("/customers/{customer_id}", response_model=schemas.Customer)
def read_customer(
    customer_id: int, 
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener cliente específico de mi empresa"""
    return crud.get_customer_by_id_and_company(
        db=db, 
        customer_id=customer_id, 
        company_id=current_user.company_id
    )

@router.post("/customers", response_model=schemas.Customer)
def create_customer(
    customer: schemas.CustomerCreate, 
    current_user: User = Depends(check_permission(role="user")),
    db: Session = Depends(database.get_db)
):
    """Crear cliente en mi empresa"""
    return crud.create_customer_for_company(
        db=db, 
        customer=customer, 
        company_id=current_user.company_id
    )

@router.put("/customers/{customer_id}", response_model=schemas.Customer)
def update_customer(
    customer_id: int, 
    customer_data: schemas.CustomerUpdate, 
    current_user: User = Depends(check_permission(role="user")),
    db: Session = Depends(database.get_db)
):
    """Actualizar cliente de mi empresa"""
    return crud.update_customer_for_company(
        db=db, 
        customer_id=customer_id, 
        customer_data=customer_data,
        company_id=current_user.company_id
    )

@router.delete("/customers/{customer_id}")
def delete_customer(
    customer_id: int, 
    current_user: User = Depends(check_permission(role="manager")),
    db: Session = Depends(database.get_db)
):
    """Eliminar cliente de mi empresa"""
    return crud.delete_customer_for_company(
        db=db, 
        customer_id=customer_id,
        company_id=current_user.company_id
    )

# ================= ENDPOINTS ESPECÍFICOS =================

@router.get("/customers/{customer_id}/invoices", response_model=List[schemas.Invoice])
def get_customer_invoices(
    customer_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener facturas de un cliente específico"""
    # Verificar que el cliente pertenezca a la empresa
    customer = crud.get_customer_by_id_and_company(
        db=db, 
        customer_id=customer_id, 
        company_id=current_user.company_id
    )
    
    if not customer:
        raise HTTPException(
            status_code=404, 
            detail="Customer not found in your company"
        )
    
    return crud.get_invoices_by_customer_and_company(
        db=db,
        customer_id=customer_id,
        company_id=current_user.company_id
    )

@router.get("/customers/search", response_model=List[schemas.Customer])
def search_customers(
    q: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Buscar clientes por nombre o email en mi empresa"""
    return crud.search_customers_by_company(
        db=db,
        company_id=current_user.company_id,
        search_term=q
    )

@router.get("/customers/stats/summary")
def get_customers_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Resumen estadístico de clientes de mi empresa"""
    return crud.get_customers_stats_by_company(
        db=db,
        company_id=current_user.company_id
    )

@router.get("/customers/top-by-sales")
def get_top_customers(
    limit: int = 10,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener top clientes por volumen de ventas"""
    return crud.get_top_customers_by_sales(
        db=db,
        company_id=current_user.company_id,
        limit=limit
    )

@router.get("/customers/{customer_id}/balance")
def get_customer_balance(
    customer_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(database.get_db)
):
    """Obtener balance de cuenta de un cliente"""
    # Verificar que el cliente pertenezca a la empresa
    customer = crud.get_customer_by_id_and_company(
        db=db, 
        customer_id=customer_id, 
        company_id=current_user.company_id
    )
    
    if not customer:
        raise HTTPException(
            status_code=404, 
            detail="Customer not found in your company"
        )
    
    return crud.get_customer_balance(
        db=db,
        customer_id=customer_id,
        company_id=current_user.company_id
    )