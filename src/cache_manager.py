# src/cache_manager.py
"""
Sistema de caché inteligente para Narrivox.
Proporciona caché en memoria con políticas de expiración, persistencia y compresión.
"""

import hashlib
import json
import logging
import pickle
import threading
import time
import weakref
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union

logger = logging.getLogger("Narrivox")

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Entrada de caché con metadatos."""
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    size_bytes: int
    ttl: Optional[float] = None

    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado."""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl

    def touch(self):
        """Actualiza el tiempo de último acceso."""
        self.last_accessed = time.time()
        self.access_count += 1


class CachePolicy(ABC):
    """Interfaz para políticas de expulsión de caché."""

    @abstractmethod
    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """Determina si una entrada debe ser expulsada."""
        pass


class LRUPolicy(CachePolicy):
    """Política Least Recently Used."""

    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """Expulsa las entradas menos usadas primero."""
        return cache_size >= max_size


class LFUPolicy(CachePolicy):
    """Política Least Frequently Used."""

    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """Expulsa las entradas menos frecuentemente usadas."""
        if cache_size < max_size:
            return False
        # En una implementación real, compararía con otras entradas
        return True


class TTLPolicy(CachePolicy):
    """Política basada en tiempo de vida."""

    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """Expulsa entradas expiradas."""
        return entry.is_expired()


