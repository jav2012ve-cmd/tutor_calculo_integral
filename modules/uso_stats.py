"""
Contador de accesos anónimo: registra qué módulos se usan y cuántas consultas
hay en cada uno. No identifica al usuario.
"""
from __future__ import annotations

import json
import os

MODULOS = (
    "Entrenamiento",
    "Respuesta Guiada",
    "Quiz",
    "Tutor Preguntas Abiertas",
    "Corrección de Manuscritos",
)


def _ruta_archivo() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta = os.path.join(base, "data")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "uso_stats.json")


def _cargar() -> dict[str, int]:
    ruta = _ruta_archivo()
    if not os.path.isfile(ruta):
        return {m: 0 for m in MODULOS}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        for m in MODULOS:
            data.setdefault(m, 0)
        return data
    except (json.JSONDecodeError, OSError):
        return {m: 0 for m in MODULOS}


def _guardar(data: dict[str, int]) -> None:
    try:
        with open(_ruta_archivo(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def registrar_uso(modulo: str) -> None:
    """
    Incrementa en 1 el contador del módulo indicado.
    No identifica al usuario; solo registra uso anónimo.
    """
    if modulo not in MODULOS:
        return
    data = _cargar()
    data[modulo] = data.get(modulo, 0) + 1
    _guardar(data)


def obtener_estadisticas() -> dict[str, int]:
    """Devuelve los contadores actuales (solo lectura)."""
    return _cargar().copy()
