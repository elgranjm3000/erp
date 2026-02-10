"""
BCV (Banco Central de Venezuela) Exchange Rate Provider
Implementa scraper para obtener tasas oficiales del BCV
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from decimal import Decimal
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

from .base import ExchangeRateProvider, ExchangeRateProviderError, ProviderNotAvailableError


logger = logging.getLogger(__name__)


@dataclass
class BCVRate:
    """Representa una tasa de cambio del BCV"""
    currency_code: str
    rate: Decimal
    date: datetime
    source: str = "BCV"


class BCVProvider(ExchangeRateProvider):
    """
    Proveedor de tasas de cambio del Banco Central de Venezuela.

    Obtiene las tasas oficiales haciendo scraping al sitio del BCV.
    Cachea las tasas localmente para no saturar el servidor.
    """

    # URL del BCV
    BCV_URL = "https://www.bcv.org.ve/"

    # Monedas soportadas por el BCV
    SUPPORTED_CURRENCIES = ["USD", "EUR", "CNY", "TRY", "RUB", "BRL"]

    # Cache en memoria (en producción usar Redis)
    _rate_cache: dict[str, BCVRate] = {}
    _last_refresh: Optional[datetime] = None
    _cache_ttl: timedelta = timedelta(hours=1)  # Cache por 1 hora

    def __init__(self, cache_ttl: timedelta = timedelta(hours=1)):
        """
        Inicializa el proveedor BCV.

        Args:
            cache_ttl: Tiempo de vida del caché
        """
        self._cache_ttl = cache_ttl

    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: Optional[datetime] = None
    ) -> Optional[Decimal]:
        """
        Obtiene la tasa de cambio desde/hacia VES.

        Nota: El BCV solo publica tasas desde VES hacia otras monedas.
        Para tasas inversas, se calcula el recíproco.

        Args:
            from_currency: Moneda origen
            to_currency: Moneda destino
            date: Fecha (opcional, no soportado por BCV)

        Returns:
            Decimal: Tasa de cambio
        """
        # Si pide tasa histórica, BCV no la tiene
        if date and date.date() < datetime.now().date():
            logger.warning(f"BCV does not support historical rates for date {date}")
            return None

        # Normalizar códigos
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Verificar si el caché expiró
        if self._should_refresh_cache():
            try:
                self.refresh_rates()
            except Exception as e:
                logger.error(f"Failed to refresh BCV rates: {e}")
                # Si hay caché válido, usarlo aunque expire
                if not self._rate_cache:
                    raise ProviderNotAvailableError(f"BCV provider unavailable: {e}")

        # Caso 1: VES -> Otra moneda
        if from_currency == "VES" and to_currency in self.SUPPORTED_CURRENCIES:
            cached_rate = self._rate_cache.get(to_currency)
            if cached_rate:
                return cached_rate.rate

        # Caso 2: Otra moneda -> VES (recíproco)
        elif to_currency == "VES" and from_currency in self.SUPPORTED_CURRENCIES:
            cached_rate = self._rate_cache.get(from_currency)
            if cached_rate and cached_rate.rate != 0:
                return Decimal("1") / cached_rate.rate

        # Caso 3: Entre monedas extranjeras (usar VES como pivote)
        elif from_currency in self.SUPPORTED_CURRENCIES and to_currency in self.SUPPORTED_CURRENCIES:
            rate_from_ves = self.get_rate("VES", from_currency)
            rate_to_ves = self.get_rate(to_currency, "VES")
            if rate_from_ves and rate_to_ves:
                return rate_to_ves / rate_from_ves

        return None

    def get_supported_currencies(self) -> List[str]:
        """Retorna monedas soportadas por BCV"""
        return self.SUPPORTED_CURRENCIES.copy()

    def refresh_rates(self, verify_ssl: bool = False) -> bool:
        """
        Actualiza las tasas desde el sitio del BCV.

        Args:
            verify_ssl: Si debe verificar el certificado SSL (default: False para evitar errores en desarrollo)

        Returns:
            bool: True si la actualización fue exitosa
        """
        try:
            logger.info("Refreshing BCV exchange rates...")

            # Hacer request al BCV (sin verificar SSL por problemas con el certificado)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(
                self.BCV_URL,
                headers=headers,
                timeout=30,
                verify=verify_ssl  # ⚠️ Deshabilitar verificación SSL en desarrollo
            )
            response.raise_for_status()

            # Parsear HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Buscar tasas de cambio
            rates_found = 0

            for currency_code in self.SUPPORTED_CURRENCIES:
                # El BCV usa IDs específicos para cada moneda
                rate_element = soup.find(id="dolar") if currency_code == "USD" else None

                if not rate_element:
                    # Buscar por texto alternativo
                    rate_element = soup.find(
                        "div",
                        class_="view-tipo-cambio",
                        string=lambda text: text and currency_code in text
                    )

                if rate_element:
                    # Extraer valor numérico
                    rate_text = rate_element.get_text()
                    rate_text = rate_text.replace(",", ".").strip()

                    # Limpiar formato venezolano (ej: "36,50")
                    rate_text = "".join(c for c in rate_text if c.isdigit() or c == ".")

                    try:
                        rate_value = Decimal(rate_text)

                        self._rate_cache[currency_code] = BCVRate(
                            currency_code=currency_code,
                            rate=rate_value,
                            date=datetime.now()
                        )
                        rates_found += 1
                        logger.info(f"BCV {currency_code}: {rate_value}")

                    except Exception as e:
                        logger.error(f"Error parsing {currency_code} rate: {e}")

            self._last_refresh = datetime.now()

            if rates_found > 0:
                logger.info(f"Successfully refreshed {rates_found} BCV rates")
                return True
            else:
                logger.error("No BCV rates found in page")
                return False

        except requests.RequestException as e:
            logger.error(f"HTTP error fetching BCV rates: {e}")
            raise ProviderNotAvailableError(f"Cannot connect to BCV: {e}")
        except Exception as e:
            logger.error(f"Unexpected error refreshing BCV rates: {e}")
            raise ExchangeRateProviderError(f"Error refreshing BCV: {e}")

    def get_last_update_time(self) -> Optional[datetime]:
        """Retorna timestamp de última actualización"""
        return self._last_refresh

    def is_available(self) -> bool:
        """Verifica si el proveedor está disponible"""
        try:
            # Intentar hacer un ping simple
            response = requests.head(self.BCV_URL, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def _should_refresh_cache(self) -> bool:
        """Determina si el caché debe ser actualizado"""
        if not self._last_refresh:
            return True

        if datetime.now() - self._last_refresh > self._cache_ttl:
            return True

        return False

    def get_cached_rates(self) -> Dict[str, BCVRate]:
        """
        Retorna las tasas actualmente en caché.

        Returns:
            Dict con tasas cacheadas
        """
        return self._rate_cache.copy()
