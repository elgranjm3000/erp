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

# Umbrales para retención de IVA (en USD aproximado)
IVA_RETENTION_75_THRESHOLD = 50.0  # Más de 50 USD en IVA
IVA_RETENTION_100_THRESHOLD = 100.0  # Más de 100 USD en IVA

# Umbrales para retención de ISLR (personas jurídicas)
ISLR_RETENTION_1_THRESHOLD = 5000.0  # 1%
ISLR_RETENTION_2_THRESHOLD = 10000.0  # 2%
ISLR_RETENTION_3_THRESHOLD = 20000.0  # 3%

# Timado fiscal
STAMP_TAX_RATE = 1.0  # 1% del total


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


def calculate_iva_retention(
    iva_amount: float,
    company: Company = None
) -> Tuple[float, float]:
    """
    Calcular retención de IVA

    Args:
        iva_amount: Monto de IVA
        company: Empresa (para verificar si es agente de retención)

    Returns:
        Tuple con (monto_retención, porcentaje_aplicado)
    """
    # Si la empresa no es agente de retención, no retiene
    if company and not company.iva_retention_agent:
        return 0.0, 0.0

    # Determinar porcentaje según umbral
    if iva_amount > IVA_RETENTION_100_THRESHOLD:
        percentage = 100.0
    elif iva_amount > IVA_RETENTION_75_THRESHOLD:
        percentage = 75.0
    else:
        return 0.0, 0.0

    retention = round(iva_amount * (percentage / 100), 2)
    return retention, percentage


def calculate_islr_retention(
    amount: float,
    company: Company = None
) -> Tuple[float, float]:
    """
    Calcular retención de ISLR

    Args:
        amount: Monto gravable
        company: Empresa (para verificar si es agente de retención)

    Returns:
        Tuple con (monto_retención, porcentaje_aplicado)
    """
    # Si la empresa no es agente de retención, no retiene
    if company and not company.islr_retention_agent:
        return 0.0, 0.0

    # Determinar porcentaje según umbral
    if amount > ISLR_RETENTION_3_THRESHOLD:
        percentage = 3.0
    elif amount > ISLR_RETENTION_2_THRESHOLD:
        percentage = 2.0
    elif amount > ISLR_RETENTION_1_THRESHOLD:
        percentage = 1.0
    else:
        return 0.0, 0.0

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
    company: Company = None
) -> Dict:
    """
    Calcular todos los totales de una factura según normativa venezolana

    Args:
        items: Lista de items con tax_rate y quantity
        discount: Descuento global (porcentaje)
        iva_percentage: Tasa de IVA general
        company: Empresa para verificar retenciones

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

    # Calcular retenciones
    iva_retention, iva_retention_pct = calculate_iva_retention(iva_amount, company)
    islr_retention, islr_retention_pct = calculate_islr_retention(subtotal, company)

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


def validate_rif(rif: str) -> bool:
    """
    Validar formato de RIF venezolano

    Formato esperado: J-123456789-X o V-12345678-X o E-12345678-X

    Args:
        rif: RIF a validar

    Returns:
        True si el formato es válido, False si no
    """
    if not rif:
        return False

    parts = rif.split('-')
    if len(parts) != 3:
        return False

    letter, number, digit = parts

    # Validar letra (tipo de persona)
    if letter not in ['J', 'V', 'E', 'G', 'P']:
        return False

    # Validar número (debe ser dígitos)
    if not number.isdigit() or len(number) < 8 or len(number) > 10:
        return False

    # Validar dígito verificador
    if not digit.isdigit() or len(digit) != 1:
        return False

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
