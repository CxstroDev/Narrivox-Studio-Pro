# ui/components/inputs.py
"""
Sistema de campos de entrada mejorado para Narrivox Studio Pro.
Proporciona inputs consistentes con mejor diseño y UX.
"""

from collections.abc import Callable

import customtkinter as ctk

from ui import styles as st


class StyledEntry(ctk.CTkEntry):
    """
    Campo de texto con estilo mejorado.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        placeholder: str = "",
        width: int | None = None,
        height: int | None = None,
        **kwargs
    ):
        """
        Crea un campo de texto con estilo mejorado.

        Args:
            parent: Widget padre
            placeholder: Texto de placeholder
            width: Ancho del campo
            height: Alto del campo
            **kwargs: Argumentos adicionales para CTkEntry
        """
        default_width = width if width else 240
        default_height = height if height else 40

        super().__init__(
            parent,
            placeholder_text=placeholder,
            width=default_width,
            height=default_height,
            corner_radius=st.RADIUS_MD,
            border_width=1,
            border_color=st.COLOR_BORDER,
            fg_color=st.COLOR_FG_BOX,
            placeholder_text_color=st.COLOR_TEXT_DIM,
            text_color=st.COLOR_TEXT,
            font=st.FONT_BODY,
            **kwargs
        )


class StyledTextarea(ctk.CTkTextbox):
    """
    Área de texto con estilo mejorado.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        width: int | None = None,
        height: int | None = None,
        placeholder: str = "",
        **kwargs
    ):
        """
        Crea un área de texto con estilo mejorado.

        Args:
            parent: Widget padre
            width: Ancho del área
            height: Alto del área
            placeholder: Texto de placeholder
            **kwargs: Argumentos adicionales para CTkTextbox
        """
        default_width = width if width else 300
        default_height = height if height else 120

        super().__init__(
            parent,
            width=default_width,
            height=default_height,
            corner_radius=st.RADIUS_MD,
            border_width=1,
            border_color=st.COLOR_BORDER,
            fg_color=st.COLOR_FG_BOX,
            text_color=st.COLOR_TEXT,
            font=st.FONT_BODY,
            **kwargs
        )

        # Insertar placeholder si se proporciona
        if placeholder:
            self.insert("0.0", placeholder)
            self.configure(text_color=st.COLOR_TEXT_DIM)


