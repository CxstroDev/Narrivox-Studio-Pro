# ui/main_window.py
import customtkinter as ctk
from src.ai_engine import AIEngine
from src.cinematic_engine import CinematicEngine
from src.config_manager import load_config
from src.data_manager import DataManager
from src.image_engine import ImageEngine
from src.marketing_engine import MarketingEngine
from src.model_manager import ModelManager
from src.orchestrator import Orchestrator
from src.sound_engine import SoundEngine
from src.tts_engine import TTSEngine

from ui import styles as st
from ui.frames.ajustes_frame import AjustesFrame
from ui.frames.explorador_frame import ExploradorFrame
from ui.frames.guionista_frame import GuionistaFrame
from ui.frames.video_director_frame import VideoDirectorFrame
from ui.frames.image_generator_frame import ImageGeneratorFrame
from ui.frames.proyectos_frame import ProyectosFrame


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Narrivox Studio Pro v14")
        self.geometry("1400x900") # Aumentado para mejor visualización del timeline
        self.minsize(1200, 800)
        self.configure(fg_color=st.COLOR_BG)

        
        self.config = load_config()
        self.ai = AIEngine(self.config)
        self.tts = TTSEngine(self.config)
        self.data = DataManager(self.config)
        self.image_engine = ImageEngine(self.config)
        self.cinematic = CinematicEngine(self.config)
        self.sound = SoundEngine(self.config)
        self.marketing = MarketingEngine(self.config, self.ai, self.image_engine)
        self.orchestrator = Orchestrator(self.config, self.ai, self.tts, self.data)
        self.model_manager = ModelManager(self.config)

        self.setup_ui()

    def setup_ui(self):
        # Sidebar mejorado con mejor espaciado y diseño
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=st.COLOR_SIDEBAR)
        self.sidebar.pack(side="left", fill="y")

        # Logo y título mejorados
        sidebar_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        sidebar_header.pack(fill="x", pady=(30, 20), padx=20)

        ctk.CTkLabel(sidebar_header, text="NARRIVOX", font=st.FONT_H1,
                     text_color=st.COLOR_ACCENT).pack(anchor="w")
        ctk.CTkLabel(sidebar_header, text="Studio Pro", font=st.FONT_BODY_LARGE,
                     text_color=st.COLOR_TEXT_DIM).pack(anchor="w")

        # Separador
        ctk.CTkFrame(self.sidebar, height=2, fg_color=st.COLOR_BORDER).pack(fill="x", padx=20, pady=(0, 20))

        # Botones de navegación mejorados
        self.nav_buttons = {}
        nav_items = [
            ("Inicio", st.ICONS["INICIO"], self.show_explorador),
            ("Guionista", st.ICONS["GUION"], self.show_guionista),
            ("Generador de Arte", st.ICONS["VISUAL"], self.show_image_generator),
            ("Editor de Video", st.ICONS["VIDEO"], self.show_visual),
            ("Proyectos", st.ICONS["LIB"], self.show_proyectos),
            ("Ajustes", st.ICONS["AJUSTES"], self.show_ajustes)
        ]

        for name, icon, cmd in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {name}",
                anchor="w",
                height=50,
                fg_color="transparent",
                hover_color=st.COLOR_ACCENT_LIGHT,
                text_color=st.COLOR_TEXT,
                font=st.FONT_BUTTON,
                corner_radius=st.RADIUS_MD,
                command=cmd
            )
            # Mejora de accesibilidad: El texto del botón ya es descriptivo, 
            # pero aseguramos que sea accesible para herramientas de inspección.
            btn.pack(fill="x", padx=15, pady=4)
            self.nav_buttons[name] = btn

        # Footer del sidebar con información de versión
        sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        sidebar_footer.pack(side="bottom", fill="x", pady=20, padx=20)

        ctk.CTkLabel(sidebar_footer, text="v14.0", font=st.FONT_BODY_SMALL,
                     text_color=st.COLOR_TEXT_DIM).pack(anchor="w")

        # Main content area mejorado
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(side="right", fill="both", expand=True, padx=24, pady=24)

        # Inicializar frames
        self.frames = {}
        self._current_frame_name = "Inicio"
        self.frames["Inicio"] = ExploradorFrame(self.main_content, self)
        self.frames["Guionista"] = GuionistaFrame(self.main_content, self)
        self.frames["Generador de Arte"] = ImageGeneratorFrame(self.main_content, self)
        self.frames["Director de Video"] = VideoDirectorFrame(self.main_content, self)
        self.frames["Proyectos"] = ProyectosFrame(self.main_content, self)
        self.frames["Ajustes"] = AjustesFrame(self.main_content, self)

        # Mostrar inicio
        self.show_explorador()

    def show_frame(self, name):
        self._current_frame_name = name
        
        # Mapeo para resaltar el botón correcto
        btn_map = {
            "Inicio": "Inicio",
            "Guionista": "Guionista",
            "Generador de Arte": "Generador de Arte",
            "Director de Video": "Editor de Video",
            "Proyectos": "Proyectos",
            "Ajustes": "Ajustes"
        }

        # Actualizar estado de botones de navegación
        for n, btn in self.nav_buttons.items():
            if btn_map.get(name) == n:
                # Estado activo
                btn.configure(
                    fg_color=st.COLOR_ACCENT,
                    hover_color=st.COLOR_ACCENT_HOVER,
                    text_color="#ffffff"
                )
            else:
                # Estado inactivo
                btn.configure(
                    fg_color="transparent",
                    hover_color=st.COLOR_ACCENT_LIGHT,
                    text_color=st.COLOR_TEXT
                )

        # Ocultar todos los frames y mostrar el seleccionado
        for f in self.frames.values():
            f.pack_forget()
        
        if name in self.frames:
            self.frames[name].pack(fill="both", expand=True)

            # Llamar al método on_show si existe
            if hasattr(self.frames[name], 'on_show'):
                self.frames[name].on_show()

    def show_explorador(self): self.show_frame("Inicio")
    def show_guionista(self): self.show_frame("Guionista")
    def show_image_generator(self): self.show_frame("Generador de Arte")
    def show_visual(self): self.show_frame("Director de Video")
    def show_ajustes(self): self.show_frame("Ajustes")

    def show_proyectos(self):
        if "Proyectos" in self.frames:
            self.frames["Proyectos"].refresh_proyectos()
        self.show_frame("Proyectos")

    def show_toast(self, message, duration=3000, bg_color=None, text_color=None):
        """Muestra un mensaje temporal mejorado en la parte inferior derecha."""
        # Usar colores del sistema de diseño si no se especifican
        toast_bg = bg_color if bg_color else st.COLOR_TEXT
        toast_text = text_color if text_color else st.COLOR_BG

        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(fg_color=toast_bg, corner_radius=st.RADIUS_LG)

        # Contenedor del mensaje
        container = ctk.CTkFrame(toast, fg_color="transparent")
        container.pack(padx=16, pady=12)

        # Icono y texto
        label = ctk.CTkLabel(
            container,
            text=f"{st.ICONS['INFO']}  {message}",
            text_color=toast_text,
            font=st.FONT_BODY
        )
        label.pack()

        # Posicionar en la esquina inferior derecha de la ventana principal
        try:
            self.update_idletasks()
            x = self.winfo_x() + self.winfo_width() - 320
            y = self.winfo_y() + self.winfo_height() - 100
            toast.geometry(f"+{x}+{y}")
        except:
            # Fallback para entornos sin GUI real
            pass

        toast.after(duration, toast.destroy)

    def guardar_desde_visual(self):
        if "Guionista" in self.frames:
            self.frames["Guionista"].master_save()

    def get_current_frame_name(self):
        return self._current_frame_name
