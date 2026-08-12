import pytest
import os
from unittest.mock import MagicMock, patch
from src.engines.video.composer import VideoComposer
from src.engines.video.subtitles import SubtitleManager

@pytest.fixture
def mock_moviepy():
    with patch('src.engines.video.composer.MOVIEPY_AVAILABLE', True), \
         patch('src.engines.video.subtitles.MOVIEPY_AVAILABLE', True), \
         patch('src.engines.video.composer.AudioFileClip') as mock_audio, \
         patch('src.engines.video.composer.ImageClip') as mock_image, \
         patch('src.engines.video.composer.CompositeVideoClip') as mock_composite, \
         patch('src.engines.video.subtitles.TextClip') as mock_text, \
         patch('src.engines.video.subtitles.SubtitlesClip') as mock_subs_clip:
        
        mock_audio_inst = mock_audio.return_value
        mock_audio_inst.duration = 10.0
        
        mock_image_inst = mock_image.return_value
        mock_image_inst.w = 1280
        mock_image_inst.h = 720
        mock_image_inst.resized.return_value = mock_image_inst
        
        mock_composite_inst = MagicMock()
        mock_composite_inst.with_audio.return_value = mock_composite_inst
        mock_composite.return_value = mock_composite_inst
        
        mock_subs_inst = mock_subs_clip.return_value
        mock_subs_inst.with_position.return_value = mock_subs_inst
        
        yield {
            "audio": mock_audio,
            "image": mock_image,
            "composite": mock_composite,
            "text": mock_text,
            "subs": mock_subs_clip,
            "composite_inst": mock_composite_inst
        }

def test_subtitle_manager_create(mock_moviepy):
    srt_path = "test.srt"
    video_width = 1280
    
    subs = SubtitleManager.create_subtitles(srt_path, video_width)
    
    mock_moviepy["subs"].assert_called_once()
    assert subs is not None

def test_video_composer_compose(mock_moviepy, temp_dir):
    image_path = os.path.join(temp_dir, "input.png")
    audio_path = os.path.join(temp_dir, "input.mp3")
    srt_path = os.path.join(temp_dir, "input.srt")
    output_path = os.path.join(temp_dir, "output.mp4")
    
    # Create dummy files
    for p in [image_path, audio_path, srt_path]:
        with open(p, "w") as f: f.write("test")
        
    success = VideoComposer.compose(image_path, audio_path, srt_path, output_path)
    
    assert success is True
    mock_moviepy["composite_inst"].write_videofile.assert_called()

def test_video_composer_no_moviepy():
    with patch('src.engines.video.composer.MOVIEPY_AVAILABLE', False):
        success = VideoComposer.compose("img", "audio", "srt", "out")
        assert success is False
