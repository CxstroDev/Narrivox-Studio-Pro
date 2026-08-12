# main.py
import os
import sys

import customtkinter as ctk
from huggingface_hub import login
from src.config_manager import load_config
from ui.main_window import MainWindow

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# === Autenticación HugugingFace===
config_temp = load_config()
hf_token = config_temp.get("hf_token", "")
if hf_token:
    try:
        login(token=hf_token)
    except Exception as exc:
        # El inicio de la aplicación no debe depender de la red.
        print(f"Aviso: no se pudo validar el token de Hugging Face: {exc}")
# =================================

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = MainWindow()
    app.mainloop()