class StyledComboBox(ctk.CTkComboBox):
    """
    ComboBox con estilo mejorado.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        values: list[str] | None = None,
        width: int | None = None,
        height: int | None = None,
        **kwargs
    ):
        """
        Crea un ComboBox con estilo mejorado.

        Args:
            parent: Widget padre
            values: Lista de valores
            width: Ancho del ComboBox
            height: Alto del ComboBox
            **kwargs: Argumentos adicionales para CTkComboBox
        """
        default_width = width if width else 240
        default_height = height if height else 40

        super().__init__(
            parent,
            values=values if values else [],
            width=default_width,
            height=default_height,
            corner_radius=st.RADIUS_MD,
            border_width=1,
            border_color=st.COLOR_BORDER,
            fg_color=st.COLOR_FG_BOX,
            button_color=st.COLOR_BORDER,
            button_hover_color=st.COLOR_ACCENT,
            dropdown_fg_color=st.COLOR_CARD,
            dropdown_hover_color=st.COLOR_ACCENT_LIGHT,
            dropdown_text_color=st.COLOR_TEXT,
            text_color=st.COLOR_TEXT,
            font=st.FONT_BODY,
            **kwargs
        )


class SearchBox(ctk.CTkFrame):
    """
    Campo de búsqueda con diseño mejorado.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        placeholder: str = "Buscar...",
        width: int | None = None,
        height: int | None = None,
        on_search: Callable | None = None,
        **kwargs
    ):
        """
        Crea un campo de búsqueda.

        Args:
            parent: Widget padre
            placeholder: Texto de placeholder
            width: Ancho del campo
            height: Alto del campo
            on_search: Función a ejecutar al buscar
            **kwargs: Argumentos adicionales
        """
        default_width = width if width else 300
        default_height = height if height else 40

        super().__init__(
            parent,
            width=default_width,
            height=default_height,
            corner_radius=st.RADIUS_MD,
            fg_color=st.COLOR_FG_BOX,
            border_width=1,
            border_color=st.COLOR_BORDER,
            **kwargs
        )

        # Icono de búsqueda
        self.search_icon = ctk.CTkLabel(
            self,
            text=st.ICONS["SEARCH"],
            font=(st.FONT_FAMILY, 16, "normal"),
            text_color=st.COLOR_TEXT_DIM
        )
        self.search_icon.pack(side="left", padx=(12, 8))

        # Campo de entrada
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            fg_color="transparent",
            border_width=0,
            height=default_height - 2,
            text_color=st.COLOR_TEXT,
            placeholder_text_color=st.COLOR_TEXT_DIM,
            font=st.FONT_BODY
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Configurar evento de búsqueda
        if on_search:
            self.entry.bind("<Return>", lambda e: on_search(self.entry.get()))
            self.entry.bind("<KeyRelease>", lambda e: self._on_key_release(on_search))

    def _on_key_release(self, on_search: Callable):
        """Maneja el evento de liberación de tecla."""
        # Implementar búsqueda en tiempo real si es necesario
        pass

    def get_text(self) -> str:
        """Obtiene el texto del campo de búsqueda."""
        return self.entry.get()

    def set_text(self, text: str):
        """Establece el texto del campo de búsqueda."""
        self.entry.delete(0, "end")
        self.entry.insert(0, text)

    def clear(self):
        """Limpia el campo de búsqueda."""
        self.entry.delete(0, "end")


class LabeledInput(ctk.CTkFrame):
    """
    Contenedor con etiqueta y campo de entrada.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        label: str,
        input_type: str = "entry",
        placeholder: str = "",
        width: int | None = None,
        **kwargs
    ):
        """
        Crea un contenedor con etiqueta y campo de entrada.

        Args:
            parent: Widget padre
            label: Texto de la etiqueta
            input_type: Tipo de entrada (entry, textarea, combobox)
            placeholder: Texto de placeholder
            width: Ancho del contenedor
            **kwargs: Argumentos adicionales
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.input_type = input_type
        default_width = width if width else 240

        # Etiqueta
        self.label_widget = ctk.CTkLabel(
            self,
            text=label,
            font=st.FONT_LABEL_SMALL,
            text_color=st.COLOR_TEXT
        )
        self.label_widget.pack(anchor="w", pady=(0, st.SPACING_XS))

        # Campo de entrada según el tipo
        if input_type == "entry":
            self.input_widget = StyledEntry(self, placeholder=placeholder, width=default_width)
        elif input_type == "textarea":
            self.input_widget = StyledTextarea(self, placeholder=placeholder, width=default_width)
        elif input_type == "combobox":
            self.input_widget = StyledComboBox(self, width=default_width)
        else:
            self.input_widget = StyledEntry(self, placeholder=placeholder, width=default_width)

        self.input_widget.pack(fill="x")

    def get_value(self) -> str:
        """Obtiene el valor del campo de entrada."""
        if self.input_type == "textarea":
            return self.input_widget.get("0.0", "end").strip()
        elif self.input_type == "combobox":
            return self.input_widget.get()
        else:
            return self.input_widget.get()

    def set_value(self, value: str):
        """Establece el valor del campo de entrada."""
        if self.input_type == "textarea":
            self.input_widget.delete("0.0", "end")
            self.input_widget.insert("0.0", value)
        elif self.input_type == "combobox":
            self.input_widget.set(value)
        else:
            self.input_widget.delete(0, "end")
            self.input_widget.insert(0, value)

    def get_input_widget(self):
        """Obtiene el widget de entrada."""
        return self.input_widget
