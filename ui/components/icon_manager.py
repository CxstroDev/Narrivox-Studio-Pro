# ui/components/icon_manager.py
"""
Sistema de iconos mejorado para Narrivox Studio Pro.
Proporciona una interfaz consistente para manejar iconos Unicode
y prepara el camino para futuros iconos SVG.
"""


import customtkinter as ctk

from ui import styles as st


class IconManager:
    """
    Gestor de iconos que proporciona acceso consistente a los iconos
    y maneja el renderizado con mejor calidad visual.
    """

    def __init__(self):
        self._icon_cache: dict[str, ctk.CTkLabel] = {}
        self._icon_registry = st.ICONS

    def get_icon(self, icon_name: str, size: int = 20,
                 color: str | None = None, parent: ctk.CTk | None = None) -> str:
        """
        Obtiene un icono por su nombre.

        Args:
            icon_name: Nombre del icono (debe existir en st.ICONS)
            size: Tamaño del icono en píxeles
            color: Color del icono (opcional, usa el color del texto por defecto)
            parent: Widget padre (opcional)

        Returns:
            str: El carácter Unicode del icono
        """
        if icon_name not in self._icon_registry:
            # Fallback a un icono genérico si no existe
            return self._icon_registry.get("INFO", "ℹ️")

        return self._icon_registry[icon_name]

    def create_icon_label(self, parent: ctk.CTk, icon_name: str,
                         size: int = 20, color: str | None = None,
                         **kwargs) -> ctk.CTkLabel:
        """
        Crea una etiqueta con un icono.

        Args:
            parent: Widget padre
            icon_name: Nombre del icono
            size: Tamaño del icono
            color: Color del icono (opcional)
            **kwargs: Argumentos adicionales para CTkLabel

        Returns:
            ctk.CTkLabel: Etiqueta con el icono
        """
        icon_char = self.get_icon(icon_name)

        # Configurar fuente con tamaño específico para el icono
        font_config = (st.FONT_FAMILY, size, "normal")

        # Configurar color
        text_color = color if color else st.COLOR_TEXT

        label = ctk.CTkLabel(
            parent,
            text=icon_char,
            font=font_config,
            text_color=text_color,
            **kwargs
        )

        return label

    def create_icon_button(self, parent: ctk.CTk, icon_name: str,
                           command: callable | None = None,
                           size: int = 20, width: int = 40, height: int = 40,
                           fg_color: str | None = None,
                           hover_color: str | None = None,
                           text_color: str | None = None,
                           tooltip: str | None = None,
                           **kwargs) -> ctk.CTkButton:
        """
        Crea un botón con un icono.

        Args:
            parent: Widget padre
            icon_name: Nombre del icono
            command: Función a ejecutar al hacer clic
            size: Tamaño del icono
            width: Ancho del botón
            height: Alto del botón
            fg_color: Color de fondo
            hover_color: Color al pasar el mouse
            text_color: Color del texto/icono
            tooltip: Texto de tooltip (opcional)
            **kwargs: Argumentos adicionales para CTkButton

        Returns:
            ctk.CTkButton: Botón con el icono
        """
        icon_char = self.get_icon(icon_name)

        # Configurar colores
        button_fg_color = fg_color if fg_color else "transparent"
        button_hover_color = hover_color if hover_color else st.COLOR_ACCENT_LIGHT
        button_text_color = text_color if text_color else st.COLOR_TEXT

        # Configurar fuente
        font_config = (st.FONT_FAMILY, size, "normal")

        button = ctk.CTkButton(
            parent,
            text=icon_char,
            font=font_config,
            width=width,
            height=height,
            fg_color=button_fg_color,
            hover_color=button_hover_color,
            text_color=button_text_color,
            command=command,
            **kwargs
        )

        # Añadir tooltip si se proporciona
        if tooltip:
            from ui.components.tooltip import ToolTip
            ToolTip(button, tooltip)

        return button

    def get_icon_with_text(self, icon_name: str, text: str,
                          separator: str = " ") -> str:
        """
        Combina un icono con texto.

        Args:
            icon_name: Nombre del icono
            text: Texto a combinar
            separator: Separador entre icono y texto

        Returns:
            str: Icono combinado con texto
        """
        icon_char = self.get_icon(icon_name)
        return f"{icon_char}{separator}{text}"

    def register_custom_icon(self, name: str, icon_char: str):
        """
        Registra un icono personalizado.

        Args:
            name: Nombre del icono
            icon_char: Carácter Unicode del icono
        """
        self._icon_registry[name] = icon_char

    def is_icon_available(self, icon_name: str) -> bool:
        """
        Verifica si un icono está disponible.

        Args:
            icon_name: Nombre del icono

        Returns:
            bool: True si el icono está disponible
        """
        return icon_name in self._icon_registry

    def get_all_icons(self) -> dict[str, str]:
        """
        Obtiene todos los iconos disponibles.

        Returns:
            Dict[str, str]: Diccionario con todos los iconos
        """
        return self._icon_registry.copy()


# Instancia global del gestor de iconos
icon_manager = IconManager()


def get_icon(icon_name: str, size: int = 20,
             color: str | None = None) -> str:
    """
    Función de conveniencia para obtener un icono.

    Args:
        icon_name: Nombre del icono
        size: Tamaño del icono
        color: Color del icono

    Returns:
        str: Carácter Unicode del icono
    """
    return icon_manager.get_icon(icon_name, size, color)


def create_icon_label(parent: ctk.CTk, icon_name: str,
                      size: int = 20, color: str | None = None,
                      **kwargs) -> ctk.CTkLabel:
    """
    Función de conveniencia para crear una etiqueta con icono.

    Args:
        parent: Widget padre
        icon_name: Nombre del icono
        size: Tamaño del icono
        color: Color del icono
        **kwargs: Argumentos adicionales

    Returns:
        ctk.CTkLabel: Etiqueta con el icono
    """
    return icon_manager.create_icon_label(parent, icon_name, size, color, **kwargs)


def create_icon_button(parent: ctk.CTk, icon_name: str,
                      command: callable | None = None,
                      size: int = 20, width: int = 40, height: int = 40,
                      fg_color: str | None = None,
                      hover_color: str | None = None,
                      text_color: str | None = None,
                      tooltip: str | None = None,
                      **kwargs) -> ctk.CTkButton:
    """
    Función de conveniencia para crear un botón con icono.

    Args:
        parent: Widget padre
        icon_name: Nombre del icono
        command: Función a ejecutar
        size: Tamaño del icono
        width: Ancho del botón
        height: Alto del botón
        fg_color: Color de fondo
        hover_color: Color al pasar el mouse
        text_color: Color del texto
        tooltip: Texto de tooltip
        **kwargs: Argumentos adicionales

    Returns:
        ctk.CTkButton: Botón con el icono
    """
    return icon_manager.create_icon_button(
        parent, icon_name, command, size, width, height,
        fg_color, hover_color, text_color, tooltip, **kwargs
    )
