from __future__ import annotations

import os
from typing import Optional

import streamlit as st
from PIL import Image
from modules.temario import LISTA_TEMAS
from modules import uso_stats
from modules import seguimos

# Nombre de la aplicación (pestaña del navegador, títulos principales)
# ∑ (U+2211) sustituye la S inicial de «Sigma» en pantalla y en la pestaña del navegador.
APP_DISPLAY_NAME = "\N{N-ARY SUMMATION}igma tu Tutor de Cálculo Integral"

# Logo de bienvenida (raíz del proyecto o carpeta assets; prioriza .jpg)
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_LOGO_JPG = os.path.join(_ROOT, "LogoSigma.jpg")
_LOGO_JPG_ASSETS = os.path.join(_ROOT, "assets", "LogoSigma.jpg")
_LOGO_PNG = os.path.join(_ROOT, "LogoSigma.png")
_LOGO_PNG_ASSETS = os.path.join(_ROOT, "assets", "LogoSigma.png")


def _ruta_logo_sigma() -> Optional[str]:
    for p in (_LOGO_JPG, _LOGO_JPG_ASSETS, _LOGO_PNG, _LOGO_PNG_ASSETS):
        if os.path.isfile(p):
            return p
    return None


def _ruta_primera_existente(*rel_paths: str) -> Optional[str]:
    for rel in rel_paths:
        for base in (_ROOT, os.path.join(_ROOT, "assets")):
            p = os.path.join(base, rel)
            if os.path.isfile(p):
                return p
    return None


def _imagen_por_modo(modo_id: str) -> Optional[str]:
    mapping: dict[str, Optional[str]] = {
        seguimos.MODO_ID: _ruta_primera_existente(
            "botonSeguimos.jpg",
            "BotonSeguimos.jpg",
            "seguimos.jpg",
            "Seguimos.jpg",
        ),
        "a) Entrenamiento (Temario)": _ruta_primera_existente(
            "botonApracticar.jpg",
            "BotonApracticar.jpg",
            "a_practicar.jpg",
            "A_practicar.jpg",
        ),
        "b) Respuesta Guiada (Consultas)": _ruta_primera_existente(
            "BotonVamosPaso.jpg",
            "botonVamosPaso.jpg",
            "vamos_paso_a_paso.jpg",
            "VamosPaso.jpg",
        ),
        "c) Autoevaluación (Quiz)": _ruta_primera_existente(
            "BotonSimulacro.jpg",
            "botonSimulacro.jpg",
            "simulacro.jpg",
            "Simulacro.jpg",
            "Botones.png",
        ),
        "d) Tutor: Preguntas Abiertas": _ruta_primera_existente(
            "BotonDime.jpg",
            "botonDime.jpg",
            "dime_y_te_digo.jpg",
            "Dime.jpg",
        ),
        "e) Corrección de Manuscritos": _ruta_primera_existente(
            "BotonTeloReviso.jpg",
            "botonTeloReviso.jpg",
            "te_lo_reviso.jpg",
            "TeLoReviso.jpg",
        ),
    }
    return mapping.get(modo_id)


def ruta_imagen_modo(modo_id: str) -> Optional[str]:
    """Ruta del botón/imagen asociada a un modo (si existe)."""
    return _imagen_por_modo(modo_id)


def _recorte_vertical_superior(
    path_img: str, fraccion_altura: float = 0.40
) -> Optional[Image.Image]:
    """
    Recorta una franja superior del alto total (fraccion_altura = fracción que se conserva).
    Por defecto 0.40 → se muestra el 40% superior (se elimina el 60% inferior), ancho intacto, y=0.
    """
    try:
        with Image.open(path_img) as im:
            w, h = im.size
            if h <= 2:
                return im.copy()
            bottom = max(1, min(h, int(round(h * float(fraccion_altura)))))
            return im.crop((0, 0, w, bottom)).copy()
    except Exception:
        return None

