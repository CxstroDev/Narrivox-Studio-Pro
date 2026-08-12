import os
import pytest
from unittest.mock import MagicMock, patch
import customtkinter as ctk
from ui.main_window import MainWindow

# Verificar si hay display disponible
has_display = True
if os.name != 'nt': # En Linux/Mac check DISPLAY
    has_display = "DISPLAY" in os.environ
else:
    # En Windows es más difícil detectar headless sin intentar crear un widget,
    # así que permitiremos el intento pero saltaremos si falla el init.
    pass

@pytest.fixture
def app():
    # Mocking components that might trigger network or heavy E/S
    mock_config = {
        "directory": {
            "TEMAS": ["Sci-Fi"],
            "OBJETOS": ["Cápsula"],
            "ANOMALIAS": ["Glitch"],
            "EMOCIONES": ["Pavor"]
        },
        "tts_provider": "edge",
        "user_name": "Productor"
    }
    try:
        with patch('ui.main_window.load_config', return_value=mock_config), \
             patch('ui.main_window.AIEngine'), \
             patch('ui.main_window.TTSEngine'), \
             patch('ui.main_window.DataManager'), \
             patch('ui.main_window.ImageEngine'), \
             patch('ui.main_window.CinematicEngine'), \
             patch('ui.main_window.SoundEngine'), \
             patch('ui.main_window.MarketingEngine'), \
             patch('ui.main_window.Orchestrator'), \
             patch('ui.main_window.ModelManager'):
            
            # Para evitar problemas con Tcl/Tk en entornos sin GUI
            with patch('customtkinter.CTk.mainloop'), \
                 patch('customtkinter.CTk.update'):
                app = MainWindow()
                yield app
                app.destroy()
    except Exception as e:
        pytest.skip(f"Error al inicializar GUI: {e}")

@pytest.mark.skipif(not has_display, reason="Requiere entorno gráfico")
def test_main_window_init(app):
    assert app.title() == "Narrivox Studio Pro v14"
    assert "Inicio" in app.frames
    assert "Guionista" in app.frames

@pytest.mark.skipif(not has_display, reason="Requiere entorno gráfico")
def test_show_frame(app):
    app.show_frame("Guionista")
    assert app.get_current_frame_name() == "Guionista"

@pytest.mark.skipif(not has_display, reason="Requiere entorno gráfico")
def test_show_image_generator(app):
    app.show_image_generator()
    assert app.get_current_frame_name() == "Generador de Arte"

@pytest.mark.skipif(not has_display, reason="Requiere entorno gráfico")
def test_show_visual(app):
    app.show_visual()
    assert app.get_current_frame_name() == "Director Visual"

@pytest.mark.skipif(not has_display, reason="Requiere entorno gráfico")
def test_sidebar_buttons_exist(app):
    assert "Inicio" in app.nav_buttons
    assert "Guionista" in app.nav_buttons
    assert "Ajustes" in app.nav_buttons

@pytest.mark.skipif(not has_display, reason="Requiere entorno gráfico")
def test_show_toast(app):
    # This just ensures it doesn't crash
    app.show_toast("Test message")
