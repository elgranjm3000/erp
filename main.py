from fastapi import FastAPI, Depends, HTTPException,status
from sqlalchemy.orm import Session
from routers import products, movements,warehouses,users


# Crear la aplicación FastAPI
app = FastAPI()


app.include_router(users.router)
app.include_router(products.router)
app.include_router(movements.router)
app.include_router(warehouses.router)





# Crear las tablas en la base de datos
"""models.Base.metadata.create_all(bind=database.engine)

# Ruta para obtener productos
@app.get("/products/", response_model=list[schemas.Product])
def read_products(skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products

# Ruta para obtener un producto específico
@app.get("/products/{product_id}", response_model=schemas.Product)
def read_product(product_id: int, db: Session = Depends(database.get_db)):
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

# Ruta para crear un producto
@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(database.get_db)):
    return crud.create_product(db=db, product=product)
"""


"""

Product.quantity	Total del producto en todos los almacenes	Ver el total disponible en inventario
WarehouseProduct.stock	Cantidad del producto en un almacén específico	Distribución del inventario por almacén
InventoryMovement.quantity	Cantidad de unidades movidas en una transacción	Registro de entrada/salida del inventario

"""