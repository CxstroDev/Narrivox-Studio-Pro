# src/config_manager.py
import json
import os
import logging
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger("Narrivox")

# Detectar la raíz del proyecto (donde está main.py)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(dotenv_path=ENV_PATH)

CONFIG_FILE = BASE_DIR / "config_narrivox.json"

DEFAULT_CONFIG = {
    # General
    "base_folder": str(BASE_DIR / "PROYECTOS_NARRIVOX"),
    "user_name": "Narrivox Studio Pro",
    "max_workers": 4,

    # IA - Texto
    "ia_provider": "deepseek",
    "ia_model": "deepseek-chat",
    "ia_temp": 0.7,
    "enable_fallback": True,
    "ai_fallback_chain": [
        {"provider": "deepseek", "model": "deepseek-chat"},
        {"provider": "gemini", "model": "gemini-2.0-flash"},
        {"provider": "openrouter", "model": "google/gemma-3-27b-it"},
        {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        {"provider": "ollama", "model": "llama3"}
    ],
    "ai_fallback_chain_str": "deepseek:deepseek-chat\ngemini:gemini-2.0-flash\nopenrouter:google/gemma-3-27b-it\ngroq:llama-3.3-70b-versatile\nollama:llama3",

    # API Keys IA (vacías por seguridad, se cargan desde .env)
    "api_key": "",
    "deepseek_api_key": "",
    "openrouter_api_key": "",
    "gemini_api_key": "",
    "openai_api_key": "",
    "openai_base_url": "https://api.openai.com/v1",
    "ollama_base_url": "http://localhost:11434/v1",

    # TTS
    "tts_provider": "edge",
    "elevenlabs_api_key": "",
    "elevenlabs_voice_id": "21m00Tcm4TlvDq8ikWAM",
    "unrealspeech_api_key": "",

    # Imagen
    "image_provider": "zimage",
    "hf_token": "",
    "hf_model_id": "stabilityai/stable-diffusion-xl-base-1.0",
    "local_model_id": "stabilityai/stable-diffusion-xl-base-1.0",
    "zimage_space": "mrfakename/Z-Image-Turbo",
    "pollinations_api_key": "",
    "cloudflare_ID": "",
    "cloudflare_token": "",

    # Video / B-Roll
    "enable_ken_burns": True,
    "enable_broll": False,
    "broll_provider": "none",
    "pexels_api_key": "",
    "pixabay_api_key": "",
    "helios_space": "BestWishYsh/Helios-14B-RealTime-AOTI",
    "svd_space": "stabilityai/stable-video-diffusion-img2vid",

    # Marketing
    "enable_marketing": True,

    # Plantillas
    "prompt_template": "Eres un guionista experto en videos de 60 segundos. Serie: '{serie}', parte {parte}. Tema: {tema}, Objeto: {objeto}, Anomalía: {anomalia}, Emoción: {emocion}, Tono: {tono}. Estructura: {estructura}. Notas: {notas}. Usa frases cortas y termina con un cliffhanger brutal.",
    "visual_prompt_template": "Basado en el siguiente guion, genera 4 prompts detallados para IA de imagen (Midjourney/DALL-E). Cada prompt debe describir una escena clave con estilo {estilo}, iluminación dramática y calidad 8k. Guion: {guion}",

    # Directorio creativo
    "directory": {
        "TEMAS": ["Terror Psicológico", "Suspenso", "Misterio", "Sci-Fi Oscuro", "Cyberpunk", "Fantasía Épica", "Terror", "Sci-Fi", "Drama", "Acción", "Crimen", "Isekai"],
        "OBJETOS": ["Un viejo cassette", "Una cámara Parlante", "Un espejo manchado", "Libro", "Reloj de arena", "Daga de cristal", "Chip de memoria", "Espejo", "Reloj", "Puerta", "Juguete"],
        "ANOMALIAS": ["Voces extrañas", "Sombras vivas", "Eco temporal", "Gravedad inversa", "Colores imposibles", "Muestra el futuro", "Cambia de forma", "Viaje en el tiempo", "Invasión"],
        "EMOCIONES": ["Incomodidad", "Pavor", "Nostalgia", "Paranoia", "Miedo", "Ansiedad", "Curiosidad", "Tristeza", "Ira", "Alegría"],
        "ESTADOS": ["Pendiente", "Para Grabar", "Listo", "Publicado"]
    },
    "visual_styles": ["Fotorrealista", "Gótico A24", "Cyberpunk Oscuro", "Óleo Macabro", "Anime Gore", "Realismo Analógico"],

    # NUEVAS CLAVES PARA MODO HÍBRIDO LOCAL/ONLINE
    "local_providers": {
        "text": {
            "enabled": False,
            "model_id": "Qwen/Qwen2.5-1.5B-Instruct",  # Modelo por defecto
            "local_path": "models/qwen2.5-1.5b-instruct",
            "device": "cpu",
            "quantize": None,
            "selected_model": "",  # Se llenará automáticamente
            "installed": {}        # Se llenará con el escaneo
        },
        "tts": {
            "enabled": False,
            "model_id": "hexgrad/Kokoro-82M",
            "local_path": "models/kokoro",
            "device": "cpu",
            "port": 8880,
            "selected_model": "",
            "installed": {}
        },
        "image": {
            "enabled": False,
            "model_id": "OFA-Sys/small-stable-diffusion-v0",
            "local_path": "models/small-sd-v0",
            "device": "cpu",
            "scheduler": "ddim",
            "selected_model": "",
            "installed": {}
        },
        "video": {
            "enabled": False,
            "model_id": "cerspense/zeroscope_v2_576w",
            "local_path": "models/zeroscope_v2",
            "device": "cpu",
            "fps": 8,
            "selected_model": "",
            "installed": {}
        }
    },
    "prefer_local": False,
    "fallback_to_online": True,
}

def load_models_catalog():
    """Carga el catálogo de modelos desde models_catalog.json."""
    catalog_path = BASE_DIR / "models_catalog.json"
    if catalog_path.exists():
        try:
            with open(catalog_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando catálogo de modelos: {e}")
    return {
        "text": [],
        "image": [],
        "tts": []
    }

def load_config():
    """Carga configuración: primero defaults, luego JSON, finalmente variables de entorno."""
    config = DEFAULT_CONFIG.copy()

    # 1. Cargar desde archivo JSON si existe
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            logger.error(f"Error leyendo config JSON: {e}")

    # 2. Sobrescribir con variables de entorno (máxima prioridad)
    env_map = {
        "api_key": "GROQ_API_KEY",
        "deepseek_api_key": "DEEPSEEK_API_KEY",
        "gemini_api_key": "GEMINI_API_KEY",
        "openai_api_key": "OPENAI_API_KEY",
        "openrouter_api_key": "OPENROUTER_API_KEY",
        "elevenlabs_api_key": "ELEVENLABS_API_KEY",
        "unrealspeech_api_key": "UNREALSPEECH_API_KEY",
        "hf_token": "HF_TOKEN",
        "pexels_api_key": "PEXELS_API_KEY",
        "pixabay_api_key": "PIXABAY_API_KEY",
        "pollinations_api_key": "POLLINATIONS_API_KEY",
        "cf_account_id": "CF_ACCOUNT_ID",
        "cf_api_token": "CF_API_TOKEN",
    }

    for config_key, env_var in env_map.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            config[config_key] = env_value

    # 3. Asegurar que base_folder sea absoluto y exista
    base = Path(config["base_folder"])
    if not base.is_absolute():
        base = BASE_DIR / base
    base.mkdir(parents=True, exist_ok=True)
    config["base_folder"] = str(base)

    return config

def save_config(config_data):
    """Guarda la configuración en JSON, omitiendo claves sensibles."""
    safe_config = config_data.copy()
    # Claves que NUNCA deben guardarse en el JSON
    sensitive_keys = [
        "api_key", "deepseek_api_key", "gemini_api_key", "openai_api_key",
        "openrouter_api_key", "elevenlabs_api_key", "unrealspeech_api_key",
        "hf_token", "pexels_api_key", "pixabay_api_key", "pollinations_api_key",
        "cf_api_token", "cloudflare_token"
    ]
    for key in sensitive_keys:
        if key in safe_config:
            # Siempre eliminar del JSON, independientemente de su origen
            safe_config[key] = ""

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(safe_config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error guardando config: {e}")
        return False
