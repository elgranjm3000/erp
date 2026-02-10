"""
Servicio de Tasas Diarias - Sistema Multi-Moneda Escalable
Integra BCVProvider con DailyRate para historial completo de tasas
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.daily_rates import DailyRate
from models.currency_config import Currency
from core.exchange_rate_providers.bcv_provider import BCVProvider


logger = logging.getLogger(__name__)


class DailyRateService:
    """
    Servicio para gestión de tasas diarias de cambio.

    Características:
    - Obtiene tasas del BCV automáticamente
    - Guarda historial completo en DailyRate
    - Proporciona tasa del día para facturas
    - Soporta tasas manuales con override
    - Cache para optimizar consultas
    """

    def __init__(self, db: Session, company_id: int):
        """
        Inicializa el servicio de tasas diarias.

        Args:
            db: Sesión de base de datos
            company_id: ID de la empresa
        """
        self.db = db
        self.company_id = company_id
        self.bcv_provider = BCVProvider()

    def sync_bcv_rates(
        self,
        user_id: Optional[int] = None,
        force_refresh: bool = False
    ) -> Dict[str, any]:
        """
        Sincroniza las tasas del BCV con la base de datos.

        Args:
            user_id: ID del usuario que inicia la sincronización
            force_refresh: Forzar actualización aunque el cache sea válido

        Returns:
            Dict con resultados de la sincronización
        """
        results = {
            "synced_rates": [],
            "failed_rates": [],
            "skipped_rates": [],
            "timestamp": datetime.now().isoformat(),
            "total_synced": 0,
            "total_failed": 0
        }

        try:
            # Forzar refresh del provider si es necesario
            if force_refresh:
                self.bcv_provider.refresh_rates()

            # Obtener monedas activas de la empresa
            currencies = self.db.query(Currency).filter(
                Currency.company_id == self.company_id,
                Currency.is_active == True
            ).all()

            # Obtener VES como moneda base
            ves_currency = self.db.query(Currency).filter(
                Currency.company_id == self.company_id,
                Currency.code == "VES",
                Currency.is_base_currency == True
            ).first()

            if not ves_currency:
                results["failed_rates"].append({
                    "currency": "VES",
                    "error": "VES base currency not found"
                })
                return results

            today = date.today()

            # Sincronizar cada moneda soportada por BCV
            for currency in currencies:
                if currency.code == "VES":
                    continue  # Skip VES

                try:
                    # Obtener tasa desde BCV (VES → USD)
                    # BCV publica tasas desde VES hacia otras monedas
                    bcv_rate = self.bcv_provider.get_rate(
                        from_currency="VES",
                        to_currency=currency.code
                    )

                    if bcv_rate is None:
                        results["skipped_rates"].append({
                            "code": currency.code,
                            "reason": "Rate not available from BCV"
                        })
                        continue

                    # Verificar si ya existe tasa para hoy
                    existing_rate = self.db.query(DailyRate).filter(
                        DailyRate.company_id == self.company_id,
                        DailyRate.base_currency_id == ves_currency.id,
                        DailyRate.target_currency_id == currency.id,
                        DailyRate.rate_date == today
                    ).first()

                    if existing_rate:
                        # Si la tasa no cambió, skip
                        if Decimal(str(existing_rate.exchange_rate)) == Decimal(str(bcv_rate)):
                            results["skipped_rates"].append({
                                "code": currency.code,
                                "rate": float(bcv_rate),
                                "reason": "Rate unchanged"
                            })
                            continue

                        # Actualizar tasa existente
                        existing_rate.exchange_rate = float(bcv_rate)
                        existing_rate.source = "BCV"
                        existing_rate.updated_at = datetime.now()
                        existing_rate.updated_by = user_id
                        existing_rate.is_active = True

                        results["synced_rates"].append({
                            "code": currency.code,
                            "rate": float(bcv_rate),
                            "action": "updated"
                        })

                    else:
                        # Crear nueva tasa diaria
                        daily_rate = DailyRate(
                            company_id=self.company_id,
                            base_currency_id=ves_currency.id,
                            target_currency_id=currency.id,
                            rate_date=today,
                            exchange_rate=float(bcv_rate),
                            source="BCV",
                            is_active=True,
                            created_by=user_id
                        )

                        self.db.add(daily_rate)
                        results["synced_rates"].append({
                            "code": currency.code,
                            "rate": float(bcv_rate),
                            "action": "created"
                        })

                    results["total_synced"] += 1

                except Exception as e:
                    logger.error(f"Error syncing {currency.code}: {e}")
                    results["failed_rates"].append({
                        "code": currency.code,
                        "error": str(e)
                    })
                    results["total_failed"] += 1

            # Commit de todos los cambios
            self.db.commit()

            logger.info(
                f"BCV sync completed: {results['total_synced']} synced, "
                f"{results['total_failed']} failed"
            )

        except Exception as e:
            logger.error(f"Error in sync_bcv_rates: {e}")
            self.db.rollback()
            results["error"] = str(e)

        return results

    def get_rate_for_date(
        self,
        from_currency_code: str,
        to_currency_code: str,
        rate_date: date
    ) -> Optional[DailyRate]:
        """
        Obtiene la tasa de cambio para una fecha específica.

        Args:
            from_currency_code: Moneda origen (ej: "USD")
            to_currency_code: Moneda destino (ej: "VES")
            rate_date: Fecha de la tasa

        Returns:
            DailyRate o None si no existe
        """
        from_currency = self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.code == from_currency_code,
            Currency.is_active == True
        ).first()

        to_currency = self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.code == to_currency_code,
            Currency.is_active == True
        ).first()

        if not from_currency or not to_currency:
            return None

        return self.db.query(DailyRate).filter(
            DailyRate.company_id == self.company_id,
            DailyRate.base_currency_id == from_currency.id,
            DailyRate.target_currency_id == to_currency.id,
            DailyRate.rate_date == rate_date,
            DailyRate.is_active == True
        ).first()

    def get_today_rate(
        self,
        from_currency_code: str,
        to_currency_code: str
    ) -> Optional[DailyRate]:
        """
        Obtiene la tasa de cambio de hoy.

        Si no existe tasa para hoy, intenta obtenerla del BCV
        y guardarla automáticamente.

        Args:
            from_currency_code: Moneda origen (ej: "USD")
            to_currency_code: Moneda destino (ej: "VES")

        Returns:
            DailyRate o None si no está disponible
        """
        logger.info(f"🔍 get_today_rate: {from_currency_code} → {to_currency_code} | Company: {self.company_id}")

        today = date.today()

        # Buscar tasa directa (ej: USD → VES)
        rate = self.get_rate_for_date(from_currency_code, to_currency_code, today)
        logger.info(f"  Direct rate {from_currency_code} → {to_currency_code}: {rate}")

        if rate:
            logger.info(f"✅ Returning direct rate: {rate.exchange_rate}")
            return rate

        # Si no existe, buscar tasa inversa (ej: VES → USD) y usar el mismo rate
        # Nota: BCV publica tasas como "1 USD = X VES", así que el rate es el mismo
        # en ambas direcciones para efectos de conversión
        inverse_rate = self.get_rate_for_date(to_currency_code, from_currency_code, today)
        logger.info(f"  Inverse rate {to_currency_code} → {from_currency_code}: {inverse_rate}")

        if inverse_rate:
            # Crear un objeto DailyRate con el mismo rate (no invertido)
            from_currency = self.db.query(Currency).filter(
                Currency.company_id == self.company_id,
                Currency.code == from_currency_code,
                Currency.is_active == True
            ).first()

            to_currency = self.db.query(Currency).filter(
                Currency.company_id == self.company_id,
                Currency.code == to_currency_code,
                Currency.is_active == True
            ).first()

            logger.info(f"  Currency objects: {from_currency_code} (ID:{from_currency.id if from_currency else None}), {to_currency_code} (ID:{to_currency.id if to_currency else None})")

            if from_currency and to_currency:
                # Retornar un DailyRate temporal con el mismo rate
                # Si VES → USD es 344.507, entonces USD → VES también es 344.507
                # (porque BCV publica "1 USD = 344.507 VES")
                result = DailyRate(
                    id=inverse_rate.id,
                    company_id=self.company_id,
                    base_currency_id=from_currency.id,
                    target_currency_id=to_currency.id,
                    rate_date=today,
                    exchange_rate=inverse_rate.exchange_rate,  # Usar el mismo rate
                    source=inverse_rate.source,
                    is_active=True,
                    created_at=inverse_rate.created_at,
                    updated_at=inverse_rate.updated_at
                )
                logger.info(f"✅ Returning inverse rate: {result.exchange_rate}")
                return result
            else:
                logger.error(f"❌ Currency objects not found: from={from_currency}, to={to_currency}")

        # Si no existe y es USD→VES o VES→USD, intentar obtener del BCV
        if {from_currency_code, to_currency_code} & {"USD", "VES"}:
            logger.info(f"  Attempting BCV sync...")
            try:
                sync_result = self.sync_bcv_rates(user_id=None)
                logger.info(f"  BCV sync result: {sync_result}")
                if sync_result.get("total_synced", 0) > 0:
                    # Reintentar búsqueda
                    rate = self.get_rate_for_date(
                        from_currency_code,
                        to_currency_code,
                        today
                    )
                    if rate:
                        logger.info(f"✅ Returning rate after sync: {rate.exchange_rate}")
                        return rate

                    # Intentar nuevamente con tasa inversa
                    inverse_rate = self.get_rate_for_date(to_currency_code, from_currency_code, today)
                    if inverse_rate:
                        from_currency = self.db.query(Currency).filter(
                            Currency.company_id == self.company_id,
                            Currency.code == from_currency_code,
                            Currency.is_active == True
                        ).first()

                        to_currency = self.db.query(Currency).filter(
                            Currency.company_id == self.company_id,
                            Currency.code == to_currency_code,
                            Currency.is_active == True
                        ).first()

                        if from_currency and to_currency:
                            result = DailyRate(
                                id=inverse_rate.id,
                                company_id=self.company_id,
                                base_currency_id=from_currency.id,
                                target_currency_id=to_currency.id,
                                rate_date=today,
                                exchange_rate=inverse_rate.exchange_rate,  # Usar el mismo rate
                                source=inverse_rate.source,
                                is_active=True,
                                created_at=inverse_rate.created_at,
                                updated_at=inverse_rate.updated_at
                            )
                            logger.info(f"✅ Returning inverse rate after sync: {result.exchange_rate}")
                            return result
            except Exception as e:
                logger.error(f"Error auto-syncing BCV rate: {e}")

        # Si no hay tasa de hoy, buscar la más reciente
        logger.info(f"  No rate found, trying latest...")
        latest = self.get_latest_rate(from_currency_code, to_currency_code)
        logger.info(f"  Latest rate: {latest}")
        return latest

    def get_latest_rate(
        self,
        from_currency_code: str,
        to_currency_code: str
    ) -> Optional[DailyRate]:
        """
        Obtiene la tasa más reciente disponible.

        Args:
            from_currency_code: Moneda origen
            to_currency_code: Moneda destino

        Returns:
            DailyRate más reciente o None
        """
        from_currency = self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.code == from_currency_code,
            Currency.is_active == True
        ).first()

        to_currency = self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.code == to_currency_code,
            Currency.is_active == True
        ).first()

        if not from_currency or not to_currency:
            return None

        return self.db.query(DailyRate).filter(
            DailyRate.company_id == self.company_id,
            DailyRate.base_currency_id == from_currency.id,
            DailyRate.target_currency_id == to_currency.id,
            DailyRate.is_active == True
        ).order_by(DailyRate.rate_date.desc()).first()

    def create_manual_rate(
        self,
        from_currency_code: str,
        to_currency_code: str,
        rate_date: date,
        exchange_rate: float,
        user_id: int,
        notes: Optional[str] = None
    ) -> DailyRate:
        """
        Crea una tasa manual con override.

        Args:
            from_currency_code: Moneda origen
            to_currency_code: Moneda destino
            rate_date: Fecha de la tasa
            exchange_rate: Tasa de cambio
            user_id: ID del usuario
            notes: Notas justificando la tasa manual

        Returns:
            DailyRate creada
        """
        from_currency = self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.code == from_currency_code,
            Currency.is_active == True
        ).first()

        to_currency = self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.code == to_currency_code,
            Currency.is_active == True
        ).first()

        if not from_currency or not to_currency:
            raise ValueError(f"Currencies not found: {from_currency_code} → {to_currency_code}")

        # Verificar si ya existe tasa para esa fecha
        existing = self.db.query(DailyRate).filter(
            DailyRate.company_id == self.company_id,
            DailyRate.base_currency_id == from_currency.id,
            DailyRate.target_currency_id == to_currency.id,
            DailyRate.rate_date == rate_date
        ).first()

        if existing:
            # Desactivar la anterior
            existing.is_active = False
            existing.updated_by = user_id
            existing.updated_at = datetime.now()

        # Crear nueva tasa manual
        daily_rate = DailyRate(
            company_id=self.company_id,
            base_currency_id=from_currency.id,
            target_currency_id=to_currency.id,
            rate_date=rate_date,
            exchange_rate=exchange_rate,
            source="MANUAL",
            is_active=True,
            created_by=user_id,
            notes=notes
        )

        self.db.add(daily_rate)
        self.db.commit()
        self.db.refresh(daily_rate)

        logger.info(
            f"Manual rate created: {from_currency_code}→{to_currency_code} = {exchange_rate} "
            f"for {rate_date} by user {user_id}"
        )

        return daily_rate

    def get_rate_history(
        self,
        from_currency_code: str,
        to_currency_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[DailyRate]:
        """
        Obtiene el historial de tasas para un par de monedas.

        Args:
            from_currency_code: Moneda origen
            to_currency_code: Moneda destino
            start_date: Fecha inicial (opcional)
            end_date: Fecha final (opcional)
            limit: Límite de registros

        Returns:
            Lista de DailyRate ordenadas por fecha descendente
        """
        from_currency = self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.code == from_currency_code,
            Currency.is_active == True
        ).first()

        to_currency = self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.code == to_currency_code,
            Currency.is_active == True
        ).first()

        if not from_currency or not to_currency:
            return []

        query = self.db.query(DailyRate).filter(
            DailyRate.company_id == self.company_id,
            DailyRate.base_currency_id == from_currency.id,
            DailyRate.target_currency_id == to_currency.id,
            DailyRate.is_active == True
        )

        if start_date:
            query = query.filter(DailyRate.rate_date >= start_date)

        if end_date:
            query = query.filter(DailyRate.rate_date <= end_date)

        return query.order_by(DailyRate.rate_date.desc()).limit(limit).all()

    def calculate_conversion(
        self,
        amount: Decimal,
        from_currency_code: str,
        to_currency_code: str,
        rate_date: Optional[date] = None,
        manual_rate: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Convierte un monto de una moneda a otra.

        Args:
            amount: Monto a convertir
            from_currency_code: Moneda origen
            to_currency_code: Moneda destino
            rate_date: Fecha de la tasa (usar hoy si es None)
            manual_rate: Tasa manual para override (opcional)

        Returns:
            Dict con:
                - converted_amount: Monto convertido
                - rate: Tasa utilizada
                - rate_date: Fecha de la tasa
                - source: Fuente de la tasa (BCV/MANUAL)
                - inverse_rate: Tasa inversa
        """
        if manual_rate is not None:
            # Usar tasa manual
            rate_value = Decimal(str(manual_rate))
            rate_source = "MANUAL"
            used_date = rate_date or date.today()
        else:
            # Buscar tasa en la base de datos
            used_date = rate_date or date.today()
            daily_rate = self.get_today_rate(from_currency_code, to_currency_code)

            if not daily_rate:
                raise ValueError(
                    f"No rate available for {from_currency_code}→{to_currency_code} "
                    f"on {used_date}"
                )

            rate_value = Decimal(str(daily_rate.exchange_rate))
            rate_source = daily_rate.source
            used_date = daily_rate.rate_date

        # Calcular conversión
        converted_amount = amount * rate_value

        # Calcular tasa inversa
        inverse_rate = Decimal("1") / rate_value if rate_value != 0 else None

        return {
            "converted_amount": converted_amount,
            "rate": rate_value,
            "rate_date": used_date,
            "source": rate_source,
            "inverse_rate": inverse_rate
        }

    def get_bcv_status(self) -> Dict[str, any]:
        """
        Obtiene el estado del servicio BCV.

        Returns:
            Dict con información del estado
        """
        try:
            is_available = self.bcv_provider.is_available()
            last_update = self.bcv_provider.get_last_update_time()
            cached_rates = self.bcv_provider.get_cached_rates()

            return {
                "available": is_available,
                "last_update": last_update.isoformat() if last_update else None,
                "cached_rates": {
                    code: {
                        "rate": float(rate.rate),
                        "date": rate.date.isoformat()
                    }
                    for code, rate in cached_rates.items()
                },
                "supported_currencies": self.bcv_provider.get_supported_currencies()
            }

        except Exception as e:
            logger.error(f"Error getting BCV status: {e}")
            return {
                "available": False,
                "error": str(e)
            }
