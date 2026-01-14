# Sistema ERP - Backend FastAPI 🇻🇪

Sistema de planificación de recursos empresariales (ERP) desarrollado con FastAPI, **con cumplimiento completo de la normativa fiscal SENIAT de Venezuela**.

## 🚀 Características

### Gestión Empresarial
- **Multi-empresa**: Soporte multi-tenant con aislamiento completo de datos
- **Gestión de Productos**: CRUD completo con categorías jerárquicas
- **Control de Inventario**: Seguimiento de stock por almacén y movimientos de inventario
- **Sistema de Ventas**: Presupuestos, facturas y gestión de clientes
  - Actualización automática de stock en almacenes al crear facturas
  - Revertido de stock al editar facturas confirmadas
- **Gestión de Compras**: Registro de compras a proveedores con actualización automática de inventario
  - Actualización automática de stock al recibir compras
  - Revertido de stock al cambiar estado de compras
- **Multi-almacén**: Soporte para múltiples almacenes con stock independiente
  - Consulta de productos por almacén
  - Transferencia de stock entre almacenes
  - Ajustes de stock en almacenes
- **Gestión de Categorías**: Organización de productos en categorías jerárquicas
- **Autenticación**: Sistema de autenticación JWT para usuarios
- **Base de datos**: Integración con MySQL usando SQLAlchemy ORM
- **Migraciones**: Control de versiones de base de datos con Alembic

### 🇻🇪 Cumplimiento Fiscal Venezuela (SENIAT)

**Soporte completo para facturación electrónica según normativa venezolana:**

- **✅ IVA (Impuesto al Valor Agregado)**
  - Tasas oficiales: 16% (general), 8% (reducida), 0% (exento)
  - Base imponible y monto exento separados
  - Items exentos individuales por producto
  - Cálculo automático de IVA por item

- **✅ Retención de IVA**
  - Umbrales oficiales en VES: >200 VES (75%), >300 VES (100%)
  - Conversión automática USD→VES con tasa de cambio configurable
  - Verificación de agente de retención
  - Porcentaje configurable por empresa

- **✅ Retención de ISLR (Impuesto Sobre la Renta)**
  - Umbrales progresivos: >5k VES (1%), >10k VES (2%), >20k VES (3%)
  - Conversión automática de moneda
  - Verificación de agente de retención ISLR

- **✅ Timado Fiscal**
  - 1% del total de la factura
  - Cálculo automático

- **✅ Numeración Fiscal**
  - Número de factura (independiente por empresa)
  - **Número de control SENIAT** (obligatorio según normativa)
  - Prefijos configurables

- **✅ RIF Venezolano**
  - Validación con **dígito verificador** (algoritmo SENIAT)
  - Soporta: J (empresas), V (venezolanos), E (extranjeros), G (gobierno)
  - Formateo automático (J-12345678-9)
  - Validación obligatoria según monto de factura

- **✅ Información Fiscal Completa**
  - Tipo de transacción: contado/crédito
  - Método de pago: efectivo, transferencia, zelle, pago móvil, etc.
  - Días de crédito
  - Dirección fiscal del cliente
  - Teléfono de contacto

- **✅ Notas de Crédito/Débito**
  - Referencia a factura original
  - Número de control original
  - Motivo de la nota

**📖 Documentación completa:** [VENEZUELA_TAX_COMPLIANCE.md](VENEZUELA_TAX_COMPLIANCE.md)

## 🛠️ Tecnologías

- **FastAPI 0.128.0**: Framework web moderno y rápido
- **Pydantic 2.12.5**: Validación de datos con typing
- **SQLAlchemy 2.0**: ORM para Python
- **MySQL**: Base de datos relacional
- **Alembic**: Herramienta de migración de base de datos
- **JWT**: Autenticación basada en tokens
- **bcrypt**: Cifrado de contraseñas

## 📝 Changelog y Mejoras Recientes

### ✅ Enero 2026 - Mejora en Detalle de Facturas
**Corrección importante**: Los items de las facturas ahora incluyen información completa del producto.

**Antes:**
```json
{
  "id": 1,
  "product_id": 6,
  "quantity": 1,
  "price_per_unit": 300.0,
  "total_price": 300.0
}
```

**Ahora:**
```json
{
  "id": 1,
  "product_id": 6,
  "product_name": "lismarys",           ✅ NUEVO
  "product_description": "aaa",         ✅ NUEVO
  "product_sku": "PROD-865126-458",     ✅ NUEVO
  "quantity": 1,
  "price_per_unit": 300.0,
  "total_price": 300.0,
  "tax_rate": 16.0,
  "tax_amount": 48.0,
  "is_exempt": false
}
```

