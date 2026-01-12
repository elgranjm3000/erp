# crud/venezuela_tax.py
"""
Funciones auxiliares para cálculos de impuestos en Venezuela
"""

from typing import Tuple, Dict
from models import Company

# ================= CONSTANTES SENIAT =================

# Tasas de IVA vigentes en Venezuela
IVA_GENERAL = 16.0  # 16%
IVA_REDUCIDA = 8.0  # 8%
IVA_EXENTO = 0.0  # 0%

# Umbrales para retención de IVA (en VES - Bolívares)
# Según Providencia Administrativa SNAT/2015/0064
IVA_RETENTION_75_THRESHOLD_VES = 200.0  # Más de 200 VES en IVA (75%)
IVA_RETENTION_100_THRESHOLD_VES = 300.0  # Más de 300 VES en IVA (100%)

# Umbrales para retención de ISLR (personas jurídicas) en VES
# Según normativa vigente SENIAT
ISLR_RETENTION_1_THRESHOLD_VES = 5000.0  # 1%
ISLR_RETENTION_2_THRESHOLD_VES = 10000.0  # 2%
ISLR_RETENTION_3_THRESHOLD_VES = 20000.0  # 3%

# Timado fiscal
STAMP_TAX_RATE = 1.0  # 1% del total

# Umbrales en USD (para compatibilidad, usar VES preferiblemente)
IVA_RETENTION_75_THRESHOLD_USD = 50.0  # Más de 50 USD en IVA (75%)
IVA_RETENTION_100_THRESHOLD_USD = 100.0  # Más de 100 USD en IVA (100%)


# ================= FUNCIONES DE CÁLCULO =================

def calculate_iva(taxable_base: float, rate: float = IVA_GENERAL) -> float:
    """
    Calcular IVA

    Args:
        taxable_base: Base imponible
        rate: Tasa de IVA (16%, 8%, 0%)

    Returns:
        Monto de IVA calculado
    """
    if rate == 0:
        return 0.0
    return round(taxable_base * (rate / 100), 2)


def convert_to_ves(amount: float, company: Company = None) -> float:
    """
    Convertir monto de USD a VES usando la tasa de cambio de la empresa

    Args:
        amount: Monto en USD
        company: Empresa con tasa de cambio configurada

    Returns:
        Monto convertido a VES (o mismo monto si no hay tasa)
    """
    if company and hasattr(company, 'exchange_rate') and company.exchange_rate:
        return amount * company.exchange_rate
    return amount


def calculate_iva_retention(
    iva_amount: float,
    company: Company = None,
    currency: str = "USD"
) -> Tuple[float, float]:
    """
    Calcular retención de IVA según normativa SENIAT

    Args:
        iva_amount: Monto de IVA (en la moneda especificada)
        company: Empresa (para verificar si es agente de retención y tasa de cambio)
        currency: Moneda del monto ("USD" o "VES")

    Returns:
        Tuple con (monto_retención, porcentaje_aplicado)
    """
    # Si la empresa no es agente de retención, no retiene
    if company and not company.iva_retention_agent:
        return 0.0, 0.0

    # Convertir a VES si está en USD
    iva_amount_ves = iva_amount
    if currency == "USD":
        iva_amount_ves = convert_to_ves(iva_amount, company)

    # Determinar porcentaje según umbral EN VES
    if iva_amount_ves > IVA_RETENTION_100_THRESHOLD_VES:
        percentage = 100.0
    elif iva_amount_ves > IVA_RETENTION_75_THRESHOLD_VES:
        percentage = 75.0
    else:
        return 0.0, 0.0

    # Calcular retención sobre el monto original (en la moneda original)
    retention = round(iva_amount * (percentage / 100), 2)
    return retention, percentage