class CacheManager:
    """
    Gestor de caché con múltiples niveles y políticas configurables.
    """

    _instances = weakref.WeakValueDictionary()

    def __new__(cls, name: str = "default"):
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]

    def __init__(self, name: str = "default"):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._name = name
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._policy = LRUPolicy()
        self._max_size = 1000  # Máximo número de entradas
        self._max_memory_mb = 100  # Máximo memoria en MB
        self._default_ttl = 3600  # TTL por defecto: 1 hora
        self._enable_compression = True
        self._enable_persistence = False
        self._persistence_path: Optional[Path] = None

        # Estadísticas
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_bytes': 0
        }

    def configure(self,
                  max_size: int = 1000,
                  max_memory_mb: int = 100,
                  default_ttl: Optional[float] = 3600,
                  policy: CachePolicy = LRUPolicy(),
                  enable_compression: bool = True,
                  enable_persistence: bool = False,
                  persistence_path: Optional[str] = None):
        """Configura el gestor de caché."""
        with self._lock:
            self._max_size = max_size
            self._max_memory_mb = max_memory_mb
            self._default_ttl = default_ttl
            self._policy = policy
            self._enable_compression = enable_compression
            self._enable_persistence = enable_persistence

            if persistence_path:
                self._persistence_path = Path(persistence_path)
                self._persistence_path.mkdir(parents=True, exist_ok=True)

            logger.info(f"CacheManager '{self._name}' configurado: "
                        f"max_size={max_size}, max_memory={max_memory_mb}MB, ttl={default_ttl}s")

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Genera una clave de caché única."""
        key_data = {
            'prefix': prefix,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        return f"{prefix}_{key_hash}"

    def _serialize_value(self, value: Any) -> tuple[bytes, int]:
        """Serializa y opcionalmente comprime un valor."""
        try:
            data = pickle.dumps(value)

            if self._enable_compression and len(data) > 1024:  # Solo comprimir si > 1KB
                try:
                    import zlib
                    compressed = zlib.compress(data, level=6)
                    if len(compressed) < len(data):
                        return compressed, len(compressed)
                except Exception as e:
                    logger.debug(f"Error comprimiendo valor: {e}")

            return data, len(data)
        except Exception as e:
            logger.error(f"Error serializando valor: {e}")
            raise

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserializa y descomprime un valor."""
        try:
            # Intentar descomprimir
            if self._enable_compression:
                try:
                    import zlib
                    return pickle.loads(zlib.decompress(data))
                except Exception:
                    pass  # No estaba comprimido

            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Error deserializando valor: {e}")
            raise

    def _check_memory_pressure(self) -> bool:
        """Verifica si hay presión de memoria."""
        current_memory_mb = self._stats['size_bytes'] / (1024 * 1024)
        return current_memory_mb >= self._max_memory_mb

    def _evict_if_needed(self):
        """Expulsa entradas si es necesario según la política."""
        with self._lock:
            while (len(self._cache) >= self._max_size or
                   self._check_memory_pressure()):

                if not self._cache:
                    break

                # Encontrar entrada a expulsar según política
                keys_to_evict = []
                for key, entry in self._cache.items():
                    if self._policy.should_evict(entry, len(self._cache), self._max_size):
                        keys_to_evict.append(key)

                # Expulsar entradas
                for key in keys_to_evict[:1]:  # Expulsar de una en una
                    entry = self._cache.pop(key)
                    self._stats['size_bytes'] -= entry.size_bytes
                    self._stats['evictions'] += 1
                    logger.debug(f"Entrada '{key}' expulsada del caché")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor del caché.

        Args:
            key: Clave del valor
            default: Valor por defecto si no existe

        Returns:
            Valor almacenado o default
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats['misses'] += 1
                return default

            if entry.is_expired():
                # Entrada expirada, eliminar y retornar default
                del self._cache[key]
                self._stats['size_bytes'] -= entry.size_bytes
                self._stats['misses'] += 1
                return default

            # Actualizar metadatos
            entry.touch()
            # Mover al final (más recientemente usado)
            self._cache.move_to_end(key)

            self._stats['hits'] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Almacena un valor en el caché.

        Args:
            key: Clave del valor
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos (None usa el default)

        Returns:
            True si se almacenó exitosamente
        """
        try:
            with self._lock:
                # Serializar valor
                serialized, size = self._serialize_value(value)

                # Verificar si el valor es demasiado grande
                max_entry_size = self._max_memory_mb * 1024 * 1024 // 10  # 10% del máximo
                if size > max_entry_size:
                    logger.warning(f"Valor demasiado grande para caché: {size} bytes")
                    return False

                # Si ya existe, restar tamaño anterior
                if key in self._cache:
                    old_entry = self._cache[key]
                    self._stats['size_bytes'] -= old_entry.size_bytes

                # Crear entrada
                entry = CacheEntry(
                    value=value,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    access_count=0,
                    size_bytes=size,
                    ttl=ttl or self._default_ttl
                )

                # Almacenar
                self._cache[key] = entry
                self._stats['size_bytes'] += size
                self._cache.move_to_end(key)

                # Expulsar si es necesario
                self._evict_if_needed()

                # Persistir si está habilitado
                if self._enable_persistence and self._persistence_path:
                    self._persist_entry(key, entry)

                return True

        except Exception as e:
            logger.error(f"Error almacenando en caché: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Elimina un valor del caché.

        Args:
            key: Clave del valor a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self._stats['size_bytes'] -= entry.size_bytes
                return True
            return False

    def clear(self):
        """Limpia todo el caché."""
        with self._lock:
            self._cache.clear()
            self._stats['size_bytes'] = 0
            logger.info(f"Caché '{self._name}' limpiado")

    def get_stats(self) -> dict:
        """Obtiene estadísticas del caché."""
        with self._lock:
            stats = self._stats.copy()
            stats['entries'] = len(self._cache)
            stats['size_mb'] = self._stats['size_bytes'] / (1024 * 1024)
            stats['hit_rate'] = (
                self._stats['hits'] / (self._stats['hits'] + self._stats['misses'])
                if (self._stats['hits'] + self._stats['misses']) > 0 else 0.0
            )
            return stats

    def _persist_entry(self, key: str, entry: CacheEntry):
        """Persiste una entrada en disco."""
        if not self._persistence_path:
            return

        try:
            cache_file = self._persistence_path / f"{key}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.error(f"Error persistiendo entrada {key}: {e}")

    def _load_persistent(self):
        """Carga entradas persistidas desde disco."""
        if not self._persistence_path or not self._persistence_path.exists():
            return

        try:
            for cache_file in self._persistence_path.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)

                    if not entry.is_expired():
                        key = cache_file.stem
                        self._cache[key] = entry
                        self._stats['size_bytes'] += entry.size_bytes
                except Exception as e:
                    logger.debug(f"Error cargando {cache_file}: {e}")

            logger.info(f"Cargadas {len(self._cache)} entradas desde disco")
        except Exception as e:
            logger.error(f"Error cargando caché persistente: {e}")

    def memoize(self, ttl: Optional[float] = None):
        """
        Decorador para memoizar funciones.

        Args:
            ttl: Tiempo de vida en segundos

        Returns:
            Decorador configurado
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            def wrapper(*args, **kwargs) -> T:
                # Generar clave única
                key = self._generate_key(func.__name__, *args, **kwargs)

                # Intentar obtener del caché
                cached_value = self.get(key)
                if cached_value is not None:
                    return cached_value

                # Ejecutar función y cachear resultado
                result = func(*args, **kwargs)
                self.set(key, result, ttl=ttl)

                return result

            return wrapper
        return decorator


# Instancias globales de caché para diferentes propósitos
_cache_instances = {}


def get_cache(name: str = "default") -> CacheManager:
    """Obtiene una instancia de caché por nombre."""
    if name not in _cache_instances:
        _cache_instances[name] = CacheManager(name)
    return _cache_instances[name]


def configure_global_cache(max_size: int = 1000, max_memory_mb: int = 100,
                          default_ttl: Optional[float] = 3600,
                          enable_compression: bool = True):
    """Configura el caché global."""
    cache = get_cache("default")
    cache.configure(
        max_size=max_size,
        max_memory_mb=max_memory_mb,
        default_ttl=default_ttl,
        enable_compression=enable_compression
    )