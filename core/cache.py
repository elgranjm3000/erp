"""
Sistema de Caching Simple para ERP

Usa functools.lru_cache para caché en memoria con soporte para invalidación.
"""

from functools import lru_cache, wraps
from typing import Any, Callable, Dict, Optional, TypeVar
from datetime import datetime, timedelta
import threading
import hashlib
import json

T = TypeVar('T')

class TTLCache:
    """
    Caché con TTL (Time To Live) simple usando threading.Lock.
    """

    def __init__(self, maxsize: int = 128, default_ttl: int = 300):
        """
        Args:
            maxsize: Máximo número de entradas
            default_ttl: TTL en segundos (default: 5 minutos)
        """
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._lock = threading.RLock()
        self._access_times: Dict[str, datetime] = {}

    def _is_expired(self, key: str) -> bool:
        """Verifica si una entrada ha expirado"""
        if key not in self._cache:
            return True

        _, expiry_time = self._cache[key]
        return datetime.now() > expiry_time

    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché"""
        with self._lock:
            if self._is_expired(key):
                self._remove(key)
                return None

            self._access_times[key] = datetime.now()
            value, _ = self._cache[key]
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Guarda un valor en el caché"""
        with self._lock:
            # Si el caché está lleno, remover entrada más antigua
            if len(self._cache) >= self.maxsize and key not in self._cache:
                self._evict_oldest()

            ttl = ttl or self.default_ttl
            expiry_time = datetime.now() + timedelta(seconds=ttl)
            self._cache[key] = (value, expiry_time)
            self._access_times[key] = datetime.now()

    def _remove(self, key: str) -> None:
        """Remueve una entrada del caché"""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)

    def _evict_oldest(self) -> None:
        """Remueve la entrada más antigua (LRU)"""
        if not self._access_times:
            return

        oldest_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        self._remove(oldest_key)

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalida entradas del caché.

        Args:
            pattern: Si se proporciona, solo invalida keys que contengan este patrón

        Returns:
            Número de entradas invalidadas
        """
        with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                self._access_times.clear()
                return count

            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                self._remove(key)
            return len(keys_to_remove)

    def clear(self) -> None:
        """Limpia todo el caché"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del caché"""
        with self._lock:
            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "ttl": self.default_ttl,
                "keys": list(self._cache.keys())
            }


# Instancia global del caché
_currency_cache = TTLCache(maxsize=256, default_ttl=300)  # 5 minutos TTL


def cache_key_generator(*args, **kwargs) -> str:
    """
    Genera una key de caché basada en los argumentos.
    """
    # Crear string representando args y kwargs
    parts = []

    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            parts.append(str(arg))
        elif hasattr(arg, '__dict__'):
            # Para objetos, usar clase y ID
            parts.append(f"{arg.__class__.__name__}:{getattr(arg, 'id', 'unknown')}")
        else:
            parts.append(str(hash(str(arg))))

    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            parts.append(f"{k}:{v}")
        elif hasattr(v, '__dict__'):
            parts.append(f"{k}:{v.__class__.__name__}:{getattr(v, 'id', 'unknown')}")
        else:
            parts.append(f"{k}:{hash(str(v))}")

    key_string = ":".join(parts)
    return hashlib.md5(key_string.encode()).hexdigest()[:16]


def cached_result(ttl: int = 300, key_prefix: str = "default"):
    """
    Decorador para cachear resultados de funciones.

    Args:
        ttl: Time to live en segundos
        key_prefix: Prefijo para la key del caché

    Example:
        @cached_result(ttl=60, key_prefix="currencies")
        def get_expensive_operation(currency_id: int):
            # ... operación costosa
            return result
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generar key de caché
            func_key = f"{key_prefix}:{func.__name__}:{cache_key_generator(*args, **kwargs)}"

            # Intentar obtener del caché
            cached_value = _currency_cache.get(func_key)
            if cached_value is not None:
                return cached_value

            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            _currency_cache.set(func_key, result, ttl=ttl)

            return result

        # Agregar método para invalidar caché de esta función
        wrapper.invalidate = lambda *args, **kwargs: _currency_cache.invalidate(
            f"{key_prefix}:{func.__name__}:{cache_key_generator(*args, **kwargs)}"
        )

        return wrapper

    return decorator


def invalidate_caches(pattern: Optional[str] = None) -> int:
    """
    Invalida cachés por patrón.

    Args:
        pattern: Patrón de key a invalidar. Si es None, limpia todo.

    Returns:
        Número de entradas invalidadas
    """
    return _currency_cache.invalidate(pattern)


def get_cache_stats() -> Dict[str, Any]:
    """Retorna estadísticas del caché global"""
    return _currency_cache.stats()


def clear_all_caches() -> None:
    """Limpia todos los cachés"""
    _currency_cache.clear()