def calculate_islr_retention(
    amount: float,
    company: Company = None,
    currency: str = "USD"
) -> Tuple[float, float]:
    """
    Calcular retención de ISLR según normativa SENIAT

    Args:
        amount: Monto gravable (en la moneda especificada)
        company: Empresa (para verificar si es agente de retención y tasa de cambio)
        currency: Moneda del monto ("USD" o "VES")

    Returns:
        Tuple con (monto_retención, porcentaje_aplicado)
    """
    # Si la empresa no es agente de retención, no retiene
    if company and not company.islr_retention_agent:
        return 0.0, 0.0

    # Convertir a VES si está en USD
    amount_ves = amount
    if currency == "USD":
        amount_ves = convert_to_ves(amount, company)

    # Determinar porcentaje según umbral EN VES
    if amount_ves > ISLR_RETENTION_3_THRESHOLD_VES:
        percentage = 3.0
    elif amount_ves > ISLR_RETENTION_2_THRESHOLD_VES:
        percentage = 2.0
    elif amount_ves > ISLR_RETENTION_1_THRESHOLD_VES:
        percentage = 1.0
    else:
        return 0.0, 0.0

    # Calcular retención sobre el monto original (en la moneda original)
    retention = round(amount * (percentage / 100), 2)
    return retention, percentage


def calculate_stamp_tax(total: float) -> float:
    """
    Calcular timado fiscal (1%)

    Args:
        total: Total de la factura

    Returns:
        Monto del timado fiscal
    """
    return round(total * (STAMP_TAX_RATE / 100), 2)


def calculate_invoice_totals(
    items: list,
    discount: float = 0.0,
    iva_percentage: float = IVA_GENERAL,
    company: Company = None,
    currency: str = "USD"
) -> Dict:
    """
    Calcular todos los totales de una factura según normativa venezolana

    Args:
        items: Lista de items con tax_rate y quantity
        discount: Descuento global (porcentaje)
        iva_percentage: Tasa de IVA general
        company: Empresa para verificar retenciones y tasa de cambio
        currency: Moneda de trabajo ("USD" o "VES")

    Returns:
        Diccionario con todos los totales calculados
    """
    subtotal = 0.0
    taxable_base = 0.0
    exempt_amount = 0.0
    iva_amount = 0.0

    # Calcular totales por item
    for item in items:
        item_total = item.get('price', 0) * item.get('quantity', 0)
        tax_rate = item.get('tax_rate', iva_percentage)
        is_exempt = item.get('is_exempt', False)

        if is_exempt or tax_rate == 0:
            exempt_amount += item_total
        else:
            taxable_base += item_total
            item_iva = calculate_iva(item_total, tax_rate)
            iva_amount += item_iva

        subtotal += item_total

    # Aplicar descuento global
    if discount > 0:
        discount_amount = round(subtotal * (discount / 100), 2)
        taxable_base = round(taxable_base - discount_amount, 2)
        # Recalcular IVA con la base imponible descontada
        iva_amount = calculate_iva(taxable_base, iva_percentage)
        subtotal = round(subtotal - discount_amount, 2)

    # Calcular retenciones con conversión a VES si es necesario
    iva_retention, iva_retention_pct = calculate_iva_retention(
        iva_amount, company, currency
    )
    islr_retention, islr_retention_pct = calculate_islr_retention(
        subtotal, company, currency
    )

    # Calcular timado fiscal
    stamp_tax = calculate_stamp_tax(subtotal)

    # Total con impuestos
    total_with_taxes = round(subtotal + iva_amount - iva_retention - islr_retention + stamp_tax, 2)

    return {
        'subtotal': subtotal,
        'taxable_base': taxable_base,
        'exempt_amount': exempt_amount,
        'iva_amount': iva_amount,
        'iva_percentage': iva_percentage,
        'iva_retention': iva_retention,
        'iva_retention_percentage': iva_retention_pct,
        'islr_retention': islr_retention,
        'islr_retention_percentage': islr_retention_pct,
        'stamp_tax': stamp_tax,
        'total_with_taxes': total_with_taxes,
        'currency': currency,
    }


