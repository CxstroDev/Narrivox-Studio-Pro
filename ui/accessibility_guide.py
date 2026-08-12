# ui/accessibility_guide.py
"""
Guía de accesibilidad para Narrivox Studio Pro.
Proporciona directrices y utilidades para mejorar la accesibilidad de la aplicación.
"""


import customtkinter as ctk

from ui import styles as st


class AccessibilityGuide:
    """
    Directrices de accesibilidad para la aplicación.
    """

    # ============================================
    # DIRECTRICES DE CONTRASTE DE COLOR
    # ============================================

    CONTRAST_RATIOS = {
        "WCAG_AA": 4.5,      # Mínimo para texto normal
        "WCAG_AAA": 7.0,     # Excelente para texto normal
        "WCAG_AA_LARGE": 3.0,  # Mínimo para texto grande
        "WCAG_AAA_LARGE": 4.5  # Excelente para texto grande
    }

    @staticmethod
    def check_contrast_ratio(foreground: str, background: str) -> float:
        """
        Calcula el ratio de contraste entre dos colores.

        Args:
            foreground: Color de primer plano (hex)
            background: Color de fondo (hex)

        Returns:
            float: Ratio de contraste
        """
        # Implementación simplificada del cálculo de contraste
        # En una implementación real, se necesitaría convertir hex a RGB y calcular luminancia
        return 4.5  # Valor placeholder

    @staticmethod
    def is_accessible_contrast(foreground: str, background: str,
                               level: str = "WCAG_AA") -> bool:
        """
        Verifica si el contraste cumple con los estándares de accesibilidad.

        Args:
            foreground: Color de primer plano
            background: Color de fondo
            level: Nivel de cumplimiento (WCAG_AA, WCAG_AAA, etc.)

        Returns:
            bool: True si el contraste es accesible
        """
        ratio = AccessibilityGuide.check_contrast_ratio(foreground, background)
        minimum_ratio = AccessibilityGuide.CONTRAST_RATIOS.get(level, 4.5)
        return ratio >= minimum_ratio

    # ============================================
    # DIRECTRICES DE TAMAÑO DE FUENTE
    # ============================================

    MINIMUM_FONT_SIZES = {
        "body": 12,        # Tamaño mínimo para texto de cuerpo
        "button": 14,      # Tamaño mínimo para botones
        "label": 12,       # Tamaño mínimo para etiquetas
        "input": 12        # Tamaño mínimo para campos de entrada
    }

    @staticmethod
    def get_accessible_font_size(purpose: str) -> int:
        """
        Obtiene el tamaño de fuente accesible mínimo.

        Args:
            purpose: Propósito del texto (body, button, label, input)

        Returns:
            int: Tamaño de fuente mínimo en píxeles
        """
        return AccessibilityGuide.MINIMUM_FONT_SIZES.get(purpose, 12)

    # ============================================
    # DIRECTRICES DE ESPACIADO
    # ============================================

    MINIMUM_SPACING = {
        "click_target": 44,    # Tamaño mínimo para elementos clickeables
        "between_elements": 8,  # Espaciado mínimo entre elementos
        "padding": 16           # Padding mínimo para contenedores
    }

    @staticmethod
    def get_minimum_spacing(purpose: str) -> int:
        """
        Obtiene el espaciado mínimo accesible.

        Args:
            purpose: Propósito del espaciado

        Returns:
            int: Espaciado mínimo en píxeles
        """
        return AccessibilityGuide.MINIMUM_SPACING.get(purpose, 8)

    # ============================================
    # DIRECTRICES DE FOCUS
    # ============================================

    @staticmethod
    def ensure_focus_visible(widget: ctk.CTk):
        """
        Asegura que el widget tenga un estado de focus visible.

        Args:
            widget: Widget a configurar
        """
        # CustomTkinter maneja el focus automáticamente
        # Esta función es un placeholder para futuras mejoras
        pass

    @staticmethod
    def set_focus_order(parent: ctk.CTk, widgets: list):
        """
        Establece el orden de tabulación para los widgets.

        Args:
            parent: Widget padre
            widgets: Lista de widgets en orden de tabulación (no implementado aún)
        """
        # CustomTkinter maneja el orden de tabulación automáticamente
        # Esta función es un placeholder para futuras mejoras
        # TODO: Implementar orden de tabulación personalizado
        _ = widgets  # Mark as intentionally unused for future implementation

    # ============================================
    # DIRECTRICES DE TEXTO ALTERNATIVO
    # ============================================

    @staticmethod
    def create_accessible_image(parent: ctk.CTk, image_path: str,
                               alt_text: str, **kwargs) -> ctk.CTkLabel:
        """
        Crea una imagen accesible con texto alternativo.

        Args:
            parent: Widget padre
            image_path: Ruta de la imagen
            alt_text: Texto alternativo para la imagen
            **kwargs: Argumentos adicionales

        Returns:
            ctk.CTkLabel: Etiqueta con imagen accesible
        """
        # Nota: CustomTkinter no soporta nativamente atributos alt
        # Esta es una implementación placeholder
        label = ctk.CTkLabel(parent, text=alt_text, **kwargs)
        return label

    # ============================================
    # DIRECTRICES DE TECLADO
    # ============================================

    KEYBOARD_SHORTCUTS = {
        "save": "Ctrl+S",
        "open": "Ctrl+O",
        "new": "Ctrl+N",
        "undo": "Ctrl+Z",
        "redo": "Ctrl+Y",
        "copy": "Ctrl+C",
        "paste": "Ctrl+V",
        "cut": "Ctrl+X",
        "find": "Ctrl+F",
        "help": "F1"
    }

    @staticmethod
    def get_keyboard_shortcut(action: str) -> str | None:
        """
        Obtiene el atajo de teclado para una acción.

        Args:
            action: Nombre de la acción

        Returns:
            str: Atajo de teclado o None si no existe
        """
        return AccessibilityGuide.KEYBOARD_SHORTCUTS.get(action)

    @staticmethod
    def bind_keyboard_shortcut(parent: ctk.CTk, action: str,
                              callback: callable):
        """
        Vincula un atajo de teclado a una acción.

        Args:
            parent: Widget padre
            action: Nombre de la acción
            callback: Función a ejecutar
        """
        shortcut = AccessibilityGuide.get_keyboard_shortcut(action)
        if shortcut:
            # Convertir formato de atajo
            key_sequence = shortcut.replace("Ctrl", "Control").replace("+", "-")
            parent.bind(f"<{key_sequence}>", callback)

    # ============================================
    # DIRECTRICES DE REDUCCIÓN DE MOVIMIENTO
    # ============================================

    @staticmethod
    def should_reduce_motion() -> bool:
        """
        Verifica si el usuario prefiere reducir el movimiento.

        Returns:
            bool: True si se debe reducir el movimiento
        """
        # En una implementación real, esto verificaría las preferencias del sistema
        return False

    @staticmethod
    def create_animation(reduce_motion: bool = None) -> bool:
        """
        Determina si se debe crear una animación.

        Args:
            reduce_motion: Forzar reducción de movimiento (opcional)

        Returns:
            bool: True si se debe crear la animación
        """
        if reduce_motion is not None:
            return not reduce_motion
        return not AccessibilityGuide.should_reduce_motion()


