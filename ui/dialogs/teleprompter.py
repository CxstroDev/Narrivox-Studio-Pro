# ui/dialogs/teleprompter.py
import tkinter as tk

import customtkinter as ctk

from ui import styles as st


class TeleprompterWindow(ctk.CTkToplevel):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.title("Narrivox Teleprompter")
        self.geometry("900x700")
        self.configure(fg_color="black")
        self.attributes("-topmost", True)

        self.is_scrolling = False
        self.speed = 25

        # Área de texto
        self.txt = tk.Text(self, bg="black", fg="white", font=("Segoe UI", 42, "bold"),
                           wrap="word", borderwidth=0, padx=50, pady=250)
        self.txt.pack(fill="both", expand=True)
        self.txt.insert("1.0", text)
        self.txt.tag_configure("center", justify='center')
        self.txt.tag_add("center", "1.0", "end")
        self.txt.config(state="disabled")

        # Controles
        f = ctk.CTkFrame(self, fg_color="#111", height=80)
        f.pack(side="bottom", fill="x", padx=20, pady=20)

        self.btn_play = ctk.CTkButton(f, text="▶ INICIAR", fg_color=st.COLOR_SUCCESS,
                                      command=self.toggle_scroll)
        self.btn_play.pack(side="left", padx=20)

        ctk.CTkLabel(f, text="Velocidad:").pack(side="left", padx=10)
        self.speed_slider = ctk.CTkSlider(f, from_=5, to=100, command=self.set_speed)
        self.speed_slider.pack(side="left", fill="x", expand=True, padx=10)
        self.speed_slider.set(self.speed)

    def set_speed(self, val):
        self.speed = int(val)

    def toggle_scroll(self):
        self.is_scrolling = not self.is_scrolling
        self.btn_play.configure(text="⏸ PAUSAR" if self.is_scrolling else "▶ CONTINUAR",
                                fg_color="#d9534f" if self.is_scrolling else st.COLOR_SUCCESS)
        if self.is_scrolling:
            self.scroll_logic()

    def scroll_logic(self):
        if self.is_scrolling:
            self.txt.yview_scroll(1, "units")
            delay = int(2000 / self.speed)
            self.after(delay, self.scroll_logic)
