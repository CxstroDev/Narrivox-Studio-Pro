# ui/components/concept_card.py
import customtkinter as ctk

from ui import styles as st


class ConceptCard(ctk.CTkFrame):
    """Tarjeta de concepto mejorada con mejor diseño y UX."""

    def __init__(self, parent, title, icon, value_text, color):
        super().__init__(
            parent,
            fg_color=st.COLOR_CARD,
            corner_radius=st.RADIUS_XL,
            border_width=2,
            border_color=st.COLOR_BORDER_SUBTLE
        )
        self.is_locked = False
        self.default_border_color = st.COLOR_BORDER_SUBTLE
        self.locked_border_color = color
        self.hover_border_color = st.COLOR_ACCENT

        # Configurar eventos de hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # Contenedor principal
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Cabecera con título e icono
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        # Icono y título
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        icon_label = ctk.CTkLabel(
            title_frame,
            text=icon,
            font=(st.FONT_FAMILY, 18, "normal"),
            text_color=color
        )
        icon_label.pack(side="left", padx=(0, 8))

        self.lbl_title = ctk.CTkLabel(
            title_frame,
            text=title,
            font=st.FONT_LABEL,
            text_color=color
        )
        self.lbl_title.pack(side="left")

        # Indicador de estado
        self.status_indicator = ctk.CTkLabel(
            header,
            text=st.ICONS["UNLOCK"],
            font=(st.FONT_FAMILY, 14, "normal"),
            text_color=st.COLOR_TEXT_DIM
        )
        self.status_indicator.pack(side="right")

        # Separador
        ctk.CTkFrame(container, height=1, fg_color=st.COLOR_BORDER_SUBTLE).pack(
            fill="x", pady=(0, 12)
        )

        # Valor principal
        value_container = ctk.CTkFrame(container, fg_color="transparent")
        value_container.pack(fill="both", expand=True, pady=(0, 12))

        self.lbl_value = ctk.CTkLabel(
            value_container,
            text=value_text,
            font=st.FONT_H4,
            wraplength=200,
            text_color=st.COLOR_TEXT,
            justify="center"
        )
        self.lbl_value.pack(expand=True)

        # Botón de bloqueo mejorado
        self.btn_lock = ctk.CTkButton(
            self,
            text=f"{st.ICONS['UNLOCK']}  Desbloquear",
            height=36,
            corner_radius=st.RADIUS_MD,
            fg_color=st.COLOR_FG_BOX,
            hover_color=st.COLOR_BORDER,
            text_color=st.COLOR_TEXT,
            font=st.FONT_BUTTON_SMALL,
            command=self.toggle_lock
        )
        self.btn_lock.pack(side="bottom", fill="x", padx=16, pady=(0, 16))

    def _on_enter(self, event):
        """Maneja el evento cuando el mouse entra en la tarjeta."""
        if not self.is_locked:
            self.configure(border_color=self.hover_border_color)

    def _on_leave(self, event):
        """Maneja el evento cuando el mouse sale de la tarjeta."""
        if not self.is_locked:
            self.configure(border_color=self.default_border_color)

    def toggle_lock(self):
        """Alterna el estado de bloqueo de la tarjeta."""
        self.is_locked = not self.is_locked

        if self.is_locked:
            # Estado bloqueado
            self.btn_lock.configure(
                text=f"{st.ICONS['LOCK']}  Bloqueado",
                fg_color=st.COLOR_ACCENT,
                hover_color=st.COLOR_ACCENT_HOVER,
                text_color="#ffffff"
            )
            self.status_indicator.configure(
                text=st.ICONS["LOCK"],
                text_color=st.COLOR_ACCENT
            )
            self.configure(border_color=self.locked_border_color)
        else:
            # Estado desbloqueado
            self.btn_lock.configure(
                text=f"{st.ICONS['UNLOCK']}  Desbloquear",
                fg_color=st.COLOR_FG_BOX,
                hover_color=st.COLOR_BORDER,
                text_color=st.COLOR_TEXT
            )
            self.status_indicator.configure(
                text=st.ICONS["UNLOCK"],
                text_color=st.COLOR_TEXT_DIM
            )
            self.configure(border_color=self.default_border_color)

    def update_value(self, new_value):
        """Actualiza el valor de la tarjeta si no está bloqueada."""
        if not self.is_locked:
            self.lbl_value.configure(text=new_value)

    def get_value(self):
        """Obtiene el valor actual de la tarjeta."""
        return self.lbl_value.cget("text")
