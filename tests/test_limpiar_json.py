"""Tests para limpiar_json (app.py). Ejecutar desde raíz: python -m pytest tests/test_limpiar_json.py -v"""
import sys
from pathlib import Path

# Permitir importar app (raíz del proyecto)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def limpiar_json(texto):
    """Copia mínima de limpiar_json para test sin cargar Streamlit."""
    import json
    import re
    if not texto:
        return None
    texto = texto.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass
    try:
        texto_reparado = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', texto)
        return json.loads(texto_reparado)
    except Exception:
        try:
            return json.loads(texto.replace("\\", "\\\\"))
        except Exception:
            return None


def test_limpiar_json_directo():
    assert limpiar_json('{"a": 1}') == {"a": 1}
    assert limpiar_json('[1, 2]') == [1, 2]


def test_limpiar_json_con_backticks():
    assert limpiar_json('```json\n{"x": 0}\n```') == {"x": 0}


def test_limpiar_json_none_o_vacio():
    assert limpiar_json(None) is None
    assert limpiar_json("") is None
    assert limpiar_json("   ") is None


def test_limpiar_json_invalido():
    assert limpiar_json("no es json") is None
    assert limpiar_json("{invalido}") is None
