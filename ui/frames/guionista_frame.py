# ui/frames/guionista_frame.py
import json
import os
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
from src.error_handling import translate_error
from src.utils import clean_filename, logger
from src.voice_manager import VoiceManager

from ui import styles as st
from ui.dialogs.biblia_manager import BibliaManager


class GuionistaFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.selected_voice = None
        self.selected_provider = None
        self.selected_voice_display = None

        # Título
        ctk.CTkLabel(self, text="EDITOR DE GUION MAESTRO", font=st.FONT_TITLE).pack(pady=(0, 20))

        # Layout de dos columnas
        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True)

        # Columna izquierda: controles
        col_left = ctk.CTkFrame(split, width=300, fg_color=st.COLOR_CARD, corner_radius=15)
        col_left.pack(side="left", fill="y", padx=(0, 20), pady=10)

        self.serie_entry = ctk.CTkEntry(col_left, placeholder_text="Nombre de la Serie", width=240)
        self.serie_entry.pack(pady=10)

        self.parte_sel = ctk.CTkComboBox(col_left, values=[str(i) for i in range(1, 21)], width=240)
        self.parte_sel.pack(pady=5)
        self.parte_sel.set("1")

        self.tone_sel = ctk.CTkComboBox(col_left, values=["Oscuro", "Misterioso", "Épico", "Realista"], width=240)
        self.tone_sel.pack(pady=5)
        self.tone_sel.set("Oscuro")

        self.struct_sel = ctk.CTkComboBox(col_left, values=["Caja de Misterio", "Loop Infinito", "Viaje del Héroe"], width=240)
        self.struct_sel.pack(pady=5)
        self.struct_sel.set("Caja de Misterio")

        self.script_notes = ctk.CTkTextbox(col_left, height=120, width=240,
                                           fg_color=st.COLOR_FG_BOX, text_color=st.COLOR_TEXT)
        self.script_notes.pack(pady=5, padx=5)

        self.btn_biblia = ctk.CTkButton(col_left, text="📖 EDITAR BIBLIA", height=35, width=240,
                                        fg_color="#6a0dad", command=self.open_biblia_manager)
        self.btn_biblia.pack(pady=5)

        self.btn_ai_gen = ctk.CTkButton(col_left, text="✨ GENERAR GUION", height=50, width=240,
                                        fg_color=st.COLOR_IA, font=("Segoe UI", 14, "bold"),
                                        command=self.run_ai_script)
        self.btn_ai_gen.pack(pady=20)

        # Barra de progreso indeterminada (oculta inicialmente)
        self.ai_progress = ctk.CTkProgressBar(col_left, mode="indeterminate")
        self.ai_progress.pack(pady=5, fill="x", padx=10)
        self.ai_progress.pack_forget()

        # Columna derecha: editor y controles de audio
        col_right = ctk.CTkFrame(split, fg_color="transparent")
        col_right.pack(side="right", fill="both", expand=True)

        self.script_editor = ctk.CTkTextbox(col_right, font=("Segoe UI", 14),
                                            fg_color=st.COLOR_FG_BOX, text_color=st.COLOR_TEXT,
                                            border_width=1, border_color="#333")
        self.script_editor.pack(fill="both", expand=True, pady=(0, 15))

        # Estadísticas en tiempo real
        self.stats_label = ctk.CTkLabel(col_right, text="Palabras: 0 | Caracteres: 0 | Duración est.: 0:00",
                                        font=("Segoe UI", 11), text_color=st.COLOR_TEXT_DIM)
        self.stats_label.pack(side="bottom", anchor="e", pady=(5, 0))
        self.script_editor.bind("<KeyRelease>", self.update_stats)

        # Barra de herramientas
        f_tts = ctk.CTkFrame(col_right, fg_color="transparent")
        f_tts.pack(fill="x", pady=(0, 10))

        btn_f = ctk.CTkFrame(col_right, fg_color="transparent")
        btn_f.pack(fill="x")

        ctk.CTkButton(btn_f, text="📋 Copiar", width=100,
                      command=lambda: self.clipboard_copy(self.script_editor.get("1.0", "end-1c"))).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="💾 GUARDAR PROYECTO", width=180, fg_color=st.COLOR_SUCCESS,
                      command=self.master_save).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="🖼️ Generar Visuales", width=160, fg_color=st.COLOR_ACCENT,
                      command=self.send_to_visual).pack(side="right", padx=5)
        ctk.CTkButton(btn_f, text="🎤 PROMPTER", width=120, fg_color="#f0ad4e", text_color="black",
                      command=self.launch_prompter).pack(side="right", padx=5)

        # Controles de audio
        ctk.CTkButton(f_tts, text="⏹", width=40, height=35, fg_color="#d9534f",
                      command=self.app.tts.stop_audio).pack(side="left")
        self.btn_listen = ctk.CTkButton(f_tts, text="🔊 ESCUCHAR", width=110, height=35,
                                        fg_color="#4b0082", font=("Segoe UI", 11, "bold"),
                                        command=self.play_script_audio)
        self.btn_listen.pack(side="left", padx=5)

        self.lbl_tts_status = ctk.CTkLabel(col_right, text="", font=("Segoe UI", 11, "italic"),
                                           text_color=st.COLOR_ACCENT)
        self.lbl_tts_status.pack(pady=(0, 10))

        # Botón para seleccionar voz
        self.voice_button = ctk.CTkButton(f_tts, text="Seleccionar voz", width=160, height=35,
                                          fg_color=st.COLOR_CARD, hover_color=st.COLOR_ACCENT,
                                          command=self.open_voice_selector)
        self.voice_button.pack(side="right", padx=5)
        
        # Botón de previsualización de voz
        self.btn_preview_voice = ctk.CTkButton(f_tts, text="🎧 Probar", width=80, height=35,
                                               fg_color=st.COLOR_FG_BOX, border_width=1,
                                               command=self.preview_voice_sample)
        self.btn_preview_voice.pack(side="right", padx=5)
        
        ctk.CTkLabel(f_tts, text="Narrador:", font=("Segoe UI", 11)).pack(side="right", padx=5)

        # Conectar callback para cuando se carguen voces dinámicas
        self.app.tts.on_voices_loaded = self.on_voices_loaded

    # ---------- MÉTODOS ----------
    def preview_voice_sample(self):
        """Reproduce una muestra corta de la voz seleccionada."""
        if not self.selected_voice:
            self.set_default_voice()
            if not self.selected_voice:
                messagebox.showwarning("Aviso", "Primero selecciona una voz.")
                return
        
        sample_text = "Esta es una muestra de la voz seleccionada en Narrivox Studio Pro."
        provider = self.selected_provider or self.app.config.get("tts_provider", "edge")
        voice_code = self.app.tts.get_voice_code(self.selected_voice, "Todos") or self.selected_voice
        
        self.lbl_tts_status.configure(text=f"🎧 Probando voz: {self.selected_voice_display}...")
        self.app.tts.play_preview(sample_text, voice_code)
        self.after(3000, lambda: self.lbl_tts_status.configure(text=""))

    def clipboard_copy(self, text):
        self.app.clipboard_clear()
        self.app.clipboard_append(text)

    def on_voices_loaded(self):
        """Se llama cuando las voces del proveedor actual están listas."""
        # Si no hay voz seleccionada, intentar seleccionar una por defecto
        if not self.selected_voice:
            self.set_default_voice()

    def set_default_voice(self):
        """Establece una voz por defecto según el proveedor configurado."""
        provider = self.app.config.get("tts_provider", "edge")
        voices = self.app.tts.get_filtered_voices("Todos")
        if voices:
            # Preferir voces en español
            spanish_voices = {k: v for k, v in voices.items() if "español" in k.lower() or "es-" in k.lower()}
            if spanish_voices:
                voice_id = list(spanish_voices.keys())[0]
            else:
                voice_id = list(voices.keys())[0]
            display_name = voice_id  # En algunos casos el diccionario ya tiene el display_name como clave
            # Obtener el display_name real
            vm = VoiceManager()
            real_display = vm.get_voice_display_name(provider, voice_id)
            self.on_voice_selected(voice_id, provider, real_display)
            logger.info(f"Voz por defecto establecida: {real_display}")

    def open_voice_selector(self):
        current_provider = self.app.config.get("tts_provider", "edge")
        current_voice = self.selected_voice
        from ui.dialogs.voice_selector import VoiceSelectorDialog
        VoiceSelectorDialog(self, current_voice, current_provider,
                            on_select=self.on_voice_selected)

    def on_voice_selected(self, voice_id, provider, display_name):
        """Callback cuando se selecciona una voz en el diálogo."""
        self.selected_voice = voice_id
        self.selected_provider = provider
        self.selected_voice_display = display_name

        # Actualizar el botón
        self.voice_button.configure(text=display_name, fg_color=st.COLOR_ACCENT)

        # Habilitar el botón de escuchar si hay texto
        text = self.script_editor.get("1.0", "end-1c").strip()
        if len(text) > 5:
            self.btn_listen.configure(state="normal")

        logger.info(f"Voz seleccionada en frame: {voice_id} ({display_name}) para proveedor {provider}")

    def play_script_audio(self):
        if not self.selected_voice:
            # Intentar establecer una por defecto si no hay
            self.set_default_voice()
            if not self.selected_voice:
                messagebox.showwarning("Aviso", "Primero selecciona una voz (clic en 'Seleccionar voz').")
                return

        text = self.script_editor.get("1.0", "end-1c").strip()
        if len(text) < 5:
            messagebox.showwarning("Aviso", "No hay texto para narrar.")
            return

        # Obtener el código de voz adecuado para el proveedor actual
        provider = self.selected_provider or self.app.config.get("tts_provider", "edge")
        voice_code = self.app.tts.get_voice_code(self.selected_voice, "Todos")
        if not voice_code:
            voice_code = self.selected_voice  # Fallback

        self.btn_listen.configure(state="disabled", text="⏳ PROCESANDO...")
        self.after(0, lambda: self.lbl_tts_status.configure(text="🌐 Conectando con Neural Voices..."))

        def safe_ready_callback():
            self.after(0, self.on_audio_ready)

        self.app.tts.play_preview(text, voice_code, on_ready_callback=safe_ready_callback)


    def open_biblia_manager(self):
        serie = self.serie_entry.get().strip()
        if not serie:
            messagebox.showwarning("Aviso", "Primero ingresa el nombre de la serie.")
            return
        base_folder = self.app.config.get("base_folder", os.getcwd())
        serie_clean = clean_filename(serie)
        biblia_folder = os.path.join(base_folder, "PROYECTOS_NARRIVOX", serie_clean)
        os.makedirs(biblia_folder, exist_ok=True)
        BibliaManager(self, serie, biblia_folder)

    def update_stats(self, event=None):
        text = self.script_editor.get("1.0", "end-1c").strip()
        words = len(text.split())
        chars = len(text)
        minutes = words / 150
        time_str = f"{int(minutes)}:{int((minutes%1)*60):02d}"
        self.stats_label.configure(text=f"Palabras: {words} | Caracteres: {chars} | Duración est.: {time_str}")

    def run_ai_script(self):
        cards = self.app.frames["Inicio"].cards
        data = {
            "serie": self.serie_entry.get() or "S/N",
            "parte": self.parte_sel.get(),
            "tema": cards["TEMAS"].get_value(),
            "objeto": cards["OBJETOS"].get_value(),
            "anomalia": cards["ANOMALIAS"].get_value(),
            "emocion": cards["EMOCIONES"].get_value(),
            "tono": self.tone_sel.get(),
            "estructura": self.struct_sel.get(),
            "notas": self.script_notes.get("1.0", "end-1c")
        }

        context = ""
        serie = self.serie_entry.get().strip()
        if serie:
            base_folder = self.app.config.get("base_folder", os.getcwd())
            serie_clean = clean_filename(serie)
            biblia_path = os.path.join(base_folder, "PROYECTOS_NARRIVOX", serie_clean, "biblia_serie.json")
            if os.path.exists(biblia_path):
                try:
                    with open(biblia_path, encoding="utf-8") as f:
                        biblia = json.load(f)
                    context = (f"Contexto de la serie (Biblia):\n"
                               f"Descripción: {biblia.get('descripcion','')}\n"
                               f"Personajes: {biblia.get('personajes','')}\n"
                               f"Trama: {biblia.get('trama','')}\n"
                               f"Estilo: {biblia.get('estilo','')}\n\n")
                except Exception as e:
                    logger.error(f"Error cargando biblia: {e}")

        system_msg = "Eres un guionista experto en narrativa de misterio y ciencia ficción."
        if context:
            system_msg += "\n" + context

        user_prompt = self.app.ai.format_prompt(self.app.config.get("prompt_template", ""), data)

        self.btn_ai_gen.configure(state="disabled", text="Escribiendo...")
        self.ai_progress.pack(pady=5, fill="x", padx=10)  # Mostrar barra
        self.ai_progress.start()
        self.after(0, lambda: self.lbl_tts_status.configure(text="Generando guion con IA..."))

        def safe_callback(result, success, cancelled=False):
            self.after(0, lambda: self.on_ai_finish(result, success, cancelled))

        self.app.ai.generate_script_with_context(system_msg, user_prompt, safe_callback)

    def on_ai_finish(self, result, success, cancelled=False):
        self.ai_progress.stop()
        self.ai_progress.pack_forget()
        self.btn_ai_gen.configure(state="normal", text="✨ GENERAR GUION")
        self.lbl_tts_status.configure(text="")
        if cancelled:
            self.script_editor.delete("1.0", "end")
            self.script_editor.insert("1.0", "Generación cancelada por el usuario.\n")
            self.update_stats()
            return
        if not success:
            error_msg = translate_error(Exception(result), "generación de guion")
            messagebox.showerror("Error", error_msg, parent=self)
            return
        self.script_editor.delete("1.0", "end")
        self.script_editor.insert("1.0", result)
        self.update_stats()


    def on_audio_ready(self):
        self.btn_listen.configure(state="normal", text="🔊 ESCUCHAR")
        self.lbl_tts_status.configure(text="▶ Reproduciendo narración...")
        self.after(5000, lambda: self.lbl_tts_status.configure(text=""))

    def send_to_visual(self):
        script = self.script_editor.get("1.0", "end-1c").strip()
        if len(script) > 10:
            # Ahora enviamos al Generador de Arte
            self.app.show_image_generator()
        else:
            messagebox.showwarning("Aviso", "No hay guion para enviar.")

    def launch_prompter(self):
        text = self.script_editor.get("1.0", "end-1c").strip()
        if len(text) > 10:
            from ui.dialogs.teleprompter import TeleprompterWindow
            TeleprompterWindow(self, text)
        else:
            messagebox.showwarning("Aviso", "No hay texto para el teleprompter.")

    def master_save(self):
        try:
            serie = self.serie_entry.get().strip()
            parte = self.parte_sel.get()
            script = self.script_editor.get("1.0", "end-1c").strip()
            if not serie or len(script) < 10:
                messagebox.showwarning("Error", "Falta nombre de serie o guion.")
                return

            visual_frame = self.app.frames.get("Director Visual")
            prompts = visual_frame.get_prompts() if visual_frame else ""
            folder = self.app.data.create_project_folder(serie, parte)

            txt_ok = self.app.data.export_text_files(folder, serie, parte, script, prompts)
            pdf_ok = self.app.data.export_pdf(folder, serie, parte, script, self.app.config.get("user_name", "Productor"))

            s_clean = clean_filename(serie)  # Usamos la función importada
            audio_path = os.path.join(folder, f"Narracion_{s_clean}_P{parte}.mp3")
            srt_content = ""
            audio_ok = False
            srt_ok = False
            try:
                if not self.selected_voice:
                    raise Exception("No hay voz seleccionada")
                voice_code = self.app.tts.get_voice_code(self.selected_voice, "Todos")
                if not voice_code:
                    voice_code = "es-MX-JorgeNeural"

                # Generar audio con mezcla
                temp_narration = os.path.join(folder, f"Narracion_temp_{s_clean}_P{parte}.mp3")
                srt_content = self.app.tts.generate_audio(script, temp_narration, voice_code)
                if os.path.exists(temp_narration):
                    emotion = self.app.frames["Inicio"].cards["EMOCIONES"].get_value()
                    final_audio_path = os.path.join(folder, f"Narracion_{s_clean}_P{parte}.mp3")
                    mixed = self.app.sound.generate_soundtrack(temp_narration, emotion, output_path=final_audio_path)
                    if mixed:
                        audio_ok = True
                        os.remove(temp_narration)
                    else:
                        os.rename(temp_narration, final_audio_path)
                        audio_ok = True

                else:
                    audio_ok = False
                srt_ok = self.app.data.export_subtitles(folder, serie, parte, srt_content) if srt_content else False
            except Exception as e:
                logger.error(f"Error generando audio: {e}")
                messagebox.showwarning("Audio", f"No se pudo generar el audio: {e}")

            img_ok = False
            if visual_frame and hasattr(visual_frame, 'last_img_bytes') and visual_frame.last_img_bytes:
                img_ok = self.app.data.save_image(visual_frame.last_img_bytes, folder, serie, parte)

            excel_data = {
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Serie": serie,
                "Parte": int(parte),
                "Tema": self.app.frames["Inicio"].cards["TEMAS"].get_value(),
                "Objeto": self.app.frames["Inicio"].cards["OBJETOS"].get_value(),
                "Anomalía": self.app.frames["Inicio"].cards["ANOMALIAS"].get_value(),
                "Emoción": self.app.frames["Inicio"].cards["EMOCIONES"].get_value(),
                "Tono": self.tone_sel.get(),
                "Estructura": self.struct_sel.get(),
                "Estado": "Pendiente",
                "Carpeta": folder
            }
            excel_ok = self.app.data.save_project(excel_data)
            
            # Actualizar proyecto actual en el orquestador para otros frames
            if hasattr(self.app, 'orchestrator'):
                self.app.orchestrator.current_project = excel_data

            results = {
                'txt': txt_ok,
                'pdf': pdf_ok,
                'audio': audio_ok,
                'srt': srt_ok,
                'img': img_ok,
                'excel': excel_ok
            }
            from ui.dialogs.save_success import SaveSuccessWindow
            SaveSuccessWindow(self.app, serie, parte, folder, results)

            if self.app.config.get("enable_marketing", True):
                try:
                    marketing_dir = os.path.join(folder, "marketing")
                    os.makedirs(marketing_dir, exist_ok=True)
                    emotion = self.app.frames["Inicio"].cards["EMOCIONES"].get_value()
                    self.app.marketing.generate_marketing_assets(
                        script, serie, int(parte), emotion, marketing_dir
                    )
                    logger.info("Assets de marketing generados.")
                except Exception as e:
                    logger.error(f"Error generando marketing: {e}")

            current = self.app.get_current_frame_name()
            if current == "Proyectos":
                self.app.frames["Proyectos"].refresh_proyectos()
        except Exception as e:
            from src.error_handling import handle_error
            handle_error(e, "guardar proyecto", self)