**Archivos modificados:**
- `schemas.py` - Agregados campos `product_name`, `product_description`, `product_sku` a `InvoiceItem`
- `crud/invoices.py` - Actualizadas funciones `view_invoice_by_company` y `get_invoices_by_company` para incluir detalles de productos

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
├── alembic/                      # Configuración y migraciones de Alembic
│   ├── versions/                # Archivos de migración
│   └── env.py                   # Configuración del entorno de Alembic
├── routers/                     # Rutas de la API organizadas por módulos
│   ├── products.py              # Endpoints de productos
│   ├── invoices.py              # Endpoints de facturas
│   ├── purchases.py             # Endpoints de compras
│   ├── warehouses.py            # Endpoints de almacenes
│   ├── warehousesproducts.py    # Endpoints de productos por almacén
│   ├── categories.py            # Endpoints de categorías
│   ├── customers.py             # Endpoints de clientes
│   ├── suppliers.py             # Endpoints de proveedores
│   ├── companies.py             # Endpoints de empresas
│   ├── movements.py             # Endpoints de movimientos
│   └── users.py                 # Endpoints de usuarios y autenticación
├── crud/                        # Operaciones CRUD de base de datos
│   ├── base.py                  # Funciones base y utilidades
│   ├── products.py              # CRUD de productos
│   ├── invoices.py              # CRUD de facturas
│   ├── purchases.py             # CRUD de compras
│   ├── warehouses.py            # CRUD de almacenes
│   ├── warehousesproducts.py    # CRUD de productos por almacén
│   ├── categories.py            # CRUD de categorías
│   ├── customers.py             # CRUD de clientes
│   ├── suppliers.py             # CRUD de proveedores
│   ├── companies.py             # CRUD de empresas (multi-tenant)
│   └── venezuela_tax.py         # 🇻🇪 Módulo de cálculos fiscales SENIAT
├── main.py                      # Archivo principal de la aplicación
├── models.py                    # Modelos de SQLAlchemy
├── schemas.py                   # Esquemas de Pydantic
├── database.py                  # Configuración de base de datos
├── auth.py                      # Sistema de autenticación
├── config.py                    # Configuraciones de la aplicación
├── alembic.ini                  # Configuración de Alembic
├── requirements.txt             # Dependencias del proyecto
├── .env.example                 # Ejemplo de variables de entorno
├── SETUP.md                     # Guía de configuración
└── VENEZUELA_TAX_COMPLIANCE.md  # 🇻🇪 Documentación fiscal venezolana
```

## 🔑 Autenticación

El sistema utiliza JWT para la autenticación. Para acceder a endpoints protegidos:

1. **Crear usuario**: `POST /users/`
2. **Iniciar sesión**: `POST /login/`
3. **Usar token**: Incluir en headers: `Authorization: Bearer <token>`

## 📊 Principales Endpoints

### Autenticación y Usuarios
- `POST /api/v1/auth/register-company` - Registrar nueva empresa con admin
- `POST /api/v1/auth/login` - Iniciar sesión
- `GET /api/v1/users/me` - Ver perfil de usuario

### Categorías
- `GET /api/v1/categories` - Listar categorías
- `POST /api/v1/categories` - Crear categoría (requiere rol manager)
- `PUT /api/v1/categories/{id}` - Actualizar categoría
- `DELETE /api/v1/categories/{id}` - Eliminar categoría

### Productos
- `GET /api/v1/products` - Listar productos
- `POST /api/v1/products` - Crear producto
- `GET /api/v1/products/{id}` - Ver producto
- `PUT /api/v1/products/{id}` - Actualizar producto
- `DELETE /api/v1/products/{id}` - Eliminar producto

### Almacenes
- `GET /api/v1/warehouses` - Listar almacenes
- `POST /api/v1/warehouses` - Crear almacén
- `GET /api/v1/warehouses/{id}` - Ver almacén
- `PUT /api/v1/warehouses/{id}` - Actualizar almacén
- `DELETE /api/v1/warehouses/{id}` - Eliminar almacén
- `GET /api/v1/warehouses/{id}/products` - **Ver productos en almacén**
- `GET /api/v1/warehouses/products/low-stock` - Productos con stock bajo

### Gestión de Stock por Almacén
- `POST /api/v1/warehouse-products/` - Asignar producto a almacén
- `PUT /api/v1/warehouse-products/{warehouse_id}/{product_id}` - Actualizar stock
- `POST /api/v1/warehouse-products/transfer` - **Transferir stock entre almacenes**
- `POST /api/v1/warehouse-products/adjust` - **Ajustar stock con motivo**

### Clientes
- `GET /api/v1/customers` - Listar clientes
- `POST /api/v1/customers` - Crear cliente
- `PUT /api/v1/customers/{id}` - Actualizar cliente
- `DELETE /api/v1/customers/{id}` - Eliminar cliente

### Proveedores
- `GET /api/v1/suppliers` - Listar proveedores
- `POST /api/v1/suppliers` - Crear proveedor
- `PUT /api/v1/suppliers/{id}` - Actualizar proveedor
- `DELETE /api/v1/suppliers/{id}` - Eliminar proveedor

### Facturas (Ventas)
- `POST /api/v1/invoices/` - Crear factura (actualiza stock en almacén)
- `GET /api/v1/invoices` - Listar facturas con detalles completos de productos
- `GET /api/v1/invoices/{id}` - Ver factura con detalles completos de productos
- `PUT /api/v1/invoices/{id}` - **Editar factura (revierte y aplica stock)**
- `DELETE /api/v1/invoices/{id}` - Eliminar factura
- `PUT /api/v1/invoices/{id}/status` - Cambiar estado (presupuesto → factura)

**✅ Items de factura incluyen:**
- `product_name` - Nombre del producto
- `product_description` - Descripción del producto
- `product_sku` - SKU del producto
- `quantity` - Cantidad
- `price_per_unit` - Precio unitario
- `total_price` - Total
- `tax_rate` - Tasa impositiva
- `tax_amount` - Monto de IVA
- `is_exempt` - Indicador de exención

### Compras
- `POST /api/v1/purchases` - Registrar compra (actualiza stock en almacén)
- `GET /api/v1/purchases` - Listar compras
- `GET /api/v1/purchases/{id}` - Ver compra
- `PUT /api/v1/purchases/{id}` - Actualizar compra
- `DELETE /api/v1/purchases/{id}` - Eliminar compra
- `PUT /api/v1/purchases/{id}/status` - **Cambiar estado (actualiza/revierte stock)**

### Movimientos de Inventario
- `GET /api/v1/movements` - Ver movimientos (con referencia a almacén)

## 🗄️ Modelo de Datos

El sistema maneja las siguientes entidades principales:

- **Companies**: Empresas (multi-tenant)
  - Información fiscal: RIF, dirección fiscal, tipo de contribuyente
  - Configuración SENIAT: agente de retención IVA/ISLR, tasas personalizadas
  - Tasa de cambio USD→VES para cálculos de retenciones
  - Umbral para requerir RIF del cliente
- **Products**: Productos del inventario
- **Categories**: Categorías de productos
- **Warehouses**: Almacenes
- **WarehouseProducts**: Stock por almacén (relación muchos a muchos)
- **Invoices**: Facturas y presupuestos
  - **Campos SENIAT**: número de control, IVA, retenciones, timado fiscal
  - Información de transacción y cliente
  - Soporte para notas de crédito/débito
- **InvoiceItems**: Detalles de facturas
  - Tasa impositiva por item
  - Monto de IVA por item
  - Indicador de exención
- **Purchases**: Compras a proveedores
- **PurchaseItems**: Detalles de compras
- **InventoryMovements**: Movimientos de inventario (con referencia a almacén)
- **Users**: Usuarios del sistema
- **Customers**: Clientes
  - **RIF/CI obligatorio** según umbral configurado
- **Suppliers**: Proveedores

### Características Avanzadas del Modelo:

- **Multi-tenant**: Todos los datos están aislados por empresa
- **Stock por almacén**: Cada producto puede tener stock en múltiples almacenes
- **Movimientos rastreados**: Todos los movimientos de inventario registran:
  - Producto afectado
  - Almacén (si aplica)
  - Tipo de movimiento (venta, compra, ajuste, transferencia)
  - Cantidad y timestamp
  - Descripción del movimiento

## 🔄 Flujo de Trabajo

### Configuración Inicial
1. **Registrar empresa** con usuario administrador
2. **Configurar almacenes** donde se almacenarán los productos
3. **Crear categorías** para organizar el inventario
4. **Registrar proveedores** y **clientes**

### Gestión de Inventario
5. **Crear productos** y asignarlos a categorías
6. **Registrar compras** a proveedores:
   - Al crear compra con estado "received", el stock se agrega automáticamente
   - Se actualiza stock global y stock del almacén especificado
   - Se crea movimiento de inventario con referencia al almacén
7. **Distribuir stock** entre almacenes (si es necesario):
   - Usar endpoint de transferencia entre almacenes
   - Ajustar stock con motivos específicos (daño, pérdida, etc.)

### Ventas y Facturación
8. **Crear facturas** para registrar ventas:
   - Al confirmar factura, el stock se descuenta automáticamente
   - Se descuenta stock del almacén especificado en la factura
   - Se crea movimiento de inventario con referencia al almacén
9. **Editar facturas** (si es necesario):
   - El sistema revierte el stock anterior y aplica el nuevo
   - Funciona incluso con facturas confirmadas
10. **Monitorear movimientos** de inventario con filtros por almacén

### Gestión de Estados
- **Compras**: Cambiar estado de "pending" a "received" para agregar stock
- **Compras**: Cambiar de "received" a otro estado para revertir stock
- **Facturas**: Cambiar de "presupuesto" a "factura" para confirmar venta

## 💡 Ejemplos de Uso

### 🇻🇪 Crear factura venezolana con cálculos automáticos

```json
POST /api/v1/invoices/
{
  "customer_id": 1,
  "warehouse_id": 2,
  "status": "factura",
  "date": "2026-01-12",
  "transaction_type": "contado",
  "payment_method": "transferencia",
  "iva_percentage": 16,
  "items": [
    {
      "product_id": 10,
      "quantity": 10,
      "price_per_unit": 100.00,
      "tax_rate": 16,
      "is_exempt": false
    },
    {
      "product_id": 15,
      "quantity": 5,
      "price_per_unit": 50.00,
      "tax_rate": 0,
      "is_exempt": true  // Producto exento de IVA
    }
  ]
}
```

**Resultado automático:**
- ✅ IVA calculado: 160.00 (16% sobre 1000)
- ✅ Base imponible: 1000.00
- ✅ Monto exento: 250.00
- ✅ Retención IVA: según umbral VES (usando tasa de cambio)
- ✅ Retención ISLR: según umbral VES
- ✅ Timado fiscal: 12.50 (1% del subtotal)
- ✅ Número de control: generado automáticamente
- ✅ Stock actualizado en almacén

### Registrar empresa con configuración SENIAT

```json
POST /api/v1/auth/register-company
{
  "company_name": "Mi Empresa CA",
  "company_legal_name": "Mi Empresa C.A.",
  "company_tax_id": "J-12345678-9",
  "currency": "USD",
  "exchange_rate": 35.5,
  "iva_retention_agent": true,
  "islr_retention_agent": true,
  "require_customer_tax_id_threshold": 0.0,
  "admin_username": "admin",
  "admin_email": "admin@empresa.com",
  "admin_password": "secure_password"
}
```

### Validar RIF venezolano

```python
from crud.venezuela_tax import validate_rif, calculate_rif_digit

