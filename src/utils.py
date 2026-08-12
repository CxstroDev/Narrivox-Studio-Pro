# src/utils.py
import logging
import os
import platform
import re
import subprocess
import unicodedata
from datetime import datetime
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Configurar logging con rotación (máximo 5 MB por archivo, 3 backups)
log_file = os.path.join(LOGS_DIR, "narrivox.log")
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger("Narrivox")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(console_handler)


def clean_filename(text: str) -> str:
    """
    Sanitiza un string para usarlo como nombre de archivo/carpeta.
    Elimina acentos, caracteres especiales y reemplaza espacios por guiones bajos.
    """
    if not text:
        return "sin_nombre"
    # Normalizar Unicode (NFKD) y eliminar acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Reemplazar caracteres no permitidos por guión bajo
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    # Reemplazar espacios y otros separadores por guión bajo
    text = re.sub(r'[\s]+', '_', text)
    return text.strip('_')


def open_folder(path: str):
    if not os.path.exists(path):
        logger.warning(f"Intento de abrir carpeta inexistente: {path}")
        return
    try:
        # Validar que la ruta sea segura
        if not os.path.isabs(path):
            logger.warning(f"Ruta relativa no permitida: {path}")
            return

        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)
    except Exception as e:
        logger.error(f"Error al abrir carpeta {path}: {e}")


def format_time(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
