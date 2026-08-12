# src/concurrency_manager.py
"""
Gestor de concurrencia centralizado para Narrivox.
Proporciona un pool de threads reutilizable, gestión de tareas y sincronización mejorada.
"""

import concurrent.futures
import logging
import queue
import threading
import time
import weakref
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("Narrivox")


class TaskPriority(Enum):
    """Prioridades de tareas para el gestor de concurrencia."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Task:
    """Representa una tarea en el sistema de concurrencia."""
    id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    callback: Optional[Callable[[Any, bool, str], None]] = None
    timeout: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    cancel_event: Optional[threading.Event] = None

    def __lt__(self, other):
        """Para ordenar por prioridad."""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


class ConcurrencyManager:
    """
    Gestor centralizado de concurrencia con pool de threads y cola de prioridades.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._max_workers = 4  # Configurable según necesidades
        self._task_queue = queue.PriorityQueue()
        self._active_tasks: dict[str, Task] = {}
        self._task_results: dict[str, Any] = {}
        self._cancel_events: dict[str, threading.Event] = {}
        self._shutdown = False
        self._workers: list[threading.Thread] = []

        # Statistics
        self._stats_lock = threading.Lock()
        self._stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'active_workers': 0
        }

        # Iniciar workers
        self._start_workers()

        # Registrar para limpieza
        self._register_cleanup()

    def _start_workers(self):
        """Inicia los hilos trabajadores del pool."""
        for i in range(self._max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"ConcurrencyWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
            logger.info(f"Worker {i} iniciado")

    def _worker_loop(self):
        """Loop principal de los trabajadores."""
        while not self._shutdown:
            try:
                # Obtener tarea con timeout para permitir shutdown
                task = self._task_queue.get(timeout=1.0)

                if task is None:
                    continue

                # Ejecutar tarea
                self._execute_task(task)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error en worker loop: {e}")

    def _execute_task(self, task: Task):
        """Ejecuta una tarea individual."""
        task_id = task.id

        try:
            # Registrar tarea activa
            with self._stats_lock:
                self._stats['active_workers'] += 1
            self._active_tasks[task_id] = task

            # Verificar cancelación antes de ejecutar
            if task.cancel_event and task.cancel_event.is_set():
                self._handle_task_completion(task_id, None, False, True, "Cancelada antes de ejecutar")
                return

            # Ejecutar con timeout si especificado
            if task.timeout:
                result = self._execute_with_timeout(task)
            else:
                result = task.func(*task.args, **task.kwargs)

            # Verificar cancelación después de ejecutar
            if task.cancel_event and task.cancel_event.is_set():
                self._handle_task_completion(task_id, None, False, True, "Cancelada durante ejecución")
                return

            self._handle_task_completion(task_id, result, True, False, "")

        except TimeoutError:
            error_msg = f"Timeout después de {task.timeout}s"
            logger.warning(f"Tarea {task_id} timeout: {error_msg}")
            self._handle_task_completion(task_id, None, False, False, error_msg)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error ejecutando tarea {task_id}: {error_msg}")
            self._handle_task_completion(task_id, None, False, False, error_msg)

        finally:
            # Limpiar tarea activa
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
            with self._stats_lock:
                self._stats['active_workers'] -= 1
            self._task_queue.task_done()

    def _execute_with_timeout(self, task: Task) -> Any:
        """Ejecuta una tarea con timeout usando thread separado."""
        result_container = []
        error_container = []
        event = threading.Event()

        def target():
            try:
                result = task.func(*task.args, **task.kwargs)
                result_container.append(result)
            except Exception as e:
                error_container.append(e)
            finally:
                event.set()

        thread = threading.Thread(target=target, daemon=True)
        thread.start()

        # Esperar resultado o timeout
        if not event.wait(timeout=task.timeout):
            if task.cancel_event:
                task.cancel_event.set()
            raise TimeoutError()

        if error_container:
            raise error_container[0]

        return result_container[0]

    def _handle_task_completion(self, task_id: str, result: Any, success: bool,
                                cancelled: bool, error_message: str):
        """Maneja la completion de una tarea."""
        # Guardar resultado
        self._task_results[task_id] = {
            'result': result,
            'success': success,
            'cancelled': cancelled,
            'error_message': error_message,
            'completed_at': time.time()
        }

        # Actualizar estadísticas
        with self._stats_lock:
            self._stats['completed_tasks'] += 1
            if cancelled:
                self._stats['cancelled_tasks'] += 1
            elif not success:
                self._stats['failed_tasks'] += 1

        # Llamar callback si existe
        task = self._active_tasks.get(task_id)
        if task and task.callback:
            try:
                # Ejecutar callback en thread seguro
                self._safe_callback(task.callback, result, success, error_message)
            except Exception as e:
                logger.error(f"Error en callback de tarea {task_id}: {e}")

    def _safe_callback(self, callback: Callable, *args):
        """Ejecuta callback de forma segura en el thread principal si es necesario."""
        try:
            import tkinter as tk
            root = tk._default_root
            if root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                root.after(0, lambda: callback(*args))
            else:
                callback(*args)
        except Exception:
            callback(*args)

    def submit_task(self, func: Callable, *args, priority: TaskPriority = TaskPriority.NORMAL,
                   callback: Optional[Callable] = None, timeout: Optional[float] = None,
                   **kwargs) -> str:
        """
        Envía una tarea para ejecución asíncrona.

        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            priority: Prioridad de la tarea
            callback: Función de callback (result, success, error_message)
            timeout: Timeout máximo en segundos
            **kwargs: Argumentos nombrados

        Returns:
            ID de la tarea creada
        """
        if self._shutdown:
            raise RuntimeError("ConcurrencyManager está en shutdown")

        task_id = f"task_{int(time.time() * 1000)}_{id(func)}"
        cancel_event = threading.Event()

        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            callback=callback,
            timeout=timeout,
            cancel_event=cancel_event
        )

        self._cancel_events[task_id] = cancel_event
        self._task_queue.put(task)

        with self._stats_lock:
            self._stats['total_tasks'] += 1

        logger.debug(f"Tarea {task_id} enviada con prioridad {priority.name}")
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancela una tarea por su ID.

        Args:
            task_id: ID de la tarea a cancelar

        Returns:
            True si se canceló exitosamente
        """
        if task_id in self._cancel_events:
            self._cancel_events[task_id].set()
            logger.info(f"Tarea {task_id} marcada para cancelación")
            return True
        return False

    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[dict]:
        """
        Obtiene el resultado de una tarea.

        Args:
            task_id: ID de la tarea
            timeout: Tiempo máximo de espera

        Returns:
            Diccionario con resultado o None si no está disponible
        """
        start_time = time.time()

        while True:
            if task_id in self._task_results:
                return self._task_results[task_id]

            if timeout and (time.time() - start_time) > timeout:
                return None

            time.sleep(0.1)

    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """
        Espera a que una tarea se complete.

        Args:
            task_id: ID de la tarea
            timeout: Tiempo máximo de espera

        Returns:
            True si la tarea se completó
        """
        result = self.get_task_result(task_id, timeout)
        return result is not None

    def get_stats(self) -> dict:
        """Obtiene estadísticas del gestor de concurrencia."""
        with self._stats_lock:
            stats = self._stats.copy()
        stats['queue_size'] = self._task_queue.qsize()
        stats['active_tasks'] = len(self._active_tasks)
        return stats

    def shutdown(self, wait: bool = True):
        """
        Apaga el gestor de concurrencia.

        Args:
            wait: Si debe esperar a que las tareas actuales terminen
        """
        logger.info("Iniciando shutdown de ConcurrencyManager")
        self._shutdown = True

        if wait:
            # Esperar a que la cola se vacíe
            self._task_queue.join()

            # Esperar a que los workers terminen
            for worker in self._workers:
                worker.join(timeout=5.0)

        logger.info("ConcurrencyManager apagado")

    def _register_cleanup(self):
        """Registra el gestor para limpieza al salir."""
        import atexit
        atexit.register(self.shutdown)

    def is_task_active(self, task_id: str) -> bool:
        """Verifica si una tarea está activa."""
        return task_id in self._active_tasks

    def get_active_tasks(self) -> list[str]:
        """Obtiene lista de IDs de tareas activas."""
        return list(self._active_tasks.keys())

    def clear_completed_results(self, older_than: float = 3600):
        """
        Limpia resultados de tareas completadas antiguas.

        Args:
            older_than: Edad máxima en segundos para mantener resultados
        """
        current_time = time.time()
        to_remove = []

        for task_id, result_data in self._task_results.items():
            age = current_time - result_data['completed_at']
            if age > older_than:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self._task_results[task_id]
            if task_id in self._cancel_events:
                del self._cancel_events[task_id]

        logger.debug(f"Limpiados {len(to_remove)} resultados antiguos")


# Instancia global del gestor de concurrencia
_concurrency_manager = None


def get_concurrency_manager() -> ConcurrencyManager:
    """Obtiene la instancia global del gestor de concurrencia."""
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ConcurrencyManager()
    return _concurrency_manager