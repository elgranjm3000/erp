# Cumplimiento de Normativa Fiscal SENIAT - Venezuela

Este ERP cumple con los requisitos de facturación establecidos por el SENIAT (Servicio Nacional Integrado de Administración Aduanera y Tributaria) de Venezuela.

## Tipos de RIF Soportados

El sistema valida y acepta los siguientes tipos de identificación fiscal venezolana:

| Tipo | Descripción | Formato | Ejemplo |
|------|-------------|---------|---------|
| **J** | Persona Jurídica (Empresas) | J-XXXXXXXX-X | J-12345678-9 |
| **V** | Persona Natural Venezolana | V-XXXXXXXX-X | V-12345678-9 |
| **E** | Extranjero | E-XXXXXXXX-X | E-12345678-9 |
| **G** | Gobierno | G-XXXXXXXX-X | G-12345678-9 |

### Formato del RIF
- **Estructura**: `LETRA-NÚMERO-DÍGITO`
- **Letra**: J, V, E, o G
- **Número**: 7-9 dígitos (se rellena con ceros a la izquierda si es necesario)
- **Dígito verificador**: 1 dígito (calculado con algoritmo SENIAT)

### Validación de Dígito Verificador

El sistema implementa el algoritmo oficial del SENIAT para validar el dígito verificador del RIF:

1. El número se rellena a 9 dígitos con ceros a la izquierda
2. Se multiplica cada dígito por los coeficientes: 4, 3, 2, 7, 6, 5, 4, 3, 2
3. Se suman los productos
4. Se divide entre 11 y se obtiene el residuo
5. Si el residuo < 2: ese es el dígito verificador
6. Si el residuo ≥ 2: 11 - residuo = dígito verificador

## Impuestos Implementados

### 1. IVA (Impuesto al Valor Agregado)

**Tasas vigentes:**
- **16%**: Tasa general (aplicable a la mayoría de bienes y servicios)
- **8%**: Tasa reducida (bienes y servicios específicos)
- **0%**: Exento (alimentos básicos, medicamentos, etc.)

**Cálculo:**
```
IVA = Base Imponible × Tasa
Base Imponible = Precio Unitario × Cantidad (para items gravados)
```

**Items exentos:**
- Los items pueden marcarse como exentos individualmente
- El monto exento se registra separadamente de la base imponible

### 2. Retención de IVA

Los agentes de retención deben retener IVA según los umbrales establecidos:

| Monto de IVA (en VES) | Porcentaje de Retención |
|----------------------|------------------------|
> 200 VES | 75% |
> 300 VES | 100% |

**Nota:** Los umbrales están en Bolívares (VES) según normativa oficial. El sistema convierte automáticamente desde USD usando la tasa de cambio configurada en la empresa.

**Requisitos:**
- La empresa debe estar registrada como Agente de Retención de IVA
- Se calcula sobre el monto de IVA de la factura

### 3. Retención de ISLR (Impuesto Sobre la Renta)

Umbrales progresivos para personas jurídicas:

| Monto Gravable (en VES) | Porcentaje de Retención |
|------------------------|------------------------|
> 5.000 VES | 1% |
> 10.000 VES | 2% |
> 20.000 VES | 3% |

**Nota:** Los umbrales están en Bolívares (VES). El sistema convierte desde USD usando la tasa de cambio.

**Requisitos:**
- La empresa debe estar registrada como Agente de Retención de ISLR
- Se calcula sobre el subtotal de la factura (antes de impuestos)

### 4. Timado Fiscal

- **Tasa:** 1% del total de la factura
- **Cálculo:** `Timado = Total × 0.01`
- Aplicable a todas las transacciones

## Información Fiscal Requerida

### Datos de la Empresa

Para cumplimiento normativo, la empresa debe configurar:

- **RIF**: Registro de Información Fiscal (formato J-XXXXXXXX-X)
- **Dirección fiscal**: Dirección exacta para facturas
- **Tipo de contribuyente**: Ordinario o Contribuyente Especial
- **Certificado SENIAT**: Número de certificado de contribuyente especial (si aplica)
- **Agente de retención IVA**: Sí/No
- **Agente de retención ISLR**: Sí/No
- **Tasa de cambio**: Tasa USD→VES para cálculos de retenciones (ej: 35.5)
- **Umbral RIF cliente**: Monto mínimo a partir del cual se requiere RIF del cliente

### Datos del Cliente

Según normativa SENIAT, para facturas que superen cierto monto, es obligatorio:

- **RIF/CI del cliente**: Identificación fiscal completa
- **Dirección del cliente**: Dirección fiscal o de entrega
- **Teléfono del cliente**: Número de contacto

**Configuración:**
Cada empresa puede configurar el umbral a partir del cual se requiere el RIF del cliente:

```python
require_customer_tax_id_threshold = 0.0  # 0 = siempre requerir
# Ejemplos:
# 0.0 = Siempre requerir RIF (recomendado para cumplimiento estricto)
# 100.0 = Requerir RIF solo para facturas > 100 USD/VES
# -1.0 = Nunca requerir RIF (no recomendado)
```

