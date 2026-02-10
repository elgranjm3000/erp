"""
Dynamic Tax Engine
Motor de impuestos configurable y extensible
"""

import logging
from typing import Optional, Dict, List, Type
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class TaxType(Enum):
    """Tipos de impuestos soportados"""
    IVA = "iva"  # Impuesto al Valor Agregado
    IGTF = "igtf"  # Impuesto a Grandes Transacciones Financieras
    ISLR = "islr"  # Impuesto Sobre la Renta
    MUNICIPAL = "municipal"  # Impuesto municipal
    CUSTOM = "custom"  # Impuesto personalizado


@dataclass(frozen=True)
class TaxRule:
    """
    Regla de impuesto inmutable.

    Attributes:
        tax_type: Tipo de impuesto
        name: Nombre del impuesto
        rate: Tasa (porcentaje, ej: 16 para 16%)
        is_active: Si está activa
        valid_from: Fecha de inicio de vigencia
        valid_until: Fecha de fin de vigencia (None = indefinido)
        min_amount: Monto mínimo para aplicar
        max_amount: Monto máximo para aplicar
        currency: Moneda para min/max (None = cualquiera)
        conditions: Condiciones adicionales (JSON)
        priority: Prioridad de aplicación (mayor = primero)
    """
    tax_type: TaxType
    name: str
    rate: Decimal
    is_active: bool = True
    valid_from: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    conditions: Optional[Dict] = None
    priority: int = 0

    def is_applicable(
        self,
        amount: Decimal,
        currency: str,
        date: datetime = None
    ) -> bool:
        """
        Verifica si esta regla es aplicable a una transacción.

        Args:
            amount: Monto de la transacción
            currency: Moneda del monto
            date: Fecha de la transacción

        Returns:
            bool: True si la regla es aplicable
        """
        if not self.is_active:
            return False

        # Verificar vigencia temporal
        check_date = date or datetime.now()
        if check_date < self.valid_from:
            return False

        if self.valid_until and check_date > self.valid_until:
            return False

        # Verificar rangos de monto
        if self.min_amount and amount < self.min_amount:
            return False

        if self.max_amount and amount > self.max_amount:
            return False

        # Verificar moneda si está especificada
        if self.currency and currency != self.currency:
            return False

        return True

    def calculate(self, amount: Decimal) -> Decimal:
        """
        Calcula el monto del impuesto.

        Args:
            amount: Monto gravable

        Returns:
            Decimal: Monto del impuesto
        """
        return (amount * self.rate) / Decimal("100")


@dataclass(frozen=True)
class TaxCalculation:
    """
    Resultado de cálculo de impuestos.

    Attributes:
        taxable_amount: Monto gravable
        tax_type: Tipo de impuesto
        tax_name: Nombre del impuesto
        rate: Tasa aplicada
        tax_amount: Monto del impuesto
        rule_id: ID de la regla aplicada
        calculated_at: Timestamp de cálculo
    """
    taxable_amount: Decimal
    tax_type: TaxType
    tax_name: str
    rate: Decimal
    tax_amount: Decimal
    rule_id: str
    calculated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convierte a diccionario"""
        return {
            "taxable_amount": str(self.taxable_amount),
            "tax_type": self.tax_type.value,
            "tax_name": self.tax_name,
            "rate": str(self.rate),
            "tax_amount": str(self.tax_amount),
            "rule_id": self.rule_id,
            "calculated_at": self.calculated_at.isoformat()
        }


class TaxRuleRepository(ABC):
    """Interfaz para repositorio de reglas de impuestos"""

    @abstractmethod
    def get_active_rules(
        self,
        tax_type: Optional[TaxType] = None,
        date: datetime = None
    ) -> List[TaxRule]:
        """Obtiene reglas activas"""
        pass

    @abstractmethod
    def save_rule(self, rule: TaxRule) -> TaxRule:
        """Guarda una regla"""
        pass


class InMemoryTaxRuleRepository(TaxRuleRepository):
    """Repositorio en memoria para reglas de impuestos"""

    def __init__(self):
        self._rules: Dict[str, TaxRule] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Inicializa reglas por defecto (Venezuela)"""

        # IVA estándar (16%)
        iva_standard = TaxRule(
            tax_type=TaxType.IVA,
            name="IVA Estándar",
            rate=Decimal("16"),
            is_active=True,
            priority=10
        )

        # IVA reducido (8%)
        iva_reducido = TaxRule(
            tax_type=TaxType.IVA,
            name="IVA Reducido",
            rate=Decimal("8"),
            is_active=True,
            priority=9,
            conditions={"category": "basic"}
        )

        # IGTF (3% para pagos en divisas)
        igtf_divisas = TaxRule(
            tax_type=TaxType.IGTF,
            name="IGTF Divisas",
            rate=Decimal("3"),
            is_active=True,
            min_amount=Decimal("1000"),
            currency="USD",
            priority=5
        )

        # IGTF Bolívares (exento, 0%)
        igtf_bolivares = TaxRule(
            tax_type=TaxType.IGTF,
            name="IGTF Bolívares",
            rate=Decimal("0"),
            is_active=True,
            currency="VES",
            priority=5
        )

        self.save_rule(iva_standard)
        self.save_rule(iva_reducido)
        self.save_rule(igtf_divisas)
        self.save_rule(igtf_bolivares)

        logger.info("Initialized default tax rules for Venezuela")

    def get_active_rules(
        self,
        tax_type: Optional[TaxType] = None,
        date: datetime = None
    ) -> List[TaxRule]:
        rules = list(self._rules.values())

        if tax_type:
            rules = [r for r in rules if r.tax_type == tax_type]

        # Filtrar por vigencia
        check_date = date or datetime.now()
        rules = [
            r for r in rules
            if r.is_active and r.valid_from <= check_date
            and (not r.valid_until or r.valid_until >= check_date)
        ]

        # Ordenar por prioridad descendente
        rules.sort(key=lambda x: x.priority, reverse=True)

        return rules

    def save_rule(self, rule: TaxRule) -> TaxRule:
        rule_id = f"{rule.tax_type.value}_{rule.name.lower().replace(' ', '_')}"
        # Guardar copia inmutable
        self._rules[rule_id] = rule
        return rule