# Validar RIF con dígito verificador
validate_rif("J-12345678-9")  # True (válido)
validate_rif("J-12345678-0")  # False (dígito incorrecto)

# Calcular dígito verificador
calculate_rif_digit("12345678")  # Retorna: 9
```

### Registrar una compra con recepción inmediata
```json
POST /api/v1/purchases
{
  "supplier_id": 3,
  "warehouse_id": 5,
  "status": "received",
  "date": "2026-01-06",
  "items": [
    {
      "product_id": 18,
      "quantity": 50,
      "price_per_unit": 1200.00
    }
  ]
}
```
**Resultado**: El stock del producto aumenta en 50 unidades en el almacén 5.

### Transferir stock entre almacenes
```json
POST /api/v1/warehouse-products/transfer
{
  "from_warehouse_id": 1,
  "to_warehouse_id": 2,
  "product_id": 10,
  "quantity": 25
}
```
**Resultado**: 25 unidades se mueven del almacén 1 al almacén 2.

### Ver productos de un almacén
```
GET /api/v1/warehouses/5/products
```
**Resultado**: Lista todos los productos con su stock en el almacén 5.

### Editar factura confirmada
```json
PUT /api/v1/invoices/123
{
  "customer_id": 5,
  "warehouse_id": 2,
  "status": "factura",
  "items": [
    {
      "product_id": 10,
      "quantity": 15,
      "price": 100.00
    }
  ]
}
```
**Resultado**: El sistema revierte el stock anterior y descuenta el nuevo stock del almacén 2.

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
