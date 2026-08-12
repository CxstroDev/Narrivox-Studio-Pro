# ui/dialogs/biblia_manager.py
import json
import os
from tkinter import messagebox

import customtkinter as ctk

from ui import styles as st


class BibliaManager(ctk.CTkToplevel):
    def __init__(self, parent, serie_name, base_folder):
        super().__init__(parent)
        self.title(f"Biblia Narrativa - {serie_name}")
        self.geometry("700x600")
        self.configure(fg_color=st.COLOR_BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self.serie_name = serie_name
        self.base_folder = base_folder
        self.biblia_path = os.path.join(base_folder, "biblia_serie.json")
        self.data = self._load_biblia()

        # Título
        ctk.CTkLabel(self, text=f"📖 BIBLIA DE LA SERIE: {serie_name}",
                     font=st.FONT_TITLE, text_color=st.COLOR_ACCENT).pack(pady=15)

        # Campos de edición
        fields = [
            ("Descripción General", "descripcion", 4),
            ("Personajes Principales", "personajes", 6),
            ("Trama General / Arcos", "trama", 6),
            ("Estilo Narrativo / Reglas", "estilo", 4)
        ]

        self.entries = {}
        for label, key, height in fields:
            frame = ctk.CTkFrame(self, fg_color=st.COLOR_CARD, corner_radius=10)
            frame.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(frame, text=label, font=st.FONT_SUBTITLE,
                         text_color=st.COLOR_TEXT).pack(anchor="w", padx=15, pady=(10,0))
            textbox = ctk.CTkTextbox(frame, height=height*20, font=("Segoe UI", 12),
                                     fg_color=st.COLOR_FG_BOX, text_color=st.COLOR_TEXT)
            textbox.pack(fill="x", padx=15, pady=10)
            textbox.insert("1.0", self.data.get(key, ""))
            self.entries[key] = textbox

        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="💾 GUARDAR BIBLIA", width=200, height=40,
                      fg_color=st.COLOR_SUCCESS, command=self.save_biblia).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="❌ CANCELAR", width=150, height=40,
                      fg_color="#d9534f", command=self.destroy).pack(side="left", padx=10)

    def _load_biblia(self):
        if os.path.exists(self.biblia_path):
            try:
                with open(self.biblia_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(f"Error al leer biblia: {e}")
        return {"descripcion": "", "personajes": "", "trama": "", "estilo": ""}

    def save_biblia(self):
        data = {
            "descripcion": self.entries["descripcion"].get("1.0", "end-1c").strip(),
            "personajes": self.entries["personajes"].get("1.0", "end-1c").strip(),
            "trama": self.entries["trama"].get("1.0", "end-1c").strip(),
            "estilo": self.entries["estilo"].get("1.0", "end-1c").strip()
        }
        try:
            os.makedirs(os.path.dirname(self.biblia_path), exist_ok=True)
            with open(self.biblia_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", "Biblia guardada correctamente.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
