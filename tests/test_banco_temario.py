"""Tests para coincidencia temario/banco y obtener_preguntas_fijas. Ejecutar: python -m pytest tests/test_banco_temario.py -v"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules import temario, banco_preguntas


def test_lista_temas_no_vacia():
    assert len(temario.LISTA_TEMAS) > 0


def test_banco_tiene_preguntas():
    assert len(banco_preguntas.BANCO_FIXED) > 0


def test_cada_pregunta_del_banco_tiene_campos_requeridos():
    """Cada pregunta del banco debe tener tema, pregunta, opciones, respuesta_correcta, explicacion."""
    requeridos = {"tema", "pregunta", "opciones", "respuesta_correcta", "explicacion"}
    for p in banco_preguntas.BANCO_FIXED:
        assert requeridos.issubset(p.keys()), f"Faltan campos en pregunta: {p.get('tema', '?')}"
        assert len(p["opciones"]) == 4, f"Se esperan 4 opciones en tema {p['tema']}"


def test_obtener_preguntas_fijas_devuelve_lista():
    temas = [temario.LISTA_TEMAS[0]]
    resultado = banco_preguntas.obtener_preguntas_fijas(temas, 2)
    assert isinstance(resultado, list)
    assert len(resultado) <= 2


def test_obtener_preguntas_fijas_tema_inexistente():
    resultado = banco_preguntas.obtener_preguntas_fijas(["Tema que no existe"], 5)
    assert resultado == []
