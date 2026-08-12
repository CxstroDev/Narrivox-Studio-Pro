# ui/components/buttons.py
"""
Sistema de botones mejorado para Narrivox Studio Pro.
Proporciona botones consistentes con mejor diseño y UX.
"""

from collections.abc import Callable

import customtkinter as ctk

from ui import styles as st


class StyledButton(ctk.CTkButton):
    """
    Botón base con estilo mejorado y consistente.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        text: str,
        command: Callable | None = None,
        variant: str = "primary",
        size: str = "medium",
        icon: str | None = None,
        width: int | None = None,
        height: int | None = None,
        **kwargs
    ):
        """
        Crea un botón con estilo mejorado.

        Args:
            parent: Widget padre
            text: Texto del botón
            command: Función a ejecutar al hacer clic
            variant: Variante del botón (primary, secondary, success, warning, error, ghost)
            size: Tamaño del botón (small, medium, large)
            icon: Icono a mostrar (opcional)
            width: Ancho del botón (opcional)
            height: Alto del botón (opcional)
            **kwargs: Argumentos adicionales para CTkButton
        """
        self.variant = variant
        self.size = size
        self.icon = icon

        # Configurar colores según la variante
        colors = self._get_variant_colors()
        font = self._get_size_font()

        # Preparar texto con icono
        display_text = self._prepare_text()

        # Configurar dimensiones
        btn_width = width if width else self._get_default_width()
        btn_height = height if height else self._get_default_height()

        super().__init__(
            parent,
            text=display_text,
            font=font,
            width=btn_width,
            height=btn_height,
            fg_color=colors["fg"],
            hover_color=colors["hover"],
            text_color=colors["text"],
            corner_radius=st.RADIUS_MD,
            command=command,
            **kwargs
        )

    def _get_variant_colors(self) -> dict:
        """Obtiene los colores según la variante del botón."""
        variants = {
            "primary": {
                "fg": st.COLOR_ACCENT,
                "hover": st.COLOR_ACCENT_HOVER,
                "text": "#ffffff"
            },
            "secondary": {
                "fg": st.COLOR_FG_BOX,
                "hover": st.COLOR_BORDER,
                "text": st.COLOR_TEXT
            },
            "success": {
                "fg": st.COLOR_SUCCESS,
                "hover": st.COLOR_SUCCESS_HOVER,
                "text": "#ffffff"
            },
            "warning": {
                "fg": st.COLOR_WARNING,
                "hover": st.COLOR_WARNING_HOVER,
                "text": "#ffffff"
            },
            "error": {
                "fg": st.COLOR_ERROR,
                "hover": st.COLOR_ERROR_HOVER,
                "text": "#ffffff"
            },
            "ghost": {
                "fg": "transparent",
                "hover": st.COLOR_ACCENT_LIGHT,
                "text": st.COLOR_ACCENT
            },
            "info": {
                "fg": st.COLOR_INFO,
                "hover": st.COLOR_INFO_HOVER,
                "text": "#ffffff"
            }
        }
        return variants.get(self.variant, variants["primary"])

    def _get_size_font(self) -> tuple:
        """Obtiene la fuente según el tamaño del botón."""
        sizes = {
            "small": st.FONT_BUTTON_SMALL,
            "medium": st.FONT_BUTTON,
            "large": (st.FONT_FAMILY, 15, "bold")
        }
        return sizes.get(self.size, sizes["medium"])

    def _prepare_text(self) -> str:
        """Prepara el texto del botón con icono si se proporciona."""
        if self.icon:
            return f"{self.icon}  {self.text}"
        return self.text

    def _get_default_width(self) -> int:
        """Obtiene el ancho predeterminado según el tamaño."""
        sizes = {
            "small": 100,
            "medium": 140,
            "large": 180
        }
        return sizes.get(self.size, sizes["medium"])

    def _get_default_height(self) -> int:
        """Obtiene el alto predeterminado según el tamaño."""
        sizes = {
            "small": 32,
            "medium": 40,
            "large": 48
        }
        return sizes.get(self.size, sizes["medium"])


class IconButton(ctk.CTkButton):
    """
    Botón de icono con estilo mejorado.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        icon: str,
        command: Callable | None = None,
        size: int = 40,
        variant: str = "secondary",
        tooltip: str | None = None,
        **kwargs
    ):
        """
        Crea un botón de icono.

        Args:
            parent: Widget padre
            icon: Icono a mostrar
            command: Función a ejecutar al hacer clic
            size: Tamaño del botón (cuadrado)
            variant: Variante del botón
            tooltip: Texto de tooltip (opcional)
            **kwargs: Argumentos adicionales
        """
        self.variant = variant

        # Configurar colores
        colors = self._get_variant_colors()

        super().__init__(
            parent,
            text=icon,
            font=(st.FONT_FAMILY, int(size * 0.5), "normal"),
            width=size,
            height=size,
            fg_color=colors["fg"],
            hover_color=colors["hover"],
            text_color=colors["text"],
            corner_radius=st.RADIUS_MD,
            command=command,
            **kwargs
        )

        # Añadir tooltip si se proporciona
        if tooltip:
            from ui.components.tooltip import ToolTip
            ToolTip(self, tooltip)

    def _get_variant_colors(self) -> dict:
        """Obtiene los colores según la variante."""
        variants = {
            "primary": {
                "fg": st.COLOR_ACCENT,
                "hover": st.COLOR_ACCENT_HOVER,
                "text": "#ffffff"
            },
            "secondary": {
                "fg": st.COLOR_FG_BOX,
                "hover": st.COLOR_BORDER,
                "text": st.COLOR_TEXT
            },
            "ghost": {
                "fg": "transparent",
                "hover": st.COLOR_ACCENT_LIGHT,
                "text": st.COLOR_TEXT
            }
        }
        return variants.get(self.variant, variants["secondary"])


