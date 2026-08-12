import pytest
import os
from unittest.mock import MagicMock, patch
from src.cinematic_engine import CinematicEngine, KenBurnsEffect, BRollIntegrator, StyledSubtitles

@pytest.fixture
def cinematic_config(temp_dir):
    return {
        "base_folder": temp_dir,
        "enable_broll": True,
        "broll_provider": "pexels",
        "pexels_api_key": "test_pexels_key"
    }

@pytest.fixture
def mock_moviepy_cinematic():
    with patch('src.cinematic_engine.MOVIEPY_AVAILABLE', True), \
         patch('src.cinematic_engine.AudioFileClip') as mock_audio, \
         patch('src.cinematic_engine.ImageClip') as mock_image, \
         patch('src.cinematic_engine.CompositeVideoClip') as mock_composite, \
         patch('src.cinematic_engine.VideoClip') as mock_video_clip, \
         patch('src.cinematic_engine.VideoFileClip') as mock_video_file, \
         patch('src.cinematic_engine.TextClip') as mock_text, \
         patch('src.cinematic_engine.concatenate_videoclips') as mock_concat:
        
        mock_audio_inst = mock_audio.return_value
        mock_audio_inst.duration = 5.0
        
        mock_image_inst = mock_image.return_value
        mock_image_inst.w = 1280
        mock_image_inst.h = 720
        mock_image_inst.duration = 5.0
        mock_image_inst.resized.return_value = mock_image_inst
        
        mock_video_file_inst = mock_video_file.return_value
        mock_video_file_inst.duration = 5.0
        mock_video_file_inst.size = (1280, 720)
        mock_video_file_inst.without_audio.return_value = mock_video_file_inst
        mock_video_file_inst.loop.return_value = mock_video_file_inst
        mock_video_file_inst.subclipped.return_value = mock_video_file_inst
        
        # Subtitles clip needs margin and with_position
        mock_subs_inst = MagicMock()
        mock_subs_inst.with_position.return_value = mock_subs_inst
        mock_subs_inst.margin.return_value = mock_subs_inst
        mock_subs_inst.with_duration.return_value = mock_subs_inst
        mock_subs_inst.crossfadein.return_value = mock_subs_inst
        
        mock_composite.return_value = mock_subs_inst # It's used for both subs and final assembly
        
        yield {
            "audio": mock_audio,
            "image": mock_image,
            "composite": mock_composite,
            "video_clip": mock_video_clip,
            "video_file": mock_video_file,
            "text": mock_text,
            "concat": mock_concat,
            "subs_inst": mock_subs_inst
        }

def test_ken_burns_effect(mock_moviepy_cinematic):
    clip = mock_moviepy_cinematic["image"].return_value
    effect_clip = KenBurnsEffect.apply(clip, duration=5.0)
    assert effect_clip is not None
    mock_moviepy_cinematic["video_clip"].assert_called()

def test_broll_integrator_keywords():
    bi = BRollIntegrator({"broll_provider": "pexels"})
    script = "Un gran misterio en el bosque profundo con una llave antigua."
    keywords = bi.extract_keywords(script)
    assert any(k in ["misterio", "bosque", "llave", "antigua"] for k in [kw.lower() for kw in keywords])

def test_broll_integrator_search(cinematic_config):
    bi = BRollIntegrator(cinematic_config)
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "videos": [{"video_files": [{"link": "http://fake.url/video.mp4", "quality": "sd"}]}]
        }
        urls = bi.search_videos("forest")
        assert len(urls) == 1
        assert urls[0] == "http://fake.url/video.mp4"

def test_cinematic_engine_assemble(mock_moviepy_cinematic, cinematic_config, temp_dir):
    ce = CinematicEngine(cinematic_config)
    
    img_path = os.path.join(temp_dir, "base.jpg")
    audio_path = os.path.join(temp_dir, "audio.mp3")
    srt_path = os.path.join(temp_dir, "subs.srt")
    out_path = os.path.join(temp_dir, "final.mp4")
    
    for p in [img_path, audio_path, srt_path]:
        with open(p, "w") as f: f.write("dummy")
        
    # Mock parse_srt to avoid complex subtitle generation logic in this test
    with patch.object(StyledSubtitles, 'parse_srt') as mock_parse:
        mock_parse.return_value = mock_moviepy_cinematic["subs_inst"]
        
        # Mock Gradio not available to trigger Ken Burns fallback
        with patch('src.cinematic_engine.GRADIO_AVAILABLE', False):
            success = ce.assemble_dynamic_video(img_path, audio_path, srt_path, out_path, script_text="Test script")
            assert success is True
            mock_moviepy_cinematic["subs_inst"].with_audio.return_value.write_videofile.assert_called()

@patch('src.cinematic_engine.Client')
@patch('src.cinematic_engine.handle_file')
def test_cinematic_engine_helios(mock_handle, mock_client, mock_moviepy_cinematic, cinematic_config, temp_dir):
    ce = CinematicEngine(cinematic_config)
    
    # Mock Gradio client response
    client_inst = mock_client.return_value
    client_inst.predict.side_effect = [
        None, # update_conditional_visibility
        ("/tmp/fake_helios.mp4",) # generate_video
    ]
    
    with patch('src.cinematic_engine.GRADIO_AVAILABLE', True), \
         patch('os.path.exists', return_value=True), \
         patch('shutil.move'):
        
        img_path = "img.jpg"
        out_path = "out.mp4"
        
        # Testing private method directly for easier verification of logic
        success = ce._generate_helios_video(img_path, "prompt", out_path)
        assert success is True
        assert client_inst.predict.call_count == 2
