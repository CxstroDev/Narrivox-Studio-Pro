# src/security.py
"""
Sistema de seguridad mejorado para Narrivox.
Proporciona sanitización de inputs, validación de rutas y protección contra ataques comunes.
"""

import html
import os
import re
import secrets
import string
from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import urlparse, urlunparse

from src.exceptions import ValidationError


class SecurityManager:
    """Gestor centralizado de seguridad."""

    # Patrones peligrosos a detectar
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'\.\./',  # Path traversal
        r'\.\.\\',  # Path traversal Windows
        r'~/',  # Home directory traversal
        r'/etc/',  # System files
        r'/sys/',  # System files
        r'/proc/',  # System files
        r'\0',  # Null byte injection
        r'[\x00-\x1f\x7f]',  # Control characters
    ]

    # Extensiones de archivo permitidas
    ALLOWED_EXTENSIONS = {
        # Imágenes
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
        # Audio
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a',
        # Video
        '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv',
        # Documentos
        '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
        # Subtítulos
        '.srt', '.vtt', '.ass',
        # Configuración
        '.json', '.xml', '.yaml', '.yml'
    }

    # Extensiones prohibidas
    FORBIDDEN_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs', '.js',
        '.dll', '.so', '.dylib', '.app', '.deb', '.rpm',
        '.zip', '.rar', '.tar', '.gz', '.7z',  # Archivos comprimidos
    }

    @staticmethod
    def sanitize_string(input_string: str, max_length: int = 10000,
                       allow_html: bool = False) -> str:
        """
        Sanitiza un string para prevenir inyecciones.

        Args:
            input_string: String a sanitizar
            max_length: Longitud máxima permitida
            allow_html: Si permite HTML (solo tags seguros)

        Returns:
            String sanitizado
        """
        if not isinstance(input_string, str):
            raise ValidationError("Input debe ser un string")

        # Truncar si es muy largo
        if len(input_string) > max_length:
            input_string = input_string[:max_length]

        # Eliminar caracteres de control
        input_string = ''.join(char for char in input_string
                              if char not in '\x00-\x1f\x7f')

        # Detectar patrones peligrosos
        for pattern in SecurityManager.DANGEROUS_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                raise ValidationError(
                    "Input contiene patrones potencialmente peligrosos",
                    field="input_string",
                    constraint="no_dangerous_patterns"
                )

        # Escapar HTML si no está permitido
        if not allow_html:
            input_string = html.escape(input_string)

        return input_string.strip()

    @staticmethod
    def validate_path(file_path: Union[str, Path],
                     base_dir: Optional[Union[str, Path]] = None,
                     must_exist: bool = False,
                     must_be_file: bool = False,
                     must_be_dir: bool = False) -> Path:
        """
        Valida y normaliza una ruta de archivo.

        Args:
            file_path: Ruta a validar
            base_dir: Directorio base (para prevenir path traversal)
            must_exist: Si debe existir
            must_be_file: Si debe ser un archivo
            must_be_dir: Si debe ser un directorio

        Returns:
            Ruta validada y normalizada
        """
        try:
            path = Path(file_path).expanduser().resolve()

            # Verificar path traversal
            if base_dir:
                base_path = Path(base_dir).resolve()
                try:
                    path.relative_to(base_path)
                except ValueError:
                    raise ValidationError(
                        "La ruta está fuera del directorio base permitido",
                        field="file_path",
                        value=str(path)
                    )

            # Verificar existencia
            if must_exist and not path.exists():
                raise ValidationError(
                    "La ruta no existe",
                    field="file_path",
                    value=str(path)
                )

            # Verificar tipo
            if must_be_file and path.exists() and not path.is_file():
                raise ValidationError(
                    "La ruta debe ser un archivo",
                    field="file_path",
                    value=str(path)
                )

            if must_be_dir and path.exists() and not path.is_dir():
                raise ValidationError(
                    "La ruta debe ser un directorio",
                    field="file_path",
                    value=str(path)
                )

            return path

        except (TypeError, ValueError) as e:
            raise ValidationError(
                f"Ruta inválida: {e}",
                field="file_path",
                value=str(file_path)
            )

    @staticmethod
    def validate_file_extension(filename: str,
                               allowed: Optional[set[str]] = None,
                               forbidden: Optional[set[str]] = None) -> str:
        """
        Valida la extensión de un archivo.

        Args:
            filename: Nombre del archivo
            allowed: Extensiones permitidas (usa default si None)
            forbidden: Extensiones prohibidas (usa default si None)

        Returns:
            Nombre de archivo validado
        """
        if not filename:
            raise ValidationError("Nombre de archivo vacío", field="filename")

        # Usar defaults si no se especifican
        allowed = allowed if allowed is not None else SecurityManager.ALLOWED_EXTENSIONS
        forbidden = forbidden if forbidden is not None else SecurityManager.FORBIDDEN_EXTENSIONS

        # Obtener extensión
        ext = Path(filename).suffix.lower()

        # Verificar extensiones prohibidas
        if ext in forbidden:
            raise ValidationError(
                f"Extensión '{ext}' no permitida",
                field="filename",
                value=filename,
                constraint=f"forbidden_extensions={forbidden}"
            )

        # Verificar extensiones permitidas
        if allowed and ext not in allowed:
            raise ValidationError(
                f"Extensión '{ext}' no está en las extensiones permitidas",
                field="filename",
                value=filename,
                constraint=f"allowed_extensions={allowed}"
            )

        return filename

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """
        Sanitiza un nombre de archivo para uso seguro.

        Args:
            filename: Nombre del archivo
            max_length: Longitud máxima

        Returns:
            Nombre de archivo sanitizado
        """
        if not filename:
            return "unnamed"

        # Eliminar caracteres peligrosos
        dangerous_chars = '<>:"/\\|?*\0'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Eliminar espacios al inicio y final
        filename = filename.strip()

        # Limitar longitud
        if len(filename) > max_length:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            name = name[:max_length - len(ext) - 1]
            filename = f"{name}.{ext}" if ext else name

        # Asegurar que no esté vacío después de sanitización
        if not filename:
            return "unnamed"

        return filename

    @staticmethod
    def validate_url(url: str,
                    allowed_schemes: Optional[list[str]] = None,
                    allow_local: bool = False) -> str:
        """
        Valida una URL.

        Args:
            url: URL a validar
            allowed_schemes: Esquemas permitidos
            allow_local: Si permite URLs locales

        Returns:
            URL validada
        """
        if not url or not url.strip():
            raise ValidationError("URL vacía", field="url")

        # Usar defaults si no se especifican
        allowed_schemes = allowed_schemes or ['http', 'https']

        try:
            parsed = urlparse(url)

            # Verificar esquema
            if not parsed.scheme:
                raise ValidationError("URL sin esquema", field="url", value=url)

            if parsed.scheme not in allowed_schemes:
                raise ValidationError(
                    f"Esquema '{parsed.scheme}' no permitido",
                    field="url",
                    value=url,
                    constraint=f"allowed_schemes={allowed_schemes}"
                )

            # Verificar URLs locales si no están permitidas
            if not allow_local:
                hostname = parsed.hostname or ''
                if hostname in ['localhost', '127.0.0.1', '::1'] or hostname.startswith('192.168.'):
                    raise ValidationError(
                        "URLs locales no permitidas",
                        field="url",
                        value=url
                    )

            # Reconstruir URL limpia
            clean_url = urlunparse(parsed)
            return clean_url

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"URL inválida: {e}",
                field="url",
                value=url
            )

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Genera un token seguro aleatorio.

        Args:
            length: Longitud del token

        Returns:
            Token seguro
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def generate_api_key(prefix: str = "nvx", length: int = 32) -> str:
        """
        Genera una API key segura.

        Args:
            prefix: Prefijo de la API key
            length: Longitud del componente aleatorio

        Returns:
            API key formateada
        """
        random_part = SecurityManager.generate_secure_token(length)
        return f"{prefix}_{random_part}"

    @staticmethod
    def hash_string(input_string: str, salt: Optional[str] = None) -> str:
        """
        Hashea un string de forma segura.

        Args:
            input_string: String a hashear
            salt: Salt opcional

        Returns:
            Hash del string
        """
        import hashlib

        if salt:
            input_string = f"{salt}{input_string}"

        return hashlib.sha256(input_string.encode()).hexdigest()

    @staticmethod
    def validate_command(command: str, allowed_commands: Optional[list[str]] = None) -> bool:
        """
        Valida un comando de shell para prevenir inyección.

        Args:
            command: Comando a validar
            allowed_commands: Lista de comandos permitidos

        Returns:
            True si el comando es seguro
        """
        if not command or not command.strip():
            return False

        # Verificar caracteres peligrosos
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
        for char in dangerous_chars:
            if char in command:
                return False

        # Verificar comandos permitidos
        if allowed_commands:
            command_base = command.split()[0] if command.split() else ""
            if command_base not in allowed_commands:
                return False

        return True

    @staticmethod
    def sanitize_json(json_string: str, max_size: int = 1024 * 1024) -> dict:
        """
        Sanitiza y parsea JSON de forma segura.

        Args:
            json_string: String JSON
            max_size: Tamaño máximo en bytes

        Returns:
            Diccionario parseado
        """
        if not json_string or not json_string.strip():
            raise ValidationError("JSON vacío", field="json")

        if len(json_string.encode()) > max_size:
            raise ValidationError(
                "JSON demasiado grande",
                field="json",
                constraint=f"max_size={max_size}"
            )

        try:
            import json
            data = json.loads(json_string)

            # Verificar que sea un diccionario
            if not isinstance(data, dict):
                raise ValidationError("JSON debe ser un objeto", field="json")

            return data

        except json.JSONDecodeError as e:
            raise ValidationError(
                f"JSON inválido: {e}",
                field="json",
                value=json_string
            )

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Valida una dirección de email.

        Args:
            email: Email a validar

        Returns:
            Email validado
        """
        if not email or not email.strip():
            raise ValidationError("Email vacío", field="email")

        email = email.strip().lower()

        # Patrón básico de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            raise ValidationError(
                "Formato de email inválido",
                field="email",
                value=email
            )

        return email

    @staticmethod
    def validate_phone(phone: str) -> str:
        """
        Valida un número de teléfono.

        Args:
            phone: Teléfono a validar

        Returns:
            Teléfono validado
        """
        if not phone or not phone.strip():
            raise ValidationError("Teléfono vacío", field="phone")

        # Eliminar caracteres no numéricos
        phone = re.sub(r'[^\d+]', '', phone)

        # Verificar longitud mínima
        if len(phone) < 10:
            raise ValidationError(
                "Teléfono demasiado corto",
                field="phone",
                value=phone
            )

        # Verificar longitud máxima
        if len(phone) > 15:
            raise ValidationError(
                "Teléfono demasiado largo",
                field="phone",
                value=phone
            )

        return phone

    @staticmethod
    def rate_limit_check(identifier: str,
                        max_requests: int = 100,
                        window_seconds: int = 60) -> bool:
        """
        Verifica si un identificador ha excedido el límite de rate limiting.

        Args:
            identifier: Identificador único (IP, user_id, etc.)
            max_requests: Máximo número de requests
            window_seconds: Ventana de tiempo en segundos

        Returns:
            True si está dentro del límite
        """
        # Implementación básica con diccionario en memoria
        # En producción, usar Redis o similar
        from collections import defaultdict
        import time

        if not hasattr(SecurityManager, '_rate_limit_data'):
            SecurityManager._rate_limit_data = defaultdict(list)

        current_time = time.time()
        requests = SecurityManager._rate_limit_data[identifier]

        # Limpiar requests antiguos
        requests = [req_time for req_time in requests
                    if current_time - req_time < window_seconds]
        SecurityManager._rate_limit_data[identifier] = requests

        # Verificar límite
        if len(requests) >= max_requests:
            return False

        # Agregar request actual
        requests.append(current_time)
        return True


class InputSanitizer:
    """Clase de utilidad para sanitización de inputs."""

    @staticmethod
    def sanitize_all(data: Any, max_depth: int = 10) -> Any:
        """
        Sanitiza recursivamente una estructura de datos.

        Args:
            data: Datos a sanitizar
            max_depth: Profundidad máxima de recursión

        Returns:
            Datos sanitizados
        """
        if max_depth <= 0:
            return data

        if isinstance(data, str):
            return SecurityManager.sanitize_string(data)

        elif isinstance(data, dict):
            return {key: InputSanitizer.sanitize_all(value, max_depth - 1)
                   for key, value in data.items()}

        elif isinstance(data, (list, tuple)):
            return [InputSanitizer.sanitize_all(item, max_depth - 1)
                   for item in data]

        elif isinstance(data, (int, float, bool)) or data is None:
            return data

        else:
            # Para otros tipos, intentar convertir a string
            try:
                return SecurityManager.sanitize_string(str(data))
            except Exception:
                return str(data)[:1000]  # Limitar longitud