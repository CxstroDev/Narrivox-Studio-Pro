# ui/components/cards.py
"""
Sistema de tarjetas mejorado para Narrivox Studio Pro.
Proporciona tarjetas consistentes con mejor diseño y UX.
"""

from collections.abc import Callable

import customtkinter as ctk

from ui import styles as st


class BaseCard(ctk.CTkFrame):
    """
    Tarjeta base con estilo mejorado.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        title: str | None = None,
        icon: str | None = None,
        **kwargs
    ):
        """
        Crea una tarjeta base.

        Args:
            parent: Widget padre
            title: Título de la tarjeta (opcional)
            icon: Icono de la tarjeta (opcional)
            **kwargs: Argumentos adicionales
        """
        super().__init__(
            parent,
            fg_color=st.COLOR_CARD,
            corner_radius=st.RADIUS_XL,
            border_width=1,
            border_color=st.COLOR_BORDER_SUBTLE,
            **kwargs
        )

        self.title = title
        self.icon = icon

        # Configurar eventos de hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # Crear contenido si se proporciona título o icono
        if title or icon:
            self._create_header()

    def _create_header(self):
        """Crea la cabecera de la tarjeta."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))

        # Icono y título
        if self.icon and self.title:
            icon_label = ctk.CTkLabel(
                header,
                text=self.icon,
                font=(st.FONT_FAMILY, 18, "normal"),
                text_color=st.COLOR_ACCENT
            )
            icon_label.pack(side="left", padx=(0, 8))

            title_label = ctk.CTkLabel(
                header,
                text=self.title,
                font=st.FONT_H4,
                text_color=st.COLOR_TEXT
            )
            title_label.pack(side="left")

        elif self.icon:
            icon_label = ctk.CTkLabel(
                header,
                text=self.icon,
                font=(st.FONT_FAMILY, 18, "normal"),
                text_color=st.COLOR_ACCENT
            )
            icon_label.pack(side="left")

        elif self.title:
            title_label = ctk.CTkLabel(
                header,
                text=self.title,
                font=st.FONT_H4,
                text_color=st.COLOR_TEXT
            )
            title_label.pack(side="left")

        # Separador
        ctk.CTkFrame(self, height=1, fg_color=st.COLOR_BORDER_SUBTLE).pack(
            fill="x", padx=16, pady=(0, 12)
        )

    def _on_enter(self, event):
        """Maneja el evento cuando el mouse entra en la tarjeta."""
        self.configure(border_color=st.COLOR_ACCENT)

    def _on_leave(self, event):
        """Maneja el evento cuando el mouse sale de la tarjeta."""
        self.configure(border_color=st.COLOR_BORDER_SUBTLE)


class ContentCard(BaseCard):
    """
    Tarjeta de contenido con área de texto.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        title: str | None = None,
        icon: str | None = None,
        content: str = "",
        **kwargs
    ):
        """
        Crea una tarjeta de contenido.

        Args:
            parent: Widget padre
            title: Título de la tarjeta
            icon: Icono de la tarjeta
            content: Contenido de la tarjeta
            **kwargs: Argumentos adicionales
        """
        super().__init__(parent, title, icon, **kwargs)

        # Área de contenido
        self.content_label = ctk.CTkLabel(
            self,
            text=content,
            font=st.FONT_BODY,
            text_color=st.COLOR_TEXT,
            wraplength=300,
            justify="left"
        )
        self.content_label.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def set_content(self, content: str):
        """Establece el contenido de la tarjeta."""
        self.content_label.configure(text=content)

    def get_content(self) -> str:
        """Obtiene el contenido de la tarjeta."""
        return self.content_label.cget("text")


class ActionCard(BaseCard):
    """
    Tarjeta con botón de acción.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        title: str | None = None,
        icon: str | None = None,
        button_text: str = "Acción",
        button_command: Callable | None = None,
        **kwargs
    ):
        """
        Crea una tarjeta con botón de acción.

        Args:
            parent: Widget padre
            title: Título de la tarjeta
            icon: Icono de la tarjeta
            button_text: Texto del botón
            button_command: Función del botón
            **kwargs: Argumentos adicionales
        """
        super().__init__(parent, title, icon, **kwargs)

        # Botón de acción
        from ui.components.buttons import StyledButton

        self.action_button = StyledButton(
            self,
            text=button_text,
            command=button_command,
            variant="primary"
        )
        self.action_button.pack(fill="x", padx=16, pady=(0, 16))


