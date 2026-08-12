# ui/components/model_card.py
from tkinter import messagebox

import customtkinter as ctk

from ui import styles as st
from ui.components.tooltip import ToolTip


class ModelCard(ctk.CTkFrame):
    """
    Tarjeta mejorada para mostrar un modelo de IA local.
    Puede representar un modelo instalado, en descarga o del catálogo.
    """

    def __init__(
        self,
        parent,
        model_data: dict,
        category: str,
        is_installed: bool = False,
        is_active: bool = False,
        on_download=None,
        on_delete=None,
        on_set_active=None,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=st.COLOR_CARD,
            corner_radius=st.RADIUS_XL,
            border_width=1,
            border_color=st.COLOR_BORDER_SUBTLE,
            **kwargs
        )

        self.model_data = model_data
        self.category = category
        self.is_installed = is_installed
        self.is_active = is_active
        self.on_download = on_download
        self.on_delete = on_delete
        self.on_set_active = on_set_active
        self.downloading = False

        # Configurar eventos de hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        self.grid_columnconfigure(0, weight=1)

        # --- Cabecera: nombre y estado ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        # Nombre del modelo
        name_text = model_data.get("name", model_data["id"])
        auth_text = f" {st.ICONS['LOCK']}" if model_data.get("requires_auth") else ""

        name_label = ctk.CTkLabel(
            header,
            text=f"{name_text}{auth_text}",
            font=st.FONT_H4,
            text_color=st.COLOR_TEXT
        )
        name_label.pack(side="left")

        # Estado del modelo
        self.status_label = ctk.CTkLabel(
            header,
            text="",
            font=st.FONT_BODY_SMALL
        )
        self.status_label.pack(side="right")

        # --- Detalles (tamaño, descripción) ---
        size_gb = model_data.get("size_gb", 0)
        size_text = f"{size_gb:.1f} GB" if size_gb else "Tamaño desconocido"
        description = model_data.get("description", "")

        details = f"{size_text}\n{description}"
        self.details_label = ctk.CTkLabel(
            self,
            text=details,
            font=st.FONT_BODY_SMALL,
            text_color=st.COLOR_TEXT_DIM,
            justify="left",
            wraplength=400
        )
        self.details_label.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        # --- Barra de progreso (oculta inicialmente) ---
        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=8,
            corner_radius=st.RADIUS_SM
        )
        self.progress_bar.grid(row=2, column=0, padx=16, pady=(0, 4), sticky="ew")
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=st.FONT_BODY_TINY,
            text_color=st.COLOR_TEXT_DIM
        )
        self.progress_label.grid(row=3, column=0, padx=16, pady=(0, 8), sticky="w")
        self.progress_label.grid_remove()

        # --- Botones de acción ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=16, pady=(8, 16), sticky="ew")

        self.primary_btn = ctk.CTkButton(
            btn_frame,
            text="",
            height=36,
            corner_radius=st.RADIUS_MD,
            font=st.FONT_BUTTON_SMALL,
            command=self._on_primary_action
        )
        self.primary_btn.pack(side="right", padx=4)
        ToolTip(self.primary_btn, "Acción principal: descargar, activar o cancelar.")

        self.secondary_btn = ctk.CTkButton(
            btn_frame,
            text="",
            height=36,
            corner_radius=st.RADIUS_MD,
            font=st.FONT_BUTTON_SMALL,
            command=self._on_secondary_action
        )
        self.secondary_btn.pack(side="right", padx=4)
        ToolTip(self.secondary_btn, "Eliminar modelo del disco.")

        self._update_ui()

    def _on_enter(self, event):
        """Maneja el evento cuando el mouse entra en la tarjeta."""
        if not self.is_active:
            self.configure(border_color=st.COLOR_ACCENT)

    def _on_leave(self, event):
        """Maneja el evento cuando el mouse sale de la tarjeta."""
        if not self.is_active:
            self.configure(border_color=st.COLOR_BORDER_SUBTLE)

    def _update_ui(self):
        """Actualiza la UI según el estado actual."""
        if self.downloading:
            # Estado descargando
            self.status_label.configure(
                text=f"{st.ICONS['MODEL_DOWNLOADING']} Descargando...",
                text_color=st.COLOR_WARNING
            )
            self.primary_btn.configure(
                text="Cancelar",
                fg_color=st.COLOR_ERROR,
                hover_color=st.COLOR_ERROR_HOVER,
                text_color="#ffffff",
                state="normal"
            )
            self.secondary_btn.pack_forget()
            self.progress_bar.grid()
            self.progress_label.grid()

        elif self.is_installed:
            if self.is_active:
                # Estado activo
                self.status_label.configure(
                    text=f"{st.ICONS['MODEL_ACTIVE']} Activo",
                    text_color=st.COLOR_SUCCESS
                )
                self.primary_btn.configure(
                    text=f"{st.ICONS['STAR']} Activo",
                    fg_color=st.COLOR_SUCCESS,
                    hover_color=st.COLOR_SUCCESS_HOVER,
                    text_color="#ffffff",
                    state="disabled"
                )
                self.configure(border_color=st.COLOR_SUCCESS)
            else:
                # Estado instalado
                self.status_label.configure(
                    text=f"{st.ICONS['MODEL_INSTALLED']} Instalado",
                    text_color=st.COLOR_SUCCESS
                )
                self.primary_btn.configure(
                    text="Usar como activo",
                    fg_color=st.COLOR_ACCENT,
                    hover_color=st.COLOR_ACCENT_HOVER,
                    text_color="#ffffff",
                    state="normal"
                )

            self.secondary_btn.configure(
                text=f"{st.ICONS['DELETE']} Eliminar",
                fg_color=st.COLOR_ERROR,
                hover_color=st.COLOR_ERROR_HOVER,
                text_color="#ffffff",
                state="normal"
            )
            self.secondary_btn.pack(side="right", padx=4)
            self.progress_bar.grid_remove()
            self.progress_label.grid_remove()

        else:
            # Estado no instalado
            self.status_label.configure(
                text=f"{st.ICONS['MODEL_AVAILABLE']} Disponible",
                text_color=st.COLOR_TEXT_DIM
            )
            self.primary_btn.configure(
                text=f"{st.ICONS['DOWNLOAD']} Descargar",
                fg_color=st.COLOR_ACCENT,
                hover_color=st.COLOR_ACCENT_HOVER,
                text_color="#ffffff",
                state="normal"
            )
            self.secondary_btn.pack_forget()
            self.progress_bar.grid_remove()
            self.progress_label.grid_remove()

    def _on_primary_action(self):
        """Maneja la acción principal del botón."""
        if self.downloading:
            # Cancelar descarga
            if self.on_download:
                self.on_download(self.model_data["id"], cancel=True)
        elif self.is_installed and not self.is_active:
            # Establecer como activo
            if self.on_set_active:
                self.on_set_active(self.model_data["id"])
        elif not self.is_installed:
            # Iniciar descarga
            if self.on_download:
                self.on_download(self.model_data["id"])

    def _on_secondary_action(self):
        """Maneja la acción secundaria del botón."""
        if self.is_installed:
            # Eliminar modelo
            if messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Seguro que deseas eliminar el modelo '{self.model_data['name']}'?\n"
                "Esta acción no se puede deshacer."
            ):
                if self.on_delete:
                    self.on_delete(self.model_data["id"])

    def set_download_progress(self, percent: float, message: str):
        """Actualiza la barra de progreso durante la descarga."""
        self.downloading = True
        self._update_ui()
        self.progress_bar.set(percent)
        self.progress_label.configure(text=f"{message} ({percent*100:.0f}%)")

    def set_download_complete(self, success: bool):
        """Finaliza el estado de descarga."""
        self.downloading = False
        if success:
            self.is_installed = True
        self._update_ui()

    def set_active(self, active: bool):
        """Cambia el estado activo de la tarjeta."""
        self.is_active = active
        self._update_ui()
