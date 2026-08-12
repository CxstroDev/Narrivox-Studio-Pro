# ui/styles.py
# Configuración de colores, fuentes e iconos para Narrivox Studio Pro
# Sistema de diseño mejorado con mejor contraste, jerarquía visual y accesibilidad

# ============================================
# SISTEMA DE COLORES MEJORADO
# ============================================

# Colores de fondo - Mayor contraste y mejor legibilidad
COLOR_BG = ("#f8fafc", "#0f172a")           # Fondo principal (slate-50 / slate-900)
COLOR_SIDEBAR = ("#f1f5f9", "#1e293b")      # Sidebar (slate-100 / slate-800)
COLOR_CARD = ("#ffffff", "#1e293b")        # Tarjetas (white / slate-800)
COLOR_CARD_HOVER = ("#f8fafc", "#334155")   # Tarjetas hover (slate-50 / slate-700)

# Colores de texto - Mejor contraste para accesibilidad
COLOR_TEXT = ("#0f172a", "#f8fafc")         # Texto principal (slate-900 / slate-50)
COLOR_TEXT_DIM = ("#475569", "#94a3b8")     # Texto secundario (slate-600 / slate-400)
COLOR_TEXT_MUTED = ("#64748b", "#64748b")    # Texto deshabilitado (slate-500)

# Colores de elementos interactivos
COLOR_FG_BOX = ("#e2e8f0", "#334155")       # Cajas de entrada (slate-200 / slate-700)
COLOR_BORDER = ("#cbd5e1", "#475569")      # Bordes (slate-300 / slate-600)
COLOR_BORDER_SUBTLE = ("#e2e8f0", "#334155") # Bordes sutiles

# Colores de acento - Paleta moderna y coherente
COLOR_ACCENT = ("#6366f1", "#6366f1")      # Acento principal (indigo-500)
COLOR_ACCENT_HOVER = ("#4f46e5", "#4f46e5") # Acento hover (indigo-600)
COLOR_ACCENT_LIGHT = ("#e0e7ff", "#312e81") # Acento claro/oscuro (indigo-100 / indigo-900)

COLOR_SUCCESS = ("#10b981", "#10b981")      # Éxito (emerald-500)
COLOR_SUCCESS_HOVER = ("#059669", "#059669") # Éxito hover (emerald-600)
COLOR_SUCCESS_LIGHT = ("#d1fae5", "#064e3b") # Éxito claro/oscuro

COLOR_WARNING = ("#f59e0b", "#f59e0b")      # Advertencia (amber-500)
COLOR_WARNING_HOVER = ("#d97706", "#d97706") # Advertencia hover (amber-600)
COLOR_WARNING_LIGHT = ("#fef3c7", "#78350f") # Advertencia claro/oscuro

COLOR_ERROR = ("#ef4444", "#ef4444")        # Error (red-500)
COLOR_ERROR_HOVER = ("#dc2626", "#dc2626")  # Error hover (red-600)
COLOR_ERROR_LIGHT = ("#fee2e2", "#7f1d1d")  # Error claro/oscuro

COLOR_INFO = ("#3b82f6", "#3b82f6")         # Información (blue-500)
COLOR_INFO_HOVER = ("#2563eb", "#2563eb")   # Información hover (blue-600)
COLOR_INFO_LIGHT = ("#dbeafe", "#1e3a8a")   # Información claro/oscuro

# Colores específicos de IA
COLOR_IA = ("#8b5cf6", "#8b5cf6")           # IA (violet-500)
COLOR_IA_HOVER = ("7c3aed", "#7c3aed")     # IA hover (violet-600)
COLOR_IA_LIGHT = ("#ede9fe", "#4c1d95")    # IA claro/oscuro

# Colores de categorías
COLOR_CATEGORY_THEME = ("#8b5cf6", "#8b5cf6")    # Temas (violet)
COLOR_CATEGORY_OBJECT = ("#3b82f6", "#3b82f6")     # Objetos (blue)
COLOR_CATEGORY_ANOMALY = ("#f59e0b", "#f59e0b")    # Anomalías (amber)
COLOR_CATEGORY_EMOTION = ("#10b981", "#10b981")   # Emociones (emerald)

# ============================================
# SISTEMA DE TIPOGRAFÍA MEJORADO
# ============================================

# Fuentes principales - Usamos fuentes del sistema para mejor rendimiento
FONT_FAMILY = "Segoe UI"  # Fuente principal (puede ser "Roboto", "Helvetica", etc.)

# Tamaños y pesos de fuente
FONT_H1 = (FONT_FAMILY, 28, "bold")        # Títulos principales
FONT_H2 = (FONT_FAMILY, 24, "bold")        # Títulos de sección
FONT_H3 = (FONT_FAMILY, 20, "bold")        # Subtítulos
FONT_H4 = (FONT_FAMILY, 18, "bold")        # Encabezados de tarjeta
FONT_H5 = (FONT_FAMILY, 16, "bold")        # Encabezados pequeños

