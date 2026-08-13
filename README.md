[README.md](https://github.com/user-attachments/files/31009307/README.md)
# Narrivox Studio Pro

> Plataforma de escritorio para convertir ideas, guiones y referencias visuales en contenido audiovisual asistido por inteligencia artificial.

Narrivox Studio Pro centraliza en una sola aplicación el flujo de creación de videos cortos: ideación, escritura de guiones, generación de imágenes, narración, edición visual y gestión de proyectos. Está diseñada para creadores de contenido, equipos audiovisuales y personas que quieren trabajar con IA sin tener que combinar varias herramientas independientes.

## Qué resuelve

Crear un video con IA suele implicar saltar entre un generador de texto, un servicio de voz, un generador de imágenes, un editor y varias carpetas de trabajo. Narrivox organiza ese proceso en una interfaz gráfica con proveedores intercambiables y configuración centralizada.

## Funcionalidades principales

- Generación de ideas y guiones con proveedores de texto configurables.
- Flujo de trabajo por series, capítulos y proyectos.
- Generación de imágenes con proveedores online, espacios de Hugging Face y modelos locales.
- Texto a voz con Edge TTS, ElevenLabs, UnrealSpeech y motores locales.
- Ensamblado de videos con MoviePy, efecto Ken Burns, subtítulos y B-Roll.
- Fallback entre proveedores cuando está habilitado.
- Gestión de modelos locales mediante Hugging Face.
- Biblioteca de voces y configuración de estilos visuales.
- Persistencia local de proyectos mediante SQLite.
- Interfaz de escritorio basada en CustomTkinter.
- Empaquetado para Windows mediante PyInstaller.

## Experiencia para usuarios no técnicos

Las API no se configuran editando el código fuente.

### Opción recomendada: panel de Ajustes

1. Abre Narrivox.
2. Entra en **Ajustes**.
3. Selecciona el proveedor de texto, imagen, voz o B-Roll.
4. Introduce la clave en el campo correspondiente.
5. Guarda la configuración.

El panel muestra únicamente los campos relacionados con el proveedor elegido. Por ejemplo, al seleccionar Groq aparece su clave; al seleccionar Cloudflare aparecen el Account ID, el token y el modelo.

### Opción recomendada para despliegues: archivo `.env`

Para conservar las credenciales entre sesiones o distribuir una instalación controlada:

1. Copia `.env.example` como `.env`.
2. Abre `.env` con el Bloc de notas.
3. Completa únicamente los servicios que vayas a utilizar.
4. Guarda el archivo y ejecuta Narrivox.

Ejemplo:

```env
GROQ_API_KEY=tu_clave_de_groq
ELEVENLABS_API_KEY=tu_clave_de_elevenlabs
HF_TOKEN=tu_token_de_huggingface
```

No es necesario completar todas las variables. Los proveedores que no utilices pueden permanecer vacíos.

### Proveedores disponibles

| Área | Proveedores |
|---|---|
| Texto | DeepSeek, Gemini, OpenRouter, Groq, OpenAI, Ollama y modelos locales |
| Imagen | Z-Image, Pollinations, Hugging Face, Cloudflare, Puter y modelos locales |
| Voz | Edge TTS, ElevenLabs, UnrealSpeech y motores locales |
| B-Roll | Pexels y Pixabay |

Las funciones online requieren conexión a Internet y, según el proveedor, una cuenta o una API válida. Edge TTS, Puter o algunos proveedores públicos pueden funcionar sin una clave propia, sujetos a sus límites y disponibilidad.

## Ejecutar desde el código fuente

### Requisitos

- Windows 10 o posterior.
- Python 3.11 o superior.
- Conexión a Internet para proveedores online.
- Espacio adicional si se descargan modelos locales.
- FFmpeg para determinadas funciones de audio y video.

### Instalación

```powershell
git clone <github.com/CxstroDev/Narrivox-studio-pro>
cd narrivox

py -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Configura las credenciales:

```powershell
Copy-Item .env.example .env
```

Después, inicia la aplicación:

```powershell
python main.py
```

Narrivox crea automáticamente la carpeta de proyectos y la base de datos local cuando se necesitan.


## Arquitectura

```text
narrivox/
├── main.py                    # Punto de entrada de la aplicación
├── src/                       # Lógica de negocio y servicios
│   ├── engines/               # Proveedores de texto, imagen, TTS y video
│   ├── ai_engine.py           # Generación de texto y fallback
│   ├── data_manager.py        # Persistencia de proyectos
│   ├── image_engine.py        # Fachada de generación de imágenes
│   ├── orchestrator.py        # Flujo completo de capítulos
│   ├── tts_engine.py          # Texto a voz
│   └── cinematic_engine.py    # Ensamblado audiovisual
├── ui/                        # Interfaz CustomTkinter
│   ├── frames/                # Vistas principales
│   ├── components/            # Componentes reutilizables
│   └── dialogs/               # Ventanas auxiliares
├── tests/                     # Pruebas automatizadas
├── models_catalog.json        # Catálogo de modelos disponibles
├── src/voices.json            # Catálogo de voces
├── requirements.txt           # Dependencias Python
├── pyproject.toml             # Configuración de herramientas
├── .env.example               # Plantilla de credenciales
└── build_windows.ps1          # Compilación del ejecutable
```

La aplicación mantiene separadas la interfaz y la lógica de negocio. Cada proveedor de IA funciona como un módulo intercambiable, lo que facilita agregar nuevos servicios sin rediseñar toda la aplicación.

## Pruebas y calidad

Ejecuta la suite con:

```powershell
python -m pytest -q
```

Comprobaciones adicionales:

```powershell
python -m compileall -q src ui main.py
python -m pip check
```

Estado verificado durante el desarrollo:

```text
28 passed, 6 skipped
```

Las pruebas de interfaz se omiten cuando no existe una sesión gráfica disponible.


## Limitaciones conocidas

- Los proveedores online dependen de sus APIs, límites y disponibilidad.
- Los modelos locales pueden requerir varios gigabytes de almacenamiento y memoria.
- Algunas funciones de audio y video requieren FFmpeg.
- El ejecutable de Windows se distribuye como carpeta portable; no es un instalador MSI.
- La primera carga puede tardar más cuando se inicializan bibliotecas de IA o modelos locales.

## Roadmap

- Instalador de Windows con acceso directo.
- Gestión de perfiles de proveedores y credenciales desde la interfaz.
- Exportación de proyectos y plantillas reutilizables.
- Mejoras de observabilidad y mensajes de error orientados a usuarios.
- Soporte ampliado para proveedores y modelos locales.

## Licencia

Narrivox Studio Pro se distribuye bajo la Apache License 2.0.
Esta licencia permite utilizar, modificar y distribuir el código, incluyendo usos comerciales, siempre que se conserve el aviso de copyright y la licencia correspondiente.

Consulta el texto completo en el archivo LICENSE o en:
https://www.apache.org/licenses/LICENSE-2.0
Copyright 2026 CxstroDev — Narrivox Studio Pro.

##Dependencias y servicios externos

El proyecto utiliza bibliotecas, modelos y servicios de terceros que pueden estar sujetos a sus propias licencias y condiciones de uso. La licencia Apache 2.0 de Narrivox aplica únicamente al código original de este proyecto.

Antes de distribuir una versión, revisa las condiciones de las APIs, modelos de inteligencia artificial, bibliotecas y recursos externos incluidos.

## Autoría y propósito

Narrivox Studio Pro es un proyecto demostrativo de ingeniería de software aplicada a herramientas creativas con IA. Su objetivo es mostrar arquitectura modular, integración de servicios externos, experiencia de usuario, persistencia local, automatización audiovisual y empaquetado de escritorio.