class ActionButton(ctk.CTkButton):
    """
    Botón de acción principal con diseño destacado.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        text: str,
        command: Callable | None = None,
        icon: str | None = None,
        **kwargs
    ):
        """
        Crea un botón de acción principal.

        Args:
            parent: Widget padre
            text: Texto del botón
            command: Función a ejecutar
            icon: Icono opcional
            **kwargs: Argumentos adicionales
        """
        display_text = f"{icon}  {text}" if icon else text

        super().__init__(
            parent,
            text=display_text,
            font=st.FONT_BUTTON,
            height=48,
            corner_radius=st.RADIUS_LG,
            fg_color=st.COLOR_ACCENT,
            hover_color=st.COLOR_ACCENT_HOVER,
            text_color="#ffffff",
            command=command,
            **kwargs
        )


class SecondaryButton(ctk.CTkButton):
    """
    Botón secundario con diseño más sutil.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        text: str,
        command: Callable | None = None,
        icon: str | None = None,
        **kwargs
    ):
        """
        Crea un botón secundario.

        Args:
            parent: Widget padre
            text: Texto del botón
            command: Función a ejecutar
            icon: Icono opcional
            **kwargs: Argumentos adicionales
        """
        display_text = f"{icon}  {text}" if icon else text

        super().__init__(
            parent,
            text=display_text,
            font=st.FONT_BUTTON,
            height=40,
            corner_radius=st.RADIUS_MD,
            fg_color=st.COLOR_FG_BOX,
            hover_color=st.COLOR_BORDER,
            text_color=st.COLOR_TEXT,
            command=command,
            **kwargs
        )


class DangerButton(ctk.CTkButton):
    """
    Botón de acción destructiva con diseño de advertencia.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        text: str,
        command: Callable | None = None,
        icon: str | None = None,
        **kwargs
    ):
        """
        Crea un botón de acción destructiva.

        Args:
            parent: Widget padre
            text: Texto del botón
            command: Función a ejecutar
            icon: Icono opcional
            **kwargs: Argumentos adicionales
        """
        display_text = f"{icon}  {text}" if icon else text

        super().__init__(
            parent,
            text=display_text,
            font=st.FONT_BUTTON,
            height=40,
            corner_radius=st.RADIUS_MD,
            fg_color=st.COLOR_ERROR,
            hover_color=st.COLOR_ERROR_HOVER,
            text_color="#ffffff",
            command=command,
            **kwargs
        )