class TaxEngine:
    """
    Motor de cálculo de impuestos dinámico y extensible.

    Características:
    - Reglas configurables
    - Múltiples impuestos por transacción
    - Priorización de reglas
    - Auditoría de cálculos
    """

    def __init__(self, repository: Optional[TaxRuleRepository] = None):
        """
        Inicializa el motor de impuestos.

        Args:
            repository: Repositorio de reglas (usa InMemory por defecto)
        """
        self.repository = repository or InMemoryTaxRuleRepository()
        logger.info("Tax engine initialized")

    def calculate_tax(
        self,
        amount: Decimal,
        currency: str,
        tax_type: TaxType,
        date: Optional[datetime] = None,
        context: Optional[Dict] = None
    ) -> Optional[TaxCalculation]:
        """
        Calcula un impuesto específico para un monto.

        Args:
            amount: Monto gravable
            currency: Moneda del monto
            tax_type: Tipo de impuesto a calcular
            date: Fecha de la transacción
            context: Contexto adicional (ej: método de pago)

        Returns:
            TaxCalculation: Resultado del cálculo o None si no aplica
        """
        rules = self.repository.get_active_rules(tax_type=tax_type, date=date)

        # Encontrar primera regla aplicable (ordenadas por prioridad)
        for rule in rules:
            if rule.is_applicable(amount, currency, date):
                tax_amount = rule.calculate(amount)

                calculation = TaxCalculation(
                    taxable_amount=amount,
                    tax_type=rule.tax_type,
                    tax_name=rule.name,
                    rate=rule.rate,
                    tax_amount=tax_amount,
                    rule_id=f"{rule.tax_type.value}_{rule.name}"
                )

                logger.info(
                    f"Calculated {rule.tax_type.value}: {tax_amount} "
                    f"({rule.rate}% of {amount} {currency})"
                )

                return calculation

        logger.warning(f"No applicable tax rule found for {tax_type.value}")
        return None

    def calculate_all_taxes(
        self,
        amount: Decimal,
        currency: str,
        date: Optional[datetime] = None,
        context: Optional[Dict] = None
    ) -> List[TaxCalculation]:
        """
        Calcula todos los impuestos aplicables a un monto.

        Args:
            amount: Monto gravable
            currency: Moneda del monto
            date: Fecha de transacción
            context: Contexto adicional

        Returns:
            List[TaxCalculation]: Lista de impuestos calculados
        """
        calculations = []

        # Obtener todos los tipos de impuesto
        all_rules = self.repository.get_active_rules(date=date)
        tax_types = set(r.tax_type for r in all_rules)

        # Calcular cada tipo
        for tax_type in tax_types:
            calculation = self.calculate_tax(
                amount=amount,
                currency=currency,
                tax_type=tax_type,
                date=date,
                context=context
            )

            if calculation:
                calculations.append(calculation)

        return calculations

    def calculate_total_tax(
        self,
        amount: Decimal,
        currency: str,
        date: Optional[datetime] = None,
        context: Optional[Dict] = None
    ) -> Decimal:
        """
        Calcula el total de impuestos para un monto.

        Args:
            amount: Monto gravable
            currency: Moneda
            date: Fecha
            context: Contexto

        Returns:
            Decimal: Suma de todos los impuestos
        """
        calculations = self.calculate_all_taxes(amount, currency, date, context)
        return sum(c.tax_amount for c in calculations)

    def add_rule(self, rule: TaxRule) -> TaxRule:
        """
        Agrega una nueva regla de impuesto.

        Args:
            rule: Regla a agregar

        Returns:
            TaxRule: Regla guardada
        """
        saved_rule = self.repository.save_rule(rule)
        logger.info(f"Added tax rule: {saved_rule.name} ({saved_rule.tax_type.value})")
        return saved_rule

    def get_applicable_rules(
        self,
        amount: Decimal,
        currency: str,
        date: Optional[datetime] = None
    ) -> List[TaxRule]:
        """
        Retorna todas las reglas aplicables a un monto.

        Args:
            amount: Monto
            currency: Moneda
            date: Fecha

        Returns:
            List[TaxRule]: Reglas aplicables
        """
        all_rules = self.repository.get_active_rules(date=date)

        applicable = [
            r for r in all_rules
            if r.is_applicable(amount, currency, date)
        ]

        # Ordenar por prioridad
        applicable.sort(key=lambda x: x.priority, reverse=True)

        return applicable