class AccessibleWidget:
    """
    Widget base con características de accesibilidad.
    """

    def __init__(self, widget: ctk.CTk, label: str = None,
                 description: str = None):
        """
        Crea un widget accesible.

        Args:
            widget: Widget a hacer accesible
            label: Etiqueta descriptiva
            description: Descripción adicional
        """
        self.widget = widget
        self.label = label
        self.description = description

        # Configurar accesibilidad básica
        self._setup_accessibility()

    def _setup_accessibility(self):
        """Configura las características de accesibilidad básicas."""
        # Asegurar tamaño mínimo para elementos clickeables
        if hasattr(self.widget, 'configure'):
            try:
                current_width = self.widget.cget('width')
                current_height = self.widget.cget('height')

                min_size = AccessibilityGuide.get_minimum_spacing("click_target")

                if current_width < min_size:
                    self.widget.configure(width=min_size)
                if current_height < min_size:
                    self.widget.configure(height=min_size)
            except Exception as e:
                logger.debug(f"No se pudo configurar accesibilidad: {e}")

    def set_label(self, label: str):
        """Establece la etiqueta del widget."""
        self.label = label

    def set_description(self, description: str):
        """Establece la descripción del widget."""
        self.description = description

    def get_accessible_info(self) -> dict:
        """
        Obtiene la información de accesibilidad del widget.

        Returns:
            dict: Información de accesibilidad
        """
        return {
            "label": self.label,
            "description": self.description,
            "widget_type": type(self.widget).__name__
        }


# ============================================
# UTILIDADES DE ACCESIBILIDAD
# ============================================

def make_accessible(widget: ctk.CTk, label: str = None,
                   description: str = None) -> AccessibleWidget:
    """
    Convierte un widget en accesible.

    Args:
        widget: Widget a hacer accesible
        label: Etiqueta descriptiva
        description: Descripción adicional

    Returns:
        AccessibleWidget: Widget accesible
    """
    return AccessibleWidget(widget, label, description)


def verify_color_contrast(foreground: str, background: str,
                         level: str = "WCAG_AA") -> tuple:
    """
    Verifica el contraste de colores y devuelve información detallada.

    Args:
        foreground: Color de primer plano
        background: Color de fondo
        level: Nivel de cumplimiento

    Returns:
        tuple: (es_accesible, ratio, nivel_requerido)
    """
    ratio = AccessibilityGuide.check_contrast_ratio(foreground, background)
    is_accessible = AccessibilityGuide.is_accessible_contrast(
        foreground, background, level
    )
    required_ratio = AccessibilityGuide.CONTRAST_RATIOS.get(level, 4.5)

    return (is_accessible, ratio, required_ratio)


def get_accessible_colors() -> dict:
    """
    Obtiene una paleta de colores accesible.

    Returns:
        dict: Paleta de colores accesible
    """
    return {
        "text_primary": st.COLOR_TEXT,
        "text_secondary": st.COLOR_TEXT_DIM,
        "background_primary": st.COLOR_BG,
        "background_secondary": st.COLOR_CARD,
        "accent": st.COLOR_ACCENT,
        "success": st.COLOR_SUCCESS,
        "warning": st.COLOR_WARNING,
        "error": st.COLOR_ERROR,
        "info": st.COLOR_INFO
    }