# Matriz 2×3: (id interno, etiqueta en el botón, texto del tooltip al pasar el ratón)
MATRIZ_MODOS_2X3: tuple[tuple[tuple[str, str, str], ...], ...] = (
    (
        (
            seguimos.MODO_ID,
            "Seguimos adelante // Regístrate si eres nuevo",
            "Regístrate (si eres nuevo) o inicia sesión y revisa prioridades del temario, cobertura del curso "
            "y un plan para combinar A practicar, Vamos paso a paso, Simulacro, Dime y te digo y Te lo reviso.",
        ),
        (
            "a) Entrenamiento (Temario)",
            "A practicar",
            "Serie guiada paso a paso (estrategia, hito intermedio, resultado). En varios temas hay "
            "gráfico interactivo Plotly en el hito para validar límites y regiones.",
        ),
        (
            "b) Respuesta Guiada (Consultas)",
            "Vamos paso a paso",
            "Sube foto o texto de un ejercicio; el tutor analiza el problema y te guía con opciones "
            "de estrategia y pasos sin dar la solución de golpe.",
        ),
    ),
    (
        (
            "c) Autoevaluación (Quiz)",
            "Simulacro",
            "Simulacro tipo parcial (primer, segundo o temas personalizados) con calificación y "
            "descarga de informe en PDF al finalizar.",
        ),
        (
            "d) Tutor: Preguntas Abiertas",
            "Dime y te digo",
            "Chat para teoría y ejercicios del curso, alineado al estilo del banco y del temario.",
        ),
        (
            "e) Corrección de Manuscritos",
            "Te lo reviso",
            "Sube una foto de tu resolución escrita: se identifica el enunciado, se valora tu trabajo "
            "(correcto / parcial / incorrecto) y se sugieren mejoras.",
        ),
    ),
)

