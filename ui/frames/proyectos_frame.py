# ui/frames/proyectos_frame.py
import os
import threading
import time
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pygame
from PIL import Image
from src.error_handling import handle_error
from src.utils import logger, open_folder

from ui import styles as st


class ProyectosFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        # Estado de reproducción
        self.playback_mode = None
        self.current_single_audio = None
        self.marathon_running = False
        self.marathon_paused = False
        self.marathon_stop_event = None
        self.current_marathon_thread = None
        self.current_playing_path = None
        self.is_marathon_mode = False

        # Cola para comandos de pygame (thread-safe)
        self._pygame_queue = []
        self._queue_lock = threading.Lock()
        self._process_pygame_queue()  # Inicia el procesamiento periódico

        # Título
        ctk.CTkLabel(self, text="GESTIÓN DE PROYECTOS", font=st.FONT_TITLE).pack(pady=(0, 20))

        # Header con controles globales
        header = ctk.CTkFrame(self, fg_color=st.COLOR_CARD, corner_radius=15)
        header.pack(fill="x", pady=(0, 15))

        # Fila superior: búsqueda y exportar
        top_row = ctk.CTkFrame(header, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=10)

        self.search_entry = ctk.CTkEntry(top_row, placeholder_text="🔍 Buscar serie...", width=300)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_proyectos())

        ctk.CTkButton(top_row, text="📎 Exportar a Excel", width=150,
                      command=self.export_to_excel).pack(side="right", padx=5)

        # Fila inferior: controles de maratón y selector de serie
        bottom_row = ctk.CTkFrame(header, fg_color="transparent")
        bottom_row.pack(fill="x", padx=20, pady=(0, 10))

        self.serie_filter = ctk.CTkComboBox(bottom_row, values=["Todas las series"], width=200,
                                            command=lambda _: self.refresh_proyectos())
        self.serie_filter.pack(side="left", padx=5)

        # Botones de control global (afectan a cualquier reproducción)
        ctk.CTkButton(bottom_row, text="⏹", width=40, height=35, fg_color="#d9534f",
                    command=self.stop_audio_global).pack(side="right", padx=2)
        ctk.CTkButton(bottom_row, text="▶", width=40, height=35, fg_color=st.COLOR_SUCCESS,
                    command=self.resume_audio_global).pack(side="right", padx=2)
        ctk.CTkButton(bottom_row, text="⏸", width=40, height=35, fg_color="#f0ad4e",
                    command=self.pause_audio_global).pack(side="right", padx=2)

        self.btn_maraton = ctk.CTkButton(bottom_row, text="🎧 MODO MARATÓN", fg_color=st.COLOR_IA,
                                         height=35, command=self.start_marathon)
        self.btn_maraton.pack(side="right", padx=10)

        self.lbl_stats = ctk.CTkLabel(bottom_row, text="", font=("Segoe UI", 11, "italic"))
        self.lbl_stats.pack(side="right", padx=10)

        self.btn_marathon_plus = ctk.CTkButton(bottom_row, text="⚡ MARATHON+", fg_color="#9b59b6",
                                            height=35, command=self.start_marathon_plus)
        self.btn_marathon_plus.pack(side="right", padx=5)

        # Área scrollable para los álbumes de series
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=st.COLOR_FG_BOX, corner_radius=15)
        self.scroll_frame.pack(fill="both", expand=True, pady=10)

        self.refresh_proyectos()

    # ---------- PROCESAMIENTO DE COLA DE PYGAME (THREAD-SAFE) ----------
    def _process_pygame_queue(self):
        """Procesa comandos de pygame en el hilo principal periódicamente."""
        with self._queue_lock:
            # Procesar todos los comandos pendientes
            while self._pygame_queue:
                cmd, args, kwargs = self._pygame_queue.pop(0)
                try:
                    if cmd == "load":
                        pygame.mixer.music.load(*args, **kwargs)
                    elif cmd == "play":
                        pygame.mixer.music.play(*args, **kwargs)
                    elif cmd == "stop":
                        pygame.mixer.music.stop()
                    elif cmd == "unload":
                        pygame.mixer.music.unload()
                    elif cmd == "pause":
                        pygame.mixer.music.pause()
                    elif cmd == "unpause":
                        pygame.mixer.music.unpause()
                    elif cmd == "get_busy":
                        # Este es especial porque devuelve valor, lo manejamos en el momento
                        pass
                except Exception as e:
                    logger.error(f"Error en comando pygame '{cmd}': {e}")
        # Volver a programar en 100 ms
        self.after(100, self._process_pygame_queue)

    def _enqueue_pygame(self, cmd, *args, **kwargs):
        """Añade un comando a la cola de pygame."""
        with self._queue_lock:
            self._pygame_queue.append((cmd, args, kwargs))

    def _is_pygame_busy(self):
        """Consulta síncrona de si pygame está reproduciendo (debe llamarse desde hilo principal)."""
        return pygame.mixer.music.get_busy()

    # ---------- REPRODUCCIÓN INDIVIDUAL ----------
    def _play_single_audio(self, path):
        """Reproduce un solo audio de forma segura."""
        if not os.path.exists(path):
            return
            
        def start_playback():
            self._enqueue_pygame("stop")
            self._enqueue_pygame("unload")
            self._enqueue_pygame("load", path)
            self._enqueue_pygame("play")
            self.current_playing_path = path
            self.is_marathon_mode = False
            self.marathon_running = False

        # Detener maratón si está activo
        if self.marathon_running:
            self.stop_marathon()
            # Esperar a que el hilo se detenga antes de iniciar la nueva reproducción
            self.after(200, start_playback)
        else:
            start_playback()

    # ---------- CONTROL GLOBAL ----------
    def pause_audio_global(self):
        if self.marathon_running:
            if not self.marathon_paused:
                self.marathon_paused = True
                # Guardar posición actual
                if self._is_pygame_busy():
                    self.marathon_current_pos = pygame.mixer.music.get_pos() / 1000.0
                else:
                    self.marathon_current_pos = 0.0
                self._enqueue_pygame("stop")
        elif self.current_playing_path:
            self._enqueue_pygame("pause")

    def resume_audio_global(self):
        if self.marathon_running and self.marathon_paused:
            self.marathon_paused = False
            # Reanudar desde posición guardada
            if self.current_playlist and self.current_track_index is not None:
                track = self.current_playlist[self.current_track_index]
                if os.path.exists(track):
                    self._enqueue_pygame("load", track)
                    self._enqueue_pygame("play", start=self.marathon_current_pos)
        elif self.current_playing_path:
            self._enqueue_pygame("unpause")

    def stop_audio_global(self):
        if self.marathon_running:
            self.stop_marathon()
        elif self.current_playing_path:
            self._enqueue_pygame("stop")
            self._enqueue_pygame("unload")
            self.current_playing_path = None

    # ---------- MODO MARATÓN (ADAPTADO A COLA) ----------
    def start_marathon(self):
        if self.current_playing_path:
            self.stop_audio_global()
        if self.marathon_running:
            self.stop_marathon()
            time.sleep(0.2)

        selected_serie = self.serie_filter.get()
        if selected_serie == "Todas las series":
            messagebox.showinfo("Maratón", "Selecciona una serie específica en el filtro.")
            return

        proyectos = self.app.data.get_projects_by_serie(selected_serie)
        if not proyectos:
            messagebox.showinfo("Maratón", "No hay proyectos para esta serie.")
            return

        playlist = []
        for proj in sorted(proyectos, key=lambda x: x['parte']):
            folder = proj['carpeta']
            parte = proj['parte']
            s_clean = self.app.data.clean_filename(selected_serie)
            audio_path = os.path.join(folder, f"Narracion_{s_clean}_P{parte}.mp3")
            if not os.path.exists(audio_path):
                audio_path = os.path.join(folder, f"Narracion_{s_clean}_{parte}.mp3")
            if os.path.exists(audio_path):
                playlist.append(audio_path)

        if not playlist:
            messagebox.showinfo("Maratón", "No hay archivos de audio disponibles.")
            return

        self.marathon_running = True
        self.marathon_paused = False
        self.is_marathon_mode = True
        self.current_playing_path = None
        self.marathon_stop_event = threading.Event()
        self.current_playlist = playlist
        self.current_track_index = 0
        self.marathon_current_pos = 0.0
        self.btn_maraton.configure(fg_color="#d9534f", text="🎧 MARATÓN ACTIVO")

        def worker():
            stop_event = self.marathon_stop_event
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                while not stop_event.is_set():
                    # Esperar si está pausado
                    while self.marathon_paused and not stop_event.is_set():
                        time.sleep(0.2)
                    if stop_event.is_set():
                        break
                    if self.current_track_index >= len(self.current_playlist):
                        break
                    track = self.current_playlist[self.current_track_index]
                    # Encolar carga y reproducción
                    self._enqueue_pygame("load", track)
                    self._enqueue_pygame("play", start=self.marathon_current_pos)
                    # Esperar a que termine la pista o se pause/detenga
                    while not stop_event.is_set():
                        if self.marathon_paused:
                            # Guardar posición antes de pausar
                            if self._is_pygame_busy():
                                self.marathon_current_pos = pygame.mixer.music.get_pos() / 1000.0
                            else:
                                self.marathon_current_pos = 0.0
                            # El comando de pausa ya fue enviado por el botón global
                            break
                        if not self._is_pygame_busy():
                            # La pista terminó
                            self.current_track_index += 1
                            self.marathon_current_pos = 0.0
                            break
                        time.sleep(0.2)
                    # Si salió por pausa, esperar reanudación
                    if self.marathon_paused:
                        continue
                # Fin de maratón
            except Exception as e:
                logger.error(f"Error en hilo de maratón: {e}")
            finally:
                self.after(0, self._marathon_finished)

        self.current_marathon_thread = threading.Thread(target=worker, daemon=True)
        self.current_marathon_thread.start()

    def _marathon_finished(self):
        self.marathon_running = False
        self.is_marathon_mode = False
        self.marathon_stop_event = None
        self.current_playlist = None
        self.current_track_index = None
        self.btn_maraton.configure(fg_color=st.COLOR_IA, text="🎧 MODO MARATÓN")
        self._enqueue_pygame("stop")
        self._enqueue_pygame("unload")

    def stop_marathon(self):
        if self.marathon_running:
            if self.marathon_stop_event:
                self.marathon_stop_event.set()
            self._enqueue_pygame("stop")
            self._enqueue_pygame("unload")
            if self.current_marathon_thread and self.current_marathon_thread.is_alive():
                self.current_marathon_thread.join(timeout=0.5)
            self.marathon_running = False
            self.is_marathon_mode = False
            self.btn_maraton.configure(fg_color=st.COLOR_IA, text="🎧 MODO MARATÓN")

    def start_marathon_plus(self):
        from tkinter import simpledialog
        serie = self.serie_filter.get()
        if serie == "Todas las series":
            messagebox.showwarning("Marathon+", "Selecciona una serie específica.")
            return
        num_parts = simpledialog.askinteger("Marathon+", f"¿Cuántos capítulos generar para '{serie}'?", minvalue=1, maxvalue=20)
        if not num_parts:
            return

        # Obtener datos base desde los frames actuales
        explorador = self.app.frames["Inicio"]
        guionista = self.app.frames["Guionista"]
        base_data = {
            "serie": serie,
            "tema": explorador.cards["TEMAS"].get_value(),
            "objeto": explorador.cards["OBJETOS"].get_value(),
            "anomalia": explorador.cards["ANOMALIAS"].get_value(),
            "emocion": explorador.cards["EMOCIONES"].get_value(),
            "tono": guionista.tone_sel.get(),
            "estructura": guionista.struct_sel.get(),
            "notas": guionista.script_notes.get("1.0", "end-1c")
        }
        voice_name = guionista.selected_voice
        if not voice_name:
            voice_name = "Jorge (México)"
        emotion = base_data["emocion"]

        # Deshabilitar botones durante la generación
        self.btn_marathon_plus.configure(state="disabled", text="⏳ Generando...")

        def progress_callback(msg, progress):
            self.lbl_stats.configure(text=f"{msg} ({int(progress*100)}%)")

        def generation_done(results):
            self.btn_marathon_plus.configure(state="normal", text="⚡ MARATHON+")
            self.lbl_stats.configure(text="")
            success_count = sum(1 for r in results if r.get("success"))
            messagebox.showinfo("Marathon+", f"Generados {success_count} de {len(results)} capítulos.")
            self.refresh_proyectos()

        def run_marathon():
            results = self.app.orchestrator.generate_series(
                serie=serie,
                num_parts=num_parts,
                base_prompt_data=base_data,
                voice_name=voice_name,
                emotion=emotion,
                max_workers=self.app.config.get("max_workers", 4),
                progress_callback=progress_callback
            )
            self.after(0, lambda: generation_done(results))

        threading.Thread(target=run_marathon, daemon=True).start()


    # ---------- MÉTODOS DE GESTIÓN DE PROYECTOS ----------
    def refresh_proyectos(self):
        for child in self.scroll_frame.winfo_children():
            child.destroy()
        search_term = self.search_entry.get().lower()
        series = self.app.data.get_all_series()
        if not series:
            ctk.CTkLabel(self.scroll_frame, text="No hay proyectos guardados.",
                         text_color=st.COLOR_TEXT_DIM).pack(pady=50)
            return
        series_list = ["Todas las series"] + series
        self.serie_filter.configure(values=series_list)
        selected = self.serie_filter.get()
        if selected not in series_list:
            self.serie_filter.set("Todas las series")
        for serie in series:
            if search_term and search_term not in serie.lower():
                continue
            if selected != "Todas las series" and serie != selected:
                continue
            proyectos = self.app.data.get_projects_by_serie(serie)
            if proyectos:
                self._add_serie_album(serie, proyectos)

    def _add_serie_album(self, serie, proyectos):
        album = ctk.CTkFrame(self.scroll_frame, fg_color=st.COLOR_CARD, corner_radius=15,
                             border_width=1, border_color="#333")
        album.pack(fill="x", pady=10, padx=15)
        header = ctk.CTkFrame(album, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header, text="🎬", font=("Segoe UI", 28)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(header, text=serie.upper(), font=("Segoe UI", 18, "bold"),
                     text_color=st.COLOR_ACCENT).pack(side="left")
        ctk.CTkLabel(header, text=f"{len(proyectos)} capítulos", font=("Segoe UI", 11),
                     text_color=st.COLOR_TEXT_DIM).pack(side="left", padx=15)
        btn_toggle = ctk.CTkButton(header, text="👁️ VER CAPÍTULOS", width=140, height=35,
                                   fg_color=st.COLOR_ACCENT,
                                   command=lambda: self._toggle_album(parts_container, btn_toggle))
        btn_toggle.pack(side="right")
        parts_container = ctk.CTkFrame(album, fg_color=st.COLOR_FG_BOX, corner_radius=0)
        for proj in proyectos:
            self._add_part_row(parts_container, proj, serie)

    def _toggle_album(self, container, button):
        if container.winfo_ismapped():
            container.pack_forget()
            button.configure(text="👁️ VER CAPÍTULOS", fg_color=st.COLOR_ACCENT)
        else:
            container.pack(fill="x", padx=15, pady=(0, 15))
            button.configure(text="❌ CERRAR", fg_color="#d9534f")

    def _add_part_row(self, parent, proj, serie):
        parte = proj['parte']
        folder = proj['carpeta']
        s_clean = self.app.data.clean_filename(serie)
        status = self._scan_files(folder, serie, parte)
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=5)
        img_frame = ctk.CTkFrame(row, width=60, height=60, fg_color=st.COLOR_BG, corner_radius=8)
        img_frame.pack(side="left", padx=(0, 10))
        img_frame.pack_propagate(False)
        img_label = ctk.CTkLabel(img_frame, text="🖼️", font=("Segoe UI", 20))
        img_label.pack(expand=True)
        img_path = os.path.join(folder, f"Imagen_{s_clean}_P{parte}.jpg")
        if not os.path.exists(img_path):
            img_path = os.path.join(folder, f"Imagen_{s_clean}_{parte}.jpg")
        if status["jpg"] and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path).resize((60, 60))
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))
                img_label.configure(image=ctk_img, text="")
            except Exception as e:
                logger.debug(f"Error al cargar imagen: {e}")
        info_f = ctk.CTkFrame(row, fg_color="transparent")
        info_f.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info_f, text=f"Parte {parte} — {proj.get('tema', 'Sin tema')}",
                     font=("Segoe UI", 12, "bold"), text_color=st.COLOR_TEXT).pack(anchor="w")
        badges_f = ctk.CTkFrame(info_f, fg_color="transparent")
        badges_f.pack(anchor="w", pady=2)
        for ext in ["txt", "pdf", "mp3", "srt", "jpg"]:
            color = st.COLOR_SUCCESS if status[ext] else "#444"
            lbl = ctk.CTkLabel(badges_f, text=f" {ext.upper()} ", font=("Consolas", 9, "bold"),
                               fg_color=color, text_color="white", corner_radius=4)
            lbl.pack(side="left", padx=2)
        btn_frame = ctk.CTkFrame(row, fg_color="transparent")
        btn_frame.pack(side="right")
        audio_path = os.path.join(folder, f"Narracion_{s_clean}_P{parte}.mp3")
        if not os.path.exists(audio_path):
            audio_path = os.path.join(folder, f"Narracion_{s_clean}_{parte}.mp3")
        ctk.CTkButton(btn_frame, text="▶ OIR", width=70, height=30,
                      fg_color=st.COLOR_SUCCESS if status["mp3"] else "#333",
                      state="normal" if status["mp3"] else "disabled",
                      command=lambda p=audio_path: self._play_single_audio(p)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="✏️", width=35, height=30, fg_color=st.COLOR_ACCENT,
                      command=lambda p=proj: self._edit_project(p)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="🗑️", width=35, height=30, fg_color="#d9534f",
                      command=lambda p=proj: self._delete_project(p)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="📂", width=45, height=30, fg_color="#444",
                      command=lambda f=folder: open_folder(f)).pack(side="left", padx=2)
        ctk.CTkFrame(parent, height=1, fg_color=("#dbdbdb", "#2a2a2a")).pack(fill="x", padx=25)

    def _scan_files(self, folder, serie, parte):
        s_clean = self.app.data.clean_filename(serie)
        status = {"txt": False, "pdf": False, "mp3": False, "srt": False, "jpg": False}
        prefixes = {"txt": "Guion", "pdf": "Guion", "mp3": "Narracion", "srt": "Subtitulos", "jpg": "Imagen"}
        for key, pref in prefixes.items():
            ext = ".txt" if key == "txt" else (".pdf" if key == "pdf" else (".mp3" if key == "mp3" else (".srt" if key == "srt" else ".jpg")))
            path_a = os.path.join(folder, f"{pref}_{s_clean}_P{parte}{ext}")
            path_b = os.path.join(folder, f"{pref}_{s_clean}_{parte}{ext}")
            if os.path.exists(path_a) or os.path.exists(path_b):
                status[key] = True
        return status


    def _edit_project(self, proj):
        try:
            guionista = self.app.frames["Guionista"]
            guionista.serie_entry.delete(0, "end")
            guionista.serie_entry.insert(0, proj['serie'])
            guionista.parte_sel.set(str(proj['parte']))
            guionista.tone_sel.set(proj.get('tono', 'Oscuro'))
            guionista.struct_sel.set(proj.get('estructura', 'Caja de Misterio'))
            folder = proj['carpeta']
            s_clean = self.app.data.clean_filename(proj['serie'])
            parte = proj['parte']
            txt_path = os.path.join(folder, f"Guion_{s_clean}_P{parte}.txt")
            if not os.path.exists(txt_path):
                txt_path = os.path.join(folder, f"Guion_{s_clean}_{parte}.txt")
            if os.path.exists(txt_path):
                with open(txt_path, encoding="utf-8") as f:
                    content = f.read()
                    if "---" in content:
                        content = content.split("\n\n", 1)[-1]
                    guionista.script_editor.delete("1.0", "end")
                    guionista.script_editor.insert("1.0", content)
            explorador = self.app.frames["Inicio"]
            for cat in ["TEMAS", "OBJETOS", "ANOMALIAS", "EMOCIONES"]:
                key = cat.capitalize() if cat != "TEMAS" else "Tema"
                if key.lower() in proj:
                    explorador.cards[cat].update_value(proj[key.lower()])
            self.app.show_guionista()
            messagebox.showinfo("Cargado", f"Proyecto {proj['serie']} - Parte {proj['parte']} listo para editar.")
        except Exception as e:
            handle_error(e, "cargar proyecto para edición", self)

    def _delete_project(self, proj):
        ans = messagebox.askyesno("Confirmar", f"¿Eliminar {proj['serie']} - Parte {proj['parte']} de la biblioteca?")
        if not ans:
            return
        del_files = messagebox.askyesno("Archivos", "¿Borrar también la carpeta física?")
        try:
            success = self.app.data.delete_project(proj['serie'], proj['parte'], del_files, proj.get('carpeta'))
            if success:
                self.refresh_proyectos()
                messagebox.showinfo("Éxito", "Proyecto eliminado.")
            else:
                raise Exception("No se pudo eliminar el registro")
        except Exception as e:
            handle_error(e, "eliminar proyecto", self)

    def export_to_excel(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if filepath:
            try:
                success = self.app.data.export_to_excel(filepath)
                if success:
                    messagebox.showinfo("Exportado", f"Datos exportados a {filepath}")
                else:
                    raise Exception("No se pudo exportar los datos")
            except Exception as e:
                handle_error(e, "exportar a Excel", self)
