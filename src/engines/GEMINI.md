# Motores de IA (src/engines/)

Esta sección detalla la implementación de los motores de IA en Narrivox.

## Patrón de Proveedores
Todos los motores siguen un patrón de "Strategy" donde una clase base define la interfaz y múltiples proveedores implementan la lógica específica.

### 📝 Texto (`text/`)
- **Base**: `base.py` define `TextProvider`.
- **Implementaciones**: Groq, OpenAI (compatible con DeepSeek/OpenRouter/Ollama), Gemini.
- **Uso**: El `AIEngine` selecciona el proveedor según la configuración.

### 🖼️ Imagen (`image/`)
- **Base**: `base.py` define `ImageEngineBase`.
- **Implementaciones**: Pollinations (rápido, gratuito), Hugging Face (remoto), Local (Stable Diffusion).
- **Zimage**: Implementación especial para previsualizaciones rápidas.

### 🔊 TTS (`tts/`)
- **Base**: `base.py` define `TTSEngineBase`.
- **Implementaciones**: Edge TTS (gratuito), ElevenLabs (alta calidad), UnrealSpeech, Local (Kokoro).
- **Gestión de Voces**: Las voces se mapean en `src/voices.json`.

### 🎬 Video (`video/`)
- **Composer**: Gestiona el ensamble de clips, audio y superposición de imágenes usando MoviePy.
- **Subtitles**: Genera archivos SRT y los quema en el video con estilos personalizables.

## Guía de Extensión
Para añadir un nuevo proveedor:
1. Heredar de la clase `Base` correspondiente.
2. Implementar el método principal (ej. `generate` o `synthesize`).
3. Registrar el nuevo proveedor en el motor principal correspondiente (ej. `ai_engine.py` o `tts_engine.py`).