def inyectar_estilo_matematico():
    """
    CSS: fuentes (Orbitron en título principal h1; Roboto Mono en el resto), KaTeX y barra lateral oculta.
    Se ejecuta una sola vez por sesión.
    """
    if st.session_state.get("estilo_matematico_inyectado"):
        return
    st.session_state["estilo_matematico_inyectado"] = True

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700&family=Roboto+Mono:ital,wght@0,400;0,500;0,600;1,400&display=swap');

        /* Cuerpo y UI: Roboto Mono (no forzar dentro de KaTeX) */
        .stApp {
            font-family: 'Roboto Mono', monospace !important;
        }
        .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp p, .stApp label, .stApp span, .stApp li, .stApp td, .stApp th,
        .stApp button, .stApp input, .stApp textarea, .stApp select,
        .stCaption, [data-testid="stMarkdownContainer"] {
            font-family: 'Roboto Mono', monospace !important;
        }

        /* Nombre principal (st.title): Orbitron — encaja mejor con símbolos tipo \\sum en títulos */
        .stApp h1 {
            font-family: 'Orbitron', sans-serif !important;
            font-weight: 600;
            letter-spacing: 0.03em;
        }

        /* Ajustes generales para textos con LaTeX en Markdown */
        .stMarkdown p {
            line-height: 1.6;
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        /* KaTeX */
        .katex {
            font-size: 1.1em;
            max-width: 100%;
            overflow-x: auto;
            white-space: normal;
        }

        /* Contenedor que Streamlit usa para st.latex */
        .stLatex, .stLatex > div {
            max-width: 100%;
            overflow-x: auto;
        }

        /* Sin panel lateral: ancho completo para el contenido */
        section[data-testid="stSidebar"],
        div[data-testid="stSidebar"] {
            display: none !important;
        }
        div[data-testid="stSidebarCollapsedControl"],
        div[data-testid="collapsedControl"] {
            display: none !important;
        }
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* Tarjetas: st.container(border=True) — portal de registro y bloques similares */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
            border: 1px solid rgba(100, 116, 139, 0.38) !important;
            box-shadow: 0 6px 22px rgba(15, 23, 42, 0.09);
            background: linear-gradient(
                165deg,
                rgba(248, 250, 252, 0.94) 0%,
                rgba(255, 255, 255, 0.99) 100%
            );
            padding: 0.4rem 0.75rem 1rem;
            margin-bottom: 1.15rem;
        }

        [data-testid="stAppViewContainer"][data-theme="dark"] div[data-testid="stVerticalBlockBorderWrapper"],
        .stApp[data-theme="dark"] div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(
                165deg,
                rgba(30, 41, 59, 0.72) 0%,
                rgba(15, 23, 42, 0.58) 100%
            );
            border-color: rgba(148, 163, 184, 0.32) !important;
            box-shadow: 0 8px 26px rgba(0, 0, 0, 0.38);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def configurar_pagina():
    st.set_page_config(
        page_title=APP_DISPLAY_NAME,
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

def meta_modo(modo_id: str) -> tuple[str, str]:
    """Etiqueta corta del botón y texto de ayuda para un modo."""
    for fila in MATRIZ_MODOS_2X3:
        for mid, etiq, ayuda in fila:
            if mid == modo_id:
                return etiq, ayuda
    return modo_id, ""


def _limpiar_estado_volver_inicio() -> None:
    st.session_state.modo_actual = None
    st.session_state.messages = []
    st.session_state.pop("estudiante_nombre_seguimos", None)
    st.session_state.pop("estudiante_codigo_seguimos", None)
    st.session_state.pop("_seguimos_uso_registrado_sesion", None)
    st.session_state.pop("seguimos_paso", None)


def _aplicar_iniciar_modo(seleccion_visual: Optional[str]) -> None:
    """Guarda el modo y limpia estado residual al cambiar de modo."""
    if not seleccion_visual:
        return
    anterior = st.session_state.get("modo_actual")
    if seleccion_visual != anterior:
        st.session_state.quiz_activo = False
        st.session_state.preguntas_quiz = []
        st.session_state.indice_pregunta = 0
        st.session_state.respuestas_usuario = []
        if "trigger_quiz" in st.session_state:
            st.session_state.trigger_quiz = False
        st.session_state.entrenamiento_activo = False
        st.session_state.consulta_step = 0
        st.session_state.consulta_data = None
        st.session_state.consulta_validada = False
        st.session_state.historial_tutor_abierto = []
        st.session_state.manuscrito_correccion = None
    st.session_state.modo_actual = seleccion_visual
    if seleccion_visual == seguimos.MODO_ID and anterior != seguimos.MODO_ID:
        st.session_state.seguimos_paso = seguimos.SEGUIMOS_PASO_ENTRADA
    if seleccion_visual != seguimos.MODO_ID:
        st.session_state.pop("seguimos_paso", None)


def mostrar_portada_selector_modos() -> None:
    """
    Solo en la portada (sin modo activo): cuadrícula 2×3 con vista previa recortada del botón.
    Al elegir un modo, la app muestra otra «página» con imagen completa y la interfaz del modo.
    """
    st.markdown("#### 🎛️ Modo de estudio")
    st.caption(
        "Pulsa un modo para abrir su página: verás el botón completo y las herramientas de ese modo."
    )

    for i, fila in enumerate(MATRIZ_MODOS_2X3):
        cols = st.columns(3)
        for j, (modo_id, etiqueta, ayuda) in enumerate(fila):
            with cols[j]:
                if st.button(
                    etiqueta,
                    key=f"modo_tile_{i}_{j}",
                    use_container_width=True,
                    type="secondary",
                    help=ayuda,
                ):
                    _aplicar_iniciar_modo(modo_id)
                    st.rerun()
                img_modo = _imagen_por_modo(modo_id)
                if img_modo:
                    img_crop = _recorte_vertical_superior(img_modo)
                    if img_crop is not None:
                        st.image(img_crop, use_container_width=True)
                    else:
                        st.image(img_modo, use_container_width=True)
                else:
                    st.caption("Imagen no encontrada")


def _mostrar_imagen_modo_compacta(path_img: str) -> None:
    """Muestra la imagen del modo en la primera celda de una fila 1×2."""
    c_img, _ = st.columns([1, 3])
    with c_img:
        st.image(path_img, use_container_width=True)


def mostrar_cabecera_pagina_modo() -> Optional[str]:
    """
    Cabecera de la «página» del modo activo: volver, título y (si aplica) temario.
    La imagen del modo se muestra junto al título principal de la app.
    Devuelve el tema seleccionado solo en modo entrenamiento; en otros modos, None.
    """
    modo = st.session_state.get("modo_actual")
    if not modo:
        return None

    if st.button("← Volver al inicio", key="btn_volver_inicio"):
        _limpiar_estado_volver_inicio()
        st.rerun()

    etiq, ayuda = meta_modo(modo)
    st.markdown(f"### {etiq}")
    if ayuda:
        st.caption(ayuda)

    tema_seleccionado: Optional[str] = None
    if modo == "a) Entrenamiento (Temario)":
        st.divider()
        st.markdown("##### 📘 Temario detallado")
        if "tema_seleccionado" not in st.session_state:
            st.session_state.tema_seleccionado = LISTA_TEMAS[0]
        tema_seleccionado = st.selectbox("Selecciona el punto:", LISTA_TEMAS, key="tema_select_pagina_modo")
        st.session_state.tema_seleccionado = tema_seleccionado

    st.divider()
    return tema_seleccionado


def mostrar_dudas_resueltas() -> None:
    """Al pie del panel central: un solo contador con la suma de interacciones por modo."""
    st.divider()
    warn = st.session_state.get("_uso_stats_supabase_warn")
    if warn:
        st.caption(warn)
    stats = uso_stats.obtener_estadisticas()
    total = sum(int(stats.get(m, 0) or 0) for m in uso_stats.MODULOS)
    st.metric("Dudas resueltas", total)


def mostrar_bienvenida():
    """Pantalla inicial sin modo: logo y recordatorio breve."""
    logo = _ruta_logo_sigma()
    if logo:
        st.image(logo, use_container_width=True)
    else:
        st.warning(
            "No se encontró el logo. Coloca **`LogoSigma.jpg`** (o `LogoSigma.png`) en la raíz del proyecto "
            "o en la carpeta **`assets/`**."
        )

    st.info("👆 **Elige un modo en la cuadrícula de arriba para comenzar.**")