FONT_BODY_LARGE = (FONT_FAMILY, 14, "normal")  # Texto grande
FONT_BODY = (FONT_FAMILY, 13, "normal")        # Texto normal
FONT_BODY_SMALL = (FONT_FAMILY, 12, "normal")  # Texto pequeño
FONT_BODY_TINY = (FONT_FAMILY, 11, "normal")   # Texto muy pequeño

FONT_LABEL = (FONT_FAMILY, 13, "bold")     # Etiquetas
FONT_LABEL_SMALL = (FONT_FAMILY, 12, "bold") # Etiquetas pequeñas
FONT_BUTTON = (FONT_FAMILY, 13, "bold")    # Botones
FONT_BUTTON_SMALL = (FONT_FAMILY, 12, "bold") # Botones pequeños

# ============================================
# SISTEMA DE ESPACIADO
# ============================================

# Espaciado consistente
SPACING_XS = 4      # Espaciado muy pequeño
SPACING_SM = 8      # Espaciado pequeño
SPACING_MD = 16     # Espaciado medio
SPACING_LG = 24     # Espaciado grande
SPACING_XL = 32     # Espaciado muy grande
SPACING_XXL = 48    # Espaciado extra grande

# ============================================
# SISTEMA DE BORDES Y RADIOS
# ============================================

RADIUS_NONE = 0
RADIUS_SM = 4       # Bordes pequeños
RADIUS_MD = 8       # Bordes medianos
RADIUS_LG = 12      # Bordes grandes
RADIUS_XL = 16      # Bordes muy grandes
RADIUS_2XL = 20     # Bordes extra grandes
RADIUS_FULL = 9999  # Bordes completamente redondeados

# ============================================
# SISTEMA DE SOMBRAS (simulado con bordes)
# ============================================

# Sombras sutiles para dar profundidad
SHADOW_NONE = ("#e2e8f0", "#1e293b")           # Sin sombra
SHADOW_SM = ("#cbd5e1", "#334155")             # Sombra pequeña
SHADOW_MD = ("#94a3b8", "#475569")             # Sombra media
SHADOW_LG = ("#64748b", "#334155")             # Sombra grande

# ============================================
# ICONOS UNICODE (mejorados y consistentes)
# ============================================

