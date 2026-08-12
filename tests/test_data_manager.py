import pytest
import os
from src.data_manager import DataManager

def test_data_manager_init(data_manager, mock_config):
    """Verifica que el DataManager se inicialice y cree la DB."""
    assert os.path.exists(mock_config["db_path"])

def test_create_project_folder(data_manager):
    """Verifica la creación de carpetas de proyecto."""
    folder = data_manager.create_project_folder("Serie Test", "1")
    assert os.path.exists(folder)
    assert "Serie_Test" in folder
    assert "Parte_1" in folder

def test_save_and_load_timeline(data_manager):
    """Verifica la persistencia del timeline en la base de datos."""
    test_data = {"clips": [{"id": 1, "type": "image"}]}
    serie = "Serie Test"
    parte = 1
    
    # Guardar
    success = data_manager.save_timeline(serie, parte, test_data)
    assert success is True
    
    # Cargar
    loaded_data = data_manager.load_timeline(serie, parte)
    assert loaded_data == test_data

def test_save_project(data_manager):
    """Verifica el guardado de metadatos del proyecto."""
    project_data = {
        "Fecha": "2026-04-29 10:00",
        "Serie": "Serie Alpha",
        "Parte": 5,
        "Tema": "Terror",
        "Estado": "Pendiente"
    }
    success = data_manager.save_project(project_data)
    assert success is True
