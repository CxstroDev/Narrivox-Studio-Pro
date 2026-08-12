import abc
import os
import re
import logging
import mutagen.mp3

logger = logging.getLogger("Narrivox")

class BaseTTSEngine(abc.ABC):
    def __init__(self, config: dict):
        self.config = config

    @abc.abstractmethod
    def load_voices(self, on_loaded_callback=None):
        pass

    @abc.abstractmethod
    def generate_audio(self, text: str, output_path: str, voice_code: str) -> str:
        """Generates audio and returns SRT content if available."""
        pass

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'[^\w\s,.¡!¿?áéíóúÁÉÍÓÚñÑ]', '', text)
        return text.strip()

    def _chunk_text(self, text: str, max_chars: int) -> list:
        if len(text) <= max_chars:
            return [text]
        chunks = []
        current = ""
        for sentence in re.split(r'(?<=[.!?])\s+', text):
            if len(current) + len(sentence) + 1 <= max_chars:
                current += (" " + sentence if current else sentence)
            else:
                if current:
                    chunks.append(current)
                if len(sentence) > max_chars:
                    subchunks = []
                    temp = ""
                    for word in sentence.split():
                        if len(temp) + len(word) + 1 <= max_chars:
                            temp += (" " + word if temp else word)
                        else:
                            subchunks.append(temp)
                            temp = word
                    if temp:
                        subchunks.append(temp)
                    chunks.extend(subchunks)
                else:
                    current = sentence
        if current:
            chunks.append(current)
        return chunks

    def _generate_synthetic_srt(self, text: str, audio_path: str) -> str:
        try:
            audio = mutagen.mp3.MP3(audio_path)
            duration = audio.info.length
        except Exception as e:
            logger.warning(f"No se pudo leer duración de {audio_path}: {e}. Usando estimación de 150 ppm.")
            words = len(text.split())
            duration = max(1.0, words / 150.0)

        sentences = re.split(r'(?<=[.!?])\s+', text)
        if not sentences:
            sentences = [text]

        total_chars = sum(len(s) for s in sentences)
        srt_output = ""
        start_time = 0.0

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            char_ratio = len(sentence) / total_chars if total_chars > 0 else 1.0 / len(sentences)
            sent_duration = duration * char_ratio
            end_time = start_time + sent_duration

            def fmt(sec):
                ms = int((sec - int(sec)) * 1000)
                total_sec = int(sec)
                h = total_sec // 3600
                m = (total_sec % 3600) // 60
                s = total_sec % 60
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

            srt_output += f"{i+1}\n{fmt(start_time)} --> {fmt(end_time)}\n{sentence.strip()}\n\n"
            start_time = end_time

        return srt_output

    def _concatenate_audio_files(self, file_list: list, output_path: str):
        try:
            from pydub import AudioSegment
            combined = AudioSegment.empty()
            for f in file_list:
                combined += AudioSegment.from_file(f)
            combined.export(output_path, format="mp3")
        except ImportError:
            import shutil
            shutil.copyfile(file_list[0], output_path)
            logger.warning("pydub no instalado, no se puede concatenar audio correctamente.")
