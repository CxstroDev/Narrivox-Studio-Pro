# ui/frames/visual_frame.py
"""
RECREACIÓN INTEGRAL: Editor de Video Profesional Narrivox.
Sustituye al antiguo gestor de storyboard por un editor multicanal.
"""

import os
import threading
import time
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from src.preview_engine import PreviewEngine
from src.utils import logger
from ui import styles as st

class TimelineTrack(ctk.CTkFrame):
    """Componente visual para una pista del timeline."""
    def __init__(self, parent, name, color, **kwargs):
        super().__init__(parent, height=60, fg_color=st.COLOR_BG, border_width=1, border_color=st.COLOR_BORDER, **kwargs)
        self.name = name
        self.color = color
        
        self.label_frame = ctk.CTkFrame(self, width=100, fg_color=st.COLOR_SIDEBAR)
        self.label_frame.pack(side="left", fill="y")
        
        self.label = ctk.CTkLabel(self.label_frame, text=name, font=("Segoe UI", 10, "bold"), anchor="w")
        self.label.pack(pady=15, padx=10)
        
        self.canvas = ctk.CTkCanvas(self, bg="#0f172a", # Fondo ultra oscuro para el canvas
                                     highlightthickness=0, height=50)
        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    def clear(self):
        self.canvas.delete("all")

    def draw_clip(self, start_time, duration, total_duration, label_text):
        if total_duration <= 0: return
        
        # Programar dibujo para cuando el widget esté listo
        self.after(100, lambda: self._execute_draw(start_time, duration, total_duration, label_text))

    def _execute_draw(self, start_time, duration, total_duration, label_text):
        w = self.canvas.winfo_width()
        if w <= 1: w = 800 
        
        x_start = (start_time / total_duration) * w
        width = (duration / total_duration) * w
        
        # Resolver color de CTk (tuple) a string de color real
        resolved_color = self._apply_appearance_mode(self.color)
        
        # Dibujar rectángulo del clip
        self.canvas.create_rectangle(x_start, 5, x_start + width, 45, 
                                     fill=resolved_color, outline="#ffffff", width=1, tags="clip")
        # Texto del clip
        txt = label_text if len(label_text) < 25 else label_text[:22] + "..."
        self.canvas.create_text(x_start + 5, 25, text=txt, anchor="w", 
                                fill="white", font=("Segoe UI", 8), tags="clip")

class VisualFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.preview_engine = PreviewEngine(app.config)
        
        self.current_time = 0.0
        self.total_duration = 10.0
        self.is_playing = False
        self.preview_ctk_image = None
        self.visual_clips = []
        
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=3) # Preview area
        self.grid_columnconfigure(1, weight=1) # Inspector/Assets
        self.grid_rowconfigure(0, weight=2)    # Top (Preview + Inspector)
        self.grid_rowconfigure(1, weight=1)    # Bottom (Timeline)

        # --- ÁREA SUPERIOR IZQUIERDA: VISOR ---
        self.preview_container = ctk.CTkFrame(self, fg_color=st.COLOR_CARD, corner_radius=15)
        self.preview_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.preview_label = ctk.CTkLabel(self.preview_container, text="🎥 PREVISUALIZACIÓN\n(Carga un proyecto para empezar)", 
                                          fg_color="#000000", corner_radius=10)
        self.preview_label.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Controles de transporte
        self.controls_frame = ctk.CTkFrame(self.preview_container, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.btn_play = ctk.CTkButton(self.controls_frame, text="▶ PLAY", width=100, command=self.toggle_play,
                                      fg_color=st.COLOR_ACCENT, hover_color=st.COLOR_ACCENT_HOVER)
        self.btn_play.pack(side="left", padx=5)
        
        self.seekbar = ctk.CTkSlider(self.controls_frame, from_=0, to=100, command=self.on_seek,
                                     button_color=st.COLOR_ACCENT, button_hover_color=st.COLOR_ACCENT_HOVER)
        self.seekbar.pack(side="left", fill="x", expand=True, padx=20)
        self.seekbar.set(0)
        
        self.lbl_time = ctk.CTkLabel(self.controls_frame, text="00:00 / 00:00", font=("Consolas", 12))
        self.lbl_time.pack(side="right", padx=10)

        # --- ÁREA SUPERIOR DERECHA: ASSETS / INSPECTOR ---
        self.right_panel = ctk.CTkTabview(self, fg_color=st.COLOR_CARD, corner_radius=15, 
                                          segmented_button_selected_color=st.COLOR_ACCENT)
        self.right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.right_panel.add("Activos")
        self.right_panel.add("Ajustes")
        
        # Lista de activos
        self.asset_list = ctk.CTkScrollableFrame(self.right_panel.tab("Activos"), fg_color="transparent")
        self.asset_list.pack(fill="both", expand=True)
        
        header_assets = ctk.CTkFrame(self.asset_list, fg_color="transparent")
        header_assets.pack(fill="x", pady=(5, 10))
        ctk.CTkLabel(header_assets, text="Recursos", font=("Segoe UI", 12, "bold"), 
                     text_color=st.COLOR_ACCENT).pack(side="left")
        ctk.CTkButton(header_assets, text="🔄", width=30, height=24, command=self.auto_load_current_project).pack(side="right")

        # --- ÁREA INFERIOR: LÍNEA DE TIEMPO ---
        self.timeline_container = ctk.CTkFrame(self, fg_color=st.COLOR_CARD, corner_radius=15)
        self.timeline_container.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")
        
        self.tl_header = ctk.CTkFrame(self.timeline_container, fg_color="transparent", height=40)
        self.tl_header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.tl_header, text="🎞️ LÍNEA DE TIEMPO", font=st.FONT_SUBTITLE, text_color=st.COLOR_ACCENT).pack(side="left")
        
        # Botones de acción del timeline
        ctk.CTkButton(self.tl_header, text="💾 Exportar Video", width=120, height=30, 
                      fg_color=st.COLOR_SUCCESS, command=self.export_final_video).pack(side="right", padx=5)
        
        # Pistas
        self.track_visual = TimelineTrack(self.timeline_container, "VISUAL", st.COLOR_ACCENT)
        self.track_visual.pack(fill="x", padx=10, pady=2)
        
        self.track_audio = TimelineTrack(self.timeline_container, "NARRACIÓN", st.COLOR_SUCCESS)
        self.track_audio.pack(fill="x", padx=10, pady=2)
        
        self.track_music = TimelineTrack(self.timeline_container, "MÚSICA", "#9b59b6")
        self.track_music.pack(fill="x", padx=10, pady=2)

    def toggle_play(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.configure(text="⏸ PAUSA", fg_color="#e67e22")
            threading.Thread(target=self._play_loop, daemon=True).start()
        else:
            self.btn_play.configure(text="▶ PLAY", fg_color=st.COLOR_ACCENT)

    def _play_loop(self):
        while self.is_playing:
            start_time = time.time()
            self.current_time += 0.1
            if self.current_time >= self.total_duration:
                self.current_time = self.total_duration
                self.is_playing = False
                self.after(0, lambda: self.btn_play.configure(text="▶ PLAY", fg_color=st.COLOR_ACCENT))
                self.after(0, self.update_ui_from_time)
                break
            
            self.after(0, self.update_ui_from_time)
            sleep_time = max(0, 0.1 - (time.time() - start_time))
            time.sleep(sleep_time)

    def update_ui_from_time(self):
        if self.total_duration <= 0: return
        self.seekbar.set((self.current_time / self.total_duration) * 100)
        mins = int(self.current_time // 60)
        secs = int(self.current_time % 60)
        total_mins = int(self.total_duration // 60)
        total_secs = int(self.total_duration % 60)
        self.lbl_time.configure(text=f"{mins:02}:{secs:02} / {total_mins:02}:{total_secs:02}")
        
        # Actualizar visor
        frame = self.preview_engine.get_frame(self.current_time)
        if frame:
            self.preview_ctk_image = ctk.CTkImage(light_image=frame, dark_image=frame, size=(640, 360))
            self.preview_label.configure(image=self.preview_ctk_image, text="")

    def on_seek(self, value):
        self.current_time = (float(value) / 100.0) * self.total_duration
        self.update_ui_from_time()

    def on_show(self):
        logger.info("Editor Profesional visualizado")
        self.auto_load_current_project()

    def set_script(self, script):
        self.auto_load_current_project()

    def auto_load_current_project(self):
        """Carga activos automáticamente desde el contexto actual."""
        try:
            serie, parte = self._get_context()
            if not serie:
                return

            folder = self.app.data.create_project_folder(serie, parte)
            if not os.path.exists(folder):
                return

            # Limpiar
            self.track_visual.clear()
            self.track_audio.clear()
            self.visual_clips = []
            for w in self.asset_list.winfo_children():
                if isinstance(w, ctk.CTkButton): w.destroy()

            # Descubrir
            files = os.listdir(folder)
            audio_path = next((os.path.join(folder, f) for f in files if f.endswith(".mp3") and ("Narracion" in f or "temp" in f)), None)
            images = [os.path.join(folder, f) for f in files if f.lower().endswith((".jpg", ".png", ".jpeg"))]
            images.sort() # Asegurar orden

            # Procesar Audio
            if audio_path:
                try:
                    from moviepy import AudioFileClip
                    a = AudioFileClip(audio_path)
                    self.total_duration = a.duration
                    a.close()
                    self.track_audio.draw_clip(0, self.total_duration, self.total_duration, os.path.basename(audio_path))
                    self._add_asset_button(audio_path, "🎵")
                except: pass

            # Procesar Visuales
            if images:
                clip_dur = self.total_duration / len(images) if self.total_duration > 0 else 5.0
                if self.total_duration <= 0: self.total_duration = len(images) * 5.0
                
                for i, img_path in enumerate(images):
                    start = i * clip_dur
                    self.visual_clips.append({'path': img_path, 'start': start, 'end': start + clip_dur, 'type': 'image'})
                    self.track_visual.draw_clip(start, clip_dur, self.total_duration, os.path.basename(img_path))
                    self._add_asset_button(img_path, "🖼️")

            # Finalizar
            if self.visual_clips:
                self.preview_engine.update_composition(self.visual_clips, [], self.total_duration)
                self.update_ui_from_time()
                logger.info(f"Editor cargado: {serie} P{parte} ({len(images)} imágenes)")

        except Exception as e:
            logger.error(f"Error cargando proyecto en editor: {e}")

    def _get_context(self):
        """Busca el nombre de serie y parte en el orquestador o guionista."""
        orch = getattr(self.app, 'orchestrator', None)
        if orch and orch.current_project:
            return orch.current_project.get("Serie", ""), str(orch.current_project.get("Parte", "1"))
        
        guionista = self.app.frames.get("Guionista")
        if guionista:
            return guionista.serie_entry.get().strip(), str(guionista.parte_sel.get())
        
        return None, None

    def _add_asset_button(self, path, icon):
        btn = ctk.CTkButton(self.asset_list, text=f"{icon} {os.path.basename(path)}", 
                            anchor="w", fg_color="transparent", text_color=st.COLOR_TEXT,
                            font=st.FONT_BODY_SMALL, height=28,
                            command=lambda p=path: os.startfile(p))
        btn.pack(fill="x", padx=5, pady=2)

    def export_final_video(self):
        messagebox.showinfo("Exportar", "Funcionalidad de exportación final en desarrollo.")

    def get_prompts(self): return ""
