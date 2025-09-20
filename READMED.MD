# Sistema ERP - Backend FastAPI

Un sistema de planificación de recursos empresariales (ERP) desarrollado con FastAPI que maneja inventario, ventas, compras y gestión de almacenes.

## 🚀 Características

- **Gestión de Productos**: CRUD completo de productos con categorías
- **Control de Inventario**: Seguimiento de stock por almacén y movimientos de inventario
- **Sistema de Ventas**: Creación de presupuestos, facturas y gestión de clientes
- **Gestión de Compras**: Registro de compras a proveedores con actualización automática de inventario
- **Multi-almacén**: Soporte para múltiples almacenes con stock independiente
- **Autenticación**: Sistema de autenticación JWT para usuarios
- **Base de datos**: Integración con MySQL usando SQLAlchemy ORM
- **Migraciones**: Control de versiones de base de datos con Alembic

## 🛠️ Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para Python
- **MySQL**: Base de datos relacional
- **Alembic**: Herramienta de migración de base de datos
- **Pydantic**: Validación de datos
- **JWT**: Autenticación basada en tokens
- **bcrypt**: Cifrado de contraseñas

## 📋 Requisitos

- Python 3.8+
- MySQL 5.7+
- pip (gestor de paquetes de Python)

## ⚙️ Instalación

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd sistema-erp
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/macOS
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install fastapi uvicorn sqlalchemy mysql-connector-python python-jose[cryptography] passlib[bcrypt] alembic pydantic
```

O usando el archivo de requirements:
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

Actualiza la configuración de la base de datos en los siguientes archivos:

**database.py**
```python
DATABASE_URL = "mysql+mysqlconnector://usuario:contraseña@host:puerto/nombre_bd"
```

**alembic.ini**
```ini
sqlalchemy.url = mysql+mysqlconnector://usuario:contraseña@host:puerto/nombre_bd
```

### 5. Ejecutar migraciones
```bash
alembic upgrade head
```

### 6. Configurar variables de entorno

Actualiza `config.py` con tus configuraciones:
```python
SECRET_KEY = "tu_clave_secreta_super_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

## 🚀 Ejecución

Para iniciar el servidor de desarrollo:

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

## 📚 Documentación de la API

Una vez que el servidor esté en funcionamiento, puedes acceder a:

- **Documentación interactiva (Swagger)**: http://localhost:8000/docs
- **Documentación alternativa (ReDoc)**: http://localhost:8000/redoc

## 🏗️ Estructura del Proyecto

```
├── alembic/                 # Configuración y migraciones de Alembic
│   ├── versions/           # Archivos de migración
│   └── env.py             # Configuración del entorno de Alembic
├── routers/                # Rutas de la API organizadas por módulos
│   ├── products.py        # Endpoints de productos
│   ├── invoices.py        # Endpoints de facturas
│   ├── purchases.py       # Endpoints de compras
│   ├── warehouses.py      # Endpoints de almacenes
│   ├── movements.py       # Endpoints de movimientos
│   └── users.py           # Endpoints de usuarios
├── main.py                 # Archivo principal de la aplicación
├── models.py              # Modelos de SQLAlchemy
├── schemas.py             # Esquemas de Pydantic
├── crud.py                # Operaciones CRUD
├── database.py            # Configuración de base de datos
├── auth.py                # Sistema de autenticación
├── config.py              # Configuraciones de la aplicación
├── alembic.ini            # Configuración de Alembic
└── requirements.txt       # Dependencias del proyecto
```

## 🔑 Autenticación

El sistema utiliza JWT para la autenticación. Para acceder a endpoints protegidos:

1. **Crear usuario**: `POST /users/`
2. **Iniciar sesión**: `POST /login/`
3. **Usar token**: Incluir en headers: `Authorization: Bearer <token>`

## 📊 Principales Endpoints

### Productos
- `GET /products` - Listar productos
- `POST /products` - Crear producto
- `PUT /products/{id}` - Actualizar producto
- `DELETE /products/{id}` - Eliminar producto

### Facturas
- `POST /invoices/` - Crear factura
- `GET /invoices/{id}` - Ver factura
- `PUT /invoice/{id}` - Editar factura
- `DELETE /invoices/{id}` - Eliminar factura

### Compras
- `POST /purchases` - Registrar compra

### Almacenes
- `GET /warehouses` - Listar almacenes
- `POST /warehouses` - Crear almacén

### Gestión de Stock
- `POST /warehouse-products/` - Asignar producto a almacén
- `PUT /warehouse-products/{warehouse_id}/{product_id}` - Actualizar stock

## 🗄️ Modelo de Datos

El sistema maneja las siguientes entidades principales:

- **Products**: Productos del inventario
- **Categories**: Categorías de productos
- **Warehouses**: Almacenes
- **WarehouseProducts**: Stock por almacén
- **Invoices**: Facturas y presupuestos
- **InvoiceItems**: Detalles de facturas
- **Purchases**: Compras a proveedores
- **PurchaseItems**: Detalles de compras
- **InventoryMovements**: Movimientos de inventario
- **Users**: Usuarios del sistema

## 🔄 Flujo de Trabajo

1. **Configurar almacenes** y **categorías**
2. **Crear productos** y asignarlos a categorías
3. **Registrar compras** para aumentar el inventario
4. **Distribuir stock** entre almacenes
5. **Crear facturas** para registrar ventas
6. **Monitorear movimientos** de inventario

## 🐛 Resolución de Problemas

### Error de conexión a la base de datos
- Verificar que MySQL esté ejecutándose
- Comprobar credenciales en `database.py` y `alembic.ini`
- Asegurar que la base de datos existe

### Error de importación
- Verificar que todas las dependencias estén instaladas
- Activar el entorno virtual

### Error de migración
```bash
# Resetear migraciones si es necesario
alembic downgrade base
alembic upgrade head
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ✨ Características Futuras

- [ ] Dashboard web con React/Vue
- [ ] Reportes y analytics
- [ ] Notificaciones de stock bajo
- [ ] Integración con APIs de terceros
- [ ] Sistema de roles y permisos avanzado
- [ ] Backup automático de base de datos
