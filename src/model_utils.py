# src/model_utils.py
"""
Utilidades para la gestión de modelos locales.
"""
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("Narrivox")

# Detectar raíz del proyecto (donde está main.py)
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

def ensure_models_dir() -> Path:
    """Crea el directorio de modelos si no existe y devuelve su ruta."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR

def get_model_path(category: str, config: dict) -> Path:
    """Devuelve la ruta completa al modelo local."""
    local_path = config.get("local_providers", {}).get(category, {}).get("local_path", "")
    if not local_path:
        return None
    # Si la ruta ya empieza con "models", no duplicar
    if local_path.startswith("models"):
        return BASE_DIR / local_path
    return MODELS_DIR / local_path

def is_local_model_available(category: str, config: dict[str, Any]) -> bool:
    """
    Verifica si el modelo local está descargado y disponible.
    
    Comprueba que:
    1. La ruta existe
    2. La carpeta no está vacía
    3. Existe al menos un archivo de configuración típico (config.json o similar)
    """
    model_path = get_model_path(category, config)
    if not model_path or not model_path.exists():
        return False

    # Verificar que no esté vacío
    if not any(model_path.iterdir()):
        return False

    # Verificar archivos clave según categoría
    key_files = {
        'text': ['config.json', 'model.safetensors', 'pytorch_model.bin'],
        'tts': ['config.json', 'model.safetensors', 'pytorch_model.bin'],
        'image': ['model_index.json', 'vae', 'unet'],
        'video': ['model_index.json', 'vae', 'unet']
    }

    files_to_check = key_files.get(category, ['config.json'])
    for file_pattern in files_to_check:
        # Buscar archivo o carpeta que coincida
        if list(model_path.glob(file_pattern)):
            return True
        if (model_path / file_pattern).exists():
            return True

    # Si no encontramos los archivos esperados, asumimos que está incompleto
    logger.warning(f"Modelo {category} en {model_path} parece incompleto.")
    return False

def get_model_info(category: str, config: dict[str, Any]) -> dict[str, Any]:
    """
    Obtiene información sobre el estado del modelo local.
    
    Returns:
        Diccionario con:
        - 'available': bool
        - 'path': str (ruta)
        - 'size_mb': float (tamaño en MB, 0 si no existe)
        - 'model_id': str (ID del modelo configurado)
    """
    info = {
        'available': False,
        'path': '',
        'size_mb': 0.0,
        'model_id': config.get("local_providers", {}).get(category, {}).get("model_id", "")
    }

    model_path = get_model_path(category, config)
    if model_path:
        info['path'] = str(model_path)
        if model_path.exists():
            # Calcular tamaño total
            total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
            info['size_mb'] = total_size / (1024 * 1024)
            info['available'] = is_local_model_available(category, config)

    return info

def check_torch_available() -> bool:
    """Verifica si PyTorch está instalado."""
    try:
        import torch
        return True
    except ImportError:
        return False

def check_transformers_available() -> bool:
    """Verifica si Transformers está instalado."""
    try:
        import transformers
        return True
    except ImportError:
        return False

def check_diffusers_available() -> bool:
    """Verifica si Diffusers está instalado."""
    try:
        import diffusers
        return True
    except ImportError:
        return False

def lazy_import_torch():
    """Importa torch solo cuando se necesita, con mensaje de error amigable."""
    try:
        import torch
        return torch
    except ImportError:
        raise ImportError(
            "PyTorch no está instalado. Para usar modelos locales, ejecuta:\n"
            "pip install torch --index-url https://download.pytorch.org/whl/cpu"
        )

def lazy_import_transformers():
    """Importa transformers solo cuando se necesita, con mensaje de error amigable."""
    try:
        import transformers
        return transformers
    except ImportError:
        raise ImportError(
            "Transformers no está instalado. Para usar modelos locales, ejecuta:\n"
            "pip install transformers accelerate"
        )

def lazy_import_diffusers():
    """Importa diffusers solo cuando se necesita, con mensaje de error amigable."""
    try:
        import diffusers
        return diffusers
    except ImportError:
        raise ImportError(
            "Diffusers no está instalado. Para usar modelos locales, ejecuta:\n"
            "pip install diffusers"
        )

def get_download_instructions(category: str, config: dict[str, Any]) -> str:
    """
    Genera instrucciones amigables para descargar manualmente un modelo.
    """
    cat_config = config.get("local_providers", {}).get(category, {})
    model_id = cat_config.get("model_id", "")
    model_path = get_model_path(category, config)

    instructions = f"""
=== INSTRUCCIONES PARA DESCARGAR MODELO {category.upper()} ===

Modelo necesario: {model_id}

Opción 1 (Recomendada) - Usar Git LFS:
1. Instala Git LFS desde https://git-lfs.com
2. Abre una terminal en: {model_path.parent}
3. Ejecuta:
   git lfs install
   git clone https://huggingface.co/{model_id} {model_path.name}

Opción 2 - Descarga manual:
1. Visita: https://huggingface.co/{model_id}/tree/main
2. Descarga todos los archivos (especialmente config.json y los archivos .safetensors)
3. Colócalos en la carpeta: {model_path}

Tamaño estimado: 
- Qwen 2.5 1.5B (texto): ~3 GB
- Kokoro 82M (voz): ~330 MB
- Small-SD v0 (imagen): ~2 GB
- Zeroscope v2 (video): ~10 GB

Una vez descargado, reinicia la aplicación.
"""
    return instructions
