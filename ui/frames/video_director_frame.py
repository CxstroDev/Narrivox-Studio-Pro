# ui/frames/video_director_frame.py
import os
import subprocess
import sys
import threading
import time
from tkinter import filedialog, messagebox

import customtkinter as ctk
from src.utils import logger, open_folder

from ui import styles as st

# No importamos vlc globalmente para evitar errores de DLL
VLC_AVAILABLE = False
try:
    import vlc
    VLC_AVAILABLE = True
    del vlc  # Remove unused import
except (ImportError, FileNotFoundError, OSError):
    pass  # VLC no está disponible, usaremos reproductor del sistema


class VideoDirectorFrame(ctk.CTkFrame):
    """Editor de video profesional con interfaz intuitiva para crear videos narrativos."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.video_output_path = None
        self.is_initialized = False

        # Variables de estado
        self.current_project = None
        self.preview_image = None
        self.is_generating = False
        
        self.current_image_path = None
        self.current_audio_path = None
        self.current_srt_path = None
        self.video_output_path = None

        self._setup_ui()

    def _setup_ui(self):
        """Construye la interfaz de usuario del editor de video."""

        # Título principal
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(title_frame, text="🎬 ESTUDIO DE VIDEO",
                    font=st.FONT_TITLE).pack(side="left")

        # Botón de ayuda
        help_btn = ctk.CTkButton(title_frame, text="❓", width=30, height=30,
                                fg_color="transparent", text_color=st.COLOR_TEXT_DIM,
                                hover_color=st.COLOR_CARD, command=self.show_help)
        help_btn.pack(side="right")

        # Contenedor principal
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # Panel izquierdo: Herramientas de edición
        left_panel = self._create_left_panel(main_container)
        left_panel.pack(side="left", fill="y", padx=(0, 10), pady=10)

        # Panel central: Área de escenas y previsualización
        center_panel = self._create_center_panel(main_container)
        center_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Panel derecho: Configuración y exportación
        right_panel = self._create_right_panel(main_container)
        right_panel.pack(side="right", fill="y", padx=(10, 0), pady=10)

    def _create_left_panel(self, parent):
        """Crea el panel izquierdo con herramientas de edición."""
        panel = ctk.CTkFrame(parent, width=300, fg_color=st.COLOR_CARD, corner_radius=15)

        # Sección de materiales
        materials_section = ctk.CTkFrame(panel, fg_color="transparent")
        materials_section.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(materials_section, text="📦 MATERIALES",
                    font=st.FONT_SUBTITLE, text_color=st.COLOR_ACCENT).pack(anchor="w", pady=(0, 10))

        # Imagen principal
        self._create_material_selector(materials_section, "Imagen principal",
                                      "🖼️", "image", self.select_image)

        # Audio narración
        self._create_material_selector(materials_section, "Audio de narración",
                                      "🎙️", "audio", self.select_audio)

        # Botón cargar proyecto
        load_btn = ctk.CTkButton(materials_section, text="🔄 Cargar proyecto actual",
                                 fg_color=st.COLOR_ACCENT, height=35,
                                 command=self.load_current_project)
        load_btn.pack(fill="x", pady=(10, 0))

        # Separador
        ctk.CTkFrame(panel, height=2, fg_color=st.COLOR_BORDER).pack(fill="x", padx=15, pady=10)

        # Sección de Música
        music_section = ctk.CTkFrame(panel, fg_color="transparent")
        music_section.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(music_section, text="🎵 MÚSICA DE FONDO",
                    font=st.FONT_SUBTITLE, text_color=st.COLOR_ACCENT).pack(anchor="w", pady=(0, 10))

        self.music_category_var = ctk.StringVar(value="Misterio")
        music_combo = ctk.CTkComboBox(music_section, values=["Misterio", "Terror", "Épico", "Drama", "Acción", "Sci-Fi"],
                                     variable=self.music_category_var)
        music_combo.pack(fill="x", pady=(0, 5))

        self.custom_music_path = None
        self.music_file_label = ctk.CTkLabel(music_section, text="Auto-selección por categoría",
                                            font=("Segoe UI", 9), text_color=st.COLOR_TEXT_DIM)
        self.music_file_label.pack(anchor="w")

        pick_music_btn = ctk.CTkButton(music_section, text="📁 Elegir música propia", height=30,
                                      fg_color=st.COLOR_CARD_HOVER, command=self.select_custom_music)
        pick_music_btn.pack(fill="x", pady=(5, 0))

        # Separador
        ctk.CTkFrame(panel, height=2, fg_color=st.COLOR_BORDER).pack(fill="x", padx=15, pady=10)

        # Sección de efectos
        effects_section = ctk.CTkFrame(panel, fg_color="transparent")
        effects_section.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(effects_section, text="✨ EFECTOS VISUALES",
                    font=st.FONT_SUBTITLE, text_color=st.COLOR_ACCENT).pack(anchor="w", pady=(0, 10))

        # Efecto de movimiento
        self.ken_burns_var = ctk.BooleanVar(value=self.app.config.get("enable_ken_burns", True))
        ken_burns_check = ctk.CTkCheckBox(effects_section, text="Movimiento Ken Burns",
                                       variable=self.ken_burns_var)
        ken_burns_check.pack(anchor="w", pady=5)

        # Insertar escenas adicionales
        self.broll_var = ctk.BooleanVar(value=False)
        broll_check = ctk.CTkCheckBox(effects_section, text="Insertar B-Roll",
                                     variable=self.broll_var)
        broll_check.pack(anchor="w", pady=5)

        return panel

    def _create_material_selector(self, parent, label, icon, file_type, command):
        """Crea un selector de materiales para imágenes o audio."""
        selector_frame = ctk.CTkFrame(parent, fg_color="transparent")
        selector_frame.pack(fill="x", pady=5)

        # Icono y etiqueta
        icon_label = ctk.CTkLabel(selector_frame, text=icon, font=("Segoe UI", 14))
        icon_label.pack(side="left", padx=(0, 8))

        text_label = ctk.CTkLabel(selector_frame, text=label,
                                 font=st.FONT_BODY_SMALL, text_color=st.COLOR_TEXT)
        text_label.pack(side="left", fill="x", expand=True)

        # Botón de selección
        select_btn = ctk.CTkButton(selector_frame, text="📂", width=40,
                                  fg_color=st.COLOR_INFO, command=command)
        select_btn.pack(side="right")

        # Etiqueta del archivo seleccionado
        file_label = ctk.CTkLabel(selector_frame, text="Ningún archivo seleccionado",
                                 font=("Segoe UI", 9), text_color=st.COLOR_TEXT_DIM)
        file_label.pack(fill="x", pady=(5, 0))

        # Guardar referencia para actualización
        if file_type == "image":
            self.image_file_label = file_label
        elif file_type == "audio":
            self.audio_file_label = file_label

    def _create_center_panel(self, parent):
        """Crea el panel central con área de escenas y previsualización."""
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        # Área de previsualización (Superior)
        preview_container = ctk.CTkFrame(panel, fg_color=st.COLOR_CARD, corner_radius=15)
        preview_container.pack(fill="both", expand=True, pady=(0, 10))

        # Encabezado de previsualización
        preview_header = ctk.CTkFrame(preview_container, fg_color="transparent")
        preview_header.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(preview_header, text="👁️ MONITOR DE VIDEO",
                    font=st.FONT_SUBTITLE, text_color=st.COLOR_ACCENT).pack(side="left")

        # Controles de reproducción
        controls_frame = ctk.CTkFrame(preview_header, fg_color="transparent")
        controls_frame.pack(side="right")

        self.play_btn = ctk.CTkButton(controls_frame, text="▶️", width=40, height=30,
                                     fg_color=st.COLOR_SUCCESS, command=self.play_preview)
        self.play_btn.pack(side="left", padx=(0, 5))

        self.stop_btn = ctk.CTkButton(controls_frame, text="⏹️", width=40, height=30,
                                     fg_color=st.COLOR_ERROR, command=self.stop_preview)
        self.stop_btn.pack(side="left")

        # Área de previsualización
        self.preview_frame = ctk.CTkFrame(preview_container, fg_color="#000000", corner_radius=10)
        self.preview_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Etiqueta de previsualización
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Monitor de previsualización listo",
                                         font=st.FONT_BODY, text_color=st.COLOR_TEXT_DIM)
        self.preview_label.place(relx=0.5, rely=0.5, anchor="center")

        # Imagen de previsualización
        self.preview_image_label = ctk.CTkLabel(self.preview_frame, text="", fg_color="transparent")
        self.preview_image_label.place(relx=0.5, rely=0.5, anchor="center")

        # Área de escenas (Inferior - Timeline)
        scenes_container = ctk.CTkFrame(panel, fg_color=st.COLOR_CARD, corner_radius=15, height=200)
        scenes_container.pack(fill="x", pady=(10, 0))

        scenes_header = ctk.CTkFrame(scenes_container, fg_color="transparent")
        scenes_header.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(scenes_header, text="🎞️ ESCENAS DEL PROYECTO",
                    font=st.FONT_SUBTITLE, text_color=st.COLOR_ACCENT).pack(side="left")

        # Lista de escenas (scrollable)
        self.scenes_list_frame = ctk.CTkScrollableFrame(scenes_container, orientation="horizontal", 
                                                       fg_color=st.COLOR_CARD_HOVER, height=120)
        self.scenes_list_frame.pack(fill="x", padx=15, pady=(0, 15))

        return panel

    def _create_right_panel(self, parent):
        """Crea el panel derecho con configuración y exportación."""
        panel = ctk.CTkFrame(parent, width=280, fg_color=st.COLOR_CARD, corner_radius=15)

        # Sección de Calidad
        quality_section = ctk.CTkFrame(panel, fg_color="transparent")
        quality_section.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(quality_section, text="🎯 AJUSTES DE RENDER",
                    font=st.FONT_SUBTITLE, text_color=st.COLOR_ACCENT).pack(anchor="w", pady=(0, 10))

        self.quality_var = ctk.StringVar(value="Alta")
        self._create_quality_option(quality_section, "Calidad", ["Básica", "Estándar", "Alta", "Profesional"], self.quality_var)

        self.resolution_var = ctk.StringVar(value="Full HD (1080p)")
        self._create_quality_option(quality_section, "Resolución", ["HD (720p)", "Full HD (1080p)", "Ultra HD (4K)"], self.resolution_var)

        self.fps_var = ctk.StringVar(value="24 fps")
        self._create_quality_option(quality_section, "FPS", ["24 fps", "30 fps", "60 fps"], self.fps_var)

        # Separador
        ctk.CTkFrame(panel, height=2, fg_color=st.COLOR_BORDER).pack(fill="x", padx=15, pady=10)

        # Sección de Subtítulos
        subs_section = ctk.CTkFrame(panel, fg_color="transparent")
        subs_section.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(subs_section, text="🔡 SUBTÍTULOS",
                    font=st.FONT_SUBTITLE, text_color=st.COLOR_ACCENT).pack(anchor="w", pady=(0, 10))

        self.enable_subs_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(subs_section, text="Incrustar subtítulos", variable=self.enable_subs_var).pack(anchor="w", pady=5)

        # Estilo de subtítulos
        style_frame = ctk.CTkFrame(subs_section, fg_color="transparent")
        style_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(style_frame, text="Tamaño:", font=st.FONT_BODY_SMALL).pack(side="left")
        self.subs_size_var = ctk.StringVar(value="32")
        ctk.CTkComboBox(style_frame, values=["24", "28", "32", "36", "40", "48"], variable=self.subs_size_var, width=70).pack(side="right")

        # Carpeta de destino
        dest_frame = ctk.CTkFrame(panel, fg_color="transparent")
        dest_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(dest_frame, text="Carpeta destino:", font=st.FONT_BODY_SMALL).pack(anchor="w")
        self.dest_folder_var = ctk.StringVar(value=os.path.expanduser("~/Videos"))
        f_entry = ctk.CTkFrame(dest_frame, fg_color="transparent")
        f_entry.pack(fill="x")
        ctk.CTkEntry(f_entry, textvariable=self.dest_folder_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(f_entry, text="📁", width=30, command=self.browse_destination).pack(side="right")

        # Acciones Finales
        action_section = ctk.CTkFrame(panel, fg_color="transparent")
        action_section.pack(fill="x", padx=15, pady=15)

        # Progreo
        self.progress_bar = ctk.CTkProgressBar(action_section, height=10)
        self.progress_bar.pack(fill="x", pady=(0, 10))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(action_section, text="Listo para renderizar",
                                        font=("Segoe UI", 10), text_color=st.COLOR_TEXT_DIM)
        self.status_label.pack(anchor="w", pady=(0, 15))

        # Botones
        self.generate_btn = ctk.CTkButton(action_section, text="🎬 RENDERIZAR ESCENA", height=45,
                                         fg_color=st.COLOR_ACCENT, font=st.FONT_BUTTON,
                                         command=self.generate_video)
        self.generate_btn.pack(fill="x", pady=(0, 10))

        self.concat_btn = ctk.CTkButton(action_section, text="🎞️ UNIR TODAS LAS ESCENAS", height=40,
                                       fg_color=st.COLOR_SUCCESS, font=st.FONT_BUTTON,
                                       command=self.concatenate_all_scenes)
        self.concat_btn.pack(fill="x")

        return panel

    def _create_quality_option(self, parent, label, options, var):
        """Crea una opción de calidad con combobox."""
        option_frame = ctk.CTkFrame(parent, fg_color="transparent")
        option_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(option_frame, text=label + ":",
                    font=st.FONT_BODY_SMALL, text_color=st.COLOR_TEXT).pack(side="left")

        combobox = ctk.CTkComboBox(option_frame, values=options, variable=var, width=140)
        combobox.pack(side="right")

    def select_image(self):
        """Selecciona una imagen para el video."""
        filename = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.image_file_label.configure(text=os.path.basename(filename))
            self.current_image_path = filename
            self._update_preview_image(filename)

    def select_audio(self):
        """Selecciona un archivo de audio para la narración."""
        filename = filedialog.askopenfilename(
            title="Seleccionar audio",
            filetypes=[("Audio", "*.mp3 *.wav *.ogg *.m4a"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.audio_file_label.configure(text=os.path.basename(filename))
            self.current_audio_path = filename

    def select_custom_music(self):
        """Selecciona un archivo de música personalizado."""
        filename = filedialog.askopenfilename(
            title="Seleccionar música de fondo",
            filetypes=[("Audio", "*.mp3 *.wav *.ogg *.m4a"), ("Todos los archivos", "*.*")]
        )
        if filename:
            self.custom_music_path = filename
            self.music_file_label.configure(text=os.path.basename(filename), text_color=st.COLOR_SUCCESS)
            self.app.show_toast("Música personalizada seleccionada")

    def load_current_project(self):
        """Carga el proyecto actual de Narrivox y todas sus escenas."""
        try:
            orch = getattr(self.app, 'orchestrator', None)
            if orch and hasattr(orch, 'current_project') and orch.current_project:
                project = orch.current_project
                serie = project.get('serie')
                
                if not serie:
                    self._load_single_project(project)
                    return

                data_manager = getattr(self.app, 'data', None)
                if data_manager:
                    projects = data_manager.search_projects(serie)
                    serie_projects = [p for p in projects if p.get('Serie') == serie]
                    serie_projects.sort(key=lambda x: int(x.get('Parte', 0)))
                    
                    if serie_projects:
                        self.current_serie_projects = serie_projects
                        self._update_scenes_list(serie_projects)
                        self._load_single_project(serie_projects[0])
                        self.app.show_toast(f"Serie '{serie}' cargada: {len(serie_projects)} escenas")
                    else:
                        self._load_single_project(project)
                else:
                    self._load_single_project(project)
            else:
                messagebox.showinfo("Información", "No hay un proyecto activo en Narrivox.")
        except Exception as e:
            logger.error(f"Error cargando proyecto: {e}")
            messagebox.showerror("Error", f"No se pudo cargar el proyecto: {e}")

    def _load_single_project(self, project_data):
        """Carga los datos de un único proyecto/escena."""
        folder = project_data.get('Carpeta')
        
        image_path = project_data.get('image_path')
        if not image_path and folder:
            for f in os.listdir(folder):
                if f.startswith("Imagen_") and f.lower().endswith((".jpg", ".png", ".webp")):
                    image_path = os.path.join(folder, f)
                    break
        
        audio_path = project_data.get('audio_path')
        if not audio_path and folder:
            for f in os.listdir(folder):
                if f.startswith("Narracion_") and f.lower().endswith(".mp3"):
                    audio_path = os.path.join(folder, f)
                    break

        srt_path = project_data.get('srt_path')
        if not srt_path and folder:
            for f in os.listdir(folder):
                if f.startswith("Subtitulos_") and f.lower().endswith(".srt"):
                    srt_path = os.path.join(folder, f)
                    break

        if image_path:
            self.image_file_label.configure(text=os.path.basename(image_path))
            self.current_image_path = image_path
            self._update_preview_image(image_path)

        if audio_path:
            self.audio_file_label.configure(text=os.path.basename(audio_path))
            self.current_audio_path = audio_path

        self.current_srt_path = srt_path

    def _update_preview_image(self, image_path):
        """Actualiza la imagen en el monitor de previsualización."""
        try:
            from PIL import Image, ImageTk
            img = Image.open(image_path)
            monitor_w = self.preview_frame.winfo_width()
            monitor_h = self.preview_frame.winfo_height()
            if monitor_w < 100: monitor_w = 640
            if monitor_h < 100: monitor_h = 360
            
            img.thumbnail((monitor_w, monitor_h))
            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_image_label.configure(image=self.preview_image, text="")
            self.preview_label.configure(text="")
        except Exception as e:
            logger.error(f"Error actualizando imagen de previsualización: {e}")

    def _update_scenes_list(self, projects):
        """Actualiza la lista de escenas en el timeline."""
        for child in self.scenes_list_frame.winfo_children():
            child.destroy()

        for i, proj in enumerate(projects):
            scene_btn = ctk.CTkFrame(self.scenes_list_frame, fg_color=st.COLOR_CARD, 
                                    width=100, height=100, corner_radius=10)
            scene_btn.pack(side="left", padx=5, pady=5)
            
            ctk.CTkLabel(scene_btn, text=f"P{proj.get('Parte', i+1)}", 
                        font=("Segoe UI", 12, "bold"), text_color=st.COLOR_ACCENT).pack(pady=(5, 0))
            
            thumb = ctk.CTkFrame(scene_btn, fg_color=st.COLOR_CARD_HOVER, width=80, height=45)
            thumb.pack(padx=10, pady=5)
            
            select_btn = ctk.CTkButton(scene_btn, text="Ver", height=20, width=60,
                                      fg_color=st.COLOR_INFO, font=("Segoe UI", 9),
                                      command=lambda p=proj: self._load_single_project(p))
            select_btn.pack(pady=(0, 5))

    def play_preview(self):
        """Reproduce el audio de la escena actual."""
        if not self.current_audio_path: return
        try:
            if sys.platform == "win32":
                os.startfile(self.current_audio_path)
            else:
                subprocess.call(["open" if sys.platform == "darwin" else "xdg-open", self.current_audio_path])
        except: pass

    def stop_preview(self): pass

    def browse_destination(self):
        folder = filedialog.askdirectory()
        if folder: self.dest_folder_var.set(folder)

    def generate_video(self):
        if not self.current_image_path or not self.current_audio_path:
            messagebox.showerror("Error", "Faltan materiales base.")
            return
        self.generate_btn.configure(state="disabled", text="PROCESANDO...")
        threading.Thread(target=self._generate_video_thread, daemon=True).start()

    def _generate_video_thread(self):
        try:
            folder = os.path.dirname(self.current_image_path)
            output_path = os.path.join(folder, f"Scene_Render_{int(time.time())}.mp4")
            
            soundtrack = self.custom_music_path
            if not soundtrack:
                sound_engine = getattr(self.app, 'sound', None)
                if sound_engine:
                    soundtrack = sound_engine.selector.get_music_for_emotion(self.music_category_var.get())

            success = self.app.cinematic.assemble_dynamic_video(
                base_image_path=self.current_image_path,
                audio_path=self.current_audio_path,
                srt_path=getattr(self, 'current_srt_path', ""),
                output_path=output_path,
                use_ken_burns=self.ken_burns_var.get(),
                use_broll=self.broll_var.get(),
                quality=self.quality_var.get(),
                resolution=self.resolution_var.get().split('(')[1].split(')')[0],
                fps=int(self.fps_var.get().split()[0]),
                soundtrack_path=soundtrack
            )

            if success:
                self.app.show_toast("✅ Escena renderizada", bg_color=st.COLOR_SUCCESS)
            else:
                self.app.show_toast("❌ Error en render", bg_color=st.COLOR_ERROR)
        except Exception as e:
            logger.error(f"Error render: {e}")
        finally:
            self.after(0, lambda: self.generate_btn.configure(state="normal", text="🎬 RENDERIZAR ESCENA"))

    def concatenate_all_scenes(self):
        if not hasattr(self, 'current_serie_projects'): return
        video_paths = []
        for proj in self.current_serie_projects:
            folder = proj.get('Carpeta')
            if folder and os.path.exists(folder):
                for f in os.listdir(folder):
                    if f.startswith("Video_") and f.endswith(".mp4"):
                        video_paths.append(os.path.join(folder, f))
                        break
        if video_paths:
            threading.Thread(target=self._concatenate_thread, args=(video_paths,), daemon=True).start()

    def _concatenate_thread(self, video_paths):
        output_path = os.path.join(self.dest_folder_var.get(), f"Movie_{int(time.time())}.mp4")
        if self.app.cinematic.concatenate_chapters(video_paths, output_path):
            self.app.show_toast("✅ Película lista")
            open_folder(self.dest_folder_var.get())

    def show_help(self):
        messagebox.showinfo("Ayuda", "Editor de video para unir escenas y añadir música.")

    def on_show(self):
        self.load_current_project()