## Numeración de Facturas

El sistema maneja dos numeraciones obligatorias según SENIAT:

### 1. Número de Factura
- Formato: `PREFIJO-NÚMERO`
- Ejemplo: `INV-000001`
- Consecutivo por empresa
- Reinicio anual opcional

### 2. Número de Control
- **OBLIGATORIO** según normativa SENIAT
- Formato: `PREFIJO-NÚMERO`
- Ejemplo: `INV-00000001`
- Independiente del número de factura
- Requerido para declaraciones de impuestos

## Tipos de Transacción

- **Contado**: Pago inmediato
- **Crédito**: Pago diferido (con días de crédito especificados)

## Métodos de Pago Soportados

- Efectivo
- Transferencia bancaria
- Débito
- Crédito
- Zelle
- Pago Móvil
- Otros

## Notas de Crédito y Débito

El sistema soporta:

- **Notas de Crédito**: Devoluciones y descuentos posteriores
- **Notas de Débito**: Cargos adicionales

**Campos requeridos:**
- Referencia a factura original (número de factura y número de control)
- Motivo de la nota
- Monto

## Configuración Recomendada

Para empresas venezolanas, se recomienda:

```python
{
    "currency": "USD",  # o "VES"
    "exchange_rate": 35.5,  # Tasa actual BCV
    "invoice_prefix": "FAC",
    "iva_retention_agent": True,  # Si corresponde
    "islr_retention_agent": True,  # Si corresponde
    "require_customer_tax_id_threshold": 0.0,  # Siempre requerir RIF
    "taxpayer_type": "ordinario",  # o "contribuyente_especial"
    "fiscal_address": "Dirección completa fiscal",
}
```

## Referencias Normativas

- **Providencia Administrativa SNAT/2015/0064**: Umbrales de retención de IVA
- **Providencia Administrativa SNAT/2016/0075**: Modificación de umbrales
- **Ley de Impuesto al Valor Agregado (LIVA)**: Tasa general y reducida
- **Ley de Impuesto Sobre la Renta (LISLR)**: Retenciones por actividades económicas

## Funciones Auxiliares Disponibles

El módulo `crud/venezuela_tax.py` provee:

```python
# Calcular IVA
venezuela_tax.calculate_iva(base_imponible, tasa)

# Calcular retención de IVA (con conversión a VES)
venezuela_tax.calculate_iva_retention(monto_iva, company, currency)

# Calcular retención de ISLR (con conversión a VES)
venezuela_tax.calculate_islr_retention(monto_gravable, company, currency)

# Calcular timado fiscal
venezuela_tax.calculate_stamp_tax(total)

# Calcular todos los totales de factura
venezuela_tax.calculate_invoice_totals(items, discount, iva_percentage, company, currency)

# Validar RIF (con dígito verificador)
venezuela_tax.validate_rif(rif, validate_check_digit=True)

# Calcular dígito verificador de RIF
venezuela_tax.calculate_rif_digit(rif_number)

# Formatear RIF
venezuela_tax.format_rif(rif)

# Generar número de control
venezuela_tax.get_control_number(company_id, next_number, prefix)

# Generar número de factura
venezuela_tax.get_invoice_number(company_id, next_number, prefix)
```

## Ejemplos de Uso

### Crear factura con cálculo automático de impuestos

```python
from crud.venezuela_tax import calculate_invoice_totals

items = [
    {'price': 100, 'quantity': 2, 'tax_rate': 16, 'is_exempt': False},
    {'price': 50, 'quantity': 1, 'tax_rate': 0, 'is_exempt': True},  # Exento
]

resultados = calculate_invoice_totals(
    items=items,
    discount=10,  # 10% descuento
    iva_percentage=16,
    company=mi_empresa,
    currency="USD"
)

# Resultados:
# {
#     'subtotal': 250.0,
#     'taxable_base': 180.0,
#     'exempt_amount': 50.0,
#     'iva_amount': 28.8,
#     'iva_retention': 0.0,  # Depende de si es agente de retención y monto
#     'islr_retention': 0.0,  # Depende de si es agente de retención y monto
#     'stamp_tax': 2.5,
#     'total_with_taxes': 281.3,
#     'currency': 'USD'
# }
```

### Validar RIF

```python
from crud.venezuela_tax import validate_rif, calculate_rif_digit

# Validar RIF existente
es_valido = validate_rif("J-12345678-9")  # True o False

# Calcular dígito verificador
digito = calculate_rif_digit("12345678")  # Retorna el dígito correcto

# Formatear RIF (limpia espacios y pone mayúsculas)
rif_formateado = format_rif("j-12345678-9")  # "J-12345678-9"
```

## Soporte y Actualizaciones

Este módulo se mantiene actualizado según cambios en la normativa venezolana. Para sugerencias o correcciones, consultar con un contador público certificado en Venezuela.

**⚠️ Importante:** Este software es una herramienta de apoyo. Se recomienda validar los cálculos con un profesional contable certificado antes de presentar declaraciones ante el SENIAT.
