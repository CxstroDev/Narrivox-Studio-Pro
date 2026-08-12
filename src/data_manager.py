# src/data_manager.py
import os
import shutil
import sqlite3

from src.exceptions import DatabaseError
from src.utils import clean_filename, logger


class DataManager:
    def __init__(self, config: dict):
        self.config = config
        self._conn = None
        
        # Priorizar db_path de config para tests, de lo contrario usar ruta por defecto
        self.db_path = config.get("db_path")
        if not self.db_path:
            db_name = config.get("db_name", "narrivox.db")
            self.db_path = os.path.join(os.getcwd(), db_name)
            
        self._init_db()

    def _get_connection(self):
        """Obtiene una conexión persistente a la base de datos."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
            # Habilitar modo WAL para mejor concurrencia
            self._conn.execute('PRAGMA journal_mode=WAL')
        return self._conn

    def _init_db(self):
        """Crea la tabla de proyectos si no existe y los índices necesarios."""
        try:
            conn = self._get_connection()
            with conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS proyectos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TEXT NOT NULL,
                        serie TEXT NOT NULL,
                        parte INTEGER NOT NULL,
                        tema TEXT,
                        objeto TEXT,
                        anomalia TEXT,
                        emocion TEXT,
                        tono TEXT,
                        estructura TEXT,
                        estado TEXT DEFAULT 'Pendiente',
                        carpeta TEXT,
                        UNIQUE(serie, parte)
                    )
                ''')
                # Índice para búsquedas rápidas por serie
                conn.execute('CREATE INDEX IF NOT EXISTS idx_serie ON proyectos(serie)')
                
                # Nueva tabla para el timeline del editor
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS editor_timelines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        serie TEXT NOT NULL,
                        parte INTEGER NOT NULL,
                        data_json TEXT NOT NULL,
                        UNIQUE(serie, parte)
                    )
                ''')
                logger.info("Base de datos SQLite inicializada correctamente.")
        except sqlite3.Error as e:
            logger.error(f"Error al inicializar DB: {e}")
            raise DatabaseError(f"No se pudo crear la base de datos: {e}")

    def save_project(self, data: dict) -> bool:
        """Guarda o actualiza un proyecto en la base de datos."""
        import datetime
        fecha = data.get('Fecha')
        if not fecha:
            fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = self._get_connection()
            with conn:
                conn.execute('''
                    INSERT OR REPLACE INTO proyectos 
                    (fecha, serie, parte, tema, objeto, anomalia, emocion, tono, estructura, estado, carpeta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    fecha, data['Serie'], int(data['Parte']),
                    data.get('Tema', ''), data.get('Objeto', ''),
                    data.get('Anomalía', ''), data.get('Emoción', ''),
                    data.get('Tono', ''), data.get('Estructura', ''),
                    data.get('Estado', 'Pendiente'), data.get('Carpeta', '')
                ))
                logger.info(f"Proyecto guardado: {data['Serie']} - Parte {data['Parte']}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error al guardar proyecto: {e}")
            return False

    def get_all_series(self) -> list[str]:
        """Devuelve lista de nombres de series únicos ordenados."""
        try:
            conn = self._get_connection()
            cursor = conn.execute('SELECT DISTINCT serie FROM proyectos ORDER BY serie')
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error obteniendo series: {e}")
            return []

    def get_projects_by_serie(self, serie: str) -> list[dict]:
        """Devuelve todas las partes de una serie, ordenadas por parte."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM proyectos WHERE serie = ? ORDER BY parte', (serie,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error obteniendo proyectos de {serie}: {e}")
            return []

    def delete_project(self, serie: str, parte: int, delete_files: bool = False, folder_path: str = None) -> bool:
        """Elimina un proyecto de la BD. Opcionalmente borra la carpeta física."""
        try:
            conn = self._get_connection()
            with conn:
                conn.execute('DELETE FROM proyectos WHERE serie = ? AND parte = ?', (serie, parte))
                logger.info(f"Proyecto eliminado de BD: {serie} - Parte {parte}")

            if delete_files and folder_path and os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                logger.info(f"Carpeta eliminada: {folder_path}")
            return True
        except (sqlite3.Error, OSError) as e:
            logger.error(f"Error al eliminar proyecto: {e}")
            return False

    def export_to_excel(self, excel_path: str) -> bool:
        """Exporta todos los datos a un archivo Excel (opcional)."""
        try:
            import pandas as pd
            conn = self._get_connection()
            df = pd.read_sql_query("SELECT * FROM proyectos", conn)
            df.to_excel(excel_path, index=False)
            logger.info(f"Datos exportados a Excel: {excel_path}")
            return True
        except Exception as e:
            logger.error(f"Error exportando a Excel: {e}")
            return False

    def create_project_folder(self, serie: str, parte: str) -> str:
        base = self.config.get("base_folder", os.getcwd())
        serie_clean = clean_filename(serie)
        path = os.path.normpath(os.path.join(base, "PROYECTOS_NARRIVOX", serie_clean, f"Parte_{parte}"))
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    def clean_filename(self, text: str) -> str:
        return clean_filename(text)

    def export_text_files(self, folder: str, serie: str, parte: str, script: str, prompts: str) -> bool:
        try:
            s_clean = clean_filename(serie)
            with open(os.path.join(folder, f"Guion_{s_clean}_P{parte}.txt"), "w", encoding="utf-8") as f:
                f.write(f"--- GUION: {serie} (Parte {parte}) ---\n\n{script}")
            if prompts and len(prompts) > 5:
                with open(os.path.join(folder, f"Prompts_{s_clean}_P{parte}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"--- PROMPTS VISUALES: {serie} (Parte {parte}) ---\n\n{prompts}")
            return True
        except Exception as e:
            logger.error(f"Error exportando TXT: {e}")
            return False

    def export_pdf(self, folder: str, serie: str, parte: str, script: str, author: str) -> bool:
        try:
            from fpdf import FPDF
            s_clean = clean_filename(serie)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(61, 90, 254)
            pdf.cell(0, 10, "NARRIVOX STUDIO - GUION", ln=True, align="C")
            pdf.set_font("Arial", "I", 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 10, f"Serie: {serie} | Parte: {parte} | Autor: {author}", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("Arial", "", 12)
            pdf.set_text_color(0, 0, 0)
            safe_text = script.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'").replace('—', '-')
            safe_text = safe_text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, safe_text)
            pdf_path = os.path.join(folder, f"Guion_{s_clean}_P{parte}.pdf")
            pdf.output(pdf_path)
            return True
        except Exception as e:
            logger.error(f"Error exportando PDF: {e}")
            return False

    def export_subtitles(self, folder: str, serie: str, parte: str, subs_data: str) -> bool:
        if not subs_data or len(subs_data) < 10:
            return False
        try:
            s_clean = clean_filename(serie)
            path = os.path.join(folder, f"Subtitulos_{s_clean}_P{parte}.srt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(subs_data)
            return True
        except Exception as e:
            logger.error(f"Error exportando SRT: {e}")
            return False

    def save_image(self, image_bytes: bytes, folder: str, serie: str, parte: str) -> bool:
        try:
            s_clean = clean_filename(serie)
            img_path = os.path.join(folder, f"Imagen_{s_clean}_P{parte}.jpg")
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            return True
        except Exception as e:
            logger.error(f"Error guardando imagen: {e}")
            return False

    def save_timeline(self, serie: str, parte: int, data: dict) -> bool:
        import json
        try:
            conn = self._get_connection()
            with conn:
                conn.execute('''
                    INSERT OR REPLACE INTO editor_timelines (serie, parte, data_json)
                    VALUES (?, ?, ?)
                ''', (serie, parte, json.dumps(data)))
                return True
        except Exception as e:
            logger.error(f"Error guardando timeline: {e}")
            return False

    def load_timeline(self, serie: str, parte: int) -> dict:
        import json
        try:
            conn = self._get_connection()
            cursor = conn.execute('SELECT data_json FROM editor_timelines WHERE serie = ? AND parte = ?', (serie, parte))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else {}
        except Exception as e:
            logger.error(f"Error cargando timeline: {e}")
            return {}

    def close(self):
        """Cierra la conexión persistente a la base de datos."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Conexión a base de datos cerrada.")
