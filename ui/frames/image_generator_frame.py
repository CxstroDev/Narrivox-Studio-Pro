# ui/frames/image_generator_frame.py
import os
import threading
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image
try:
    from plyer import notification
except ImportError:
    # Las notificaciones de escritorio son opcionales.
    notification = None

from src.utils import logger
from ui import styles as st

class ImageGeneratorFrame(ctk.CTkFrame):
    """Suite de generación de imágenes por lotes con contexto del guionista."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.current_context = {}
        
        self._setup_ui()

    def _setup_ui(self):
        # Título y Estado de Contexto
        header = ctk.CTkFrame(self, fg_color=st.COLOR_CARD, corner_radius=15)
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text="🎨 GENERADOR DE ARTE", 
                    font=st.FONT_TITLE, text_color=st.COLOR_ACCENT).pack(side="left", padx=20, pady=15)
        
        self.context_lbl = ctk.CTkLabel(header, text="Contexto: Ninguno (Sincroniza con Guionista)", 
                                        font=st.FONT_BODY_SMALL, text_color=st.COLOR_TEXT_DIM)
        self.context_lbl.pack(side="right", padx=20)

        # Contenedor Principal (2 columnas)
        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.pack(fill="both", expand=True)

        # Columna Izquierda: Configuración
        config_panel = ctk.CTkFrame(main_split, width=320, fg_color=st.COLOR_CARD, corner_radius=15)
        config_panel.pack(side="left", fill="y", padx=(0, 15))

        ctk.CTkLabel(config_panel, text="⚙️ CONFIGURACIÓN", font=st.FONT_SUBTITLE).pack(pady=15)

        # Estilo Visual
        ctk.CTkLabel(config_panel, text="Estilo Visual:", font=st.FONT_LABEL_SMALL).pack(anchor="w", padx=20)
        self.style_sel = ctk.CTkComboBox(config_panel, values=["Cinemático", "Fotorrealista", "Anime", "Cyberpunk", "Óleo", "3D Render"], width=240)
        self.style_sel.pack(pady=(5, 15), padx=20)
        self.style_sel.set("Cinemático")

        # Rango de Partes
        ctk.CTkLabel(config_panel, text="Generar para partes (ej: 1-5):", font=st.FONT_LABEL_SMALL).pack(anchor="w", padx=20)
        self.parts_entry = ctk.CTkEntry(config_panel, placeholder_text="1-5", width=240)
        self.parts_entry.pack(pady=(5, 15), padx=20)
        self.parts_entry.insert(0, "1")

        # Proveedor
        ctk.CTkLabel(config_panel, text="Proveedor IA:", font=st.FONT_LABEL_SMALL).pack(anchor="w", padx=20)
        self.provider_sel = ctk.CTkComboBox(config_panel, values=["pollinations", "zimage", "huggingface", "local", "cloudflare", "puter"], 
                                            width=240, command=self._on_provider_changed)
        self.provider_sel.pack(pady=(5, 10), padx=20)
        self.provider_sel.set(self.app.config.get("image_provider", "pollinations"))

        # Modelo (Dinámico)
        ctk.CTkLabel(config_panel, text="Modelo Específico:", font=st.FONT_LABEL_SMALL).pack(anchor="w", padx=20)
        self.model_sel = ctk.CTkComboBox(config_panel, values=[], width=240)
        self.model_sel.pack(pady=(5, 15), padx=20)
        
        self._update_model_list()

        # Prompt Adicional
        ctk.CTkLabel(config_panel, text="Instrucciones extra (opcional):", font=st.FONT_LABEL_SMALL).pack(anchor="w", padx=20)
        self.extra_prompt = ctk.CTkTextbox(config_panel, height=80, width=240, fg_color=st.COLOR_FG_BOX)
        self.extra_prompt.pack(pady=(5, 5), padx=20)

        # Botón Refinar Prompt
        self.refine_btn = ctk.CTkButton(config_panel, text="✨ OPTIMIZAR PROMPT CON IA", height=32, 
                                        fg_color=st.COLOR_ACCENT, font=("Segoe UI", 10, "bold"),
                                        command=self.refine_prompt_with_ai)
        self.refine_btn.pack(fill="x", padx=20, pady=(0, 20))

        # Botón Generar
        self.gen_btn = ctk.CTkButton(config_panel, text="🚀 GENERAR LOTE", height=45, fg_color=st.COLOR_IA,
                                     font=st.FONT_BUTTON, command=self.start_batch_generation)
        self.gen_btn.pack(fill="x", padx=20, pady=10)
        
        # Barra de Progreso
        self.progress_bar = ctk.CTkProgressBar(config_panel, width=240, height=10)
        self.progress_bar.pack(pady=10, padx=20)
        self.progress_bar.set(0)
        
        self.status_lbl = ctk.CTkLabel(config_panel, text="Listo para generar", font=st.FONT_BODY_SMALL)
        self.status_lbl.pack(pady=5, padx=20)

        # Botones de Acción Extra
        action_frame = ctk.CTkFrame(config_panel, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=10)

        self.save_btn = ctk.CTkButton(action_frame, text="💾 GUARDAR", width=115, height=35, 
                                      fg_color=st.COLOR_SUCCESS, command=self.save_generator_state)
        self.save_btn.pack(side="left", padx=(0, 5))

        self.editor_btn = ctk.CTkButton(action_frame, text="🎬 AL EDITOR", width=115, height=35,
                                        fg_color=st.COLOR_ACCENT, command=lambda: self.app.show_visual())
        self.editor_btn.pack(side="right", padx=(5, 0))

        # Columna Derecha: Galería
        self.gallery_frame = ctk.CTkScrollableFrame(main_split, fg_color=st.COLOR_CARD, corner_radius=15)
        self.gallery_frame.pack(side="right", fill="both", expand=True)
        
        self.gallery_label = ctk.CTkLabel(self.gallery_frame, text="Los resultados aparecerán aquí...", 
                                          font=st.FONT_BODY, text_color=st.COLOR_TEXT_DIM)
        self.gallery_label.pack(pady=100)

    def _on_provider_changed(self, provider):
        self._update_model_list()
        self._on_config_changed()

    def _update_model_list(self):
        provider = self.provider_sel.get()
        models = []
        
        if provider == "huggingface":
            models = ["stabilityai/stable-diffusion-xl-base-1.0", "black-forest-labs/FLUX.1-schnell", "runwayml/stable-diffusion-v1-5"]
            current = self.app.config.get("hf_model_id")
        elif provider == "pollinations":
            models = ["flux", "turbo", "unity", "deliberate"]
            current = self.app.config.get("pollinations_model", "flux")
        elif provider == "local":
            # Obtener instalados de forma segura
            local_cfg = self.app.config.get("local_providers", {}).get("image", {})
            models = list(local_cfg.get("installed", {}).keys())
            if not models: models = ["(No instalados)"]
            current = local_cfg.get("selected_model")
        else: # zimage
            models = ["Default Space"]
            current = "Default Space"

        self.model_sel.configure(values=models)
        if current in models:
            self.model_sel.set(current)
        elif models:
            self.model_sel.set(models[0])

    def _on_config_changed(self, event=None):
        # Método placeholder por compatibilidad si es necesario
        pass

    def on_show(self):
        """Sincroniza automáticamente con el guionista al entrar."""
        self.sync_with_guionista()

    def sync_with_guionista(self):
        guionista = self.app.frames.get("Guionista")
        if guionista:
            serie = guionista.serie_entry.get().strip()
            # Obtener valores de las tarjetas de inicio de forma segura
            inicio = self.app.frames.get("Inicio")
            tema = inicio.cards["TEMAS"].get_value() if inicio else "General"
            emocion = inicio.cards["EMOCIONES"].get_value() if inicio else "Neutral"
            
            self.current_context = {
                "serie": serie or "Sin Nombre",
                "tema": tema,
                "emocion": emocion,
                "guion": guionista.script_editor.get("1.0", "end-1c").strip()
            }
            self.context_lbl.configure(text=f"Serie: {self.current_context['serie']} | {self.current_context['tema']}")
            
            # Pestaña "Arte" empuja contexto al orquestador para el Editor
            if hasattr(self.app, 'orchestrator'):
                self.app.orchestrator.current_project = {
                    "Serie": self.current_context['serie'],
                    "Parte": self.parts_entry.get().split('-')[0] or "1",
                    "Tema": tema,
                    "Emoción": emocion
                }
            
            logger.info("Generador de Imágenes sincronizado y contexto global actualizado")

    def refine_prompt_with_ai(self):
        """Genera un prompt visual detallado usando IA basado en el guion y tema."""
        if not self.current_context.get("serie"):
            messagebox.showwarning("Aviso", "No hay contexto de serie. Sincroniza con el Guionista primero.")
            return

        self.refine_btn.configure(state="disabled", text="✨ PENSANDO...")
        
        system_msg = (
            "Eres un experto en ingeniería de prompts para Stable Diffusion y Midjourney. "
            "Tu tarea es crear una descripción visual altamente detallada y profesional "
            "para una portada de serie basada en el guion proporcionado. "
            "Responde ÚNICAMENTE con el prompt optimizado en inglés para mejores resultados en IA visual. "
            "Evita textos explicativos, solo entrega el prompt visual."
        )
        
        user_msg = (
            f"Serie: {self.current_context['serie']}\n"
            f"Tema: {self.current_context['tema']}\n"
            f"Emoción: {self.current_context['emocion']}\n"
            f"Estilo deseado: {self.style_sel.get()}\n"
            f"Fragmento del guion: {self.current_context['guion'][:1000]}"
        )

        def callback(result, success, cancelled=False):
            self.after(0, lambda: self._on_refine_finish(result, success))

        self.app.ai.generate_script_with_context(system_msg, user_msg, callback)

    def _on_refine_finish(self, result, success):
        self.refine_btn.configure(state="normal", text="✨ OPTIMIZAR PROMPT CON IA")
        if success:
            self.extra_prompt.delete("1.0", "end")
            self.extra_prompt.insert("1.0", result.strip())
            logger.info("Visual Prompt optimizado con IA")
        else:
            messagebox.showerror("Error", "No se pudo optimizar el prompt.")

    def start_batch_generation(self):
        try:
            parts_str = self.parts_entry.get().strip()
            if "-" in parts_str:
                start, end = map(int, parts_str.split("-"))
                parts = list(range(start, end + 1))
            else:
                parts = [int(parts_str)]
        except:
            messagebox.showerror("Error", "Formato de partes inválido. Usa '1' o '1-5'")
            return

        self.gen_btn.configure(state="disabled", text="Generando...")
        # Limpiar galería
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()

        threading.Thread(target=self._batch_worker, args=(parts,), daemon=True).start()

    def _batch_worker(self, parts):
        import time
        style = self.style_sel.get()
        extra_base = self.extra_prompt.get("1.0", "end-1c").strip()
        provider = self.provider_sel.get()
        
        # Lista de modelos para rotar si el proveedor es pollinations
        pollinations_models = ["flux", "turbo", "unity", "deliberate"]
        current_model_idx = 0
        
        total = len(parts)
        for i, part in enumerate(parts):
            # Rotación de modelo si es Pollinations
            if provider == "pollinations":
                model_id = pollinations_models[current_model_idx % len(pollinations_models)]
                current_model_idx += 1
            else:
                model_id = self.model_sel.get()

            # Actualizar progreso
            progress = (i) / total
            self.after(0, lambda p=progress, n=part: self._update_progress(p, f"Generando parte {n} con {model_id}..."))
            self.after(0, lambda p=part: self.add_placeholder(p))

            # Cada parte es una ejecución aislada
            try:
                logger.info(f"Iniciando generación aislada para Parte {part} con modelo {model_id}")
                
                self.app.image_engine.provider = provider
                
                # Paso 1: Generar Prompt
                current_prompt = extra_base
                if len(extra_base) < 50:
                    prompt_ai = self._generate_part_specific_prompt(part, style, extra_base)
                    if prompt_ai: current_prompt = prompt_ai

                # Paso 2: Generar Imagen (bloqueante)
                img_result = [None]
                error_result = [None]
                done_event = threading.Event()

                def img_callback(img_bytes, success, error):
                    if success: img_result[0] = img_bytes
                    else: error_result[0] = error
                    done_event.set()

                self.app.image_engine.generate(current_prompt, model_id=model_id, callback=img_callback)
                if not done_event.wait(timeout=300):
                    raise Exception("Timeout en generación")
                
                if error_result[0]: raise Exception(error_result[0])
                
                # Paso 3: Guardar
                folder = self.app.data.create_project_folder(self.current_context['serie'], str(part))
                if self.app.data.save_image(img_result[0], folder, self.current_context['serie'], str(part)):
                    s_clean = self.app.data.clean_filename(self.current_context['serie'])
                    path = os.path.join(folder, f"Imagen_{s_clean}_P{part}.jpg")
                    self.after(0, lambda p=path, num=part: self.update_gallery_image(p, num))

            except Exception as e:
                logger.error(f"Error fatal en parte {part}: {e}")
                self.after(0, lambda p=part: self.show_error_in_gallery(p))
            
            # Pausa obligatoria para resetear estado
            logger.info(f"Parte {part} finalizada. Esperando para la siguiente...")
            time.sleep(3)

        # Finalizar
        self.after(0, lambda: self._update_progress(1.0, "Generación completada"))
        self.after(0, lambda: self.gen_btn.configure(state="normal", text="🚀 GENERAR LOTE"))
        
        try:
            if notification is not None:
                notification.notify(title="Narrivox Studio Pro", message="Lote completado", timeout=5)
        except: pass

    def _update_progress(self, value, text):
        self.progress_bar.set(value)
        self.status_lbl.configure(text=text)

    def _generate_part_specific_prompt(self, part_num, style, base_notes):
        """Usa IA para obtener un prompt visual detallado para un capítulo específico."""
        import threading
        event = threading.Event()
        result_container = [None]

        def ai_callback(res, success, cancelled):
            if success:
                result_container[0] = res
            event.set()

        try:
            system_msg = "Eres un director de arte que crea prompts visuales para portadas de capítulos. Responde solo con el prompt en inglés."
            user_msg = (
                f"Create a professional visual prompt for Chapter {part_num} of the series '{self.current_context['serie']}'.\n"
                f"Theme: {self.current_context['tema']}. Emotion: {self.current_context['emocion']}.\n"
                f"Style: {style}. Notes: {base_notes}\n"
                f"The image must feel like a unique cover for this specific part while keeping series consistency."
            )
            
            # generate_script_with_context(system_msg, user_prompt, callback, ...)
            self.app.ai.generate_script_with_context(system_msg, user_msg, ai_callback)
            
            # Esperar a la IA (máximo 30s)
            if event.wait(timeout=30) and result_container[0]:
                return result_container[0].strip()
            return None
        except Exception as e:
            logger.warning(f"No se pudo generar prompt específico para parte {part_num}: {e}")
            return None

    def save_generator_state(self):
        """Guarda el estado actual de la serie para el editor y la base de datos."""
        if not self.current_context.get("serie"):
            messagebox.showwarning("Aviso", "No hay proyecto activo para guardar.")
            return

        # Registrar en el orquestador para sincronización global
        if hasattr(self.app, 'orchestrator'):
            # Convertir contexto a formato compatible con Orchestrator.current_project
            self.app.orchestrator.current_project = {
                "Serie": self.current_context['serie'],
                "Parte": self.parts_entry.get().split('-')[0] or "1", # Usamos la primera parte como referencia
                "Tema": self.current_context['tema'],
                "Emoción": self.current_context['emocion']
            }

        logger.info(f"Estado del Generador de Arte guardado para {self.current_context['serie']}")
        messagebox.showinfo("Éxito", f"Proyecto '{self.current_context['serie']}' vinculado. Ya puedes ir al Editor.")

    def add_placeholder(self, part_num):
        card = ctk.CTkFrame(self.gallery_frame, fg_color=st.COLOR_FG_BOX, height=200, corner_radius=10)
        card.pack(fill="x", padx=10, pady=5)
        card._part_num = part_num
        ctk.CTkLabel(card, text=f"Parte {part_num}: Generando...", font=st.FONT_LABEL).place(relx=0.5, rely=0.5, anchor="center")

    def update_gallery_image(self, path, part_num):
        for card in self.gallery_frame.winfo_children():
            if hasattr(card, "_part_num") and card._part_num == part_num:
                for w in card.winfo_children(): w.destroy()
                
                try:
                    img = Image.open(path)
                    # Thumbnail para preview
                    img.thumbnail((300, 200))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 140))
                    
                    lbl_img = ctk.CTkLabel(card, image=ctk_img, text="")
                    lbl_img.pack(side="left", padx=10, pady=10)
                    
                    info = ctk.CTkFrame(card, fg_color="transparent")
                    info.pack(side="left", fill="both", expand=True)
                    
                    ctk.CTkLabel(info, text=f"✅ Parte {part_num} lista", font=st.FONT_LABEL, text_color=st.COLOR_SUCCESS).pack(anchor="w", pady=(20, 0))
                    ctk.CTkLabel(info, text=os.path.basename(path), font=st.FONT_BODY_TINY, text_color=st.COLOR_TEXT_DIM).pack(anchor="w")
                    
                    # Botón para abrir carpeta
                    ctk.CTkButton(info, text="📂 Ver", width=60, height=24, fg_color=st.COLOR_INFO,
                                  command=lambda p=path: os.startfile(os.path.dirname(p))).pack(anchor="w", pady=5)
                except Exception as e:
                    logger.error(f"Error cargando preview {part_num}: {e}")
                    ctk.CTkLabel(card, text=f"Error cargando preview Parte {part_num}").pack()

    def show_error_in_gallery(self, part_num):
        for card in self.gallery_frame.winfo_children():
            if hasattr(card, "_part_num") and card._part_num == part_num:
                for w in card.winfo_children(): w.destroy()
                ctk.CTkLabel(card, text=f"❌ Error en Parte {part_num}", text_color=st.COLOR_ERROR).pack(pady=20)
