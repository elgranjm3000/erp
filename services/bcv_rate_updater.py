"""
Servicio de Actualización Automática de Tasas BCV
Actualiza periódicamente las monedas configuradas con api_bcv
"""

import logging
from typing import Dict
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from models.currency_config import Currency
from core.exchange_rate_providers.bcv_provider import BCVProvider
from core.exchange_rate_providers.base import ProviderNotAvailableError
from schemas import CurrencyRateUpdate
from services.currency_business_service import CurrencyService

logger = logging.getLogger(__name__)


class BCVRateUpdater:
    """
    Servicio para actualizar automáticamente tasas BCV.

    Se puede ejecutar:
    - Manualmente vía API endpoint
    - Programado vía cron/Linux scheduler
    - Como tarea en background (Celery/Redis)
    """

    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
        self.bcv_provider = BCVProvider()

    def update_bcv_currencies(
        self,
        user_id: int,
        force_update: bool = False
    ) -> Dict[str, any]:
        """
        Actualiza todas las monedas configuradas con BCV.

        Args:
            user_id: ID de usuario que inicia la actualización
            force_update: Forzar actualización aunque el cache sea válido

        Returns:
            Dict con resultados de la actualización
        """
        results = {
            "updated_currencies": [],
            "failed_currencies": [],
            "skipped_currencies": [],
            "timestamp": datetime.now().isoformat(),
            "total_updated": 0,
            "total_failed": 0
        }

        # Forzar refresh del provider si es necesario
        if force_update:
            try:
                self.bcv_provider.refresh_rates()
            except Exception as e:
                logger.error(f"Failed to refresh BCV rates: {e}")
                results["error"] = str(e)
                return results

        # Obtener monedas configuradas para BCV
        bcv_currencies = self.db.query(Currency).filter(
            Currency.company_id == self.company_id,
            Currency.is_active == True,
            Currency.rate_update_method == 'api_bcv'
        ).all()

        if not bcv_currencies:
            logger.warning(f"No BCV currencies found for company {self.company_id}")
            return results

        # Crear servicio de monedas
        currency_service = CurrencyService(self.db)

        # Actualizar cada moneda
        for currency in bcv_currencies:
            try:
                # Obtener tasa actual desde BCV
                new_rate = self.bcv_provider.get_rate(
                    from_currency=currency.code,
                    to_currency="VES"
                )

                if new_rate is None:
                    results["failed_currencies"].append({
                        "code": currency.code,
                        "error": "Rate not available from BCV"
                    })
                    results["total_failed"] += 1
                    continue

                # Verificar si cambió la tasa
                old_rate = currency.exchange_rate
                if Decimal(str(new_rate)) == old_rate:
                    results["skipped_currencies"].append({
                        "code": currency.code,
                        "rate": float(new_rate),
                        "reason": "Rate unchanged"
                    })
                    continue

                # Crear update request
                rate_update = CurrencyRateUpdate(
                    new_rate=Decimal(str(new_rate)),
                    change_reason="Actualización automática BCV",
                    change_type="automatic_api",
                    change_source="api_bcv"
                )

                # Actualizar usando el servicio existente
                updated_currency = currency_service.update_currency_rate(
                    currency_id=currency.id,
                    rate_update=rate_update,
                    company_id=self.company_id,
                    user_id=user_id,
                    user_ip=None
                )

                results["updated_currencies"].append({
                    "code": currency.code,
                    "old_rate": float(old_rate),
                    "new_rate": float(new_rate),
                    "variation": float(new_rate - old_rate)
                })
                results["total_updated"] += 1

            except ProviderNotAvailableError as e:
                logger.error(f"BCV provider not available for {currency.code}: {e}")
                results["failed_currencies"].append({
                    "code": currency.code,
                    "error": "BCV provider unavailable"
                })
                results["total_failed"] += 1

            except Exception as e:
                logger.error(f"Error updating {currency.code}: {e}")
                results["failed_currencies"].append({
                    "code": currency.code,
                    "error": str(e)
                })
                results["total_failed"] += 1

        logger.info(
            f"BCV update completed: {results['total_updated']} updated, "
            f"{results['total_failed']} failed, "
            f"{len(results['skipped_currencies'])} skipped"
        )

        return results

    def get_bcv_status(self) -> Dict[str, any]:
        """
        Obtiene el estado del provider BCV.

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
