import pytest
import os
import shutil
import tempfile
from src.data_manager import DataManager

@pytest.fixture
def temp_dir():
    """Crea un directorio temporal para pruebas."""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)

@pytest.fixture
def mock_config(temp_dir):
    """Configuración de prueba apuntando al directorio temporal."""
    return {
        "base_folder": temp_dir,
        "db_path": os.path.join(temp_dir, "test_narrivox.db")
    }

@pytest.fixture
def data_manager(mock_config):
    """Instancia de DataManager para pruebas."""
    dm = DataManager(mock_config)
    yield dm
    dm.close()