class StatusCard(BaseCard):
    """
    Tarjeta con indicador de estado.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        title: str | None = None,
        icon: str | None = None,
        status: str = "info",
        status_text: str = "",
        **kwargs
    ):
        """
        Crea una tarjeta con indicador de estado.

        Args:
            parent: Widget padre
            title: Título de la tarjeta
            icon: Icono de la tarjeta
            status: Tipo de estado (info, success, warning, error)
            status_text: Texto del estado
            **kwargs: Argumentos adicionales
        """
        super().__init__(parent, title, icon, **kwargs)

        self.status = status
        self.status_text = status_text

        # Configurar colores según el estado
        status_colors = {
            "info": st.COLOR_INFO,
            "success": st.COLOR_SUCCESS,
            "warning": st.COLOR_WARNING,
            "error": st.COLOR_ERROR
        }
        status_color = status_colors.get(status, st.COLOR_INFO)

        # Indicador de estado
        status_container = ctk.CTkFrame(self, fg_color="transparent")
        status_container.pack(fill="x", padx=16, pady=(0, 16))

        status_icon = ctk.CTkLabel(
            status_container,
            text=self._get_status_icon(),
            font=(st.FONT_FAMILY, 16, "normal"),
            text_color=status_color
        )
        status_icon.pack(side="left", padx=(0, 8))

        status_label = ctk.CTkLabel(
            status_container,
            text=status_text,
            font=st.FONT_BODY_SMALL,
            text_color=status_color
        )
        status_label.pack(side="left")

    def _get_status_icon(self) -> str:
        """Obtiene el icono según el estado."""
        icons = {
            "info": st.ICONS["INFO"],
            "success": st.ICONS["SUCCESS"],
            "warning": st.ICONS["WARNING"],
            "error": st.ICONS["ERROR"]
        }
        return icons.get(self.status, st.ICONS["INFO"])

    def set_status(self, status: str, status_text: str):
        """Actualiza el estado de la tarjeta."""
        self.status = status
        self.status_text = status_text

        # Actualizar colores
        status_colors = {
            "info": st.COLOR_INFO,
            "success": st.COLOR_SUCCESS,
            "warning": st.COLOR_WARNING,
            "error": st.COLOR_ERROR
        }
        status_color = status_colors.get(status, st.COLOR_INFO)

        # Actualizar UI (necesitaría referencias a los widgets)
        # Por simplicidad, esto requeriría una implementación más compleja


class StatCard(BaseCard):
    """
    Tarjeta de estadísticas con número destacado.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        title: str,
        value: str,
        icon: str | None = None,
        trend: str | None = None,
        **kwargs
    ):
        """
        Crea una tarjeta de estadísticas.

        Args:
            parent: Widget padre
            title: Título de la estadística
            value: Valor de la estadística
            icon: Icono de la tarjeta
            trend: Tendencia (up, down, none)
            **kwargs: Argumentos adicionales
        """
        super().__init__(parent, title, icon, **kwargs)

        # Valor principal
        value_label = ctk.CTkLabel(
            self,
            text=value,
            font=st.FONT_H1,
            text_color=st.COLOR_TEXT
        )
        value_label.pack(pady=(8, 4))

        # Tendencia si se proporciona
        if trend:
            trend_colors = {
                "up": st.COLOR_SUCCESS,
                "down": st.COLOR_ERROR,
                "none": st.COLOR_TEXT_DIM
            }
            trend_icons = {
                "up": "↑",
                "down": "↓",
                "none": "→"
            }

            trend_color = trend_colors.get(trend, st.COLOR_TEXT_DIM)
            trend_icon = trend_icons.get(trend, "")

            trend_label = ctk.CTkLabel(
                self,
                text=f"{trend_icon} Sin cambios recientes",
                font=st.FONT_BODY_SMALL,
                text_color=trend_color
            )
            trend_label.pack(pady=(0, 16))

    def set_value(self, value: str):
        """Actualiza el valor de la estadística."""
        # Necesitaría referencia al widget del valor
        pass
