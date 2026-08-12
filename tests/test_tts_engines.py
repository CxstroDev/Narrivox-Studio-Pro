import pytest
import os
import threading
from unittest.mock import MagicMock, patch, mock_open
from src.engines.tts.edge import EdgeTTSEngine
from src.engines.tts.elevenlabs import ElevenLabsTTSEngine
from src.engines.tts.unrealspeech import UnrealSpeechTTSEngine
from src.engines.tts.local import LocalTTSEngine
from src.exceptions import AudioGenerationError

@pytest.fixture
def tts_config():
    return {
        "elevenlabs_api_key": "test_eleven_key",
        "unrealspeech_api_key": "test_unreal_key",
        "elevenlabs_model_id": "eleven_multilingual_v2"
    }

class MockAudioInfo:
    def __init__(self, length):
        self.length = length

class MockMP3:
    def __init__(self, path):
        self.info = MockAudioInfo(10.0)

# Tests for EdgeTTSEngine
def test_edge_tts_load_voices():
    config = {}
    engine = EdgeTTSEngine(config)
    
    mock_voices = [
        {'ShortName': 'es-MX-JorgeNeural', 'Locale': 'es-MX', 'Gender': 'Male'},
        {'ShortName': 'en-US-GuyNeural', 'Locale': 'en-US', 'Gender': 'Male'}
    ]
    
    with patch('edge_tts.list_voices', return_value=mock_voices):
        # We need to mock _run_coroutine because it uses asyncio.run or similar
        with patch.object(EdgeTTSEngine, '_run_coroutine', return_value=mock_voices):
            # load_voices runs in a thread, so we'll wait for it or mock the thread
            with patch('threading.Thread') as mock_thread:
                engine.load_voices()
                # Simulate thread execution
                target = mock_thread.call_args[1]['target']
                target()
                
    assert "es-MX-JorgeNeural (es-MX, Male)" in engine.all_voices
    assert engine.all_voices["es-MX-JorgeNeural (es-MX, Male)"] == "es-MX-JorgeNeural"

def test_edge_tts_generate_audio(temp_dir):
    config = {}
    engine = EdgeTTSEngine(config)
    output_path = os.path.join(temp_dir, "test.mp3")
    
    mock_chunks = [
        {"type": "audio", "data": b"fake_audio"},
        {"type": "WordBoundary", "text": "hello", "offset": 0, "duration": 10**7}
    ]
    
    class MockCommunicate:
        def __init__(self, text, voice): pass
        async def stream(self):
            for chunk in mock_chunks:
                yield chunk

    with patch('edge_tts.Communicate', return_value=MockCommunicate("test", "voice")):
        with patch.object(EdgeTTSEngine, '_run_coroutine', side_effect=lambda x: "1\n00:00:00,000 --> 00:00:01,000\nhello\n\n"):
            srt = engine.generate_audio("hello", output_path, "es-MX-JorgeNeural")
            assert "hello" in srt

# Tests for ElevenLabsTTSEngine
def test_elevenlabs_load_voices_fallback():
    engine = ElevenLabsTTSEngine({})
    engine.load_voices() # No API key, should use fallback
    assert len(engine.all_voices) > 0
    assert "Dani (Español)" in engine.all_voices

def test_elevenlabs_generate_audio(temp_dir, tts_config):
    engine = ElevenLabsTTSEngine(tts_config)
    output_path = os.path.join(temp_dir, "test_eleven.mp3")
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b"fake_audio"
        
        with patch('mutagen.mp3.MP3', return_value=MockMP3(output_path)):
            srt = engine.generate_audio("Hola mundo", output_path, "voice_id")
            assert "Hola mundo" in srt
            assert os.path.exists(output_path)

# Tests for UnrealSpeechTTSEngine
def test_unrealspeech_generate_audio(temp_dir, tts_config):
    engine = UnrealSpeechTTSEngine(tts_config)
    output_path = os.path.join(temp_dir, "test_unreal.mp3")
    
    with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"OutputUri": "http://fake.url/audio.mp3"}
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"fake_audio_unreal"
        
        with patch('mutagen.mp3.MP3', return_value=MockMP3(output_path)):
            srt = engine.generate_audio("Hello", output_path, "Dan")
            assert "Hello" in srt
            assert os.path.exists(output_path)

# Tests for LocalTTSEngine
def test_local_tts_generate_audio(temp_dir):
    with patch('src.engines.tts.local.KokoroEngine') as mock_kokoro, \
         patch('src.engines.tts.local.VoiceManager') as mock_vm:
        
        mock_kokoro_inst = mock_kokoro.return_value
        mock_kokoro_inst.is_server_running.return_value = True
        
        engine = LocalTTSEngine({})
        output_path = os.path.join(temp_dir, "test_local.mp3")
        
        def mock_gen(text, voice, path, callback):
            with open(path, "wb") as f: f.write(b"local_audio")
            callback(True, "")
            
        mock_kokoro_inst.generate_audio.side_effect = mock_gen
        
        with patch('mutagen.mp3.MP3', return_value=MockMP3(output_path)):
            srt = engine.generate_audio("Prueba local", output_path, "af_bella")
            assert "Prueba local" in srt
            assert os.path.exists(output_path)

def test_local_tts_no_server():
    with patch('src.engines.tts.local.KokoroEngine') as mock_kokoro:
        mock_kokoro_inst = mock_kokoro.return_value
        mock_kokoro_inst.is_server_running.return_value = False
        
        engine = LocalTTSEngine({})
        with pytest.raises(AudioGenerationError, match="Servidor Kokoro no está disponible"):
            engine.generate_audio("test", "path", "voice")