def validate_tax_rate(rate: float) -> bool:
    """
    Validar que la tasa de impuesto sea válida según normativa venezolana

    Args:
        rate: Tasa a validar

    Returns:
        True si es válida, False si no
    """
    return rate in [0.0, 8.0, 16.0]


def calculate_rif_digit(rif_number: str) -> int:
    """
    Calcular dígito verificador de RIF venezolano

    Algoritmo SENIAT:
    - Multiplicar cada dígito por 4, 3, 2, 7, 6, 5, 4, 3, 2
    - Sumar los productos
    - Dividir entre 11 y obtener residuo
    - Restar 11 - residuo
    - El resultado es el dígito verificador

    Args:
        rif_number: Número del RIF sin letra ni dígito verificador

    Returns:
        Dígito verificador (0-9)
    """
    # Asegurar que el número tenga 9 dígitos (completar con ceros a la izquierda si es necesario)
    rif_number = rif_number.zfill(9)

    # Coeficientes de validación
    coefficients = [4, 3, 2, 7, 6, 5, 4, 3, 2]

    # Calcular suma ponderada
    total = sum(int(digit) * coef for digit, coef in zip(rif_number, coefficients))

    # Calcular dígito verificador
    remainder = total % 11

    if remainder < 2:
        check_digit = remainder
    else:
        check_digit = 11 - remainder

    return check_digit


def validate_rif(rif: str, validate_check_digit: bool = True) -> bool:
    """
    Validar formato de RIF venezolano

    Formato esperado: J-12345678-X o V-12345678-X o E-12345678-X

    Tipos de RIF soportados:
    - J: Persona jurídica (empresas)
    - V: Persona natural (venezolano)
    - E: Extranjero
    - G: Gobierno

    Args:
        rif: RIF a validar
        validate_check_digit: Si True, valida el dígito verificador

    Returns:
        True si el formato es válido, False si no
    """
    if not rif:
        return False

    # Formatear RIF
    rif = format_rif(rif)

    parts = rif.split('-')
    if len(parts) != 3:
        return False

    letter, number, digit = parts

    # Validar letra (tipo de persona) - SOLO tipos oficiales SENIAT
    if letter not in ['J', 'V', 'E', 'G']:
        return False

    # Validar número (debe ser dígitos, 7-9 caracteres)
    if not number.isdigit() or len(number) < 7 or len(number) > 9:
        return False

    # Validar dígito verificador (debe ser un dígito)
    if not digit.isdigit() or len(digit) != 1:
        return False

    # Validar dígito verificador si se solicita
    if validate_check_digit:
        expected_digit = calculate_rif_digit(number)
        actual_digit = int(digit)
        return expected_digit == actual_digit

    return True


def format_rif(rif: str) -> str:
    """
    Formatear RIF para asegurar consistencia

    Args:
        rif: RIF a formatear

    Returns:
        RIF formateado en mayúsculas y sin espacios
    """
    return rif.upper().strip().replace(' ', '')


def get_control_number(company_id: int, next_number: int, prefix: str = "FAC") -> str:
    """
    Generar número de control para factura

    Formato: PREFIJO-NÚMERO CONSECUTIVO

    Args:
        company_id: ID de la empresa
        next_number: Próximo número consecutivo
        prefix: Prefijo (default: FAC)

    Returns:
        Número de control formateado
    """
    return f"{prefix}-{next_number:08d}"


def get_invoice_number(company_id: int, next_number: int, prefix: str = "INV") -> str:
    """
    Generar número de factura

    Formato: PREFIJO-NÚMERO CONSECUTIVO

    Args:
        company_id: ID de la empresa
        next_number: Próximo número consecutivo
        prefix: Prefijo (default: INV)

    Returns:
        Número de factura formateado
    """
    return f"{prefix}-{next_number:08d}"
