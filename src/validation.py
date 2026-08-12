# src/validation.py
"""
Sistema de validación robusto para inputs de usuario en Narrivox.
Proporciona validadores reutilizables y manejo consistente de errores.
"""

import re
from pathlib import Path
from typing import Any, Optional, Union

from src.exceptions import ValidationError


class Validator:
    """Clase base para validadores."""

    @staticmethod
    def validate_required(value: Any, field_name: str = "valor") -> Any:
        """Valida que un valor no sea None o vacío."""
        if value is None:
            raise ValidationError(f"{field_name} es requerido", field=field_name)

        if isinstance(value, str) and not value.strip():
            raise ValidationError(f"{field_name} no puede estar vacío", field=field_name)

        if isinstance(value, (list, dict)) and len(value) == 0:
            raise ValidationError(f"{field_name} no puede estar vacío", field=field_name)

        return value

    @staticmethod
    def validate_string(value: Any, field_name: str = "valor",
                       min_length: int = 0, max_length: int = 10000,
                       pattern: Optional[str] = None) -> str:
        """Valida y normaliza un string."""
        if value is None:
            raise ValidationError(f"{field_name} es requerido", field=field_name)

        if not isinstance(value, str):
            raise ValidationError(
                f"{field_name} debe ser un string, recibido: {type(value).__name__}",
                field=field_name,
                value=str(value)
            )

        value = value.strip()

        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} debe tener al menos {min_length} caracteres",
                field=field_name,
                value=value,
                constraint=f"min_length={min_length}"
            )

        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} no puede exceder {max_length} caracteres",
                field=field_name,
                value=value,
                constraint=f"max_length={max_length}"
            )

        if pattern and not re.match(pattern, value):
            raise ValidationError(
                f"{field_name} no cumple con el formato requerido",
                field=field_name,
                value=value,
                constraint=f"pattern={pattern}"
            )

        return value

    @staticmethod
    def validate_integer(value: Any, field_name: str = "valor",
                        min_value: Optional[int] = None,
                        max_value: Optional[int] = None) -> int:
        """Valida y convierte a entero."""
        if value is None:
            raise ValidationError(f"{field_name} es requerido", field=field_name)

        try:
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    raise ValueError("String vacío")

            int_value = int(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"{field_name} debe ser un entero válido",
                field=field_name,
                value=value,
                constraint="type=integer"
            )

        if min_value is not None and int_value < min_value:
            raise ValidationError(
                f"{field_name} debe ser al menos {min_value}",
                field=field_name,
                value=int_value,
                constraint=f"min_value={min_value}"
            )

        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"{field_name} no puede exceder {max_value}",
                field=field_name,
                value=int_value,
                constraint=f"max_value={max_value}"
            )

        return int_value

    @staticmethod
    def validate_float(value: Any, field_name: str = "valor",
                      min_value: Optional[float] = None,
                      max_value: Optional[float] = None) -> float:
        """Valida y convierte a float."""
        if value is None:
            raise ValidationError(f"{field_name} es requerido", field=field_name)

        try:
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    raise ValueError("String vacío")

            float_value = float(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"{field_name} debe ser un número válido",
                field=field_name,
                value=value,
                constraint="type=float"
            )

        if min_value is not None and float_value < min_value:
            raise ValidationError(
                f"{field_name} debe ser al menos {min_value}",
                field=field_name,
                value=float_value,
                constraint=f"min_value={min_value}"
            )

        if max_value is not None and float_value > max_value:
            raise ValidationError(
                f"{field_name} no puede exceder {max_value}",
                field=field_name,
                value=float_value,
                constraint=f"max_value={max_value}"
            )

        return float_value

    @staticmethod
    def validate_path(value: Any, field_name: str = "ruta",
                     must_exist: bool = False,
                     must_be_file: bool = False,
                     must_be_dir: bool = False,
                     create_if_missing: bool = False) -> Path:
        """Valida y normaliza una ruta de archivo/directorio."""
        if value is None:
            raise ValidationError(f"{field_name} es requerida", field=field_name)

        try:
            path = Path(value).expanduser().resolve()
        except (TypeError, ValueError) as e:
            raise ValidationError(
                f"{field_name} no es una ruta válida",
                field=field_name,
                value=value
            )

        # Validar que no contenga caracteres peligrosos
        path_str = str(path)
        dangerous_patterns = ['..', '~', '/etc/', '/sys/', '/proc/']
        for pattern in dangerous_patterns:
            if pattern in path_str:
                raise ValidationError(
                    f"{field_name} contiene patrones peligrosos",
                    field=field_name,
                    value=value,
                    constraint=f"no_{pattern}"
                )

        if must_exist and not path.exists():
            if create_if_missing:
                try:
                    if must_be_dir:
                        path.mkdir(parents=True, exist_ok=True)
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise ValidationError(
                        f"No se pudo crear {field_name}: {e}",
                        field=field_name,
                        value=value
                    )
            else:
                raise ValidationError(
                    f"{field_name} no existe",
                    field=field_name,
                    value=value
                )

        if must_be_file and path.exists() and not path.is_file():
            raise ValidationError(
                f"{field_name} debe ser un archivo",
                field=field_name,
                value=value
            )

        if must_be_dir and path.exists() and not path.is_dir():
            raise ValidationError(
                f"{field_name} debe ser un directorio",
                field=field_name,
                value=value
            )

        return path

    @staticmethod
    def validate_choice(value: Any, field_name: str = "valor",
                       choices: Optional[list[Any]] = None, case_sensitive: bool = True) -> Any:
        """Valida que un valor esté en una lista de opciones."""
        if value is None:
            raise ValidationError(f"{field_name} es requerido", field=field_name)

        if choices is None:
            raise ValidationError(f"{field_name} requiere una lista de choices", field=field_name)

        if not case_sensitive and isinstance(value, str):
            value_lower = value.lower()
            for choice in choices:
                if isinstance(choice, str) and choice.lower() == value_lower:
                    return choice

        if value not in choices:
            raise ValidationError(
                f"{field_name} debe ser uno de: {', '.join(map(str, choices))}",
                field=field_name,
                value=value,
                constraint=f"choices={choices}"
            )

        return value

    @staticmethod
    def validate_email(value: Any, field_name: str = "email") -> str:
        """Valida una dirección de email."""
        value = Validator.validate_string(value, field_name, max_length=254)

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValidationError(
                f"{field_name} no es una dirección de email válida",
                field=field_name,
                value=value,
                constraint="email_format"
            )

        return value

    @staticmethod
    def validate_url(value: Any, field_name: str = "url",
                    allowed_schemes: Optional[list[str]] = None) -> str:
        """Valida una URL."""
        value = Validator.validate_string(value, field_name, max_length=2048)

        if not value.startswith(('http://', 'https://')):
            raise ValidationError(
                f"{field_name} debe comenzar con http:// o https://",
                field=field_name,
                value=value,
                constraint="url_scheme"
            )

        if allowed_schemes:
            scheme = value.split('://')[0]
            if scheme not in allowed_schemes:
                raise ValidationError(
                    f"{field_name} debe usar uno de estos esquemas: {', '.join(allowed_schemes)}",
                    field=field_name,
                    value=value,
                    constraint=f"allowed_schemes={allowed_schemes}"
                )

        return value

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """Sanitiza un nombre de archivo para uso seguro."""
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
    def validate_json(value: Any, field_name: str = "json") -> dict:
        """Valida y parsea JSON."""
        if value is None:
            raise ValidationError(f"{field_name} es requerido", field=field_name)

        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValidationError(f"{field_name} no puede estar vacío", field=field_name)

            try:
                import json
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f"{field_name} no es JSON válido: {e}",
                    field=field_name,
                    value=value,
                    constraint="valid_json"
                )

        raise ValidationError(
            f"{field_name} debe ser un dict o string JSON válido",
            field=field_name,
            value=value,
            constraint="type=dict_or_json_string"
        )


