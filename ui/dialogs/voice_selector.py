# ui/dialogs/voice_selector.py
import logging
from tkinter import messagebox

import customtkinter as ctk
from src.voice_manager import VoiceManager

from ui import styles as st

logger = logging.getLogger("Narrivox")

class VoiceSelectorDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_voice, current_provider, on_select):
        super().__init__(parent)
        self.title("Seleccionar Narrador")
        self.geometry("550x700")
        self.configure(fg_color=st.COLOR_BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.voice_manager = VoiceManager()
        self.current_voice = current_voice
        self.current_provider = current_provider
        self.on_select_callback = on_select

        # Variable para voz seleccionada actualmente
        self.selected_voice_id = current_voice
        self.selected_provider_code = current_provider

        # Título
        ctk.CTkLabel(self, text="🎤 SELECCIONAR VOZ", font=st.FONT_SUBTITLE,
                     text_color=st.COLOR_ACCENT).pack(pady=(15, 5))

        # Filtro por proveedor
        provider_frame = ctk.CTkFrame(self, fg_color="transparent")
        provider_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(provider_frame, text="Proveedor:", width=80).pack(side="left")

        providers = self.voice_manager.get_providers()
        provider_names = [self.voice_manager.get_provider_name(p) for p in providers]
        self.provider_var = ctk.StringVar(value=self.voice_manager.get_provider_name(current_provider))
        self.provider_menu = ctk.CTkOptionMenu(
            provider_frame,
            values=provider_names,
            variable=self.provider_var,
            command=self.on_provider_changed
        )
        self.provider_menu.pack(side="left", padx=10, fill="x", expand=True)

        # Mapeo nombre -> código de proveedor
        self.provider_map = {self.voice_manager.get_provider_name(p): p for p in providers}

        # Filtro por idioma
        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(lang_frame, text="Idioma:", width=80).pack(side="left")

        self.lang_var = ctk.StringVar(value="Todos")
        self.lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            values=["Todos"],
            variable=self.lang_var,
            command=self.on_language_changed
        )
        self.lang_menu.pack(side="left", padx=10, fill="x", expand=True)

        # Campo de búsqueda
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self, placeholder_text="🔍 Buscar voz...",
                                         textvariable=self.search_var, width=350)
        self.search_entry.pack(pady=10, padx=20)
        self.search_var.trace("w", lambda *args: self.filter_voices())

        # Frame scrolleable para las voces
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=st.COLOR_FG_BOX,
                                                   corner_radius=15, height=350)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Etiqueta para mostrar voz seleccionada actualmente
        self.selected_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 11),
                                           text_color=st.COLOR_SUCCESS)
        self.selected_label.pack(pady=5)

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(btn_frame, text="Cancelar", width=120, fg_color="#d9534f",
                      command=self.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Seleccionar", width=120, fg_color=st.COLOR_SUCCESS,
                      command=self.select_current).pack(side="right", padx=5)

        # Cargar datos iniciales
        self.update_language_list()
        self.filter_voices()
        self.update_selected_label()
        self.after(100, self.search_entry.focus)

    def get_current_provider_code(self):
        provider_name = self.provider_var.get()
        return self.provider_map.get(provider_name, "edge")

    def on_provider_changed(self, choice):
        self.selected_provider_code = self.get_current_provider_code()
        # Al cambiar de proveedor, reiniciamos la selección de voz para evitar conflictos
        self.selected_voice_id = None
        self.update_language_list()
        self.filter_voices()
        self.update_selected_label()

    def update_language_list(self):
        provider = self.get_current_provider_code()
        languages = self.voice_manager.get_language_list(provider)
        lang_names = ["Todos"] + [lang["name"] for lang in languages]
        self.lang_menu.configure(values=lang_names)
        self.lang_var.set("Todos")
        self.lang_map = {"Todos": None}
        for lang in languages:
            self.lang_map[lang["name"]] = lang["code"]

    def on_language_changed(self, choice):
        self.filter_voices()

    def get_current_lang_code(self):
        lang_name = self.lang_var.get()
        return self.lang_map.get(lang_name)

    def filter_voices(self):
        # Limpiar frame
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        provider = self.get_current_provider_code()
        lang_code = self.get_current_lang_code()
        search_text = self.search_var.get().lower()

        # Obtener voces según filtro
        if lang_code:
            voices_dict = self.voice_manager.get_voices_for_language(provider, lang_code)
        else:
            voices_dict = self.voice_manager.get_all_voices_flat(provider)

        # Filtrar por búsqueda
        filtered = {}
        for voice_id, display_name in voices_dict.items():
            if search_text in display_name.lower() or search_text in voice_id.lower():
                filtered[voice_id] = display_name

        if not filtered:
            ctk.CTkLabel(self.scroll_frame, text="No se encontraron voces",
                         text_color=st.COLOR_TEXT_DIM).pack(pady=20)
            return

        # Mostrar voces
        for voice_id, display_name in sorted(filtered.items(), key=lambda x: x[1]):
            fg_color = st.COLOR_ACCENT if voice_id == self.selected_voice_id else "transparent"
            btn = ctk.CTkButton(self.scroll_frame, text=display_name, height=35,
                                fg_color=fg_color, hover_color=st.COLOR_ACCENT,
                                anchor="w", command=lambda vid=voice_id, name=display_name: self.set_selected(vid, name))
            btn.pack(fill="x", padx=10, pady=2)

    def set_selected(self, voice_id, display_name):
        self.selected_voice_id = voice_id
        self.selected_provider_code = self.get_current_provider_code()
        # Refrescar la UI para mostrar el resaltado
        self.filter_voices()
        self.update_selected_label()
        logger.info(f"Voz seleccionada en diálogo: {voice_id} ({display_name})")

    def update_selected_label(self):
        if self.selected_voice_id:
            provider = self.selected_provider_code
            display_name = self.voice_manager.get_voice_display_name(provider, self.selected_voice_id)
            self.selected_label.configure(text=f"✓ Voz seleccionada: {display_name}")
        else:
            self.selected_label.configure(text="")

    def select_current(self):
        if self.selected_voice_id:
            provider = self.selected_provider_code
            # Obtener el nombre para mostrar
            display_name = self.voice_manager.get_voice_display_name(provider, self.selected_voice_id)
            logger.info(f"Callback on_select con: voice_id={self.selected_voice_id}, provider={provider}")
            self.on_select_callback(self.selected_voice_id, provider, display_name)
            self.destroy()
        else:
            messagebox.showwarning("Aviso", "Por favor selecciona una voz primero.")
