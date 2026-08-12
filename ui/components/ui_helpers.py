# ui/components/ui_helpers.py
"""
Utilidades de UI mejoradas para Narrivox Studio Pro.
Proporciona funciones auxiliares para animaciones, transiciones y efectos visuales.
"""

import threading
import time
from collections.abc import Callable

import customtkinter as ctk

from ui import styles as st


class UIHelpers:
    """
    Clase de utilidades para operaciones comunes de UI.
    """

    @staticmethod
    def create_separator(parent: ctk.CTk, orientation: str = "horizontal",
                        color: str | None = None) -> ctk.CTkFrame:
        """
        Crea un separador visual.

        Args:
            parent: Widget padre
            orientation: Orientación del separador (horizontal, vertical)
            color: Color del separador (opcional)

        Returns:
            ctk.CTkFrame: Frame separador
        """
        separator_color = color if color else st.COLOR_BORDER_SUBTLE

        if orientation == "horizontal":
            separator = ctk.CTkFrame(parent, height=1, fg_color=separator_color)
        else:
            separator = ctk.CTkFrame(parent, width=1, fg_color=separator_color)

        return separator

    @staticmethod
    def create_spacer(parent: ctk.CTk, height: int = 16, width: int = 16) -> ctk.CTkFrame:
        """
        Crea un espaciador invisible.

        Args:
            parent: Widget padre
            height: Alto del espaciador
            width: Ancho del espaciador

        Returns:
            ctk.CTkFrame: Frame espaciador
        """
        spacer = ctk.CTkFrame(parent, fg_color="transparent", height=height, width=width)
        return spacer

    @staticmethod
    def create_badge(parent: ctk.CTk, text: str, variant: str = "info",
                    size: str = "small") -> ctk.CTkLabel:
        """
        Crea una insignia (badge) con estilo.

        Args:
            parent: Widget padre
            text: Texto de la insignia
            variant: Variante de la insignia (info, success, warning, error)
            size: Tamaño de la insignia (small, medium)

        Returns:
            ctk.CTkLabel: Etiqueta de insignia
        """
        # Configurar colores según la variante
        variant_colors = {
            "info": (st.COLOR_INFO_LIGHT, st.COLOR_INFO),
            "success": (st.COLOR_SUCCESS_LIGHT, st.COLOR_SUCCESS),
            "warning": (st.COLOR_WARNING_LIGHT, st.COLOR_WARNING),
            "error": (st.COLOR_ERROR_LIGHT, st.COLOR_ERROR)
        }

        bg_color, text_color = variant_colors.get(variant, variant_colors["info"])

        # Configurar tamaño
        size_config = {
            "small": (st.FONT_BODY_TINY, 4),
            "medium": (st.FONT_BODY_SMALL, 6)
        }
        font, padding = size_config.get(size, size_config["small"])

        badge = ctk.CTkLabel(
            parent,
            text=text,
            font=font,
            fg_color=bg_color,
            text_color=text_color,
            corner_radius=st.RADIUS_FULL,
            padx=padding,
            pady=2
        )

        return badge

    @staticmethod
    def create_progress_ring(parent: ctk.CTk, size: int = 40,
                           progress: float = 0.0, color: str = None) -> ctk.CTkFrame:
        """
        Crea un anillo de progreso circular (simulado).

        Args:
            parent: Widget padre
            size: Tamaño del anillo
            progress: Progreso (0.0 a 1.0)
            color: Color del progreso

        Returns:
            ctk.CTkFrame: Frame del anillo de progreso
        """
        progress_color = color if color else st.COLOR_ACCENT

        # Crear contenedor circular
        ring = ctk.CTkFrame(
            parent,
            width=size,
            height=size,
            corner_radius=st.RADIUS_FULL,
            fg_color=st.COLOR_FG_BOX,
            border_width=2,
            border_color=progress_color
        )

        # Texto de porcentaje
        percent_text = ctk.CTkLabel(
            ring,
            text=f"{int(progress * 100)}%",
            font=st.FONT_BODY_SMALL,
            text_color=st.COLOR_TEXT
        )
        percent_text.place(relx=0.5, rely=0.5, anchor="center")

        return ring

    @staticmethod
    def create_empty_state(parent: ctk.CTk, icon: str, title: str,
                          description: str, action_text: str | None = None,
                          action_command: Callable | None = None) -> ctk.CTkFrame:
        """
        Crea un estado vacío con icono y mensaje.

        Args:
            parent: Widget padre
            icon: Icono a mostrar
            title: Título del mensaje
            description: Descripción del mensaje
            action_text: Texto del botón de acción (opcional)
            action_command: Función del botón de acción (opcional)

        Returns:
            ctk.CTkFrame: Frame del estado vacío
        """
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=st.SPACING_XL, pady=st.SPACING_XL)

        # Icono grande
        icon_label = ctk.CTkLabel(
            container,
            text=icon,
            font=(st.FONT_FAMILY, 64, "normal"),
            text_color=st.COLOR_TEXT_DIM
        )
        icon_label.pack(pady=(0, st.SPACING_LG))

        # Título
        title_label = ctk.CTkLabel(
            container,
            text=title,
            font=st.FONT_H3,
            text_color=st.COLOR_TEXT
        )
        title_label.pack(pady=(0, st.SPACING_SM))

        # Descripción
        desc_label = ctk.CTkLabel(
            container,
            text=description,
            font=st.FONT_BODY,
            text_color=st.COLOR_TEXT_DIM,
            wraplength=400
        )
        desc_label.pack(pady=(0, st.SPACING_LG))

        # Botón de acción si se proporciona
        if action_text and action_command:
            from ui.components.buttons import StyledButton

            action_btn = StyledButton(
                container,
                text=action_text,
                command=action_command,
                variant="primary"
            )
            action_btn.pack()

        return container


