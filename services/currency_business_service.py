"""
Servicio de Gestión de Monedas - Lógica Contable Venezolana
Validación ISO 4217, factores de conversión, IGTF y auditoría completa
"""

import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.currency_config import Currency, CurrencyRateHistory, IGTFConfig
# Importar desde el archivo schemas.py en lugar del paquete
from schemas import (
    CurrencyCreate,
    CurrencyUpdate,
    CurrencyRateUpdate,
    ConversionMethod,
    RateUpdateMethod,
    ISO_4217_CURRENCIES
)


logger = logging.getLogger(__name__)


class CurrencyBusinessLogic:
    """
    Lógica de negocio para gestión de monedas con:
    - Validación ISO 4217
    - Factores de conversión (lógica venezolana)
    - Registro histórico de cambios
    - Configuración de IGTF
    """

    # Códigos de monedas fuertes respecto al VES
    STRONG_CURRENCIES = {"USD", "EUR", "GBP", "CHF", "CAD", "AUD"}

    # Monedas más débiles que VES (zonas fronterizas)
    WEAK_CURRENCIES = {"COP", "BRL", "ARS", "COP"}

    @staticmethod
    def validate_iso_4217(code: str) -> Tuple[bool, Optional[str]]:
        """
        Valida código ISO 4217.

        Args:
            code: Código de moneda a validar

        Returns:
            Tuple[es_válido, mensaje_error]
        """
        if not code or len(code) != 3:
            return False, f"Código debe tener 3 caracteres ISO 4217, got: {code}"

        code = code.upper()

        # Verificar formato alfanumérico
        if not code.isalpha():
            return False, f"Código debe ser solo letras, got: {code}"

        # Verificar contra lista oficial
        # ISO_4217_CURRENCIES ya está importado al nivel del módulo

        if code not in ISO_4217_CURRENCIES:
            return False, f"Código '{code}' no está en lista oficial ISO 4217"

        return True, None

    @staticmethod
    def calculate_conversion_factor(
        code: str,
        rate: Decimal,
        method: Optional[ConversionMethod]
    ) -> Tuple[Optional[Decimal], Optional[str]]:
        """
        Calcula el factor de conversión según lógica venezolana:

        1. VES: factor = None (moneda base, no aplica)
        2. Moneda más fuerte (USD, EUR): factor = 1 / rate
        3. Moneda más débil (COP): factor = rate
        4. Otras: via USD (triangulación)

        Args:
            code: Código de moneda
            rate: Tasa de cambio actual
            method: Método de conversión

        Returns:
            Tuple[factor, metodo_usado]
        """
        code = code.upper()

        # Asegurar que rate sea Decimal
        if not isinstance(rate, Decimal):
            rate = Decimal(str(rate))

        # Caso 1: VES (moneda base)
        if code == "VES":
            return None, ConversionMethod.UNDEFINED

        # Caso 2: Monedas más fuertes (USD, EUR, etc.)
        if method == ConversionMethod.DIRECT or code in CurrencyBusinessLogic.STRONG_CURRENCIES:
            # Factor = 1 / tasa
            # Ejemplo: USD 36.50 -> factor = 1/36.50 = 0.0274
            if rate > 0:
                factor = Decimal("1") / rate
                return factor.quantize(Decimal("0.0000000001")), ConversionMethod.DIRECT

        # Caso 3: Monedas más débiles (COP, etc.)
        elif method == ConversionMethod.INVERSE or code in CurrencyBusinessLogic.WEAK_CURRENCIES:
            # Factor = tasa
            # Ejemplo: COP 0.0091 -> factor = 0.0091
            return rate, ConversionMethod.INVERSE

        # Caso 4: Triangulación por USD
        elif method == ConversionMethod.VIA_USD:
            # Se calcula en tiempo real usando tasa USD->VES
            # Factor = (1 / tasa_usd_ves)
            return rate, ConversionMethod.VIA_USD

        return None, None

    @staticmethod
    def determine_igtf_applicability(code: str) -> Tuple[bool, Optional[str]]:
        """
        Determina si aplica IGTF según tipo de moneda.

        Lógica venezolana:
        - VES: NO aplica (moneda nacional)
        - USD, EUR: SÍ aplica (divisas)
        - Otras monedas: Depende de configuración

        Args:
            code: Código de moneda

        Returns:
            Tuple[aplica, razón]
        """
        code = code.upper()

        if code == "VES":
            return False, "Moneda nacional, no aplica IGTF"

        elif code in {"USD", "EUR"}:
            return True, "Divisa extranjera, aplica IGTF (Ley de IGTF)"

        else:
            return False, "Moneda no sujeta a IGTF (requiere configuración especial)"

    @staticmethod
    def calculate_igtf(
        amount: Decimal,
        currency: str,
        applies_igtf: bool,
        igtf_rate: Decimal,
        is_exempt: bool = False
    ) -> Tuple[Decimal, bool, str]:
        """
        Calcula el IGTF para un monto según moneda.

        Args:
            amount: Monto en moneda extranjera
            currency: Moneda del monto
            applies_igtf: Si aplica IGTF para esta moneda
            igtf_rate: Tasa de IGTF
            is_exempt: Si está exento

        Returns:
            Tuple[igtf_calculado, aplicó, razón]
        """
        currency = currency.upper()

        # No aplica IGTF
        if not applies_igtf or is_exempt:
            return Decimal("0"), False, f"IGTF no aplica para {currency}"

        # Verificar si la moneda es VES
        if currency == "VES":
            return Decimal("0"), False, "Moneda nacional, no aplica IGTF"

        # Calcular IGTF
        igtf_amount = (amount * igtf_rate) / Decimal("100")

        # Redondear a 2 decimales
        igtf_amount = igtf_amount.quantize(Decimal("0.01"))

        return igtf_amount, True, f"IGTF {igtf_rate}% aplicado a {currency}"

    @staticmethod
    def convert_currency(
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        method: str = "direct"
    ) -> Tuple[Decimal, Decimal, str]:
        """
        Convierte monto entre dos monedas usando tasa de cambio.

        Args:
            amount: Monto a convertir
            from_currency: Moneda origen (ej: USD, VES)
            to_currency: Moneda destino (ej: VES, USD)
            rate: Tasa de cambio (ya ajustada según dirección por get_exchange_rate_with_metadata)
            method: Método de conversión (direct, inverse, via_usd)

        Returns:
            Tuple[monto_convertido, tasa_usada, método]
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Convertir amount a Decimal para evitar errores de tipo
        amount_decimal = Decimal(str(amount))

        # Si es la misma moneda
        if from_currency == to_currency:
            return amount_decimal, Decimal("1"), "direct"

        # La tasa ya viene ajustada desde get_exchange_rate_with_metadata:
        # - USD → VES: rate = 38.5 (directa), converted = amount * rate
        # - VES → USD: rate = 1/38.5 (inversa), converted = amount * rate
        # Así que SIEMPRE multiplicamos, la tasa ya está ajustada

        if rate == 0:
            raise ValueError("Tasa de cambio no puede ser cero")

        converted = amount_decimal * rate
        return converted.quantize(Decimal("0.01")), rate, method


class CurrencyService:
    """
    Servicio de gestión de monedas con lógica de negocio y auditoría.

    Proporciona:
    - CRUD de monedas con validación
    - Actualización de tasas con registro histórico
    - Consultas de historial
    - Configuración de IGTF
    """

    def __init__(self, db: Session):
        self.db = db
        self.logic = CurrencyBusinessLogic()

    def create_currency(
        self,
        currency_data: CurrencyCreate,
        company_id: int,
        user_id: int
    ) -> Currency:
        """
        Crea nueva moneda con validaciones y cálculos automáticos.

        Args:
            currency_data: Datos de la moneda
            company_id: ID de empresa
            user_id: ID de usuario que crea

        Returns:
            Currency: Moneda creada
        """
        # 1. Validar ISO 4217
        is_valid, error_msg = self.logic.validate_iso_4217(currency_data.code)
        if not is_valid:
            raise ValueError(f"Código ISO inválido: {error_msg}")

        code = currency_data.code.upper()

        # 2. Verificar que no exista otra moneda base en la empresa
        if currency_data.is_base_currency:
            existing_base = self.db.query(Currency).filter(
                Currency.company_id == company_id,
                Currency.is_base_currency == True
            ).first()

            if existing_base:
                raise ValueError(
                    f"Ya existe moneda base: {existing_base.code}. "
                    f"Solo puede haber una moneda base por empresa."
                )

        # 3. Calcular factor de conversión
        factor, method_used = self.logic.calculate_conversion_factor(
            code=code,
            rate=currency_data.exchange_rate,
            method=currency_data.conversion_method
        )

        # 4. Crear moneda
        db_currency = Currency(
            company_id=company_id,
            code=code,
            name=currency_data.name,
            symbol=currency_data.symbol,
            exchange_rate=currency_data.exchange_rate,
            decimal_places=currency_data.decimal_places,
            is_base_currency=currency_data.is_base_currency,
            is_active=True,
            conversion_factor=factor,
            conversion_method=method_used.value if method_used else None,
            applies_igtf=currency_data.applies_igtf,
            igtf_rate=currency_data.igtf_rate,
            igtf_exempt=currency_data.igtf_exempt,
            igtf_min_amount=currency_data.igtf_min_amount,
            rate_update_method=currency_data.rate_update_method.value,
            rate_source_url=currency_data.rate_source_url,
            last_rate_update=datetime.now(),
            created_by=user_id,
            notes=currency_data.notes
        )

        self.db.add(db_currency)
        self.db.flush()
        self.db.commit()
        self.db.refresh(db_currency)

        logger.info(
            f"Currency created: {code} (company: {company_id}, user: {user_id}), "
            f"factor: {factor}, method: {method_used}"
        )

        return db_currency

    def update_currency_rate(
        self,
        currency_id: int,
        rate_update: CurrencyRateUpdate,
        company_id: int,
        user_id: int,
        user_ip: str = None
    ) -> Currency:
        """
        Actualiza la tasa de cambio con registro histórico completo.

        Args:
            currency_id: ID de moneda
            rate_update: Datos de actualización
            company_id: ID de empresa
            user_id: ID de usuario
            user_ip: IP del usuario

        Returns:
            Currency: Moneda actualizada
        """
        # 1. Obtener moneda
        currency = self.db.query(Currency).filter(
            Currency.id == currency_id,
            Currency.company_id == company_id
        ).first()

        if not currency:
            raise ValueError(f"Moneda no encontrada: ID {currency_id}")

        # 2. Guardar tasa anterior
        old_rate = currency.exchange_rate
        new_rate = rate_update.new_rate

        # Asegurar que ambos sean Decimal
        if not isinstance(old_rate, Decimal):
            old_rate = Decimal(str(old_rate))
        if not isinstance(new_rate, Decimal):
            new_rate = Decimal(str(new_rate))

        # 3. Calcular diferencia y variación
        rate_difference = new_rate - old_rate
        rate_variation = ((new_rate - old_rate) / old_rate * Decimal("100")) if old_rate > 0 else None

        # 4. Crear registro histórico ANTES de actualizar
        history = CurrencyRateHistory(
            currency_id=currency_id,
            company_id=company_id,
            old_rate=old_rate,
            new_rate=new_rate,
            rate_difference=rate_difference,
            rate_variation_percent=rate_variation,
            changed_by=user_id,
            change_type=rate_update.change_type,
            change_source=rate_update.change_source,
            user_ip=user_ip,
            change_reason=rate_update.change_reason,
            provider_metadata=str(rate_update.provider_metadata) if rate_update.provider_metadata else None,
            changed_at=datetime.now()
        )

        self.db.add(history)

        # 5. Actualizar tasa
        currency.exchange_rate = new_rate
        currency.last_rate_update = datetime.now()
        currency.updated_by = user_id

        # Recalcular factor de conversión si es necesario
        if currency.conversion_method:
            factor, _ = self.logic.calculate_conversion_factor(
                code=currency.code,
                rate=new_rate,
                method=ConversionMethod(currency.conversion_method)
            )
            currency.conversion_factor = factor

        self.db.commit()
        self.db.refresh(currency)

        logger.info(
            f"Rate updated: {currency.code} {old_rate} -> {new_rate} "
            f"(diff: {rate_difference}, var: {rate_variation}%)"
        )

        return currency

    def get_currency_history(
        self,
        currency_id: int,
        company_id: int,
        limit: int = 100
    ) -> List[CurrencyRateHistory]:
        """
        Obtiene historial de cambios de tasa de una moneda.

        Args:
            currency_id: ID de moneda
            company_id: ID de empresa
            limit: Límite de registros

        Returns:
            List[CurrencyRateHistory]: Historial ordenado por fecha descendente
        """
        history = self.db.query(CurrencyRateHistory).filter(
            CurrencyRateHistory.currency_id == currency_id,
            CurrencyRateHistory.company_id == company_id
        ).order_by(
            CurrencyRateHistory.changed_at.desc()
        ).limit(limit).all()

        return history

    def get_igtf_config(
        self,
        company_id: int,
        currency_id: Optional[int] = None
    ) -> List[IGTFConfig]:
        """
        Obtiene configuración de IGTF.

        Args:
            company_id: ID de empresa
            currency_id: ID de moneda (opcional)

        Returns:
            List[IGTFConfig]: Configuraciones vigentes
        """
        now = datetime.now()

        query = self.db.query(IGTFConfig).filter(
            IGTFConfig.company_id == company_id,
            IGTFConfig.valid_from <= now,
            or_(
                IGTFConfig.valid_until.is_(None),
                IGTFConfig.valid_until > now
            )
        )

        if currency_id:
            query = query.filter(IGTFConfig.currency_id == currency_id)

        return query.all()

    def calculate_igtf_for_transaction(
        self,
        amount: Decimal,
        currency_id: int,
        company_id: int,
        payment_method: str = "transfer"
    ) -> Tuple[Decimal, bool, Dict]:
        """
        Calcula IGTF para una transacción según configuración vigente.

        Args:
            amount: Monto en moneda extranjera
            currency_id: ID de moneda
            company_id: ID de empresa
            payment_method: Método de pago

        Returns:
            Tuple[igtf_amount, applied, metadata]
        """
        # Obtener moneda
        currency = self.db.query(Currency).filter(
            Currency.id == currency_id,
            Currency.company_id == company_id
        ).first()

        if not currency:
            raise ValueError(f"Moneda no encontrada: ID {currency_id}")

        # Obtener config de IGTF
        igtf_configs = self.get_igtf_config(company_id, currency_id)
        igtf_config = igtf_configs[0] if igtf_configs else None

        # Determinar si aplica
        applies = False
        rate = Decimal("0")
        reason = ""

        if currency.igtf_exempt:
            reason = "Moneda exenta de IGTF"
        elif not currency.applies_igtf:
            reason = f"IGTF no aplica para {currency.code}"
        elif igtf_config and igtf_config.is_exempt:
            reason = "Configuración exenta de IGTF"
        elif igtf_config and igtf_config.applicable_payment_methods:
            # Verificar si el método de pago aplica
            import json
            methods = json.loads(igtf_config.applicable_payment_methods) if isinstance(igtf_config.applicable_payment_methods, str) else igtf_config.applicable_payment_methods

            if payment_method not in methods:
                reason = f"Método {payment_method} no aplica IGTF"
            else:
                applies = True
                rate = igtf_config.igtf_rate
                reason = f"IGTF {rate}% aplicado"
        else:
            applies = True
            rate = currency.igtf_rate
            reason = f"IGTF {rate}% aplicado"

        # Calcular IGTF
        if applies:
            igtf_amount = (amount * rate) / Decimal("100")
            igtf_amount = igtf_amount.quantize(Decimal("0.01"))
        else:
            igtf_amount = Decimal("0")

        metadata = {
            "currency_code": currency.code,
            "applies": applies,
            "rate": float(rate),
            "reason": reason,
            "igtf_config_id": igtf_config.id if igtf_config else None
        }

        return igtf_amount, applies, metadata

    def get_exchange_rate_with_metadata(
        self,
        from_currency: str,
        to_currency: str,
        company_id: int,
        date: Optional[datetime] = None
    ) -> Tuple[Decimal, Dict]:
        """
        Obtiene tasa de cambio con metadata completa para auditoría.

        Args:
            from_currency: Moneda origen
            to_currency: Moneda destino
            company_id: ID de empresa
            date: Fecha para tasa histórica (opcional)

        Returns:
            Tuple[tasa, metadata]
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        base_currency = "VES"

        # Si es misma moneda
        if from_currency == to_currency:
            return Decimal("1"), {
                "rate": 1.0,
                "method": "direct",
                "source": "same_currency",
                "last_update": datetime.now().isoformat(),
                "currency_id": 0,
                "decimal_places": 2
            }

        # Estrategia para obtener la tasa correcta según dirección
        # Caso 1: Moneda fuerte (USD) → Base (VES)
        if from_currency in CurrencyBusinessLogic.STRONG_CURRENCIES and to_currency == base_currency:
            currency = self.db.query(Currency).filter(
                Currency.code == from_currency,
                Currency.company_id == company_id,
                Currency.is_active == True
            ).first()

            if not currency:
                raise ValueError(f"Moneda no encontrada o inactiva: {from_currency}")

            rate = currency.exchange_rate
            method = currency.conversion_method or "direct"
            source = currency.rate_update_method
            last_update = currency.last_rate_update

            metadata = {
                "rate": float(rate),
                "method": method,
                "source": source,
                "last_update": last_update.isoformat() if last_update else None,
                "currency_id": currency.id,
                "decimal_places": currency.decimal_places
            }

            return rate, metadata

        # Caso 2: Base (VES) → Moneda fuerte (USD) - NECESITA TASA INVERSA
        elif from_currency == base_currency and to_currency in CurrencyBusinessLogic.STRONG_CURRENCIES:
            currency = self.db.query(Currency).filter(
                Currency.code == to_currency,  # Obtener moneda destino (USD)
                Currency.company_id == company_id,
                Currency.is_active == True
            ).first()

            if not currency:
                raise ValueError(f"Moneda no encontrada o inactiva: {to_currency}")

            # Para VES → USD, necesitamos la tasa inversa de USD
            rate = currency.exchange_rate
            method = currency.conversion_method or "direct"
            source = currency.rate_update_method
            last_update = currency.last_rate_update

            # Calcular tasa inversa
            if rate == 0:
                raise ValueError("Tasa de cambio no puede ser cero")
            inverse_rate = Decimal("1") / Decimal(str(rate))

            metadata = {
                "rate": float(inverse_rate),  # Tasa inversa
                "method": "inverse",
                "source": source,
                "last_update": last_update.isoformat() if last_update else None,
                "currency_id": currency.id,
                "decimal_places": currency.decimal_places
            }

            return inverse_rate, metadata

        # Caso 3: Moneda fuerte → Moneda fuerte (USD → EUR o EUR → USD)
        # Necesitamos convertir a través de VES
        elif from_currency in CurrencyBusinessLogic.STRONG_CURRENCIES and to_currency in CurrencyBusinessLogic.STRONG_CURRENCIES:
            # Obtener ambas monedas
            from_curr = self.db.query(Currency).filter(
                Currency.code == from_currency,
                Currency.company_id == company_id,
                Currency.is_active == True
            ).first()

            to_curr = self.db.query(Currency).filter(
                Currency.code == to_currency,
                Currency.company_id == company_id,
                Currency.is_active == True
            ).first()

            if not from_curr:
                raise ValueError(f"Moneda no encontrada o inactiva: {from_currency}")
            if not to_curr:
                raise ValueError(f"Moneda no encontrada o inactiva: {to_currency}")

            # Calcular tasa cruzada a través de VES
            # Ejemplo: EUR → USD = (EUR_rate / USD_rate)
            # 100 EUR * 401.35 = 40,135 VES
            # 40,135 VES / 344.50 = 116.46 USD
            # Tasa EUR → USD = 401.35 / 344.50 = 1.165

            if from_curr.exchange_rate == 0 or to_curr.exchange_rate == 0:
                raise ValueError("Tasa de cambio no puede ser cero")

            cross_rate = Decimal(str(from_curr.exchange_rate)) / Decimal(str(to_curr.exchange_rate))

            metadata = {
                "rate": float(cross_rate),
                "method": "cross_rate",
                "source": "calculated_via_base",
                "last_update": datetime.now().isoformat(),
                "currency_id": from_curr.id,
                "decimal_places": from_curr.decimal_places
            }

            return cross_rate, metadata

        # Caso por defecto: obtener moneda origen
        else:
            currency = self.db.query(Currency).filter(
                Currency.code == from_currency,
                Currency.company_id == company_id,
                Currency.is_active == True
            ).first()

            if not currency:
                raise ValueError(f"Moneda no encontrada o inactiva: {from_currency}")

            rate = currency.exchange_rate
            method = currency.conversion_method or "direct"
            source = currency.rate_update_method
            last_update = currency.last_rate_update

            metadata = {
                "rate": float(rate),
                "method": method,
                "source": source,
                "last_update": last_update.isoformat() if last_update else None,
                "currency_id": currency.id,
                "decimal_places": currency.decimal_places
            }

            return rate, metadata

    def get_currency_statistics(
        self,
        company_id: int,
        currency_id: int
    ) -> Dict:
        """
        Obtiene estadísticas de una moneda.

        Args:
            company_id: ID de empresa
            currency_id: ID de moneda

        Returns:
            Dict con estadísticas
        """
        currency = self.db.query(Currency).filter(
            Currency.id == currency_id,
            Currency.company_id == company_id
        ).first()

        if not currency:
            raise ValueError(f"Moneda no encontrada: ID {currency_id}")

        # Obtener historial
        history = self.get_currency_history(currency_id, company_id, limit=1000)

        # Calcular estadísticas
        total_changes = len(history)

        if total_changes > 0:
            last_change = history[0]
            first_change = history[-1]

            avg_variation = sum(
                h.rate_variation_percent or 0
                for h in history
            ) / total_changes

            max_change = max(
                (h.rate_variation_percent or 0) for h in history
            )

            min_change = min(
                (h.rate_variation_percent or 0) for h in history
            )
        else:
            last_change = None
            first_change = None
            avg_variation = 0
            max_change = 0
            min_change = 0

        return {
            "currency_code": currency.code,
            "currency_name": currency.name,
            "current_rate": float(currency.exchange_rate),
            "decimal_places": currency.decimal_places,
            "is_base": currency.is_base_currency,
            "applies_igtf": currency.applies_igtf,
            "igtf_rate": float(currency.igtf_rate) if currency.igtf_rate else None,
            "total_rate_changes": total_changes,
            "last_change": last_change.to_dict() if last_change else None,
            "first_change": first_change.to_dict() if first_change else None,
            "avg_variation_percent": float(avg_variation) if avg_variation else 0,
            "max_variation_percent": float(max_change) if max_change else 0,
            "min_variation_percent": float(min_change) if min_change else 0,
            "created_at": currency.created_at.isoformat(),
            "last_update": currency.updated_at.isoformat()
        }