class ProjectValidator(Validator):
    """Validador específico para datos de proyectos."""

    @staticmethod
    def validate_serie_name(serie: str) -> str:
        """Valida el nombre de una serie."""
        serie = ProjectValidator.validate_string(
            serie, "serie",
            min_length=1, max_length=100
        )

        # Sanitizar para uso en nombres de archivo
        return Validator.sanitize_filename(serie)

    @staticmethod
    def validate_part_number(parte: Any) -> int:
        """Valida el número de parte."""
        return ProjectValidator.validate_integer(
            parte, "parte",
            min_value=1, max_value=9999
        )

    @staticmethod
    def validate_script_text(script: str) -> str:
        """Valida el texto de un guion."""
        return ProjectValidator.validate_string(
            script, "guion",
            min_length=10, max_length=50000
        )

    @staticmethod
    def validate_prompt_text(prompt: str) -> str:
        """Valida el texto de un prompt."""
        return ProjectValidator.validate_string(
            prompt, "prompt",
            min_length=5, max_length=1000
        )

    @staticmethod
    def validate_voice_code(voice_code: str) -> str:
        """Valida un código de voz."""
        return ProjectValidator.validate_string(
            voice_code, "voz",
            min_length=1, max_length=50
        )

    @staticmethod
    def validate_emotion(emotion: str) -> str:
        """Valida una emoción."""
        valid_emotions = [
            "neutral", "feliz", "triste", "enojado", "miedo",
            "sorpresa", "disgusto", "anticipación", "confianza", "alegría"
        ]
        return ProjectValidator.validate_choice(
            emotion.lower() if emotion else "neutral",
            "emoción",
            valid_emotions,
            case_sensitive=False
        )


class ConfigValidator(Validator):
    """Validador específico para configuración."""

    @staticmethod
    def validate_api_key(api_key: str, service: str) -> str:
        """Valida una API key."""
        if not api_key or not api_key.strip():
            raise ValidationError(
                f"API Key de {service} no puede estar vacía",
                field=f"{service}_api_key"
            )

        api_key = api_key.strip()

        # Validar longitud mínima (las API keys suelen tener al menos 10 caracteres)
        if len(api_key) < 10:
            raise ValidationError(
                f"API Key de {service} parece inválida (demasiado corta)",
                field=f"{service}_api_key",
                value=api_key,
                constraint="min_length=10"
            )

        return api_key

    @staticmethod
    def validate_provider(provider: str, valid_providers: list[str]) -> str:
        """Valida un proveedor de IA."""
        return ConfigValidator.validate_choice(
            provider, "proveedor",
            valid_providers,
            case_sensitive=True
        )

    @staticmethod
    def validate_model_config(config: dict) -> dict:
        """Valida la configuración de modelos."""
        if not isinstance(config, dict):
            raise ValidationError(
                "La configuración de modelos debe ser un diccionario",
                field="model_config"
            )

        # Validar estructura básica
        required_keys = ['model_id', 'device']
        for key in required_keys:
            if key not in config:
                raise ValidationError(
                    f"La configuración de modelo requiere '{key}'",
                    field="model_config",
                    constraint=f"required_keys={required_keys}"
                )

        # Validar device
        valid_devices = ['cpu', 'cuda', 'mps']
        if config['device'] not in valid_devices:
            raise ValidationError(
                f"Device debe ser uno de: {', '.join(valid_devices)}",
                field="model_config.device",
                value=config['device'],
                constraint=f"valid_devices={valid_devices}"
            )

        return config