class HoverEffects:
    """
    Efectos de hover mejorados para componentes.
    """

    @staticmethod
    def add_hover_effect(widget: ctk.CTk,
                        normal_color: str,
                        hover_color: str,
                        text_color: str | None = None,
                        hover_text_color: str | None = None):
        """
        Añade efecto de hover a un widget.

        Args:
            widget: Widget al que añadir el efecto
            normal_color: Color normal
            hover_color: Color al pasar el mouse
            text_color: Color del texto normal (opcional)
            hover_text_color: Color del texto al pasar el mouse (opcional)
        """
        def on_enter(event):
            widget.configure(fg_color=hover_color)
            if hover_text_color and text_color:
                widget.configure(text_color=hover_text_color)

        def on_leave(event):
            widget.configure(fg_color=normal_color)
            if text_color:
                widget.configure(text_color=text_color)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    @staticmethod
    def add_scale_effect(widget: ctk.CTk, scale_factor: float = 1.05):
        """
        Añade efecto de escala al hover.

        Args:
            widget: Widget al que añadir el efecto
            scale_factor: Factor de escala
        """
        # Nota: CustomTkinter no soporta transformaciones de escala nativas
        # Esta es una implementación placeholder para futuras mejoras
        _ = scale_factor  # Mark as intentionally unused for future implementation


class AnimationUtils:
    """
    Utilidades para animaciones simples.
    """

    @staticmethod
    def fade_in(widget: ctk.CTk, duration: float = 0.3):
        """
        Animación de aparición gradual (fade in).

        Args:
            widget: Widget a animar
            duration: Duración de la animación en segundos
        """
        # Nota: CustomTkinter no soporta animaciones de opacidad nativas
        # Esta es una implementación placeholder para futuras mejoras
        widget.configure(fg_color=st.COLOR_CARD)

    @staticmethod
    def fade_out(widget: ctk.CTk, duration: float = 0.3,
                callback: Callable | None = None):
        """
        Animación de desaparición gradual (fade out).

        Args:
            widget: Widget a animar
            duration: Duración de la animación en segundos
            callback: Función a ejecutar al finalizar
        """
        # Nota: CustomTkinter no soporta animaciones de opacidad nativas
        # Esta es una implementación placeholder para futuras mejoras
        if callback:
            callback()

    @staticmethod
    def delayed_action(delay: float, action: Callable):
        """
        Ejecuta una acción después de un retraso.

        Args:
            delay: Retraso en segundos
            action: Función a ejecutar
        """
        def run_action():
            time.sleep(delay)
            action()

        thread = threading.Thread(target=run_action, daemon=True)
        thread.start()


class LoadingIndicator:
    """
    Indicador de carga animado.
    """

    def __init__(self, parent: ctk.CTk, size: int = 32,
                 color: str | None = None):
        """
        Crea un indicador de carga.

        Args:
            parent: Widget padre
            size: Tamaño del indicador
            color: Color del indicador
        """
        self.parent = parent
        self.size = size
        self.color = color if color else st.COLOR_ACCENT
        self.is_running = False
        self.animation_thread = None

        # Crear contenedor
        self.container = ctk.CTkFrame(
            parent,
            width=size,
            height=size,
            fg_color="transparent"
        )

        # Crear círculo de carga (simulado)
        self.circle = ctk.CTkLabel(
            self.container,
            text="⏳",
            font=(st.FONT_FAMILY, int(size * 0.8), "normal"),
            text_color=self.color
        )
        self.circle.place(relx=0.5, rely=0.5, anchor="center")

    def start(self):
        """Inicia la animación de carga."""
        if not self.is_running:
            self.is_running = True
            self._animate()

    def stop(self):
        """Detiene la animación de carga."""
        self.is_running = False

    def _animate(self):
        """Animación interna del indicador."""
        # Nota: Esta es una implementación simplificada
        # Para una animación real, se necesitaría un sistema más complejo
        pass

    def pack(self, **kwargs):
        """Empaqueta el indicador."""
        self.container.pack(**kwargs)

    def place(self, **kwargs):
        """Coloca el indicador."""
        self.container.place(**kwargs)

    def grid(self, **kwargs):
        """Coloca el indicador en grid."""
        self.container.grid(**kwargs)


class NotificationUtils:
    """
    Utilidades para notificaciones y mensajes.
    """

    @staticmethod
    def show_info_message(parent: ctk.CTk, title: str, message: str):
        """
        Muestra un mensaje informativo.

        Args:
            parent: Widget padre
            title: Título del mensaje
            message: Contenido del mensaje
        """
        from tkinter import messagebox
        messagebox.showinfo(title, message)

    @staticmethod
    def show_warning_message(parent: ctk.CTk, title: str, message: str):
        """
        Muestra un mensaje de advertencia.

        Args:
            parent: Widget padre
            title: Título del mensaje
            message: Contenido del mensaje
        """
        from tkinter import messagebox
        messagebox.showwarning(title, message)

    @staticmethod
    def show_error_message(parent: ctk.CTk, title: str, message: str):
        """
        Muestra un mensaje de error.

        Args:
            parent: Widget padre
            title: Título del mensaje
            message: Contenido del mensaje
        """
        from tkinter import messagebox
        messagebox.showerror(title, message)

    @staticmethod
    def ask_confirmation(parent: ctk.CTk, title: str, message: str) -> bool:
        """
        Pide confirmación al usuario.

        Args:
            parent: Widget padre
            title: Título del mensaje
            message: Contenido del mensaje

        Returns:
            bool: True si el usuario confirma
        """
        from tkinter import messagebox
        return messagebox.askyesno(title, message)
