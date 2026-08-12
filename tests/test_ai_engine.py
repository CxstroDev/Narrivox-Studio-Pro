import pytest
from src.ai_engine import AIEngine

@pytest.fixture
def ai_engine(mock_config):
    """Instancia de AIEngine para pruebas."""
    return AIEngine(mock_config)

def test_format_prompt(ai_engine):
    """Verifica el formateo de prompts con variables."""
    template = "Escribe sobre {tema} con un {objeto}."
    data = {"tema": "misterio", "objeto": "libro"}
    formatted = ai_engine.format_prompt(template, data)
    assert formatted == "Escribe sobre misterio con un libro."

def test_generate_script_mock(ai_engine, mocker):
    """Prueba la generación de guion simulando un proveedor activo."""
    # Mockear el proveedor groq (que es el defecto en mock_config)
    mock_provider = mocker.Mock()
    ai_engine._providers["groq"] = mock_provider
    
    def side_effect(prompt, system_msg, callback, **kwargs):
        callback("Guion de prueba", True, False)
    mock_provider.generate.side_effect = side_effect
    
    # Usar un callback real para capturar resultado
    result_container = []
    def callback(res, success, cancelled):
        result_container.append(res)
        
    ai_engine.generate_script("Prompt de prueba", callback)
    # Como es síncrono en el mock pero AIEngine usa hilos, 
    # necesitamos esperar un momento o usar hilos en el mock.
    import time
    timeout = time.time() + 2
    while not result_container and time.time() < timeout:
        time.sleep(0.1)

    assert "Guion de prueba" in result_container

def test_fallback_logic(ai_engine, mocker):
    """Verifica que el sistema de fallback funcione cuando el primer proveedor falla."""
    import threading
    ai_engine.config["enable_fallback"] = True
    ai_engine.config["ai_fallback_chain"] = [
        {"provider": "groq", "model": "m1"},
        {"provider": "openai", "model": "m2"}
    ]
    
    # Mockear proveedores
    mock_groq = mocker.Mock()
    mock_openai = mocker.Mock()
    ai_engine._providers["groq"] = mock_groq
    ai_engine._providers["openai"] = mock_openai

    # Groq falla
    mock_groq.generate.side_effect = Exception("API Down")
    
    # OpenAI tiene éxito
    def openai_success(prompt, system_msg, callback, **kwargs):
        callback("Respuesta Exitosa", True, False)
    mock_openai.generate.side_effect = openai_success
    
    # Capturar callback con evento
    event = threading.Event()
    result_container = []
    def callback(res, success, cancelled):
        result_container.append(res)
        event.set()
    
    ai_engine.generate_script_with_context("system", "user", callback)
    
    assert event.wait(timeout=5)
    assert "Respuesta Exitosa" in result_container
