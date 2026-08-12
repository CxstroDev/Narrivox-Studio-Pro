# ui/dialogs/save_success.py
import os

import customtkinter as ctk
from src.utils import open_folder

from ui import styles as st


class SaveSuccessWindow(ctk.CTkToplevel):
    def __init__(self, parent, serie, parte, folder, results):
        super().__init__(parent)
        self.parent = parent
        self.title("¡Éxito!")
        self.geometry("500x650")
        self.configure(fg_color=st.COLOR_BG)
        self.attributes("-topmost", True)
        self.resizable(False, False)

        # Icono
        ctk.CTkLabel(self, text="🎉", font=("Segoe UI", 60)).pack(pady=(30, 5))
        ctk.CTkLabel(self, text="¡PROYECTO GUARDADO!", font=("Segoe UI", 20, "bold"),
                     text_color=st.COLOR_SUCCESS).pack()

        # Detalles
        f_details = ctk.CTkFrame(self, fg_color=st.COLOR_CARD, corner_radius=15)
        f_details.pack(fill="x", padx=40, pady=15)
        info_txt = f"Serie: {serie}\nParte: {parte}\nUbicación: {os.path.basename(folder)}"
        ctk.CTkLabel(f_details, text=info_txt, font=("Segoe UI", 12), justify="center").pack(pady=15)

        # Reporte
        f_checks = ctk.CTkFrame(self, fg_color=st.COLOR_FG_BOX, corner_radius=15)
        f_checks.pack(fill="x", padx=40, pady=5)
        ctk.CTkLabel(f_checks, text="REPORTE DE GENERACIÓN:", font=("Segoe UI", 10, "bold"),
                     text_color=st.COLOR_TEXT_DIM).pack(pady=(12, 8), padx=25, anchor="w")

        items = [
            ("Guion Maestro (TXT)", results.get('txt')),
            ("Documento de Lectura (PDF)", results.get('pdf')),
            ("Narración Neuronal (MP3)", results.get('audio')),
            ("Subtítulos Sincronizados (SRT)", results.get('srt')),
            ("Arte Visual de IA (JPG)", results.get('img')),
            ("Índice en Base de Datos", results.get('excel'))
        ]
        f_list = ctk.CTkFrame(f_checks, fg_color="transparent")
        f_list.pack(fill="x", padx=25, pady=(0, 15))

        for name, status in items:
            icon = "✅" if status else "❌"
            color = st.COLOR_SUCCESS if status else "#d9534f"
            ctk.CTkLabel(f_list, text=f"{icon} {name}", font=("Segoe UI", 11, "bold"),
                         text_color=color).pack(anchor="w", pady=2)

        # Botones
        f_btns = ctk.CTkFrame(self, fg_color="transparent")
        f_btns.pack(pady=25)

        ctk.CTkButton(f_btns, text="📂 ABRIR CARPETA", width=180, height=45,
                      fg_color=st.COLOR_ACCENT,
                      command=lambda: [open_folder(folder), self.destroy()]).pack(side="left", padx=5)

        # Botón para ir a la sección de proyectos (antes storyboard)
        ctk.CTkButton(f_btns, text="🎬 VER EN PROYECTOS", width=180, height=45,
                      fg_color=st.COLOR_IA,
                      command=lambda: [self.parent.show_proyectos(), self.destroy()]).pack(side="left", padx=5)

        ctk.CTkButton(f_btns, text="LISTO", width=120, height=45,
                      fg_color="#444", command=self.destroy).pack(side="left", padx=5)
