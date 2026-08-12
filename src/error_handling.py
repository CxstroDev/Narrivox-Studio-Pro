# src/error_handling.py
import logging
import traceback
from tkinter import messagebox

logger = logging.getLogger("Narrivox")

def handle_error(error: Exception, context: str = "", parent=None):
    """Maneja un error mostrando un mensaje amigable y registrando el traceback."""
    error_msg = translate_error(error, context)
    logger.error(f"Error en {context}: {error}\n{traceback.format_exc()}")
    if parent:
        messagebox.showerror("Error", error_msg, parent=parent)
    else:
        messagebox.showerror("Error", error_msg)

def _check_network_errors(error_str: str) -> str | None:
    """Verifica errores de red/conexión."""
    if "timeout" in error_str or "timed out" in error_str:
        return "La conexión ha tardado demasiado. Verifica tu internet y vuelve a intentarlo."
    if "connection" in error_str or "network" in error_str:
        return "Error de conexión. Comprueba tu red y que los servidores estén disponibles."
    return None

def _check_groq_errors(error_str: str) -> str | None:
    """Verifica errores de API Groq."""
    if "groq" not in error_str and "api key" not in error_str:
        return None

    if "invalid" in error_str or "unauthorized" in error_str:
        return "La clave API de Groq es inválida. Revísala en Ajustes."
    if "rate limit" in error_str:
        return "Has superado el límite de peticiones a Groq. Espera un momento y vuelve a intentar."
    if "quota" in error_str:
        return "Se ha agotado la cuota de la API de Groq. Revisa tu plan."
    return "Error con la API de Groq. Verifica tu clave en Ajustes e intenta de nuevo."

def _check_huggingface_errors(error_str: str) -> str | None:
    """Verifica errores de Hugging Face."""
    if "huggingface" not in error_str and "hf" not in error_str:
        return None

    if "token" in error_str or "authorization" in error_str:
        return "El token de Hugging Face es inválido o ha expirado. Regenera uno nuevo en Ajustes."
    if "model" in error_str and ("not found" in error_str or "unavailable" in error_str):
        return "El modelo de IA para generar imágenes no está disponible temporalmente. Intenta más tarde."
    return "Error al generar la imagen. Verifica tu token de Hugging Face."

def _check_tts_errors(error_str: str) -> str | None:
    """Verifica errores de TTS."""
    if "edge_tts" not in error_str and "tts" not in error_str:
        return None

    if "no host" in error_str or "connection" in error_str:
        return "No se pudo conectar al servicio de voz. Revisa tu conexión a internet."
    if "voice" in error_str:
        return "La voz seleccionada no está disponible. Intenta con otra."
    return "Error al generar el audio. Intenta de nuevo más tarde."

def _check_file_errors(error_str: str, context: str) -> str | None:
    """Verifica errores de archivos/carpetas."""
    if "file" not in error_str and "directory" not in error_str and "permission" not in error_str:
        return None

    if "not found" in error_str:
        return f"No se encontró el archivo o carpeta requerido. {context}"
    if "permission" in error_str:
        return "No tienes permisos para escribir en esa ubicación. Elige otra carpeta o ejecuta como administrador."
    if "exists" in error_str:
        return "El archivo ya existe y no se pudo sobrescribir."
    return "Error al acceder a los archivos del proyecto. Verifica las rutas en Ajustes."

def _check_database_errors(error_str: str) -> str | None:
    """Verifica errores de base de datos."""
    if "sqlite" in error_str or "database" in error_str:
        return "Error con la base de datos de proyectos. Cierra y abre la aplicación. Si persiste, contacta al soporte."
    return None

def translate_error(error: Exception, context: str = "") -> str:
    """Traduce errores comunes a mensajes en español."""
    error_str = str(error).lower()

    # Lista de verificadores en orden de prioridad
    error_checkers = [
        lambda s: _check_network_errors(s),
        lambda s: _check_groq_errors(s),
        lambda s: _check_huggingface_errors(s),
        lambda s: _check_tts_errors(s),
        lambda s: _check_file_errors(s, context),
        lambda s: _check_database_errors(s),
    ]

    for checker in error_checkers:
        result = checker(error_str)
        if result:
            return result

    # Error genérico
    return f"Ocurrió un error inesperado: {str(error)[:100]}. Si el problema continúa, reinicia la aplicación."
