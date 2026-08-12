# ui/dialogs/directory_manager.py
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from ui import styles as st


class DirectoryManager(ctk.CTkToplevel):
    def __init__(self, parent, directory_data, save_callback):
        super().__init__(parent)
        self.title("Gestor de Directorio - CARGA MASIVA")
        self.geometry("700x700")
        self.directory = directory_data
        self.save_callback = save_callback
        self.attributes("-topmost", True)

        mode = ctk.get_appearance_mode()
        self.lb_bg = "#c2c2c2" if mode == "Light" else "#1a1a1a"
        self.lb_fg = "#000000" if mode == "Light" else "#ffffff"

        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color=st.COLOR_ACCENT)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.listboxes = {}
        for cat in ["TEMAS", "OBJETOS", "ANOMALIAS", "EMOCIONES"]:
            self.tabview.add(cat)
            tab = self.tabview.tab(cat)
            lb = tk.Listbox(tab, bg=self.lb_bg, fg=self.lb_fg, font=("Segoe UI", 12),
                            borderwidth=0, highlightthickness=0)
            lb.pack(fill="both", expand=True, padx=5, pady=5)
            self.listboxes[cat] = lb
            self.refresh_list(cat)

        self.setup_bulk_area()

    def setup_bulk_area(self):
        f_bulk = ctk.CTkFrame(self, fg_color=st.COLOR_CARD, corner_radius=15)
        f_bulk.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkLabel(f_bulk, text="📥 CARGA MASIVA (un elemento por línea):",
                     font=("Segoe UI", 11, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(10,5), padx=20, anchor="w")
        self.bulk_text = ctk.CTkTextbox(f_bulk, height=120, font=("Segoe UI", 12),
                                        fg_color=("#c2c2c2", "#1a1a1a"), text_color=st.COLOR_TEXT)
        self.bulk_text.pack(fill="x", padx=20, pady=5)
        f_btns = ctk.CTkFrame(f_bulk, fg_color="transparent")
        f_btns.pack(fill="x", padx=20, pady=10)
        self.btn_del = ctk.CTkButton(f_btns, text="🗑️ BORRAR", height=40, width=150,
                                     fg_color="#d9534f", command=self.delete_item)
        self.btn_del.pack(side="right")
        self.btn_add_bulk = ctk.CTkButton(f_btns, text="✨ AÑADIR A LA LISTA ACTUAL", height=40,
                                          fg_color=st.COLOR_SUCCESS, command=self.process_bulk)
        self.btn_add_bulk.pack(side="left", fill="x", expand=True, padx=(0,10))

    def process_bulk(self):
        cat = self.tabview.get()
        raw = self.bulk_text.get("1.0", "end-1c").strip()
        if not raw:
            return
        nuevos = [line.strip() for line in raw.split("\n") if line.strip()]
        if nuevos:
            existentes = set(self.directory.get(cat, []))
            finales = [i for i in nuevos if i not in existentes]
            self.directory[cat].extend(finales)
            self.refresh_list(cat)
            self.bulk_text.delete("1.0", "end")
            self.save_callback()
            messagebox.showinfo("Carga Masiva", f"Añadidos {len(finales)} elementos a {cat}.")

    def refresh_list(self, cat):
        self.listboxes[cat].delete(0, tk.END)
        for item in sorted(self.directory.get(cat, [])):
            self.listboxes[cat].insert(tk.END, item)

    def delete_item(self):
        cat = self.tabview.get()
        sel = self.listboxes[cat].curselection()
        if sel:
            val = self.listboxes[cat].get(sel[0])
            self.directory[cat].remove(val)
            self.refresh_list(cat)
            self.save_callback()
