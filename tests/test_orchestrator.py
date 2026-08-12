import pytest
import threading
from src.orchestrator import Orchestrator

@pytest.fixture
def mock_ai(mocker):
    return mocker.Mock()

@pytest.fixture
def mock_tts(mocker):
    return mocker.Mock()

@pytest.fixture
def mock_image(mocker):
    return mocker.Mock()

@pytest.fixture
def mock_cinematic(mocker):
    return mocker.Mock()

@pytest.fixture
def orchestrator(mock_config, mock_ai, mock_tts, data_manager, mock_image, mock_cinematic):
    return Orchestrator(mock_config, mock_ai, mock_tts, data_manager, 
                        image_engine=mock_image, cinematic_engine=mock_cinematic)

def test_orchestrator_chapter_flow(orchestrator, mock_ai, mock_tts, mock_image, data_manager, mocker):
    """Prueba el flujo completo de un capítulo en el orquestador."""
    
    # 1. Simular éxito en IA (Guion)
    def mock_gen_script(sys, user, callback, **kwargs):
        callback("Guion orquestado", True, False)
    mock_ai.generate_script_with_context.side_effect = mock_gen_script
    
    # 2. Simular éxito en TTS
    mock_tts.generate_audio.return_value = "SRT Content Mock"
    mock_tts.get_voice_code.return_value = "es-ES-Mock"
    
    # 3. Simular éxito en Imagen
    mock_image.generate.return_value = b"Fake Image Bytes"
    
    # Datos de entrada
    serie = "Serie Orquestada"
    context = {"tema": "Misterio", "objeto": "Llave"}
    
    # Ejecutar (usamos 1 parte)
    results = orchestrator.generate_series(serie, 1, context, voice_name="es-ES-Alvaro", emotion="Misterio")
    
    # Verificaciones
    assert len(results) == 1
    assert results[0]["success"] is True
    assert results[0]["script"] == "Guion orquestado"
    
    # Verificar persistencia
    projects = data_manager.get_projects_by_serie(serie)
    assert len(projects) == 1
    assert projects[0]["serie"] == serie

def test_orchestrator_chapter_failure_script(orchestrator, mock_ai):
    """Prueba que el orquestador maneja fallos en el guion."""
    def mock_gen_script(sys, user, callback, **kwargs):
        callback("Error de IA", False, False)
    mock_ai.generate_script_with_context.side_effect = mock_gen_script
    
    results = orchestrator.generate_series("Fallo", 1, {}, voice_name="es-ES-Alvaro", emotion="Misterio")
    assert len(results) == 1
    assert results[0]["success"] is False
    assert "Fallo en generación de guion" in results[0]["error"]

def test_orchestrator_chapter_failure_audio(orchestrator, mock_ai, mock_tts):
    """Prueba que el orquestador maneja fallos en el audio."""
    def mock_gen_script(sys, user, callback, **kwargs):
        callback("Guion OK", True, False)
    mock_ai.generate_script_with_context.side_effect = mock_gen_script
    
    mock_tts.generate_audio.side_effect = Exception("TTS Error")
    mock_tts.get_voice_code.return_value = "voice_code"
    
    results = orchestrator.generate_series("FalloAudio", 1, {}, voice_name="es-ES-Alvaro", emotion="Misterio")
    assert len(results) == 1
    assert results[0]["success"] is False
    assert "TTS Error" in results[0]["error"]
