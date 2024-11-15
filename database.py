from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from contextlib import contextmanager
import os

# Configuración de la URL de conexión para MySQL
DATABASE_URL = "mysql+mysqlconnector://root:root@172.200.2.10:3306/erp"


engine = create_engine(DATABASE_URL)

# Crear el tipo base para las clases de modelos
Base = declarative_base()

# Crear una sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Función para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
