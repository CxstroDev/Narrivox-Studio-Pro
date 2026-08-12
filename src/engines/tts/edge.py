import asyncio
import logging
import threading
import edge_tts
from src.engines.tts.base import BaseTTSEngine
from src.exceptions import AudioGenerationError

logger = logging.getLogger("Narrivox")

class EdgeTTSEngine(BaseTTSEngine):
    def __init__(self, config: dict, loop=None):
        super().__init__(config)
        self.loop = loop
        self.all_voices = {}
        self.voices_by_language = {"Todos": {}, "Español": {}, "Inglés": {}}
        self.voice_names = []

    def _run_coroutine(self, coro):
        if self.loop is None:
            # Fallback if no loop provided
            return asyncio.run(coro)
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    async def _list_voices(self):
        try:
            return await edge_tts.list_voices()
        except Exception as e:
            logger.error(f"Error al listar voces Edge: {e}")
            return None

    def load_voices(self, on_loaded_callback=None):
        def load():
            try:
                voices_list = self._run_coroutine(self._list_voices())
                if voices_list:
                    self.all_voices = {}
                    self.voices_by_language = {"Todos": {}, "Español": {}, "Inglés": {}}
                    for voice in voices_list:
                        locale = voice.get('Locale', '')
                        if locale.startswith('es-') or locale.startswith('en-'):
                            code = voice['ShortName']
                            display_name = f"{code} ({locale}, {voice.get('Gender', '')})"
                            self.all_voices[display_name] = code
                            if locale.startswith('es-'):
                                self.voices_by_language["Español"][display_name] = code
                            elif locale.startswith('en-'):
                                self.voices_by_language["Inglés"][display_name] = code
                    self.voices_by_language["Todos"] = self.all_voices.copy()
                    self.voice_names = list(self.all_voices.keys())
                    logger.info(f"Voces Edge cargadas: {len(self.voice_names)} voces")
                else:
                    self._use_fallback_voices()
                
                if on_loaded_callback:
                    on_loaded_callback()
            except Exception as e:
                logger.error(f"Error cargando voces Edge: {e}")
                self._use_fallback_voices()
                if on_loaded_callback:
                    on_loaded_callback()
        
        threading.Thread(target=load, daemon=True).start()

    def _use_fallback_voices(self):
        fallback = {
            "Jorge (México)": "es-MX-JorgeNeural",
            "Dalia (México)": "es-MX-DaliaNeural",
            "Alvaro (España)": "es-ES-AlvaroNeural",
            "Elvira (España)": "es-ES-ElviraNeural",
            "Guy (EEUU)": "en-US-GuyNeural",
            "Jenny (EEUU)": "en-US-JennyNeural"
        }
        self.all_voices = fallback
        self.voices_by_language = {"Todos": fallback, "Español": {}, "Inglés": {}}
        for name, code in fallback.items():
            if "México" in name or "España" in name:
                self.voices_by_language["Español"][name] = code
            else:
                self.voices_by_language["Inglés"][name] = code
        self.voice_names = list(self.all_voices.keys())

    async def _generate_async(self, text: str, output_path: str, voice_code: str, cancel_event: threading.Event):
        cleaned = self._clean_text(text)
        if not cleaned:
            return ""
        communicate = edge_tts.Communicate(cleaned, voice_code)
        subs = []
        with open(output_path, "wb") as f:
            async for chunk in communicate.stream():
                if cancel_event and cancel_event.is_set():
                    return ""
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif "text" in chunk and "offset" in chunk:
                    subs.append(chunk)
        
        if not subs:
            return ""
        
        srt_output = ""
        for i, sub in enumerate(subs):
            start = sub["offset"] / 10**7
            end = (sub["offset"] + sub.get("duration", 0)) / 10**7
            def fmt(s):
                m, s = divmod(s, 60)
                h, m = divmod(m, 60)
                return f"{int(h):02}:{int(m):02}:{int(s):02},{int((s-int(s))*1000):03}"
            srt_output += f"{i+1}\n{fmt(start)} --> {fmt(end)}\n{sub['text']}\n\n"
        return srt_output

    def generate_audio(self, text: str, output_path: str, voice_code: str, cancel_event=None) -> str:
        try:
            srt = self._run_coroutine(self._generate_async(text, output_path, voice_code, cancel_event))
            if cancel_event and cancel_event.is_set():
                return ""
            logger.info(f"Audio Edge generado: {output_path}")
            return srt if srt else ""
        except Exception as e:
            logger.error(f"Error generando audio Edge: {e}")
            raise AudioGenerationError(f"Fallo TTS Edge: {e}")
