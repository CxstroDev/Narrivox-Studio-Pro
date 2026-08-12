# ui/frames/ajustes_frame.py
import json
import os
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
from src.ai_engine import AIEngine
from src.cinematic_engine import CinematicEngine
from src.config_manager import save_config
from src.data_manager import DataManager
from src.error_handling import handle_error
from src.hybrid_router import HybridRouter
from src.image_engine import ImageEngine
from src.marketing_engine import MarketingEngine
from src.model_manager import ModelManager
from src.orchestrator import Orchestrator
from src.sound_engine import SoundEngine
from src.tts_engine import TTSEngine
from src.utils import logger

from ui import styles as st
from ui.components.model_card import ModelCard
from ui.components.tooltip import ToolTip
from ui.dialogs.directory_manager import DirectoryManager


class AjustesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent", scrollbar_button_color=st.COLOR_ACCENT,
                       scrollbar_button_hover_color=st.COLOR_ACCENT,
                       label_text="", label_fg_color="transparent")
        self.app = app
        self.config = app.config.copy()
        self.model_manager = ModelManager(self.config)
        self.model_manager.scan_installed_models()
        self.config = self.model_manager.config

        # Diccionario para widgets dinámicos
        self.dynamic_entries = {}
        self._internet_status = True  # Asumimos True por defecto
        self._checking_internet = False
        self.original_config = json.dumps(self.config, sort_keys=True)

        # Iniciar verificación de internet en hilo separado
        self._async_check_internet()

        # Header con gradiente visual
        header_frame = ctk.CTkFrame(self, fg_color=st.COLOR_CARD, corner_radius=15, height=80)
        header_frame.pack(fill="x", pady=(0, 20), padx=10)
        header_frame.pack_propagate(False)

        ctk.CTkLabel(header_frame, text="⚙️ CONFIGURACIÓN DEL SISTEMA",
                     font=st.FONT_TITLE, text_color=st.COLOR_ACCENT).pack(pady=20)

        # Pestañas con diseño mejorado
        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color=st.COLOR_ACCENT,
                                      segmented_button_selected_hover_color=st.COLOR_ACCENT,
                                      segmented_button_unselected_color=st.COLOR_FG_BOX,
                                      segmented_button_unselected_hover_color=st.COLOR_FG_BOX)
        self.tabview.pack(fill="both", expand=True, pady=10, padx=10)

        self.tabview.add("🧠 IA")
        self.tabview.add("🎨 Imagen")
        self.tabview.add("🔊 Voz")
        self.tabview.add("🎬 Video")
        self.tabview.add("💻 Modelos")
        self.tabview.add("📁 General")

        # Botón Guardar con diseño mejorado
        save_frame = ctk.CTkFrame(self, fg_color="transparent")
        save_frame.pack(pady=20, fill="x", padx=10)

        self.btn_save = ctk.CTkButton(save_frame, text="💾 GUARDAR TODOS LOS CAMBIOS", height=55,
                                      fg_color=st.COLOR_SUCCESS, hover_color="#00a843",
                                      font=("Segoe UI", 15, "bold"), corner_radius=12,
                                      command=self.save_settings)
        self.btn_save.pack(fill="x", padx=5)

        self._build_ia_tab()
        self._build_image_tab()
        self._build_tts_tab()
        self._build_video_tab()
        self._build_local_models_tab()
        self._build_general_tab()

        self._bind_change_events()

    def _async_check_internet(self):
        """Verifica la conexión a internet sin bloquear la UI."""
        if self._checking_internet: return
        self._checking_internet = True
        
        def task():
            status = HybridRouter.has_internet()
            self.after(0, lambda: self._on_internet_checked(status))
            
        threading.Thread(target=task, daemon=True).start()

    def _on_internet_checked(self, status):
        self._internet_status = status
        self._checking_internet = False
        # Si el estado cambió a True, podríamos refrescar el catálogo automáticamente
        # Pero por ahora solo lo dejamos listo para la próxima vez que se use.

    # ------------------------------------------------------------------
    # Detección de cambios
    # ------------------------------------------------------------------
    def _bind_change_events(self):
        self.ia_model_entry.bind("<KeyRelease>", self._on_config_changed)
        self.fallback_text.bind("<KeyRelease>", self._on_config_changed)
        self.prompt_editor.bind("<KeyRelease>", self._on_config_changed)
        self.visual_prompt_editor.bind("<KeyRelease>", self._on_config_changed)
        self.folder_entry.bind("<KeyRelease>", self._on_config_changed)
        self.max_workers_entry.bind("<KeyRelease>", self._on_config_changed)

    def _on_config_changed(self, event=None):
        if hasattr(self, 'btn_save') and self.btn_save is not None:
            self.btn_save.configure(fg_color="#f0ad4e", text="⚠️ GUARDAR CAMBIOS PENDIENTES")

    # ------------------------------------------------------------------
    # Pestaña IA (Texto)
    # ------------------------------------------------------------------
    def _build_ia_tab(self):
        tab = self.tabview.tab("🧠 IA")
        tab.grid_columnconfigure(0, weight=1)

        # Sección de proveedor con tarjeta
        provider_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        provider_card.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(provider_card, text="🤖 PROVEEDOR DE IA",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        f_prov = ctk.CTkFrame(provider_card, fg_color="transparent")
        f_prov.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(f_prov, text="Proveedor principal:", width=160).pack(side="left")
        providers = ["deepseek", "gemini", "openrouter", "groq", "openai", "ollama", "local"]
        self.ia_provider_var = ctk.StringVar(value=self.config.get("ia_provider", "groq"))
        self.ia_provider_menu = ctk.CTkOptionMenu(f_prov, values=providers,
                                                  variable=self.ia_provider_var,
                                                  command=self._on_ia_provider_change)
        self.ia_provider_menu.pack(side="left", padx=10)
        self.ia_provider_var.trace_add("write", lambda *args: self._on_config_changed())

        self.ia_config_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.ia_config_frame.pack(fill="x", padx=15, pady=5)

        # Sección de modelo con tarjeta
        model_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        model_card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(model_card, text="📝 CONFIGURACIÓN DEL MODELO",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        f_model = ctk.CTkFrame(model_card, fg_color="transparent")
        f_model.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(f_model, text="Modelo:", width=160).pack(side="left")
        self.ia_model_entry = ctk.CTkEntry(f_model, width=300, corner_radius=8)
        self.ia_model_entry.pack(side="left", padx=10)
        self.ia_model_entry.insert(0, self.config.get("ia_model", "deepseek-chat"))

        # Sección de fallback con tarjeta
        fallback_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        fallback_card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(fallback_card, text="🔄 CASCADA DE FALLBACK",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        self.enable_fallback_var = ctk.BooleanVar(value=self.config.get("enable_fallback", False))
        cb = ctk.CTkCheckBox(fallback_card, text="Activar cascada de fallback (probar varios proveedores en orden)",
                             variable=self.enable_fallback_var, command=self._toggle_fallback_visibility)
        cb.pack(padx=15, pady=(0, 10), anchor="w")
        self.enable_fallback_var.trace_add("write", lambda *args: self._on_config_changed())

        self.fallback_frame = ctk.CTkFrame(fallback_card, fg_color=st.COLOR_FG_BOX, corner_radius=8)
        self.fallback_frame.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(self.fallback_frame, text="Cadena de fallback (proveedor:modelo por línea):",
                     font=("Segoe UI", 11, "bold")).pack(pady=(10,5), padx=10, anchor="w")
        self.fallback_text = ctk.CTkTextbox(self.fallback_frame, height=160, font=("Consolas", 11), corner_radius=8,
                                           scrollbar_button_color=st.COLOR_ACCENT, scrollbar_button_hover_color=st.COLOR_ACCENT)
        self.fallback_text.pack(fill="x", padx=10, pady=5)
        default_chain = self.config.get("ai_fallback_chain_str",
            "deepseek:deepseek-chat\ngemini:gemini-2.0-flash\nopenrouter:google/gemma-3-27b-it\ngroq:llama-3.3-70b-versatile\nollama:llama3")
        self.fallback_text.insert("1.0", default_chain)

        self._toggle_fallback_visibility()
        self._on_ia_provider_change(self.ia_provider_var.get())

    def _on_ia_provider_change(self, provider):
        for w in self.ia_config_frame.winfo_children():
            w.destroy()
        self.dynamic_entries = {k: v for k, v in self.dynamic_entries.items() if not k.startswith("ia_")}

        if provider == "local":
            models = self._get_installed_models_for_category("text")
            if models:
                current = self.config.get("local_providers", {}).get("text", {}).get("selected_model", models[0])
                menu, var = self._create_local_model_selector(self.ia_config_frame, "text", current)
                menu.pack(pady=5, padx=15, fill="x")
                self.dynamic_entries["ia_local_model"] = var
                self.ia_model_entry.delete(0, "end")
                self.ia_model_entry.insert(0, current)
            else:
                ctk.CTkLabel(self.ia_config_frame, text="No hay modelos de texto instalados.",
                            text_color=st.COLOR_TEXT_DIM).pack(pady=5)

        elif provider == "deepseek":
            self._add_api_key_row(self.ia_config_frame, "DeepSeek API Key:", "deepseek_api_key")
            default_model = "deepseek-chat"
            self.ia_model_entry.delete(0, "end")
            self.ia_model_entry.insert(0, default_model)
        elif provider == "gemini":
            self._add_api_key_row(self.ia_config_frame, "Gemini API Key:", "gemini_api_key")
            default_model = "gemini-2.0-flash"
            self.ia_model_entry.delete(0, "end")
            self.ia_model_entry.insert(0, default_model)
        elif provider == "openrouter":
            self._add_api_key_row(self.ia_config_frame, "OpenRouter API Key:", "openrouter_api_key")
            default_model = "google/gemma-3-27b-it"
            self.ia_model_entry.delete(0, "end")
            self.ia_model_entry.insert(0, default_model)
        elif provider == "groq":
            self._add_api_key_row(self.ia_config_frame, "Groq API Key:", "api_key")
            default_model = "llama-3.3-70b-versatile"
            self.ia_model_entry.delete(0, "end")
            self.ia_model_entry.insert(0, default_model)
        elif provider == "openai":
            self._add_api_key_row(self.ia_config_frame, "OpenAI API Key:", "openai_api_key")
            self._add_entry_row(self.ia_config_frame, "Base URL:", "openai_base_url", "https://api.openai.com/v1")
            default_model = "gpt-4o-mini"
            self.ia_model_entry.delete(0, "end")
            self.ia_model_entry.insert(0, default_model)
        elif provider == "ollama":
            self._add_entry_row(self.ia_config_frame, "Ollama URL:", "ollama_base_url", "http://localhost:11434/v1")
            default_model = "llama3"
            self.ia_model_entry.delete(0, "end")
            self.ia_model_entry.insert(0, default_model)

        self._on_config_changed()

    def _toggle_fallback_visibility(self):
        if self.enable_fallback_var.get():
            self.fallback_frame.pack(fill="x", padx=15, pady=(0, 12))
        else:
            self.fallback_frame.pack_forget()
        self._on_config_changed()

    # ------------------------------------------------------------------
    # Pestaña Imagen
    # ------------------------------------------------------------------
    def _build_image_tab(self):
        tab = self.tabview.tab("🎨 Imagen")
        tab.grid_columnconfigure(0, weight=1)

        # Sección de proveedor con tarjeta
        provider_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        provider_card.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(provider_card, text="🎨 PROVEEDOR DE IMAGEN",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        f_prov = ctk.CTkFrame(provider_card, fg_color="transparent")
        f_prov.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(f_prov, text="Proveedor:", width=160).pack(side="left")
        providers = ["zimage", "pollinations", "huggingface", "cloudflare", "puter", "local"]
        self.img_provider_var = ctk.StringVar(value=self.config.get("image_provider", "zimage"))
        self.img_provider_menu = ctk.CTkOptionMenu(f_prov, values=providers,
                                                   variable=self.img_provider_var,
                                                   command=self._on_image_provider_change)
        self.img_provider_menu.pack(side="left", padx=10)
        self.img_provider_var.trace_add("write", lambda *args: self._on_config_changed())

        self.img_config_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.img_config_frame.pack(fill="x", padx=15, pady=5)
        self._on_image_provider_change(self.img_provider_var.get())

    def _on_image_provider_change(self, provider):
        for w in self.img_config_frame.winfo_children():
            w.destroy()
        self.dynamic_entries = {k: v for k, v in self.dynamic_entries.items() if not k.startswith("img_")}

        if provider == "local":
            models = self._get_installed_models_for_category("image")
            if models:
                current = self.config.get("local_providers", {}).get("image", {}).get("selected_model", models[0])
                menu, var = self._create_local_model_selector(self.img_config_frame, "image", current)
                menu.pack(pady=5, padx=15, fill="x")
                self.dynamic_entries["img_local_model"] = var
            else:
                ctk.CTkLabel(self.img_config_frame, text="No hay modelos de imagen instalados.",
                            text_color=st.COLOR_TEXT_DIM).pack(pady=5)

        elif provider == "zimage":
            self._add_entry_row(self.img_config_frame, "Space Name:", "zimage_space", "mrfakename/Z-Image-Turbo")
        elif provider == "pollinations":
            self._add_api_key_row(self.img_config_frame, "API Key (opcional):", "pollinations_api_key")
            ctk.CTkLabel(self.img_config_frame, text="Si no se proporciona, se usa el endpoint público gratuito.",
                         font=("Segoe UI", 9), text_color=st.COLOR_TEXT_DIM).pack(anchor="w", pady=2)
        elif provider == "huggingface":
            self._add_api_key_row(self.img_config_frame, "HuggingFace Token:", "hf_token")
            self._add_entry_row(self.img_config_frame, "Model ID:", "hf_model_id", "black-forest-labs/FLUX.1-schnell")
        elif provider == "cloudflare":
            self._add_entry_row(self.img_config_frame, "Account ID:", "cf_account_id")
            self._add_api_key_row(self.img_config_frame, "API Token:", "cf_api_token")
            self._add_entry_row(self.img_config_frame, "Model ID:", "cf_model", "@cf/black-forest-labs/flux-1-schnell")
        elif provider == "puter":
            ctk.CTkLabel(self.img_config_frame, text="Puter.js es gratuito, no requiere credenciales.",
                         text_color=st.COLOR_SUCCESS).pack(pady=5)
        elif provider == "local":
            self._add_entry_row(self.img_config_frame, "Model ID:", "local_model_id", "stabilityai/stable-diffusion-xl-base-1.0")
        self._on_config_changed()

    # ------------------------------------------------------------------
    # Pestaña Voz (TTS)
    # ------------------------------------------------------------------
    def _build_tts_tab(self):
        tab = self.tabview.tab("🔊 Voz")
        tab.grid_columnconfigure(0, weight=1)

        # Sección de proveedor con tarjeta
        provider_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        provider_card.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(provider_card, text="🔊 MOTOR DE VOZ (TTS)",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        f_prov = ctk.CTkFrame(provider_card, fg_color="transparent")
        f_prov.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(f_prov, text="Motor TTS:", width=160).pack(side="left")
        providers = ["edge", "elevenlabs", "unrealspeech", "local"]
        self.tts_provider_var = ctk.StringVar(value=self.config.get("tts_provider", "edge"))
        self.tts_provider_menu = ctk.CTkOptionMenu(f_prov, values=providers,
                                                   variable=self.tts_provider_var,
                                                   command=self._on_tts_provider_change)
        self.tts_provider_menu.pack(side="left", padx=10)
        self.tts_provider_var.trace_add("write", lambda *args: self._on_config_changed())

        self.tts_config_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.tts_config_frame.pack(fill="x", padx=15, pady=5)
        self._on_tts_provider_change(self.tts_provider_var.get())

    def _on_tts_provider_change(self, provider):
        for w in self.tts_config_frame.winfo_children():
            w.destroy()
        self.dynamic_entries = {k: v for k, v in self.dynamic_entries.items() if not k.startswith("tts_")}

        if provider == "elevenlabs":
            self._add_api_key_row(self.tts_config_frame, "ElevenLabs API Key:", "elevenlabs_api_key")
            self._add_entry_row(self.tts_config_frame, "Voice ID:", "elevenlabs_voice_id", "21m00Tcm4TlvDq8ikWAM")
        elif provider == "unrealspeech":
            self._add_api_key_row(self.tts_config_frame, "Unreal Speech API Key:", "unrealspeech_api_key")
        elif provider == "edge":
            ctk.CTkLabel(self.tts_config_frame, text="Edge TTS es gratuito y no requiere configuración.",
                         text_color=st.COLOR_SUCCESS).pack(pady=5)
        elif provider == "local":
            info_frame = ctk.CTkFrame(self.tts_config_frame, fg_color=st.COLOR_CARD, corner_radius=12)
            info_frame.pack(fill="x", pady=5, padx=10)

            ctk.CTkLabel(info_frame, text="🖥️ Kokoro TTS Local", font=("Segoe UI", 12, "bold"),
                         text_color=st.COLOR_ACCENT).pack(pady=(12,8))

            instructions = (
                "Para usar Kokoro local:\n"
                "1. Asegúrate de tener Docker Desktop instalado.\n"
                "2. Ejecuta en una terminal:\n"
                "   docker run -d -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest\n"
                "3. Espera a que el contenedor esté listo.\n"
                "4. La aplicación se conectará automáticamente a http://localhost:8880"
            )
            ctk.CTkLabel(info_frame, text=instructions, justify="left",
                         font=("Segoe UI", 10)).pack(padx=15, pady=(0,12))

            self.local_status_label = ctk.CTkLabel(info_frame, text="", font=("Segoe UI", 10))
            self.local_status_label.pack(pady=(0,5))
            self.local_status_label_ref = self.local_status_label

            verify_btn = ctk.CTkButton(info_frame, text="🔍 Verificar servidor", width=150, corner_radius=8, command=self.check_kokoro_status)
            verify_btn.pack(pady=(0,12))
            ToolTip(verify_btn, "Comprueba si el servidor Docker de Kokoro está activo en http://localhost:8880")

            models = self._get_installed_models_for_category("tts")
            if models:
                current = self.config.get("local_providers", {}).get("tts", {}).get("selected_model", models[0])
                ctk.CTkLabel(info_frame, text="Voz activa:", font=("Segoe UI", 11)).pack(pady=(5,0))
                menu, var = self._create_local_model_selector(info_frame, "tts", current)
                menu.pack(pady=5, padx=15)
                self.dynamic_entries["tts_local_model"] = var
            else:
                ctk.CTkLabel(info_frame, text="No se detectó Kokoro instalado. Sigue las instrucciones de arriba.",
                             text_color=st.COLOR_TEXT_DIM).pack(pady=5)

        self._on_config_changed()

    def check_kokoro_status(self):
        try:
            from src.local_tts_engine import LocalTTSEngine
            engine = LocalTTSEngine(self.config)
            if engine.is_server_running():
                self.local_status_label_ref.configure(
                    text="✅ Servidor Kokoro está EN LÍNEA",
                    text_color=st.COLOR_SUCCESS
                )
            else:
                self.local_status_label_ref.configure(
                    text="❌ Servidor Kokoro NO detectado",
                    text_color="#d9534f"
                )
        except Exception as e:
            self.local_status_label_ref.configure(
                text=f"⚠️ Error al verificar: {e}",
                text_color="#f0ad4e"
            )

    # ------------------------------------------------------------------
    # Pestaña Video
    # ------------------------------------------------------------------
    def _build_video_tab(self):
        tab = self.tabview.tab("🎬 Video")
        tab.grid_columnconfigure(0, weight=1)

        # Sección de efectos con tarjeta
        effects_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        effects_card.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(effects_card, text="🎬 EFECTOS DE VIDEO",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        self.enable_ken_burns_var = ctk.BooleanVar(value=self.config.get("enable_ken_burns", True))
        ctk.CTkCheckBox(effects_card, text="Aplicar efecto Ken Burns (zoom dinámico)",
                        variable=self.enable_ken_burns_var, command=self._on_config_changed).pack(padx=15, pady=(0, 8), anchor="w")

        self.enable_broll_var = ctk.BooleanVar(value=self.config.get("enable_broll", False))
        ctk.CTkCheckBox(effects_card, text="Insertar B‑Roll automático (requiere API de Pexels/Pixabay)",
                        variable=self.enable_broll_var, command=self._toggle_broll_visibility).pack(padx=15, pady=(0, 12), anchor="w")

        self.broll_frame = ctk.CTkFrame(effects_card, fg_color=st.COLOR_FG_BOX, corner_radius=8)
        self.broll_frame.pack(fill="x", padx=15, pady=(0, 12))

        f_bprov = ctk.CTkFrame(self.broll_frame, fg_color="transparent")
        f_bprov.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(f_bprov, text="Proveedor:", width=120).pack(side="left")
        self.broll_provider_var = ctk.StringVar(value=self.config.get("broll_provider", "none"))
        ctk.CTkOptionMenu(f_bprov, values=["pexels", "pixabay", "none"],
                          variable=self.broll_provider_var, command=self._on_config_changed).pack(side="left", padx=10)

        self.broll_api_frame = ctk.CTkFrame(self.broll_frame, fg_color="transparent")
        self.broll_api_frame.pack(fill="x", padx=10, pady=5)
        self._add_api_key_row(self.broll_api_frame, "Pexels API Key:", "pexels_api_key")
        self._add_api_key_row(self.broll_api_frame, "Pixabay API Key:", "pixabay_api_key")

        # Sección de espacios con tarjeta
        spaces_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        spaces_card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(spaces_card, text="🚀 MOTORES DE VIDEO (GRADIO SPACES)",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        self._add_entry_row(spaces_card, "Helios Space:", "helios_space", "BestWishYsh/Helios-14B-RealTime-AOTI")
        self._add_entry_row(spaces_card, "SVD Space:", "svd_space", "stabilityai/stable-video-diffusion-img2vid")

        self._toggle_broll_visibility()

    def _toggle_broll_visibility(self):
        if self.enable_broll_var.get():
            self.broll_frame.pack(fill="x", padx=15, pady=(0, 12))
        else:
            self.broll_frame.pack_forget()
        self._on_config_changed()

    # ------------------------------------------------------------------
    # Pestaña Modelos Locales
    # ------------------------------------------------------------------
    def _build_local_models_tab(self):
        tab = self.tabview.tab("💻 Modelos")
        tab.grid_columnconfigure(0, weight=1)

        # Header informativo
        info_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        info_card.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            info_card,
            text="💻 GESTIÓN DE MODELOS LOCALES",
            font=("Segoe UI", 13, "bold"),
            text_color=st.COLOR_ACCENT
        ).pack(pady=(12, 5), padx=15, anchor="w")

        ctk.CTkLabel(
            info_card,
            text="Gestiona los modelos de IA que se ejecutan localmente en tu equipo.",
            font=("Segoe UI", 11),
            text_color=st.COLOR_TEXT_DIM
        ).pack(pady=(0, 8), padx=15, anchor="w")

        self.prefer_local_var = ctk.BooleanVar(value=self.config.get("prefer_local", False))
        cb = ctk.CTkCheckBox(
            info_card,
            text="⚡ Preferir modelos locales sobre online (cuando estén disponibles)",
            variable=self.prefer_local_var,
            command=self._on_config_changed
        )
        cb.pack(pady=(0, 12), padx=15, anchor="w")
        ToolTip(cb, "Si está activado, la app usará modelos locales siempre que sea posible, incluso teniendo conexión a internet.")

        self.space_label = ctk.CTkLabel(
            info_card,
            text="",
            font=("Segoe UI", 11),
            text_color=st.COLOR_TEXT_DIM
        )
        self.space_label.pack(pady=(0, 12), padx=15, anchor="w")
        self._update_space_label()

        sub_tabview = ctk.CTkTabview(
            tab,
            segmented_button_selected_color=st.COLOR_ACCENT,
            segmented_button_selected_hover_color=st.COLOR_ACCENT,
            segmented_button_unselected_color=st.COLOR_FG_BOX,
            segmented_button_unselected_hover_color=st.COLOR_FG_BOX,
            height=650
        )
        sub_tabview.pack(fill="both", expand=True, padx=15, pady=10)

        self.model_tabs = {}
        self.category_frames = {}
        categories = [
            ("text", "📝 Texto", "Generación de guiones"),
            ("image", "🎨 Imagen", "Generación de arte visual"),
            ("tts", "🔊 Voz", "Síntesis de voz")
        ]

        for cat_id, cat_name, cat_desc in categories:
            sub_tabview.add(cat_name)
            tab_content = sub_tabview.tab(cat_name)
            self.model_tabs[cat_id] = tab_content
            self._build_category_tab(tab_content, cat_id, cat_desc)

        refresh_btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        refresh_btn_frame.pack(pady=10, fill="x", padx=15)

        ctk.CTkButton(
            refresh_btn_frame,
            text="🔄 ACTUALIZAR LISTA DE MODELOS",
            height=45,
            fg_color=st.COLOR_ACCENT,
            hover_color="#2e4ae6",
            font=("Segoe UI", 12, "bold"),
            corner_radius=10,
            command=self._refresh_all_model_tabs
        ).pack(fill="x")

    def _build_category_tab(self, parent, category: str, description: str):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        # Modelos Instalados
        installed_label = ctk.CTkLabel(
            parent,
            text=f"📦 MODELOS INSTALADOS ({category.upper()})",
            font=st.FONT_SUBTITLE,
            text_color=st.COLOR_ACCENT
        )
        installed_label.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")

        installed_frame = ctk.CTkScrollableFrame(parent, fg_color=st.COLOR_CARD, corner_radius=12,
                                               scrollbar_button_color=st.COLOR_ACCENT,
                                               scrollbar_button_hover_color=st.COLOR_ACCENT,
                                               label_text="", height=320)
        installed_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")
        installed_frame.grid_columnconfigure(0, weight=1)

        # Catálogo Disponible
        catalog_label = ctk.CTkLabel(
            parent,
            text="🌐 CATÁLOGO DISPONIBLE",
            font=st.FONT_SUBTITLE,
            text_color=st.COLOR_ACCENT
        )
        catalog_label.grid(row=2, column=0, padx=15, pady=(10, 5), sticky="w")

        catalog_frame = ctk.CTkScrollableFrame(parent, fg_color=st.COLOR_CARD, corner_radius=12,
                                              scrollbar_button_color=st.COLOR_ACCENT,
                                              scrollbar_button_hover_color=st.COLOR_ACCENT,
                                              label_text="", height=300)
        catalog_frame.grid(row=3, column=0, padx=15, pady=(0, 10), sticky="nsew")
        catalog_frame.grid_columnconfigure(0, weight=1)

        self.category_frames[category] = {
            'installed': installed_frame,
            'catalog': catalog_frame
        }

        self._populate_category_tab(category)

    def _populate_category_tab(self, category: str):
        frames = self.category_frames.get(category)
        if not frames:
            return

        for widget in frames['installed'].winfo_children():
            widget.destroy()
        for widget in frames['catalog'].winfo_children():
            widget.destroy()

        installed_models = self.model_manager.config.get("local_providers", {}).get(category, {}).get("installed", {})
        active_model = self.model_manager.get_active_model(category)

        if installed_models:
            for model_id, model_info in installed_models.items():
                catalog_info = next((m for m in self.model_manager.get_available_catalog(category) if m["id"] == model_id), {})
                display_data = {
                    "id": model_id,
                    "name": catalog_info.get("name", model_info.get("display_name", model_id.split("/")[-1])),
                    "size_gb": model_info.get("size_mb", 0) / 1024,
                    "description": catalog_info.get("description", ""),
                    "path": model_info.get("path", "")
                }
                is_active = (model_id == active_model)
                card = ModelCard(
                    frames['installed'],
                    display_data,
                    category,
                    is_installed=True,
                    is_active=is_active,
                    on_delete=lambda mid=model_id: self._delete_model(category, mid),
                    on_set_active=lambda mid=model_id: self._set_active_model(category, mid)
                )
                card.pack(fill="x", padx=5, pady=5)
        else:
            ctk.CTkLabel(
                frames['installed'],
                text="No hay modelos instalados en esta categoría.",
                text_color=st.COLOR_TEXT_DIM
            ).pack(pady=20)

        # --- Catálogo Disponible ---
        if not self._internet_status:
            ctk.CTkLabel(
                frames['catalog'],
                text="🌐 Sin conexión a Internet.\nConéctate para ver el catálogo de modelos descargables.",
                text_color=st.COLOR_TEXT_DIM,
                justify="center"
            ).pack(pady=20)
        else:
            catalog_models = self.model_manager.get_available_catalog(category)
            installed_ids = set(installed_models.keys())
            for model in catalog_models:
                if model["id"] in installed_ids:
                    continue
                card = ModelCard(
                    frames['catalog'],
                    model,
                    category,
                    is_installed=False,
                    on_download=lambda mid=model["id"], cat=category: self._handle_download(cat, mid)
                )
                card.pack(fill="x", padx=5, pady=5)

        self._update_space_label()


    def _delete_model(self, category: str, model_id: str):
        success = self.model_manager.delete_model(category, model_id)
        if success:
            self.model_manager.save_config()
            self.config = self.model_manager.config
            self._populate_category_tab(category)
            self.app.show_toast(f"🗑️ Modelo {model_id} eliminado.")
        else:
            messagebox.showerror("Error", "No se pudo eliminar el modelo.")

    def _set_active_model(self, category: str, model_id: str):
        success = self.model_manager.set_active_model(category, model_id)
        if success:
            self.model_manager.save_config()
            self.config = self.model_manager.config
            self._populate_category_tab(category)
            self.app.show_toast(f"✅ Modelo activado: {model_id}")
        else:
            messagebox.showerror("Error", "No se pudo activar el modelo.")

    def _handle_download(self, category: str, model_id: str, cancel: bool = False):
        if cancel:
            self.model_manager.cancel_download(model_id)
        else:
            self._download_model(category, model_id)

    def _download_model(self, category: str, model_id: str):
        """Verifica requisitos y pregunta antes de descargar."""
        # --- Obtener información del catálogo ---
        catalog_entry = next(
            (m for m in self.model_manager.get_available_catalog(category)
            if m["id"] == model_id),
            None
        )
        if not catalog_entry:
            messagebox.showerror("Error", "Modelo no encontrado en el catálogo.")
            return

        name = catalog_entry.get("name", model_id)
        size_gb = catalog_entry.get("size_gb", 0)
        requirements = catalog_entry.get("requirements", {})
        ram_gb = requirements.get("ram_gb", 0)
        gpu_note = " (GPU opcional)" if requirements.get("gpu_optional", True) else ""
        docker_note = "\n\nRequiere Docker para funcionar." if requirements.get("docker", False) else ""

        # --- Calcular RAM disponible ---
        ram_available_str = ""
        warning = ""
        try:
            import psutil
            available_gb = psutil.virtual_memory().available / (1024 ** 3)
            ram_available_str = f"\nRAM disponible: {available_gb:.1f} GB"
            if ram_gb > 0 and available_gb < ram_gb:
                warning = (
                    "\n\n⚠️ ADVERTENCIA: La RAM disponible es menor que la recomendada.\n"
                    "El rendimiento puede ser muy bajo o el modelo podría no cargar correctamente.\n"
                    "Se recomienda cerrar otras aplicaciones antes de usarlo."
                )
        except ImportError:
            pass

        # --- Aviso de autenticación ---
        requires_auth = catalog_entry.get("requires_auth", False)
        token_configured = bool(self.config.get("hf_token", ""))
        auth_warning = ""
        if requires_auth and not token_configured:
            auth_warning = (
                "\n\n🔒 Este modelo requiere autenticación en Hugging Face.\n"
                "Ve a Ajustes > General y configura tu token HF para poder descargarlo."
            )

        # --- Construir mensaje ---
        msg = (
            f"Descargar modelo: {name}\n"
            f"Tamaño: {size_gb:.1f} GB\n"
            f"RAM recomendada: {ram_gb:.1f} GB{gpu_note}{ram_available_str}{docker_note}"
            f"{warning}{auth_warning}\n\n"
            f"¿Deseas continuar con la descarga?"
        )

        if not messagebox.askyesno("Confirmar descarga", msg):
            return

        # --- Buscar tarjeta del catálogo para la barra de progreso ---
        frames = self.category_frames.get(category)
        card = None
        if frames:
            for widget in frames['catalog'].winfo_children():
                if isinstance(widget, ModelCard) and widget.model_data["id"] == model_id:
                    card = widget
                    break

        if card:
            card.downloading = True
            card._update_ui()

        def progress_callback(percent, message):
            if card:
                self.after(0, lambda: card.set_download_progress(percent, message))

        def download_task():
            success = self.model_manager.download_model(
                category, model_id, progress_callback=progress_callback
            )
            self.after(0, lambda: self._on_download_complete(category, model_id, success, card))

        thread = threading.Thread(target=download_task, daemon=True)
        if not hasattr(self, '_download_threads'):
            self._download_threads = {}
        self._download_threads[model_id] = thread
        thread.start()

    def _on_download_complete(self, category: str, model_id: str, success: bool, card=None):
        if card:
            card.set_download_complete(success)
        if success:
            self.model_manager.scan_installed_models(category)
            self.model_manager.save_config()
            self.config = self.model_manager.config
            self._populate_category_tab(category)
            self.app.show_toast(f"⬇️ Modelo {model_id} instalado correctamente.")
        else:
            messagebox.showerror("Error", f"La descarga de {model_id} falló o fue cancelada.")
        if hasattr(self, '_download_threads'):
            self._download_threads.pop(model_id, None)

    def _refresh_all_model_tabs(self):
        self.model_manager.scan_installed_models()
        self.config = self.model_manager.config
        for category in self.category_frames.keys():
            self._populate_category_tab(category)
        self._update_space_label()

    def _update_space_label(self):
        total_mb = self.model_manager.get_total_size()
        total_gb = total_mb / 1024
        self.space_label.configure(text=f"💾 Espacio ocupado por modelos: {total_gb:.2f} GB")

    def _get_installed_models_for_category(self, category: str):
        installed = self.config.get("local_providers", {}).get(category, {}).get("installed", {})
        return list(installed.keys())

    def _get_model_display_name(self, category: str, model_id: str) -> str:
        installed = self.config.get("local_providers", {}).get(category, {}).get("installed", {})
        if model_id in installed:
            return installed[model_id].get("display_name", model_id)
        return model_id

    def _create_local_model_selector(self, parent, category: str, current_value: str = None):
        models = self._get_installed_models_for_category(category)
        if not models:
            models = ["(No hay modelos instalados)"]
        display_names = [self._get_model_display_name(category, m) for m in models]

        var = ctk.StringVar(value=current_value if current_value in models else (models[0] if models else ""))
        menu = ctk.CTkOptionMenu(parent, values=display_names, variable=var)
        ToolTip(menu, "Selecciona el modelo que quieres usar para esta categoría. Solo se muestran los modelos instalados.")

        if not hasattr(self, '_model_selector_map'):
            self._model_selector_map = {}
        self._model_selector_map[category] = dict(zip(display_names, models))

        return menu, var

    # ------------------------------------------------------------------
    # Pestaña General
    # ------------------------------------------------------------------
    def _build_general_tab(self):
        tab = self.tabview.tab("📁 General")
        tab.grid_columnconfigure(0, weight=1)

        # Sección de apariencia con tarjeta
        appearance_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        appearance_card.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(appearance_card, text="🎨 APARIENCIA",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        f_theme = ctk.CTkFrame(appearance_card, fg_color="transparent")
        f_theme.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(f_theme, text="Tema:", width=160).pack(side="left")
        self.theme_sel = ctk.CTkSegmentedButton(f_theme, values=["Dark", "Light", "System"],
                                                command=lambda m: ctk.set_appearance_mode(m))
        self.theme_sel.pack(side="left", padx=10)
        self.theme_sel.set(self.config.get("appearance_mode", "Dark"))

        # Sección de información con tarjeta
        info_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        info_card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(info_card, text="👤 INFORMACIÓN DEL PRODUCTOR",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        self._add_entry_row(info_card, "Nombre del productor:", "user_name", "Narrivox Studio Pro")

        # Sección de directorios con tarjeta
        folders_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        folders_card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(folders_card, text="📁 DIRECTORIOS",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        f_base = ctk.CTkFrame(folders_card, fg_color="transparent")
        f_base.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(f_base, text="Carpeta base:", width=160).pack(side="left")
        self.folder_entry = ctk.CTkEntry(f_base, width=400, corner_radius=8)
        self.folder_entry.pack(side="left", padx=10)
        self.folder_entry.insert(0, self.config.get("base_folder", os.getcwd()))
        ctk.CTkButton(f_base, text="Examinar", width=80, corner_radius=8, command=self.pick_folder).pack(side="left")

        # Sección de rendimiento con tarjeta
        performance_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        performance_card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(performance_card, text="⚡ RENDIMIENTO",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        f_workers = ctk.CTkFrame(performance_card, fg_color="transparent")
        f_workers.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkLabel(f_workers, text="Hilos Marathon+:", width=160).pack(side="left")
        self.max_workers_entry = ctk.CTkEntry(f_workers, width=60, corner_radius=8)
        self.max_workers_entry.pack(side="left")
        self.max_workers_entry.insert(0, str(self.config.get("max_workers", 4)))

        self.enable_marketing_var = ctk.BooleanVar(value=self.config.get("enable_marketing", True))
        ctk.CTkCheckBox(performance_card, text="Generar assets de marketing (miniaturas y SEO)",
                        variable=self.enable_marketing_var, command=self._on_config_changed).pack(padx=15, pady=(0, 12), anchor="w")

        # Sección de plantillas con tarjeta
        templates_card = ctk.CTkFrame(tab, fg_color=st.COLOR_CARD, corner_radius=12)
        templates_card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(templates_card, text="📝 PLANTILLAS DE PROMPT",
                     font=("Segoe UI", 13, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(12, 8), padx=15, anchor="w")

        ctk.CTkLabel(templates_card, text="Prompt maestro para guiones:", font=("Segoe UI", 10), text_color=st.COLOR_TEXT_DIM).pack(padx=15, pady=(0, 5), anchor="w")
        self.prompt_editor = ctk.CTkTextbox(templates_card, height=140, font=("Consolas", 11), fg_color=st.COLOR_FG_BOX, corner_radius=8,
                                           scrollbar_button_color=st.COLOR_ACCENT, scrollbar_button_hover_color=st.COLOR_ACCENT)
        self.prompt_editor.pack(fill="x", padx=15, pady=(0, 10))
        self.prompt_editor.insert("1.0", self.config.get("prompt_template", ""))

        ctk.CTkLabel(templates_card, text="Prompt para prompts visuales:", font=("Segoe UI", 10), text_color=st.COLOR_TEXT_DIM).pack(padx=15, pady=(0, 5), anchor="w")
        self.visual_prompt_editor = ctk.CTkTextbox(templates_card, height=120, font=("Consolas", 11), fg_color=st.COLOR_FG_BOX, corner_radius=8,
                                                   scrollbar_button_color=st.COLOR_ACCENT, scrollbar_button_hover_color=st.COLOR_ACCENT)
        self.visual_prompt_editor.pack(fill="x", padx=15, pady=(0, 12))
        self.visual_prompt_editor.insert("1.0", self.config.get("visual_prompt_template", ""))

        # Botón de gestor de directorio
        dir_manager_frame = ctk.CTkFrame(tab, fg_color="transparent")
        dir_manager_frame.pack(pady=10, fill="x", padx=15)

        ctk.CTkButton(dir_manager_frame, text="📂 ABRIR GESTOR DE DIRECTORIO CREATIVO", height=45,
                      fg_color=st.COLOR_ACCENT, hover_color="#2e4ae6",
                      font=("Segoe UI", 12, "bold"), corner_radius=10,
                      command=self.open_directory_manager).pack(fill="x")

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------
    def _add_api_key_row(self, parent, label, config_key):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=3)
        ctk.CTkLabel(frame, text=label, width=160).pack(side="left")
        entry = ctk.CTkEntry(frame, width=350, show="*", corner_radius=8)
        entry.pack(side="left", padx=5)
        entry.insert(0, self.config.get(config_key, ""))
        entry.bind("<KeyRelease>", self._on_config_changed)
        self.dynamic_entries[config_key] = entry

    def _add_entry_row(self, parent, label, config_key, default=""):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=3)
        ctk.CTkLabel(frame, text=label, width=160).pack(side="left")
        entry = ctk.CTkEntry(frame, width=350, corner_radius=8)
        entry.pack(side="left", padx=5)
        entry.insert(0, self.config.get(config_key, default))
        entry.bind("<KeyRelease>", self._on_config_changed)
        self.dynamic_entries[config_key] = entry

    def pick_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, p)
            self._on_config_changed()

    def open_directory_manager(self):
        DirectoryManager(self, self.config["directory"], self.save_settings)

    # ------------------------------------------------------------------
    # Guardar configuración
    # ------------------------------------------------------------------
    def save_settings(self):
        try:
            # Recopilar valores de widgets estáticos
            self.config["ia_provider"] = self.ia_provider_var.get()
            self.config["ia_model"] = self.ia_model_entry.get().strip()
            self.config["enable_fallback"] = self.enable_fallback_var.get()
            self.config["ai_fallback_chain_str"] = self.fallback_text.get("1.0", "end-1c").strip()

            self.config["image_provider"] = self.img_provider_var.get()
            self.config["tts_provider"] = self.tts_provider_var.get()
            self.config["enable_ken_burns"] = self.enable_ken_burns_var.get()
            self.config["enable_broll"] = self.enable_broll_var.get()
            self.config["broll_provider"] = self.broll_provider_var.get()
            self.config["enable_marketing"] = self.enable_marketing_var.get()
            self.config["prefer_local"] = self.prefer_local_var.get()
            self.config["max_workers"] = int(self.max_workers_entry.get() or "4")
            self.config["base_folder"] = self.folder_entry.get().strip()
            self.config["prompt_template"] = self.prompt_editor.get("1.0", "end-1c").strip()
            self.config["visual_prompt_template"] = self.visual_prompt_editor.get("1.0", "end-1c").strip()

            # Guardar modelo local seleccionado en cada categoría
            for category, var_key in [("text", "ia_local_model"), ("image", "img_local_model"), ("tts", "tts_local_model")]:
                if var_key in self.dynamic_entries:
                    var = self.dynamic_entries[var_key]
                    display_name = var.get()
                    model_id = self._model_selector_map.get(category, {}).get(display_name, display_name)
                    if model_id and model_id != "(No hay modelos instalados)":
                        if "local_providers" not in self.config:
                            self.config["local_providers"] = {}
                        if category not in self.config["local_providers"]:
                            self.config["local_providers"][category] = {}
                        self.config["local_providers"][category]["selected_model"] = model_id
                        # También actualizar el model_id genérico por compatibilidad
                        if category == "text":
                            self.config["ia_model"] = model_id
                        elif category == "image":
                            self.config["local_model_id"] = model_id

            # Recoger valores de entradas dinámicas (API keys, URLs, etc.)
            for key, entry in self.dynamic_entries.items():
                # Si es un StringVar (de los selectores locales)
                if isinstance(entry, ctk.StringVar):
                    continue
                # Para widgets (CTkEntry, etc.)
                try:
                    if entry.winfo_exists():
                        self.config[key] = entry.get().strip()
                    else:
                        logger.warning(f"Widget para '{key}' ya no existe, se omite su valor.")
                except Exception as e:
                    logger.warning(f"Error al obtener valor de '{key}': {e}")

            # Asegurar user_name
            if "user_name" not in self.config or not self.config["user_name"]:
                self.config["user_name"] = "Narrivox Studio Pro"

            # Convertir cadena de fallback a lista
            chain = []
            for line in self.config["ai_fallback_chain_str"].split("\n"):
                if ":" in line:
                    prov, model = line.strip().split(":", 1)
                    chain.append({"provider": prov.strip(), "model": model.strip()})
            if chain:
                self.config["ai_fallback_chain"] = chain

            if save_config(self.config):
                # Reiniciar motores con nueva configuración
                self.app.config = self.config
                self.app.ai = AIEngine(self.config)
                self.app.tts = TTSEngine(self.config)
                self.app.data = DataManager(self.config)
                self.app.image_engine = ImageEngine(self.config)
                self.app.cinematic = CinematicEngine(self.config)
                self.app.sound = SoundEngine(self.config)
                self.app.marketing = MarketingEngine(self.config, self.app.ai, self.app.image_engine)
                self.app.orchestrator = Orchestrator(self.config, self.app.ai, self.app.tts, self.app.data)

                self.original_config = json.dumps(self.config, sort_keys=True)
                self.btn_save.configure(fg_color=st.COLOR_SUCCESS, text="💾 GUARDAR TODOS LOS CAMBIOS")
                messagebox.showinfo("Ajustes", "Configuración guardada y aplicada.")
            else:
                raise Exception("No se pudo escribir el archivo de configuración")
        except Exception as e:
            handle_error(e, "guardar configuración", self)
