# src/state_manager.py
"""
Sistema de persistencia de estado y cola de tareas para Narrivox.
Proporciona gestión de estado persistente y cola de tareas con prioridades.
"""

import json
import logging
import pickle
import sqlite3
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Union

logger = logging.getLogger("Narrivox")


class TaskStatus(Enum):
    """Estados posibles de una tarea."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Prioridades de tareas."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Task:
    """Representa una tarea en el sistema."""
    id: str
    name: str
    func: str  # Nombre de la función a ejecutar
    args: list = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convierte la tarea a diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'func': self.func,
            'args': self.args,
            'kwargs': self.kwargs,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'result': str(self.result) if self.result is not None else None,
            'error': self.error,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Crea una tarea desde un diccionario."""
        return cls(
            id=data['id'],
            name=data['name'],
            func=data['func'],
            args=data.get('args', []),
            kwargs=data.get('kwargs', {}),
            priority=TaskPriority(data.get('priority', TaskPriority.NORMAL.value)),
            status=TaskStatus(data.get('status', TaskStatus.PENDING.value)),
            created_at=data.get('created_at', time.time()),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            result=data.get('result'),
            error=data.get('error'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            timeout=data.get('timeout'),
            metadata=data.get('metadata', {})
        )


class StateManager:
    """
    Gestor de estado persistente con soporte para múltiples backends.
    """

    def __init__(self, storage_path: Union[str, Path] = "narrivox_state.db"):
        self.storage_path = Path(storage_path)
        self._lock = threading.RLock()
        self._cache: dict[str, Any] = {}
        self._dirty_keys: set[str] = set()
        self._auto_save_interval = 30  # segundos
        self._last_save_time = time.time()

        # Inicializar storage
        self._init_storage()

        # Iniciar auto-save
        self._start_auto_save()

    def _init_storage(self):
        """Inicializa el sistema de almacenamiento."""
        try:
            # Crear directorio si no existe
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Inicializar SQLite
            self._conn = sqlite3.connect(str(self.storage_path), check_same_thread=False)
            self._conn.execute('PRAGMA journal_mode=WAL')
            self._conn.execute('PRAGMA synchronous=NORMAL')

            # Crear tabla de estado
            self._conn.execute('''
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    value_type TEXT NOT NULL
                )
            ''')

            # Crear índices
            self._conn.execute('CREATE INDEX IF NOT EXISTS idx_state_updated ON state(updated_at)')

            self._conn.commit()
            logger.info(f"StateManager inicializado: {self.storage_path}")

        except Exception as e:
            logger.error(f"Error inicializando StateManager: {e}")
            raise

    def _start_auto_save(self):
        """Inicia el hilo de auto-save."""
        def auto_save_worker():
            while True:
                time.sleep(self._auto_save_interval)
                try:
                    self.save_dirty()
                except Exception as e:
                    logger.error(f"Error en auto-save: {e}")

        thread = threading.Thread(target=auto_save_worker, daemon=True)
        thread.start()

    def _serialize_value(self, value: Any) -> tuple[str, str]:
        """Serializa un valor."""
        try:
            # Intentar JSON primero (más legible)
            json_str = json.dumps(value, default=str)
            return json_str, 'json'
        except (TypeError, ValueError):
            # Fallback a pickle
            pickle_bytes = pickle.dumps(value)
            import base64
            return base64.b64encode(pickle_bytes).decode(), 'pickle'

    def _deserialize_value(self, serialized: str, value_type: str) -> Any:
        """Deserializa un valor."""
        try:
            if value_type == 'json':
                return json.loads(serialized)
            elif value_type == 'pickle':
                import base64
                pickle_bytes = base64.b64decode(serialized.encode())
                return pickle.loads(pickle_bytes)
            else:
                return serialized
        except Exception as e:
            logger.error(f"Error deserializando valor: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Almacena un valor en el estado.

        Args:
            key: Clave del valor
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos

        Returns:
            True si se almacenó exitosamente
        """
        try:
            with self._lock:
                serialized, value_type = self._serialize_value(value)
                current_time = time.time()

                # Almacenar en caché
                self._cache[key] = {
                    'value': value,
                    'serialized': serialized,
                    'value_type': value_type,
                    'updated_at': current_time,
                    'ttl': ttl,
                    'expires_at': current_time + ttl if ttl else None
                }

                # Marcar como sucio para guardar
                self._dirty_keys.add(key)

                return True

        except Exception as e:
            logger.error(f"Error almacenando valor '{key}': {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor del estado.

        Args:
            key: Clave del valor
            default: Valor por defecto si no existe

        Returns:
            Valor almacenado o default
        """
        try:
            with self._lock:
                # Verificar caché primero
                if key in self._cache:
                    cached = self._cache[key]

                    # Verificar expiración
                    if cached.get('expires_at') and time.time() > cached['expires_at']:
                        del self._cache[key]
                        if key in self._dirty_keys:
                            self._dirty_keys.remove(key)
                        return default

                    return cached['value']

                # Cargar desde storage
                cursor = self._conn.execute(
                    'SELECT value, value_type FROM state WHERE key = ?',
                    (key,)
                )
                row = cursor.fetchone()

                if row:
                    serialized, value_type = row
                    value = self._deserialize_value(serialized, value_type)

                    # Cachear
                    self._cache[key] = {
                        'value': value,
                        'serialized': serialized,
                        'value_type': value_type,
                        'updated_at': time.time(),
                        'ttl': None,
                        'expires_at': None
                    }

                    return value

                return default

        except Exception as e:
            logger.error(f"Error obteniendo valor '{key}': {e}")
            return default

    def delete(self, key: str) -> bool:
        """
        Elimina un valor del estado.

        Args:
            key: Clave del valor a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        try:
            with self._lock:
                # Eliminar de caché
                if key in self._cache:
                    del self._cache[key]

                # Eliminar de dirty keys
                if key in self._dirty_keys:
                    self._dirty_keys.remove(key)

                # Eliminar de storage
                self._conn.execute('DELETE FROM state WHERE key = ?', (key,))
                self._conn.commit()

                return True

        except Exception as e:
            logger.error(f"Error eliminando valor '{key}': {e}")
            return False

    def save_dirty(self) -> bool:
        """
        Guarda los valores modificados al storage.

        Returns:
            True si se guardó exitosamente
        """
        try:
            with self._lock:
                if not self._dirty_keys:
                    return True

                current_time = time.time()
                updates = []

                for key in list(self._dirty_keys):
                    if key in self._cache:
                        cached = self._cache[key]

                        # Verificar expiración
                        if cached.get('expires_at') and current_time > cached['expires_at']:
                            # Eliminar si expiró
                            self._conn.execute('DELETE FROM state WHERE key = ?', (key,))
                            del self._cache[key]
                            continue

                        updates.append((
                            key,
                            cached['serialized'],
                            cached['value_type'],
                            current_time
                        ))

                # Guardar actualizaciones
                if updates:
                    self._conn.executemany('''
                        INSERT OR REPLACE INTO state (key, value, updated_at, value_type)
                        VALUES (?, ?, ?, ?)
                    ''', updates)
                    self._conn.commit()

                self._dirty_keys.clear()
                self._last_save_time = current_time

                logger.debug(f"Guardados {len(updates)} valores en storage")
                return True

        except Exception as e:
            logger.error(f"Error guardando valores sucios: {e}")
            return False

    def get_all_keys(self) -> list[str]:
        """Obtiene todas las claves almacenadas."""
        try:
            with self._lock:
                cursor = self._conn.execute('SELECT key FROM state')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error obteniendo claves: {e}")
            return []

    def clear_expired(self) -> int:
        """
        Limpia valores expirados.

        Returns:
            Número de valores eliminados
        """
        try:
            with self._lock:
                current_time = time.time()
                expired_keys = []

                # Verificar caché
                for key, cached in list(self._cache.items()):
                    if cached.get('expires_at') and current_time > cached['expires_at']:
                        expired_keys.append(key)
                        del self._cache[key]

                # Eliminar de storage
                if expired_keys:
                    placeholders = ','.join('?' * len(expired_keys))
                    self._conn.execute(
                        f'DELETE FROM state WHERE key IN ({placeholders})',
                        expired_keys
                    )
                    self._conn.commit()

                return len(expired_keys)

        except Exception as e:
            logger.error(f"Error limpiando expirados: {e}")
            return 0

    def get_stats(self) -> dict:
        """Obtiene estadísticas del gestor de estado."""
        try:
            with self._lock:
                cursor = self._conn.execute('SELECT COUNT(*) FROM state')
                total_keys = cursor.fetchone()[0]

                cursor = self._conn.execute('''
                    SELECT SUM(LENGTH(value)) FROM state
                ''')
                total_size = cursor.fetchone()[0] or 0

                return {
                    'total_keys': total_keys,
                    'cache_size': len(self._cache),
                    'dirty_keys': len(self._dirty_keys),
                    'total_size_bytes': total_size,
                    'total_size_mb': total_size / (1024 * 1024),
                    'last_save_time': self._last_save_time
                }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}


class TaskQueue:
    """
    Cola de tareas con prioridades y persistencia.
    """

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self._lock = threading.RLock()
        self._pending_tasks: dict[str, Task] = {}
        self._running_tasks: dict[str, Task] = {}
        self._completed_tasks: dict[str, Task] = {}
        self._task_functions: dict[str, Callable] = {}

        # Cargar tareas persistidas
        self._load_persisted_tasks()

    def _load_persisted_tasks(self):
        """Carga tareas persistidas desde el estado."""
        try:
            pending_data = self.state_manager.get('task_queue_pending', {})
            for task_data in pending_data.values():
                task = Task.from_dict(task_data)
                if task.status == TaskStatus.PENDING:
                    self._pending_tasks[task.id] = task

            logger.info(f"Cargadas {len(self._pending_tasks)} tareas pendientes")

        except Exception as e:
            logger.error(f"Error cargando tareas persistidas: {e}")

    def _persist_tasks(self):
        """Persiste el estado actual de las tareas."""
        try:
            pending_data = {
                task_id: task.to_dict()
                for task_id, task in self._pending_tasks.items()
            }
            self.state_manager.set('task_queue_pending', pending_data)

        except Exception as e:
            logger.error(f"Error persistiendo tareas: {e}")

    def register_function(self, name: str, func: Callable):
        """
        Registra una función ejecutable.

        Args:
            name: Nombre de la función
            func: Función a ejecutar
        """
        self._task_functions[name] = func
        logger.debug(f"Función '{name}' registrada")

    def enqueue(self, name: str, func: str, args: list = None,
               kwargs: dict = None, priority: TaskPriority = TaskPriority.NORMAL,
               max_retries: int = 3, timeout: Optional[float] = None,
               metadata: dict = None) -> str:
        """
        Añade una tarea a la cola.

        Args:
            name: Nombre de la tarea
            func: Nombre de la función registrada
            args: Argumentos posicionales
            kwargs: Argumentos nombrados
            priority: Prioridad de la tarea
            max_retries: Máximo número de reintentos
            timeout: Timeout máximo
            metadata: Metadatos adicionales

        Returns:
            ID de la tarea creada
        """
        import uuid

        task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args or [],
            kwargs=kwargs or {},
            priority=priority,
            max_retries=max_retries,
            timeout=timeout,
            metadata=metadata or {}
        )

        with self._lock:
            self._pending_tasks[task_id] = task
            self._persist_tasks()

        logger.info(f"Tarea '{name}' ({task_id}) encolada con prioridad {priority.name}")
        return task_id

    def dequeue(self) -> Optional[Task]:
        """
        Obtiene la siguiente tarea a ejecutar.

        Returns:
            Siguiente tarea o None
        """
        with self._lock:
            if not self._pending_tasks:
                return None

            # Obtener tarea con mayor prioridad
            task = max(self._pending_tasks.values(),
                      key=lambda t: (t.priority.value, t.created_at))

            # Mover a running
            del self._pending_tasks[task.id]
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            self._running_tasks[task.id] = task

            self._persist_tasks()
            return task

    def complete_task(self, task_id: str, result: Any = None,
                    error: Optional[str] = None) -> bool:
        """
        Marca una tarea como completada.

        Args:
            task_id: ID de la tarea
            result: Resultado de la tarea
            error: Error si falló

        Returns:
            True si se completó exitosamente
        """
        with self._lock:
            if task_id not in self._running_tasks:
                return False

            task = self._running_tasks[task_id]
            task.status = TaskStatus.COMPLETED if not error else TaskStatus.FAILED
            task.completed_at = time.time()
            task.result = result
            task.error = error

            # Mover a completed
            del self._running_tasks[task_id]
            self._completed_tasks[task_id] = task

            self._persist_tasks()
            return True

    def retry_task(self, task_id: str) -> bool:
        """
        Reintenta una tarea fallida.

        Args:
            task_id: ID de la tarea

        Returns:
            True si se reintentó exitosamente
        """
        with self._lock:
            if task_id not in self._completed_tasks:
                return False

            task = self._completed_tasks[task_id]

            if task.retry_count >= task.max_retries:
                logger.warning(f"Tarea {task_id} alcanzó máximo de reintentos")
                return False

            # Mover a pending
            del self._completed_tasks[task_id]
            task.status = TaskStatus.RETRYING
            task.retry_count += 1
            task.started_at = None
            task.completed_at = None
            task.error = None
            self._pending_tasks[task_id] = task

            self._persist_tasks()
            return True

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancela una tarea.

        Args:
            task_id: ID de la tarea

        Returns:
            True si se canceló exitosamente
        """
        with self._lock:
            # Buscar en pending
            if task_id in self._pending_tasks:
                task = self._pending_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                task.completed_at = time.time()
                del self._pending_tasks[task_id]
                self._completed_tasks[task_id] = task
                self._persist_tasks()
                return True

            # Buscar en running
            if task_id in self._running_tasks:
                task = self._running_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                task.completed_at = time.time()
                del self._running_tasks[task_id]
                self._completed_tasks[task_id] = task
                self._persist_tasks()
                return True

            return False

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Obtiene el estado de una tarea."""
        with self._lock:
            if task_id in self._pending_tasks:
                return self._pending_tasks[task_id].status
            if task_id in self._running_tasks:
                return self._running_tasks[task_id].status
            if task_id in self._completed_tasks:
                return self._completed_tasks[task_id].status
            return None

    def get_task(self, task_id: str) -> Optional[Task]:
        """Obtiene una tarea por ID."""
        with self._lock:
            if task_id in self._pending_tasks:
                return self._pending_tasks[task_id]
            if task_id in self._running_tasks:
                return self._running_tasks[task_id]
            if task_id in self._completed_tasks:
                return self._completed_tasks[task_id]
            return None

    def get_queue_size(self) -> int:
        """Obtiene el tamaño de la cola de tareas pendientes."""
        with self._lock:
            return len(self._pending_tasks)

    def get_stats(self) -> dict:
        """Obtiene estadísticas de la cola de tareas."""
        with self._lock:
            return {
                'pending': len(self._pending_tasks),
                'running': len(self._running_tasks),
                'completed': len(self._completed_tasks),
                'total': len(self._pending_tasks) + len(self._running_tasks) + len(self._completed_tasks)
            }

    def clear_old_completed(self, older_than_hours: float = 24) -> int:
        """
        Limpia tareas completadas antiguas.

        Args:
            older_than_hours: Antigüedad máxima en horas

        Returns:
            Número de tareas eliminadas
        """
        try:
            with self._lock:
                current_time = time.time()
                max_age = older_than_hours * 3600
                to_remove = []

                for task_id, task in self._completed_tasks.items():
                    if task.completed_at and (current_time - task.completed_at) > max_age:
                        to_remove.append(task_id)

                for task_id in to_remove:
                    del self._completed_tasks[task_id]

                if to_remove:
                    self._persist_tasks()

                return len(to_remove)

        except Exception as e:
            logger.error(f"Error limpiando tareas antiguas: {e}")
            return 0


# Instancias globales
_state_manager = None
_task_queue = None


def get_state_manager(storage_path: str = "narrivox_state.db") -> StateManager:
    """Obtiene la instancia global del gestor de estado."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager(storage_path)
    return _state_manager


def get_task_queue() -> TaskQueue:
    """Obtiene la instancia global de la cola de tareas."""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue(get_state_manager())
    return _task_queue