# Iconos de navegación
ICONS = {
    # Navegación principal
    "INICIO": "🏠",           # Inicio
    "GUION": "✍️",            # Guionista
    "VISUAL": "🖼️",          # Director Visual
    "VIDEO": "🎬",            # Director de Video
    "LIB": "📚",              # Proyectos
    "AJUSTES": "⚙️",          # Ajustes

    # Categorías de contenido
    "TEMAS": "🎭",            # Temas
    "OBJETOS": "🔮",          # Objetos
    "ANOMALIAS": "☣️",        # Anomalías
    "EMOCIONES": "🧠",        # Emociones
    "STORY": "📋",            # Historia

    # Estados y acciones
    "LOCK": "🔒",             # Bloqueado
    "UNLOCK": "🔓",           # Desbloqueado
    "SAVE": "💾",             # Guardar
    "LOAD": "📂",             # Cargar
    "DELETE": "🗑️",           # Eliminar
    "EDIT": "✏️",             # Editar
    "PLAY": "▶️",             # Reproducir
    "PAUSE": "⏸️",            # Pausar
    "STOP": "⏹️",             # Detener
    "DOWNLOAD": "⬇️",         # Descargar
    "UPLOAD": "⬆️",           # Subir
    "REFRESH": "🔄",          # Actualizar
    "SEARCH": "🔍",           # Buscar
    "FILTER": "🔎",           # Filtrar
    "SORT": "📊",            # Ordenar
    "SETTINGS": "⚙️",        # Configuración
    "INFO": "ℹ️",             # Información
    "WARNING": "⚠️",         # Advertencia
    "ERROR": "❌",            # Error
    "SUCCESS": "✅",          # Éxito
    "CLOSE": "✖",            # Cerrar
    "CHECK": "✔",             # Verificar
    "STAR": "⭐",             # Favorito
    "HEART": "❤️",            # Me gusta
    "SHARE": "📤",           # Compartir
    "COPY": "📋",            # Copiar
    "PASTE": "📋",           # Pegar
    "CUT": "✂️",             # Cortar
    "UNDO": "↩️",            # Deshacer
    "REDO": "↪️",            # Rehacer
    "ZOOM_IN": "🔍+",         # Acercar
    "ZOOM_OUT": "🔍-",        # Alejar
    "FULLSCREEN": "⛶",       # Pantalla completa
    "MINIMIZE": "−",         # Minimizar
    "MAXIMIZE": "□",         # Maximizar

    # Estados de modelos
    "MODEL_INSTALLED": "✅",  # Modelo instalado
    "MODEL_DOWNLOADING": "⏳", # Modelo descargando
    "MODEL_AVAILABLE": "🌐",  # Modelo disponible
    "MODEL_ACTIVE": "⭐",     # Modelo activo

    # Media
    "IMAGE": "🖼️",           # Imagen
    "VIDEO": "🎬",           # Video
    "AUDIO": "🎵",           # Audio
    "MICROPHONE": "🎤",      # Micrófono
    "VOLUME": "🔊",          # Volumen
    "MUTE": "🔇",            # Silenciar

    # AI y tecnología
    "AI": "🤖",              # Inteligencia Artificial
    "BRAIN": "🧠",           # Cerebro
    "CHIP": "💻",            # Chip/Procesador
    "NETWORK": "🌐",         # Red
    "CLOUD": "☁️",           # Nube
    "DATABASE": "🗄️",        # Base de datos

    # Documentos
    "FILE": "📄",            # Archivo
    "FOLDER": "📁",          # Carpeta
    "DOCUMENT": "📝",        # Documento
    "PDF": "📕",             # PDF
    "TEXT": "📃",            # Texto

    # Comunicación
    "MAIL": "✉️",            # Correo
    "CHAT": "💬",            # Chat
    "PHONE": "📞",           # Teléfono
    "BELL": "🔔",            # Notificación

    # Usuarios y personas
    "USER": "👤",            # Usuario
    "USERS": "👥",           # Usuarios
    "ADMIN": "👑",           # Administrador
    "GUEST": "👻",           # Invitado

    # Herramientas
    "TOOL": "🔧",            # Herramienta
    "WRENCH": "🔧",          # Llave
    "HAMMER": "🔨",          # Martillo
    "SCREWDRIVER": "🪛",     # Destornillador

    # Naturaleza y ambiente
    "SUN": "☀️",             # Sol
    "MOON": "🌙",            # Luna
    "STAR": "⭐",            # Estrella
    "CLOUD": "☁️",           # Nube
    "RAIN": "🌧️",            # Lluvia
    "SNOW": "❄️",            # Nieve
    "FIRE": "🔥",            # Fuego
    "WATER": "💧",           # Agua

    # Transporte
    "CAR": "🚗",             # Coche
    "BUS": "🚌",             # Autobús
    "TRAIN": "🚂",           # Tren
    "PLANE": "✈️",           # Avión
    "SHIP": "🚢",            # Barco

    # Comida y bebida
    "FOOD": "🍔",            # Comida
    "DRINK": "🥤",           # Bebida
    "COFFEE": "☕",          # Café
    "RESTAURANT": "🍽️",     # Restaurante

    # Deportes y entretenimiento
    "SPORT": "⚽",           # Deporte
    "MUSIC": "🎵",           # Música
    "GAME": "🎮",            # Juego
    "MOVIE": "🎬",           # Película
    "BOOK": "📚",            # Libro

    # Símbolos varios
    "PLUS": "+",             # Más
    "MINUS": "−",            # Menos
    "DIVIDE": "÷",           # Dividir
    "MULTIPLY": "×",         # Multiplicar
    "EQUAL": "=",            # Igual
    "PERCENT": "%",          # Porcentaje
    "DOLLAR": "$",           # Dólar
    "EURO": "€",             # Euro
    "POUND": "£",            # Libra
    "YEN": "¥",              # Yen
    "AT": "@",               # Arroba
    "HASH": "#",             # Numeral
    "AMPERSAND": "&",        # Ampersand
    "ASTERISK": "*",         # Asterisco
    "SLASH": "/",            # Barra
    "BACKSLASH": "\\",       # Barra invertida
    "PIPE": "|",             # Tubo
    "UNDERSCORE": "_",       # Guion bajo
    "DASH": "-",             # Guion
    "DOT": ".",              # Punto
    "COMMA": ",",            # Coma
    "COLON": ":",            # Dos puntos
    "SEMICOLON": ";",        # Punto y coma
    "QUESTION": "?",         # Interrogación
    "EXCLAMATION": "!",      # Exclamación
    "QUOTE": '"',            # Comillas
    "APOSTROPHE": "'",       # Apóstrofe
    "PARENTHESIS_LEFT": "(", # Paréntesis izquierdo
    "PARENTHESIS_RIGHT": ")",# Paréntesis derecho
    "BRACKET_LEFT": "[",     # Corchete izquierdo
    "BRACKET_RIGHT": "]",    # Corchete derecho
    "BRACE_LEFT": "{",       # Llave izquierda
    "BRACE_RIGHT": "}",      # Llave derecha
    "ANGLE_LEFT": "<",       # Ángulo izquierdo
    "ANGLE_RIGHT": ">",      # Ángulo derecho
}

# ============================================
# ALIAS PARA COMPATIBILIDAD CON CÓDIGO EXISTENTE
# ============================================

# Mantener compatibilidad con código existente
FONT_TITLE = FONT_H2
FONT_SUBTITLE = FONT_H3
FONT_NORMAL = FONT_BODY
