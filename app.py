from __future__ import annotations
import json
import os
import re
import sys
import time
import base64
from typing import Any, List, Optional, Union

import streamlit as st
from PIL import Image

# Asegura que la carpeta `modules/` esté en `sys.path` aunque Streamlit Cloud
# ejecute desde una ubicación distinta (o "App location" no sea la raíz del repo).
HERE = os.path.abspath(os.path.dirname(__file__))
modules_parent = None
for candidate in [HERE] + [os.path.abspath(os.path.join(HERE, os.pardir))] + [
    os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
]:
    if os.path.isdir(os.path.join(candidate, "modules")):
        modules_parent = candidate
        break

if modules_parent and modules_parent not in sys.path:
    sys.path.insert(0, modules_parent)

from modules import (
    ia_core,
    interfaz,
    temario,
    banco_preguntas,
    banco_muestras,
    uso_stats,
    registro_interacciones,
    graficos_entrenamiento,
    seguimos,
    auth_estudiantes,
    planes_estudio,
    planes_estudio_oficiales,
    contexto_universitario,
)

# --- CONFIGURACIÓN CENTRALIZADA ---
NUM_EJERCICIOS_ENTRENAMIENTO = 5
NUM_PREGUNTAS_QUIZ = 5
INTENTOS_MAX_IA = 3
MULTIPLICADOR_ESPERA_429 = 4  # segundos por intento ante error 429
MAX_MENSAJES_HISTORIAL_TUTOR = 10  # últimos N mensajes para contexto IA
AVISO_HISTORIAL_LARGO = 20  # si hay más mensajes, mostrar aviso

# --- 1. CONFIGURACIÓN INICIAL ---
interfaz.configurar_pagina()
interfaz.inyectar_estilo_matematico()
interfaz.inyectar_estilo_universitario()

def _decodificar_claims_jwt_sin_verificar(token: str) -> Optional[dict]:
    """
    Decodifica el payload de un JWT (sin verificar firma) para diagnóstico.
    Devuelve dict o None si no puede parsear.
    """
    try:
        parts = (token or "").strip().split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        # base64url sin padding
        payload_b64 += "=" * (-len(payload_b64) % 4)
        raw = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        data = json.loads(raw.decode("utf-8", errors="ignore"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _inyectar_supabase_desde_connections() -> None:
    """
    Compatibilidad con Streamlit Secrets usando [connections.supabase].
    Exporta a variables de entorno para que los módulos existentes lo detecten.
    """
    try:
        sec = st.secrets
        sec_get = getattr(sec, "get", None)
        if not callable(sec_get):
            return
        conns = sec_get("connections") or {}
        conns_get = getattr(conns, "get", None)
        if not callable(conns_get):
            return
        sb = conns_get("supabase") or {}
        sb_get = getattr(sb, "get", None)
        if not callable(sb_get):
            return

        url = (sb_get("SUPABASE_URL") or sb_get("url") or "").strip()
        key = (
            (sb_get("SUPABASE_SERVICE_ROLE_KEY") or sb_get("service_role_key") or sb_get("key") or "").strip()
        )
        if url and not os.environ.get("SUPABASE_URL"):
            os.environ["SUPABASE_URL"] = url
        if key and not os.environ.get("SUPABASE_SERVICE_ROLE_KEY") and not os.environ.get("SUPABASE_KEY"):
            os.environ["SUPABASE_SERVICE_ROLE_KEY"] = key

        # Aviso si parece ser anon (muy común cuando copian el key equivocado)
        if key:
            claims = _decodificar_claims_jwt_sin_verificar(key)
            if claims and claims.get("role") == "anon":
                st.warning(
                    "⚠️ Detecté que la clave de Supabase parece ser `anon` (role=anon). "
                    "Para **registro/login** necesitas la clave **service_role** "
                    "(Supabase → Project Settings → API → service_role)."
                )
    except Exception:
        return


_inyectar_supabase_desde_connections()


def _cargar_admin_dashboard():
    """Import diferido del panel admin para evitar caída global si ese módulo falla."""
    try:
        from modules import admin_dashboard as _admin_dashboard
        return _admin_dashboard
    except Exception as e:
        st.error(f"No se pudo cargar el panel admin: {e}")
        return None


def _render_admin_panel_safe() -> bool:
    """Renderiza panel admin solo si el módulo carga correctamente."""
    _ad = _cargar_admin_dashboard()
    if _ad is None:
        return False
    _ad.render_admin_panel()
    return True


def _clave_acceso_admin_portada() -> str:
    """Clave para desbloquear el panel desde la portada (override con Secrets o env)."""
    try:
        v = str(st.secrets.get("ADMIN_PORTADA_PASSWORD", "")).strip()
        if v:
            return v
    except Exception:
        pass
    return (os.environ.get("ADMIN_PORTADA_PASSWORD") or "sigma_admin").strip() or "sigma_admin"


if not ia_core.configurar_gemini():
    st.stop()

model, nombre_modelo = ia_core.iniciar_modelo()

# =======================================================
# FUNCIONES DE SEGURIDAD Y UTILIDADES
# =======================================================

def generar_contenido_seguro(
    prompt_parts: Union[str, list],
    intentos_max: Optional[int] = None,
) -> Optional[Any]:
    """
    Intenta llamar a la IA con texto o imágenes.
    Soporta lista de partes (prompt + imagen) o solo texto.
    """
    if intentos_max is None:
        intentos_max = INTENTOS_MAX_IA
    texto_pregunta = registro_interacciones.serializar_pregunta(prompt_parts)
    modelo_log = nombre_modelo or ""
    errores_recientes = ""
    for i in range(intentos_max):
        try:
            response = model.generate_content(prompt_parts)
            texto_respuesta = registro_interacciones.extraer_texto_respuesta(response)
            registro_interacciones.registrar_interaccion(
                texto_pregunta, texto_respuesta, modelo_log
            )
            return response
        except Exception as e:
            errores_recientes = str(e)
            if "429" in str(e):
                tiempo_espera = MULTIPLICADOR_ESPERA_429 * (i + 1)
                st.toast(f"🚦 Tráfico alto. Reintentando en {tiempo_espera}s...", icon="⏳")
                time.sleep(tiempo_espera)
            else:
                time.sleep(1)

    st.error(f"❌ Error de conexión: {errores_recientes}")
    registro_interacciones.registrar_interaccion(
        texto_pregunta,
        f"(sin respuesta tras reintentos) {errores_recientes}",
        modelo_log,
    )
    return None

def _parece_formula(contenido: str) -> bool:
    """True si el contenido entre backticks parece una fórmula (no texto largo)."""
    c = contenido.strip()
    if not c or len(c) > 80:
        return False
    # Exponente, LaTeX, fracción numérica, variable sola, dx/dt
    if re.search(r"\^|\\\\|\\frac|\\sqrt|\\int|\\cdot", c):
        return True
    if re.match(r"^\d+/\d+$", c):
        return True
    if re.match(r"^[a-zA-Z]$", c) or c in ("dx", "dt"):
        return True
    if re.search(r"[a-zA-Z]\^\d|[a-zA-Z]\^\{", c):
        return True
    return False


def preparar_latex_para_streamlit(texto: Optional[str]) -> str:
    if not texto:
        return ""

    # 1. Normalización de escapes de barra invertida de la IA
    t = str(texto).replace('\\\\', '\\').replace(r'\$', '$')

    # 2. Unificación: Si hay fragmentos pegados tipo "$ \int $ $ x $", los une en "$ \int x $"
    t = re.sub(r'\$\s*\$', ' ', t)

    # 3. PROTECCIÓN: Si el texto ya tiene bloques delimitados, no los tocamos.
    # Pero si detectamos comandos LaTeX fuera de $, envolvemos la frase matemática completa.

    # Expresión regular para detectar una fórmula completa (incluyendo paréntesis y potencias)
    # (reservada para extensiones; el envoltorio de integrales usa el bloque siguiente)
    patron_formula_completa = (
        r'(\\int|\\frac|\\sqrt|\\alpha|\\beta|[\w\d\s\+\-\*\/\^\(\)]+?)(?=\s|$|\.|\,)'
    )

    # Bloque integral completo (grupo), no token a token (DOTALL: \int en línea siguiente al texto)
    if ("\\int" in t or "\\frac" in t) and "$" not in t:
        t = re.sub(
            r'(\\int.*?(?:dx|dy|dt|dz))',
            r' $\1$ ',
            t,
            flags=re.DOTALL,
        )

    # Opciones de quiz / fórmulas cortas con \frac, \ln, etc. sin delimitadores
    if "$" not in t and len(t.strip()) <= 280 and re.search(
        r'\\(?:frac|sqrt|ln|int|sum|cdot|left|right|infty|partial|alpha|beta|gamma|delta|theta|pi)\b',
        t,
    ):
        t = f"${t.strip()}$"

    return t


def latex_display_puro(texto: Optional[str]) -> str:
    """
    Para campos que la IA devuelve como LaTeX puro (sin texto natural):
    paso_intermedio, resultado_final, enunciado_latex. Quita cualquier $
    residual y envuelve en $$...$$ para display math (estilo VVappy).
    Evita delimitadores rotos o dobles.
    """
    if not texto:
        return ""
    s = str(texto).replace("$", "").strip()
    if not s:
        return ""
    return f"$${s}$$"

def _limpiar_para_st_latex(texto: Any) -> str:
    """
    Streamlit `st.latex()` espera una expresión LaTeX sin delimitadores ($$ o $).
    Si la IA devolvió $...$ o $$...$$, los removemos.
    """
    s = str(texto).strip()
    if s.startswith("$$") and s.endswith("$$"):
        return s[2:-2].strip()
    if s.startswith("$") and s.endswith("$"):
        return s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    if s.endswith("$"):
        s = s[:-1].strip()
    return s

def _render_texto_con_latex(texto: Optional[str]) -> None:
    """
    Renderiza texto mixto separando por delimitadores $...$ / $$...$$.
    - Texto: `st.markdown`
    - Fórmulas: `st.latex` (sin $ / $$)

    Esto reduce fallos cuando el markdown recibe delimitadores rotos o
    cuando hay un '$' molesto en el texto natural.
    """
    if not texto:
        return

    s = preparar_latex_para_streamlit(texto)
    s = str(s)

    # Si hay un '$' suelto al final, lo quitamos (caso típico del enunciado).
    if s.count("$") % 2 != 0:
        s = re.sub(r'\$\s*$', '', s).strip()

    i = 0
    n = len(s)
    while i < n:
        if s.startswith("$$", i):
            j = s.find("$$", i + 2)
            if j == -1:
                st.markdown(s[i:])
                break
            expr = s[i + 2 : j].strip()
            if expr:
                st.latex(expr)
            i = j + 2
            continue

        if s[i] == "$":
            j = s.find("$", i + 1)
            if j == -1:
                st.markdown(s[i:])
                break
            expr = s[i + 1 : j].strip()
            if expr:
                st.latex(expr)
            i = j + 1
            continue

        # Captura texto hasta el siguiente '$'
        j = s.find("$", i)
        if j == -1:
            j = n
        chunk = s[i:j]
        if chunk.strip():
            st.markdown(chunk)
        i = j


def mostrar_como_formula_si_corresponde(texto: Optional[str]) -> str:
    """
    Para enunciados y fórmulas sueltas (pregunta, paso_intermedio, resultado_final).
    Pasa por preparar_latex; si el resultado es una sola fórmula sin $/$$, la envuelve en $$.
    Misma pauta que en Corrección de Manuscritos: no tocar texto mixto.
    """
    t = preparar_latex_para_streamlit(texto or "")
    s = t.strip()
    if not s:
        return t
    if s.startswith(("$", "$$")):
        return t
    if "\\int" in s or "\\sqrt" in s or "\\frac" in s:
        return "$$" + s + "$$"
    return t


def limpiar_json(texto: Optional[str]) -> Optional[Any]:
    """
    Limpieza quirúrgica para respuestas con LaTeX.
    Devuelve dict o list si parsea correctamente; None en caso contrario.
    """
    if not texto: return None
    texto = texto.replace("```json", "").replace("```", "").strip()
    
    # Intento 1: Directo
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    # Intento 2: Reparación Regex para LaTeX
    try:
        # Escapa barras invertidas que no sean de control JSON
        texto_reparado = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', texto)
        return json.loads(texto_reparado)
    except Exception:
        # Intento 3: Fuerza bruta si falla regex
        try:
            return json.loads(texto.replace("\\", "\\\\"))
        except Exception:
            return None


def _bloque_lista_temas_oficial() -> str:
    return "\n".join(f"  - {t}" for t in temario.LISTA_TEMAS)


def clasificar_tema_desde_texto(texto_usuario: str) -> Optional[str]:
    """
    Pide a la IA que elija un tema de LISTA_TEMAS alineado a la consulta (estadísticas).
    """
    t = (texto_usuario or "").strip()
    if not t:
        return None
    lista_txt = _bloque_lista_temas_oficial()
    prompt = f"""Eres asistente de catalogación para el curso de Cálculo Integral.
Indica a qué tema del temario oficial corresponde mejor la consulta del estudiante.

LISTA OFICIAL (elige UN solo texto EXACTO como aparece abajo, carácter por carácter, o null si ninguno encaja):
{lista_txt}

Consulta:
\"\"\"{t[:4000]}\"\"\"

Responde ÚNICAMENTE con JSON válido, sin markdown:
{{"tema_catedra": "<texto exacto de la lista>" | null}}
"""
    resp = generar_contenido_seguro(prompt)
    if not resp:
        return None
    data = limpiar_json(resp.text)
    if not isinstance(data, dict):
        return None
    return temario.normalizar_tema_curso(data.get("tema_catedra"))


def generar_tutor_paso_a_paso(pregunta_texto: str, tema: str) -> Optional[dict]:
    """Genera la tutoría para el modo Entrenamiento (Banco/IA)."""
    regla_tema = ""
    if "1.1.1" in (tema or "") or "Integrales Indefinidas" in (tema or ""):
        regla_tema = """
    RESTRICCIÓN DE CONTENIDO (CRÍTICO para este tema):
    - El tema "1.1.1 Integrales Indefinidas Directas" es EXCLUSIVO de integrales INDEFINIDAS.
    - NO uses integrales definidas: ni límites de integración (ej. \\int_a^b, \\int_0^1), ni "evalúe la integral definida", ni aplicación del teorema fundamental.
    - PROHIBIDO cambios de variable / sustitución: NUNCA escribas "u =", "cambio de variable", "sustitución", ni resuelvas con $du$.
    - Usa SOLO métodos directos:
      * Regla de la potencia para $x^n$ y polinomios ya expandidos.
      * Regla de exponentiales: integrales de $e^{ax}$.
      * Distribución por división en fracciones racionales simples (reducir por álgebra antes de integrar).
      * Multiplicación por constantes y suma distributiva.
    - Si el ejercicio que te pasan tiene integral definida, reescríbelo como integral INDEFINIDA equivalente (misma función a integrar, sin límites) o genera un ejercicio de integral indefinida acorde al tema.
    """
    prompt = f"""
    Actúa como un profesor experto. Para el ejercicio: "{pregunta_texto}"
    {regla_tema}
    Genera un objeto JSON.

    REGLAS DE FORMATO (CRÍTICO):
    1. El campo "feedback_estrategia" es texto natural.
    2. Si incluyes fórmulas dentro del texto, úsalas ASÍ: $f(x) = x^2$.
    3. NUNCA escribas párrafos largos dentro de símbolos $.

    PROHIBICIÓN DE FRAGMENTACIÓN: No cierres y abras dólares para la misma expresión.
    MAL: $\\int$ $x^2$ $dx$
    BIEN: $\\int x^2 dx$
    Escribe cada término matemático como una unidad atómica (una sola expresión debe tener un solo par $...$).

    REGLAS LATEX para paso_intermedio y resultado_final:
    - Escribe la fórmula pura. NO incluyas signos "$$" dentro del JSON.
    - Usa DOBLE BARRA para comandos: \\\\frac, \\\\int.

    Estructura JSON:
    {{
        "estrategias": ["Estrategia Correcta", "Estrategia Incorrecta 1", "Estrategia Incorrecta 2"],
        "indice_correcta": 0,
        "feedback_estrategia": "Explicación breve.",
        "paso_intermedio": "Ecuación LaTeX PURA (sin $$) del hito",
        "resultado_final": "Ecuación LaTeX PURA (sin $$) del resultado"
    }}
    Orden aleatorio en estrategias.
    """
    response = generar_contenido_seguro(prompt)
    if response:
        return limpiar_json(response.text)
    return None

def analizar_problema_usuario(
    texto_usuario: Optional[str],
    imagen_usuario: Any = None,
) -> Optional[dict]:
    """
    Analiza un problema subido por el alumno (texto o imagen).
    Distingue entre Integrales/EDO (rígido) y Aplicaciones (flexible).
    """
    prompt_base = """
    Actúa como un tutor experto de Cálculo Integral.
    Analiza el problema del estudiante (texto o imagen).

    OBJETIVO: Generar una guía paso a paso JSON.

    REGLAS DE ESTRATEGIAS (CRÍTICO):
    1. Si es INTEGRAL (Cálculo directo): Las opciones DEBEN ser Técnicas (ej. "Por Partes", "Sustitución", "Fracciones Parciales").
    2. Si es EDO (Resolver ecuación): Las opciones DEBEN ser Tipos (ej. "Variables Separables", "Lineal", "Exacta").
    3. Si es CÁLCULO DE ÁREAS, VOLÚMENES, EXCEDENTES O APLICACIONES:
       - Tienes LIBERTAD TOTAL.
       - Las opciones deben ser PLANTEAMIENTOS o ENFOQUES (ej. "Integrar con respecto a Y", "Usar método de arandelas", "Igualar Oferta y Demanda").

    REGLAS LATEX (CRÍTICO):
    1. Escribe la fórmula pura. NO incluyas signos "$$" dentro del JSON.
    2. Usa DOBLE BARRA para comandos: \\\\frac, \\\\int.
    
    Estructura JSON requerida:
    {
        "tema_detectado": "Nombre del tema (ej. Volumen de Revolución)",
        "enunciado_latex": "El problema transcrito a LaTeX (sin $$)",
        "estrategias": ["Planteamiento/Técnica CORRECTA", "Opción INCORRECTA 1", "Opción INCORRECTA 2"],
        "indice_correcta": 0,
        "feedback_estrategia": "Por qué este es el camino correcto.",
        "paso_intermedio": "Un hito clave a mitad del desarrollo (LaTeX puro, sin $$)",
        "resultado_final": "La solución final (LaTeX puro, sin $$)"
    }
    """
    
    contenido = [prompt_base]
    if texto_usuario:
        contenido.append(f"Enunciado del estudiante: {texto_usuario}")
    if imagen_usuario:
        contenido.append(imagen_usuario)
        contenido.append("Transcribe y resuelve.")

    response = generar_contenido_seguro(contenido)
    if response:
        return limpiar_json(response.text)
    return None


def evaluar_manuscrito(imagen_manuscrito: Any) -> Optional[dict]:
    """
    Analiza un manuscrito (foto de resolución del estudiante).
    Identifica el enunciado, valora la resolución y emite juicio con sugerencias.
    """
    lista_txt = _bloque_lista_temas_oficial()
    prompt = f"""
    Eres un corrector experto de Cálculo Integral y ecuaciones diferenciales para estudiantes universitarios.

    En la imagen verás un manuscrito del estudiante: suele incluir el enunciado del ejercicio y su resolución escrita.

    Realiza en orden:

    0) TEMARIO: Según el enunciado y la resolución visibles, indica a cuál de estos temas oficiales corresponde mejor el ejercicio.
       Copia UN texto EXACTO de la lista (mismo texto, carácter por carácter) o usa null si no encaja ninguno:
{lista_txt}

    1) ENUNCIADO: Identifica y transcribe con claridad el enunciado del ejercicio (qué pide el problema). Si hay fórmulas, escríbelas en LaTeX puro (usa \\\\frac, \\\\int, etc., sin $$ dentro del JSON).

    2) VALORACIÓN: Evalúa la resolución del estudiante (cálculos, método usado, resultado final). Considera si el método es correcto, si hay errores de desarrollo y si el resultado final es correcto.

    3) JUICIO: Emite exactamente uno de estos tres valores: "correcto", "parcialmente_correcto" o "incorrecto".
       - correcto: método adecuado, desarrollo sin errores relevantes y resultado final correcto.
       - parcialmente_correcto: idea o método correcto pero hay errores de cálculo o un paso mal ejecutado; o resultado final incorrecto por un desliz.
       - incorrecto: método equivocado, desarrollo mayormente erróneo o resultado final incorrecto sin rescate.

    4) ERRORES Y OMISIONES: Lista errores detectados (cálculos erróneos, signos, aplicaciones incorrectas de reglas). Lista pasos importantes que el estudiante omitió (por ejemplo, no justificar un cambio de variable, no verificar condiciones, saltarse un paso algebraico clave).

    5) SUGERENCIAS: Da sugerencias concretas de ajuste para corregir errores o completar pasos omitidos. Sé breve y didáctico.

    REGLAS DE FORMATO OBLIGATORIAS:
    1. CADA VEZ que menciones una variable (x, t, y), una función o una integral, 
       DEBES envolverla en símbolos de dólar. Ejemplo: "la variable $x$ se convierte en $t^2$".
    2. PARA EXPRESIONES LARGAS: Usa doble dólar para centrarlas. 
       Ejemplo: "La integral resultante es: $$ \\int (t^2-2) 2t dt $$"
    3. ESPACIOS: Nunca pegues texto a un símbolo $. Deja un espacio: "en $t$," en lugar de "en$t$,".
    4. JSON ESCAPE: Recuerda que en el JSON debes usar DOBLE barra invertida (\\\\int) 
       para que el sistema la reciba correctamente.

    INSTRUCCIONES DE TIPOGRAFÍA SUPERIOR (CRÍTICO):
    1. TODA expresión matemática, por mínima que sea ($x$, $t$, $dx$, $dt$), DEBE ir entre símbolos de dólar.
    2. TRANSFORMACIONES COMPLETAS: Cuando escribas una integral completa resultante de un cambio de variable
       o una simplificación mayor, DEBES usar doble dólar ($$ ... $$) en una línea independiente.
    3. No fragmentes: No escribas $\\int$ $x^2$ $dx$. Escribe $\\int x^2 dx$.
    ...

    Responde ÚNICAMENTE con un objeto JSON válido (sin markdown ni texto alrededor) con esta estructura exacta:
    {{
        "tema_catedra": "<texto exacto de la lista oficial>" | null,
        "enunciado": "Texto o LaTeX del ejercicio identificado",
        "juicio": "correcto" | "parcialmente_correcto" | "incorrecto",
        "resumen_valoracion": "Breve explicación del juicio en 1-3 oraciones.",
        "errores_detectados": ["error 1", "error 2"],
        "pasos_omitidos": ["paso omitido 1", "paso omitido 2"],
        "sugerencias": ["sugerencia 1", "sugerencia 2"]
    }}
    Si no hay errores o pasos omitidos, usa listas vacías [].
    """
    contenido = [prompt, imagen_manuscrito]
    response = generar_contenido_seguro(contenido)
    if response:
        return limpiar_json(response.text)
    return None


def generar_respuesta_tutor_abierto(
    pregunta_usuario: str,
    historial_previo: str,
) -> str:
    """
    Modo «Dime y te digo» (tutor de preguntas abiertas).
    Usa el contexto de banco_muestras y banco_preguntas para personalizar la respuesta.
    """
    # 1. Construimos el contexto (tomamos una muestra para no saturar)
    contexto_ejercicios = str(banco_preguntas.BANCO_FIXED[:10]) 
    estilos_examen = banco_muestras.EJEMPLOS_ESTILO

    inst = (st.session_state.get("auth_estudiante_institucion") or "").strip()
    carrera = (st.session_state.get("auth_estudiante_carrera") or "").strip()
    bloque_perfil_alumno = ""
    if inst and carrera:
        bloque_perfil_alumno = (
            f"Estás atendiendo a un estudiante de la {inst} de la carrera {carrera}. "
            "Ajusta tu lenguaje y prioridades de los temas según la malla programática típica de "
            "esta universidad en Venezuela (ej. UCV, USB, UNIMET)."
        )
    bloque_malla_prompt = contexto_universitario.texto_instruccion_contexto_malla(inst)
    bloque_plan_v1 = planes_estudio_oficiales.texto_bloque_plan_oficial_para_prompt(inst)
    clave_univ_plan = contexto_universitario.clave_malla_desde_institucion(inst)
    instruccion_tono_malla = planes_estudio_oficiales.instrucciones_tono_ia_por_clave(
        clave_univ_plan
    )
    bloque_institucional = planes_estudio.texto_contexto_ia_para_estudiante()
    bloques_contexto_estudiante: list[str] = []
    if bloque_perfil_alumno:
        bloques_contexto_estudiante.append(bloque_perfil_alumno)
    if bloque_malla_prompt:
        bloques_contexto_estudiante.append(bloque_malla_prompt)
    if bloque_plan_v1:
        bloques_contexto_estudiante.append(bloque_plan_v1)
    if bloque_institucional:
        bloques_contexto_estudiante.append(bloque_institucional)
    if instruccion_tono_malla:
        bloques_contexto_estudiante.append(instruccion_tono_malla)
    inyeccion_perfil_y_plan = (
        "\n\n    ".join(bloques_contexto_estudiante) if bloques_contexto_estudiante else ""
    )

    # 2. Prompt del Sistema (La personalidad del profesor)
    prompt_tutor = f"""
    Eres el tutor virtual de Cálculo Integral para estudiantes registrados en la plataforma.
    Tu objetivo es ayudar al estudiante a entender la teoría, pero SIEMPRE aterrizándola a la práctica de la clase.
    {inyeccion_perfil_y_plan if inyeccion_perfil_y_plan else ""}

    CONTEXTO DEL CURSO (Tu base de conocimiento):
    --- Estilos de Examen ---
    {estilos_examen}
    --- Ejercicios del Banco Oficial (Muestra) ---
    {contexto_ejercicios}
    
    INSTRUCCIONES CLAVE:
    1. Responde de forma clara y pedagógica.
    
    2. GESTIÓN DEL CONOCIMIENTO (CRÍTICO):
       - Usa los ejercicios del contexto para mantener el estilo y la dificultad del curso.
       - SI EL CONTEXTO NO TIENE EJEMPLOS DE UN TEMA (ej. Integrales Dobles o Impropias): 
         NO digas "el banco es pequeño" ni "no tengo ejemplos". 
         Genera tú mismo un ejemplo matemático riguroso (nivel Leithold/Larson) y preséntalo con naturalidad, diciendo: "Un caso típico que estudiamos en este tema es..." o "Para ilustrar esto, analicemos...".
    
    3. FORMATO MATEMÁTICO (CRÍTICO): 
       - Usa SIEMPRE signos de dólar para encerrar el LaTeX.
       - Para fórmulas dentro del texto usa uno solo: $ f(x) = x^2 $
       - Para ecuaciones grandes o centradas usa doble signo: $$ \\int_{{a}}^{{b}} f(x) dx $$
       
    4. VINCULACIÓN: Siempre que sea posible, menciona: "Esto sigue la lógica de nuestros ejercicios de parcial..." o "Es análogo a los problemas de oferta y demanda...".

    Historial de chat reciente:
    {historial_previo}

    Pregunta del estudiante:
    {pregunta_usuario}
    """
    
    response = generar_contenido_seguro(prompt_tutor)
    if response:
        return response.text
    return "Lo siento, tuve un problema pensando la respuesta."

def _sanitizar_para_pdf(texto: Optional[str]) -> str:
    """
    Convierte LaTeX a texto legible en el PDF: fracciones como (num/den),
    raíces como sqrt(...), integrales, exponentes, etc., sin código LaTeX crudo.
    """
    if not texto:
        return ""

    t = texto.replace("$$", "").replace("$", "").strip()

    # \frac con contenido posiblemente anidado (ej. \frac{x^3}{3})
    def _reemplazar_frac(s: str) -> str:
        out = []
        i = 0
        while i < len(s):
            if s[i : i + 6] == "\\frac{" and i + 6 < len(s):
                depth = 1
                j = i + 6
                start = j
                while j < len(s) and depth > 0:
                    if s[j] == "{":
                        depth += 1
                    elif s[j] == "}":
                        depth -= 1
                    j += 1
                num = s[start : j - 1]
                if j < len(s) and s[j] == "{":
                    depth = 1
                    j += 1
                    start_den = j
                    while j < len(s) and depth > 0:
                        if s[j] == "{":
                            depth += 1
                        elif s[j] == "}":
                            depth -= 1
                        j += 1
                    den = s[start_den : j - 1]
                    out.append(f" ({_sanitizar_para_pdf(num)}/{_sanitizar_para_pdf(den)}) ")
                    i = j
                else:
                    out.append(s[i:j])
                    i = j
            else:
                out.append(s[i])
                i += 1
        return "".join(out)

    t = _reemplazar_frac(t)

    # Raíz: \sqrt{...} -> sqrt(...) (contenido puede tener llaves anidadas)
    def _reemplazar_sqrt(s: str) -> str:
        idx = s.find("\\sqrt{")
        if idx == -1:
            return s
        depth = 1
        j = idx + 6
        while j < len(s) and depth > 0:
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                depth -= 1
            j += 1
        contenido = s[idx + 6 : j - 1]
        return s[:idx] + " sqrt(" + _sanitizar_para_pdf(contenido) + ") " + _reemplazar_sqrt(s[j:])
    t = _reemplazar_sqrt(t)

    # Exponentes: e^{...} -> e^(...), x^{...} -> x^(...)
    t = re.sub(r"e\^\{([^{}]*)\}", r"e^(\1)", t)
    t = re.sub(r"(\w)\^\{([^{}]*)\}", r"\1^(\2)", t)
    # \left( \right) \left[ \right] -> ( ) [ ]
    t = re.sub(r"\\left\s*\(\s*", " ( ", t)
    t = re.sub(r"\s*\\right\s*\)\s*", " ) ", t)
    t = re.sub(r"\\left\s*\[\s*", " [ ", t)
    t = re.sub(r"\s*\\right\s*\]\s*", " ] ", t)
    # Comandos LaTeX -> texto
    t = t.replace("\\int", " integral ")
    t = t.replace("\\ln", " ln ")
    t = t.replace("\\cdot", " ")
    t = t.replace("\\left", " ")
    t = t.replace("\\right", " ")
    # Raíz simple por si quedó algo
    t = re.sub(r"\\sqrt\{([^{}]+)\}", r" sqrt(\1) ", t)
    # Espacios múltiples y recorte
    t = re.sub(r"\s+", " ", t).strip()
    return t[:500] if len(t) > 500 else t

def generar_pdf_informe_quiz(
    respuestas_usuario: List[dict],
    nota_final: float,
) -> Union[bytes, bytearray]:
    """Genera bytes del PDF con calificación y detalle del examen."""
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=14)
    pdf.cell(0, 10, "Informe de evaluacion - Sigma tu Tutor de Calculo Integral", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 8, f"Calificacion final: {nota_final} / 20 pts", ln=True)
    pdf.cell(0, 8, "Aprobado." if nota_final >= 10 else "No aprobado.", ln=True)
    pdf.ln(4)
    for i, r in enumerate(respuestas_usuario, 1):
        pdf.set_font("Helvetica", "B", size=10)
        pts = r.get("puntos", 0)
        pdf.cell(0, 6, f"Pregunta {i} ({pts} pts)", ln=True)
        pdf.set_font("Helvetica", size=9)
        pdf.multi_cell(0, 5, _sanitizar_para_pdf(r.get("pregunta", "")))
        pdf.cell(0, 4, "Tu respuesta: " + _sanitizar_para_pdf(r.get("elegida", "")), ln=True)
        if not r.get("es_correcta", True):
            pdf.cell(0, 4, "Correcta: " + _sanitizar_para_pdf(r.get("correcta", "")), ln=True)
        pdf.cell(0, 4, "Comentario: " + _sanitizar_para_pdf(r.get("explicacion", "")), ln=True)
        pdf.ln(2)
    out = pdf.output()
    return bytes(out) if not isinstance(out, bytes) else out

# --- 2. GESTIÓN DE ESTADO ---
if "quiz_activo" not in st.session_state: st.session_state.quiz_activo = False
if "preguntas_quiz" not in st.session_state: st.session_state.preguntas_quiz = []
if "indice_pregunta" not in st.session_state: st.session_state.indice_pregunta = 0
if "respuestas_usuario" not in st.session_state: st.session_state.respuestas_usuario = [] 

# Estados para Respuesta Guiada (Modo B)
if "consulta_step" not in st.session_state: st.session_state.consulta_step = 0
if "consulta_data" not in st.session_state: st.session_state.consulta_data = None
if "consulta_validada" not in st.session_state: st.session_state.consulta_validada = False

# Estado D: Tutor Preguntas Abiertas
if "historial_tutor_abierto" not in st.session_state: st.session_state.historial_tutor_abierto = []

# Estado E: Corrección de Manuscritos
if "manuscrito_correccion" not in st.session_state: st.session_state.manuscrito_correccion = None

# Modo administrador (manual): panel de métricas; desactivar con el botón del panel o desmarcando.
ADMIN_SESSION_KEY = "modo_administrador_manual"
if ADMIN_SESSION_KEY not in st.session_state:
    st.session_state[ADMIN_SESSION_KEY] = False
try:
    _qp_ad = st.query_params.get("admin")
    if _qp_ad == "1" or (isinstance(_qp_ad, list) and "1" in _qp_ad):
        st.session_state[ADMIN_SESSION_KEY] = True
except Exception:
    pass

if st.session_state.get(ADMIN_SESSION_KEY):
    if _render_admin_panel_safe():
        st.stop()

# --- 3. INTERFAZ PRINCIPAL ---
_modo = st.session_state.get("modo_actual")
if not _modo:
    st.title(interfaz.APP_DISPLAY_NAME)
    st.info("👤 **Cuenta de participante:** el registro e inicio de sesión están dentro de **Seguimos**.")
    interfaz.mostrar_portada_selector_modos()
    interfaz.mostrar_bienvenida()

    with st.expander("Opciones avanzadas", expanded=False):
        st.caption(
            "Panel de métricas (Supabase). Al entrar se oculta el resto de la app hasta **Volver** en el panel. "
            "También puedes usar **`?admin=1`** en la URL (atajo técnico para operadores)."
        )
        if st.checkbox("Acceso Admin", key="portada_acceso_admin_cb"):
            _pw = st.text_input("Clave de acceso", type="password", key="portada_acceso_admin_pwd")
            if st.button("Entrar al panel", type="primary", key="portada_acceso_admin_btn"):
                if (_pw or "").strip() == _clave_acceso_admin_portada():
                    st.session_state[ADMIN_SESSION_KEY] = True
                    st.rerun()
                else:
                    st.error("Clave incorrecta.")

    ruta = None
else:
    c_img, c_tit = st.columns([1, 4], vertical_alignment="center")
    with c_img:
        img = interfaz.ruta_imagen_modo(_modo)
        if img:
            st.image(img, use_container_width=True)
    with c_tit:
        st.title(interfaz.APP_DISPLAY_NAME)
    # En Seguimos ya se renderiza el portal completo de acceso; evita duplicar botones.
    if _modo != seguimos.MODO_ID:
        auth_estudiantes.render_barra_sesion_compacta()
    interfaz.mostrar_cabecera_pagina_modo()
    ruta = _modo

# =======================================================
# LÓGICA 0: SEGUIMOS (continuidad, alumnos registrados en sesión)
# =======================================================
if ruta == seguimos.MODO_ID:
    seguimos.render_vista_seguimos()

# =======================================================
# LÓGICA A: MODO ENTRENAMIENTO (Dojo Matemático)
# =======================================================
elif ruta == "a) Entrenamiento (Temario)":
    st.info("Resolución paso a paso: **1. Elegir Estrategia** -> **2. Hito Intermedio** -> **3. Resultado Final**.")

    if "entrenamiento_activo" not in st.session_state:
        st.session_state.entrenamiento_activo = False

    # --- PANTALLA 0: CONFIGURACIÓN ---
    if not st.session_state.entrenamiento_activo:
        temas_entrenamiento = st.multiselect(
            "🎯 Selecciona los temas a practicar:",
            options=temario.LISTA_TEMAS,
            placeholder="Ej. Ecuaciones Diferenciales Lineales..."
        )

        if st.button(f"⚡ Iniciar Sesión ({NUM_EJERCICIOS_ENTRENAMIENTO} Ejercicios)", type="primary", use_container_width=True):
            if not temas_entrenamiento:
                st.error("⚠️ Selecciona al menos un tema.")
            else:
                cargar_exito = False
                with st.spinner("Preparando tu serie de ejercicios..."):
                    try:
                        import random
                        lista_entrenamiento = []
                        
                        # 1. Banco de Preguntas (Protegido)
                        try:
                            # Hasta completar la sesión con banco si hay ítems (incl. los que traen `grafico`)
                            preguntas_banco = banco_preguntas.obtener_preguntas_fijas(
                                temas_entrenamiento, NUM_EJERCICIOS_ENTRENAMIENTO
                            )
                            if preguntas_banco:
                                lista_entrenamiento.extend(preguntas_banco)
                        except Exception as e:
                            print(f"Aviso: Banco no disponible {e}")

                        # 2. Generación IA (Protegida)
                        faltantes = NUM_EJERCICIOS_ENTRENAMIENTO - len(lista_entrenamiento)
                        if faltantes > 0:
                            prompt_train = temario.generar_prompt_quiz(temas_entrenamiento, faltantes)
                            respuesta_ia = generar_contenido_seguro(prompt_train)
                            
                            if respuesta_ia:
                                preguntas_ia = limpiar_json(respuesta_ia.text)
                                if preguntas_ia: 
                                    lista_entrenamiento.extend(preguntas_ia)
                        
                        if not lista_entrenamiento:
                            st.error("No se encontraron preguntas. No se pudo interpretar la respuesta de la IA; intenta con otro tema o de nuevo.")
                        else:
                            random.shuffle(lista_entrenamiento)
                            st.session_state.entrenamiento_lista = lista_entrenamiento[:NUM_EJERCICIOS_ENTRENAMIENTO]
                            st.session_state.entrenamiento_idx = 0
                            st.session_state.entrenamiento_step = 1
                            st.session_state.entrenamiento_data_ia = None
                            st.session_state.entrenamiento_validado = False 
                            st.session_state.entrenamiento_activo = True
                            cargar_exito = True
                            uso_stats.registrar_uso(
                                "Entrenamiento",
                                detalle={"temas": list(temas_entrenamiento)},
                            )

                    except Exception as e:
                        st.error(f"Error técnico al iniciar: {e}")
                
                if cargar_exito:
                    st.rerun()

    # --- PANTALLA DE EJERCICIOS (El Dojo) ---
    else:
        idx = st.session_state.entrenamiento_idx
        lista = st.session_state.entrenamiento_lista
        
        if idx < len(lista):
            ejercicio = lista[idx]
            
            st.progress((idx + 1) / NUM_EJERCICIOS_ENTRENAMIENTO, text=f"Ejercicio {idx + 1} de {NUM_EJERCICIOS_ENTRENAMIENTO}")
            st.markdown(f"**Tema:** `{ejercicio.get('tema', 'General')}`")
            # Mismo pipeline que la explicación final: texto mixto vía $/$$ → markdown + st.latex
            st.markdown("### Enunciado")
            _render_texto_con_latex(ejercicio.get("pregunta"))
            st.divider()

            # --- LLAMADA A LA IA TUTOR ---
            if st.session_state.entrenamiento_data_ia is None:
                with st.spinner("🧠 El profesor está analizando el mejor camino de resolución..."):
                    datos_tutor = generar_tutor_paso_a_paso(ejercicio['pregunta'], ejercicio.get('tema', 'Cálculo'))
                    if datos_tutor:
                        st.session_state.entrenamiento_data_ia = datos_tutor
                        st.rerun()
                    else:
                        st.error("No se pudo interpretar la respuesta del tutor. Saltando ejercicio; puedes continuar con el siguiente.")
                        st.session_state.entrenamiento_idx += 1
                        time.sleep(2)
                        st.rerun()
            
            tutor = st.session_state.entrenamiento_data_ia
            step = st.session_state.entrenamiento_step

            # PASO 1: ESTRATEGIA
            if step == 1:
                st.markdown("#### 1️⃣ Paso 1: Selección de Estrategia")
                st.write("Antes de calcular, ¿cuál crees que es el camino correcto?")
                
                opcion_estrategia = st.radio("Selecciona el método:", tutor['estrategias'], index=None, key=f"radio_estrat_{idx}")
                
                if st.button("Validar Estrategia", key=f"btn_val_{idx}"):
                    if opcion_estrategia:
                        idx_seleccionado = tutor['estrategias'].index(opcion_estrategia)
                        if idx_seleccionado == tutor['indice_correcta']:
                            st.session_state.entrenamiento_validado = True 
                        else:
                            st.error("❌ Mmm, no es el mejor camino.")
                            st.warning("Pista: " + preparar_latex_para_streamlit(tutor['feedback_estrategia']))
                    else:
                        st.warning("Debes seleccionar una opción.")

                if st.session_state.get("entrenamiento_validado", False):
                    st.success("✅ ¡Exacto! Esa es la ruta.")
                    st.info("👨‍🏫 **Feedback:** " + preparar_latex_para_streamlit(tutor['feedback_estrategia']))
                    
                    if st.button("Ir al Paso Intermedio ➡️", type="primary", key=f"btn_go_step2_{idx}"):
                        st.session_state.entrenamiento_step = 2
                        st.session_state.entrenamiento_validado = False
                        st.rerun()

            # PASO 2: HITO INTERMEDIO
            if step == 2:
                st.success(f"✅ Estrategia: {tutor['estrategias'][tutor['indice_correcta']]}")
                st.markdown("#### 2️⃣ Paso 2: Ejecución Intermedia")
                st.write("Aplica la estrategia seleccionada. Deberías llegar a una expresión similar a esta:")
                
                st.latex(_limpiar_para_st_latex(tutor["paso_intermedio"]))

                graficos_entrenamiento.mostrar_si_aplica(ejercicio, en_paso_intermedio=True)
                
                st.write("¿Lograste llegar a este punto o algo equivalente?")
                
                col_si, col_no = st.columns(2)
                with col_si:
                    if st.button("👍 Sí, lo tengo", key=f"btn_si_{idx}"):
                        st.session_state.entrenamiento_step = 3
                        st.rerun()
                with col_no:
                    if st.button("👎 No, necesito ayuda", key=f"btn_no_{idx}"):
                        st.error("Revisa tus derivadas/integrales básicas o el álgebra.")

            # PASO 3: FINAL
            if step == 3:
                st.success(f"✅ Estrategia Correcta | ✅ Hito Intermedio Alcanzado")
                st.markdown("#### 3️⃣ Paso 3: Resolución Final")
                st.write("El resultado definitivo es:")
                
                st.success("✅ Resultado final:")
                st.latex(_limpiar_para_st_latex(tutor["resultado_final"]))
                
                with st.expander("Ver explicación completa"):
                    _render_texto_con_latex(ejercicio.get("explicacion", "Procedimiento estándar aplicado correctamente."))

                if st.button("Siguiente Ejercicio ➡️", type="primary", key=f"btn_next_{idx}"):
                    st.session_state.entrenamiento_idx += 1
                    st.session_state.entrenamiento_step = 1
                    st.session_state.entrenamiento_data_ia = None 
                    st.session_state.entrenamiento_validado = False
                    st.rerun()

        else:
            st.success("🎉 ¡Sesión de A practicar completada!")
            if st.button("🔄 Volver al Inicio", key="btn_reset_entrenamiento"):
                st.session_state.entrenamiento_activo = False
                st.session_state.entrenamiento_idx = 0
                st.rerun()

# =======================================================
# LÓGICA B: RESPUESTA GUIADA (Consultas) - TUTOR PERSONALIZADO
# =======================================================
elif ruta == "b) Respuesta Guiada (Consultas)":
    st.info("Sube tu ejercicio (foto o texto) y te guiaré paso a paso.")

    # 1. INPUT (Foto o Texto)
    if st.session_state.consulta_step == 0:
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            imagen_subida = st.file_uploader("📸 Foto del ejercicio", type=["png", "jpg", "jpeg"])
        with col_txt:
            texto_subido = st.text_area("✍️ O escribe el enunciado aquí:", height=100)

        if st.button("🚀 Resolver Paso a Paso", type="primary", use_container_width=True):
            if not imagen_subida and not texto_subido:
                st.warning("⚠️ Sube una imagen o escribe el texto para comenzar.")
            else:
                exito_analisis = False
                with st.spinner("🤖 Analizando el tipo de problema..."):
                    try:
                        # Solo abrir imagen si el usuario subió un archivo (flujo texto-only no usa imagen)
                        img_pil = None
                        if imagen_subida:
                            img_pil = Image.open(imagen_subida)
                        datos_problema = analizar_problema_usuario(texto_subido or None, img_pil)
                        if datos_problema:
                            st.session_state.consulta_data = datos_problema
                            st.session_state.consulta_step = 1
                            st.session_state.consulta_validada = False
                            exito_analisis = True
                            uso_stats.registrar_uso(
                                "Respuesta Guiada",
                                detalle={
                                    "tema_detectado": (
                                        (datos_problema.get("tema_detectado") or "")
                                        .strip()
                                        or None
                                    ),
                                },
                            )
                        else:
                            st.error("No se pudo interpretar la respuesta del tutor. Intenta de nuevo con otra redacción o imagen más clara.")
                    except Exception as e:
                        st.error(f"Error técnico: {e}")
                
                if exito_analisis:
                    st.rerun()

    # 2. INTERACCIÓN (Similar al Dojo pero para el problema del usuario)
    else:
        datos = st.session_state.consulta_data
        step = st.session_state.consulta_step

        # Botón para cancelar/reiniciar arriba
        if st.button("🔄 Nueva Consulta", key="btn_new_query_top"):
            st.session_state.consulta_step = 0
            st.session_state.consulta_data = None
            st.rerun()

        st.divider()
        st.markdown(f"**Tema Detectado:** `{datos.get('tema_detectado', 'Cálculo Integral')}`")
        if datos.get('enunciado_latex'):
            st.markdown("**Problema Identificado:**")
            st.markdown(latex_display_puro(datos['enunciado_latex']))
        
        # PASO 1: Identificar Técnica/Tipo o Planteamiento
        if step == 1:
            st.subheader("1️⃣ Paso 1: Planteamiento")
            
            # Lógica dinámica para el mensaje
            tema_lower = datos.get('tema_detectado', '').lower()
            if "integral" in tema_lower and "área" not in tema_lower and "volumen" not in tema_lower:
                st.write("¿Qué **técnica de integración** usarías?")
            elif "ecuación diferencial" in tema_lower and "aplicación" not in tema_lower:
                st.write("¿Qué **tipo de EDO** es esta?")
            else:
                # Caso Áreas, Volúmenes, Excedentes, etc.
                st.write("¿Cuál es el **planteamiento o enfoque** correcto?")

            opcion = st.radio("Selecciona:", datos['estrategias'], index=None, key="rad_cons")
            
            if st.button("Validar Estrategia", type="primary"):
                if opcion and datos['estrategias'].index(opcion) == datos['indice_correcta']:
                    st.session_state.consulta_validada = True
                    st.rerun()
                else:
                    st.error("❌ No es lo más eficiente.")
                    st.warning(preparar_latex_para_streamlit(datos['feedback_estrategia']))
            
            if st.session_state.consulta_validada:
                st.success("✅ ¡Correcto! Vamos a desarrollarlo.")
                if st.button("Ver Paso Intermedio ➡️"):
                    st.session_state.consulta_step = 2
                    st.session_state.consulta_validada = False
                    st.rerun()

        # PASO 2: Hito Intermedio
        if step == 2:
            st.success(f"✅ Estrategia: {datos['estrategias'][datos['indice_correcta']]}")
            st.subheader("2️⃣ Paso 2: Desarrollo")
            st.write("Aplicando la técnica, deberías llegar a esta expresión intermedia:")
            
            st.latex(_limpiar_para_st_latex(datos["paso_intermedio"]))
            
            c1, c2 = st.columns(2)
            if c1.button("👍 Llegué a eso"):
                st.session_state.consulta_step = 3
                st.rerun()
            if c2.button("👎 Me perdí, explícame"):
                st.info("💡 Pista: " + preparar_latex_para_streamlit(datos.get('feedback_estrategia', 'Revisa las operaciones algebraicas.')))

        # PASO 3: Solución Final
        if step == 3:
            st.success("✅ Desarrollo intermedio correcto")
            st.subheader("3️⃣ Solución Final")
            
            st.success("✅ Resultado final:")
            st.latex(_limpiar_para_st_latex(datos["resultado_final"]))
            
            st.balloons()
            if st.button("🏁 Terminar ejercicio"):
                st.session_state.consulta_step = 0
                st.session_state.consulta_data = None
                st.rerun()

# =======================================================
# LÓGICA C: AUTOEVALUACIÓN (Quiz)
# =======================================================
elif ruta == "c) Autoevaluación (Quiz)":
    # --- PANTALLA 1: CONFIGURACIÓN ---
    if not st.session_state.quiz_activo:
        st.info("Configura tu prueba (El sistema combinará ejercicios oficiales y generados por IA):")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏆 Generar Primer Parcial (Simulacro)", use_container_width=True):
                st.session_state.quiz_modalidad = "primer_parcial"
                st.session_state.config_temas = temario.TEMAS_PARCIAL_1
                st.session_state.config_cant = NUM_PREGUNTAS_QUIZ 
                st.session_state.trigger_quiz = True
                st.rerun()
        with col2:
            if st.button("🏆 Generar Segundo Parcial (Simulacro)", use_container_width=True):
                st.session_state.quiz_modalidad = "segundo_parcial"
                st.session_state.config_temas = temario.TEMAS_PARCIAL_2
                st.session_state.config_cant = NUM_PREGUNTAS_QUIZ
                st.session_state.trigger_quiz = True
                st.rerun()

        with st.expander("⚙️ Personalizado"):
            temas_custom = st.multiselect("Temas:", temario.LISTA_TEMAS)
            if st.button("▶️ Iniciar simulacro personalizado"):
                if not temas_custom:
                    st.error("Selecciona tema.")
                else:
                    st.session_state.quiz_modalidad = "personalizado"
                    st.session_state.config_temas = temas_custom
                    st.session_state.config_cant = NUM_PREGUNTAS_QUIZ
                    st.session_state.trigger_quiz = True
                    st.rerun()

        # --- LÓGICA DE GENERACIÓN ---
        if st.session_state.get("trigger_quiz"):
            quiz_generado = False
            with st.spinner("Compilando examen (Balanceando 50% Banco Oficial / 50% IA)..."):
                try:
                    import random
                    lista_final_preguntas = []
                    cantidad_total = st.session_state.config_cant
                    temas = st.session_state.config_temas

                    cuota_banco = cantidad_total // 2
                    cuota_ia = cantidad_total - cuota_banco

                    # 1. Banco
                    try:
                        preguntas_banco = banco_preguntas.obtener_preguntas_fijas(temas, cuota_banco)
                        if preguntas_banco:
                            lista_final_preguntas.extend(preguntas_banco)
                    except: pass
                    
                    # 2. IA
                    falta = cantidad_total - len(lista_final_preguntas)
                    if falta > 0:
                        prompt_quiz = temario.generar_prompt_quiz(temas, falta)
                        respuesta = generar_contenido_seguro(prompt_quiz)
                        if respuesta:
                            preguntas_ia = limpiar_json(respuesta.text)
                            if preguntas_ia:
                                lista_final_preguntas.extend(preguntas_ia)
                    
                    random.shuffle(lista_final_preguntas)
                    lista_final_preguntas = lista_final_preguntas[:cantidad_total]

                    if not lista_final_preguntas:
                         st.error("No se pudieron generar preguntas. No se pudo interpretar la respuesta de la IA; intenta de nuevo.")
                         st.session_state.trigger_quiz = False
                    else:
                        st.session_state.preguntas_quiz = lista_final_preguntas
                        st.session_state.indice_pregunta = 0
                        st.session_state.respuestas_usuario = []
                        st.session_state.quiz_activo = True
                        st.session_state.trigger_quiz = False
                        quiz_generado = True
                        uso_stats.registrar_uso(
                            "Quiz",
                            detalle={
                                "modalidad": st.session_state.get(
                                    "quiz_modalidad", "desconocido"
                                ),
                                "temas": list(temas),
                            },
                        )
                    
                except Exception as e:
                    st.error(f"Error generando examen: {e}")
                    st.session_state.trigger_quiz = False
            
            if quiz_generado:
                st.rerun()

    # --- PANTALLA 2 (RESPONDER) y 3 (RESULTADOS) ---
    else:
        total = len(st.session_state.preguntas_quiz)
        actual = st.session_state.indice_pregunta
        
        if actual < total:
            pregunta_data = st.session_state.preguntas_quiz[actual]
            
            st.progress((actual) / total, text=f"Pregunta {actual + 1} de {total}")
            
            # 1. RENDERIZADO DE LA PREGUNTA (misma ruta que entrenamiento: markdown + st.latex)
            st.markdown("#### Pregunta")
            _render_texto_con_latex(pregunta_data["pregunta"])
            st.divider()
            
            # 2. RENDERIZADO DE LAS OPCIONES — letra en markdown, fórmula vía _render_texto_con_latex
            st.write("Opciones:")
            col_ops = st.columns(2)
            opciones_completas = pregunta_data["opciones"]

            for i, opcion_texto in enumerate(opciones_completas):
                with col_ops[i % 2]:
                    if ")" in opcion_texto:
                        letra, resto = opcion_texto.split(")", 1)
                        st.markdown(f"**{letra.strip()})**")
                        _render_texto_con_latex(resto.strip())
                    else:
                        _render_texto_con_latex(opcion_texto)
            
            st.divider()

            # 3. SELECTOR DE RESPUESTA (LÓGICA)
            ya_respondido = len(st.session_state.respuestas_usuario) > actual
            
            if not ya_respondido:
                # Creamos opciones simplificadas (Solo A, B, C, D) para el selector
                # Así evitamos que Streamlit intente renderizar LaTeX crudo en el widget
                opciones_radio = [op.split(")")[0] + ")" for op in opciones_completas]
                
                seleccion_letra = st.radio(
                    "Selecciona tu respuesta:", 
                    opciones_radio, 
                    key=f"radio_{actual}", 
                    index=None,
                    horizontal=True
                )

                if st.button("Responder", type="primary"):
                    if seleccion_letra:
                        # Recuperamos la opción completa original basada en la letra seleccionada
                        letra_elegida = seleccion_letra.split(")")[0] # Ej: "A"
                        # Buscamos la opción original que empieza con esa letra
                        opcion_elegida_completa = next(op for op in opciones_completas if op.startswith(letra_elegida))
                        
                        letra_correcta = pregunta_data['respuesta_correcta'].strip()[0].upper()
                        es_correcta = (letra_elegida == letra_correcta)
                        pts = round(20 / total, 2) if es_correcta else 0
                        
                        st.session_state.respuestas_usuario.append({
                            "pregunta": pregunta_data['pregunta'],
                            "elegida": opcion_elegida_completa, # Guardamos la completa para el reporte final
                            "correcta": pregunta_data['respuesta_correcta'],
                            "explicacion": pregunta_data['explicacion'],
                            "puntos": pts,
                            "es_correcta": es_correcta
                        })
                        if not es_correcta:
                            t_quiz = temario.normalizar_tema_curso(
                                pregunta_data.get("tema")
                            )
                            if t_quiz:
                                uso_stats.registrar_evento_aprendizaje(
                                    "Quiz",
                                    {
                                        "tipo_evento": "quiz_respuesta_incorrecta",
                                        "tema": t_quiz,
                                        "modalidad": st.session_state.get(
                                            "quiz_modalidad", ""
                                        ),
                                        "indice_pregunta": actual + 1,
                                    },
                                )
                        st.rerun()
                    else:
                        st.warning("⚠️ Selecciona una opción.")
            
            else:
                # FEEDBACK INMEDIATO (Si ya respondió pero no ha pasado a la siguiente)
                ultimo_dato = st.session_state.respuestas_usuario[actual]
                
                st.info("**Tu respuesta:**")
                _render_texto_con_latex(ultimo_dato["elegida"])
                
                if ultimo_dato['es_correcta']:
                    st.success("✅ ¡Correcto!")
                else:
                    st.error("❌ Incorrecto. **La correcta era:**")
                    _render_texto_con_latex(ultimo_dato["correcta"])
                
                with st.expander("💡 Ver Explicación", expanded=True):
                    _render_texto_con_latex(ultimo_dato["explicacion"])
                
                if st.button("Siguiente Pregunta ➡️", type="primary"):
                    st.session_state.indice_pregunta += 1
                    st.rerun()

        else:
            # PANTALLA 3: RESULTADOS
            suma_puntos = sum(r['puntos'] for r in st.session_state.respuestas_usuario)
            nota_final = round(suma_puntos, 2)

            if nota_final >= 10:
                st.success(f"✅ Examen Finalizado - Aprobado con {nota_final}")
            else:
                st.warning(f"⚠️ Examen Finalizado - Nota: {nota_final}")
            
            col_nota_top, col_info_top = st.columns([1, 2])
            with col_nota_top:
                st.metric("Calificación Final", f"{nota_final} / 20 pts")
            with col_info_top:
                st.info("💡 Puedes **descargar el informe en PDF** con tu calificación y comentarios al final de esta página.")

            st.divider()
            st.subheader("📄 Detalle del Examen")

            for i, r in enumerate(st.session_state.respuestas_usuario):
                st.markdown(f"#### 🔹 Pregunta {i+1} ({r['puntos']} pts)")
                _render_texto_con_latex(r["pregunta"])
                
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    if r['es_correcta']:
                        st.success("✅ **Tu respuesta:**")
                    else:
                        st.error("❌ **Tu respuesta:**")
                    _render_texto_con_latex(r["elegida"])
                
                with col_res2:
                    if not r['es_correcta']:
                        st.warning("✔ **Correcta:**")
                        _render_texto_con_latex(r["correcta"])

                st.markdown("**📝 Explicación:**")
                _render_texto_con_latex(r["explicacion"])
                st.markdown("---")

            st.markdown("### 🏁 Resumen Final")
            col_nota_bot, col_info_bot = st.columns([1, 2])
            with col_nota_bot:
                st.metric("Calificación Final ", f"{nota_final} / 20 pts")
            
            st.divider()

            col_pdf, col_nuevo = st.columns(2)
            with col_pdf:
                pdf_bytes = generar_pdf_informe_quiz(st.session_state.respuestas_usuario, nota_final)
                pdf_bytes = bytes(pdf_bytes) if isinstance(pdf_bytes, bytearray) else pdf_bytes
                st.download_button(
                    "📥 Descargar informe (PDF)",
                    data=pdf_bytes,
                    file_name=f"informe_SigmaTutor_{str(nota_final).replace('.', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            with col_nuevo:
                if st.button("🔄 Comenzar Nuevo Examen", type="primary", use_container_width=True):
                    st.session_state.quiz_activo = False
                    st.session_state.indice_pregunta = 0
                    st.session_state.respuestas_usuario = []
                    st.rerun()
# =======================================================
# LÓGICA D: TUTOR PREGUNTAS ABIERTAS (NUEVO)
# =======================================================
elif ruta == "d) Tutor: Preguntas Abiertas":
    st.markdown("""
    Haz cualquier pregunta teórica. El tutor te responderá **vinculando la teoría con
    los ejercicios y estilos de examen** del curso.
    """)

    if len(st.session_state.historial_tutor_abierto) > AVISO_HISTORIAL_LARGO:
        st.info("💬 **Conversación larga.** Para respuestas más precisas, usa **← Volver al inicio** y entra de nuevo al modo, o recarga la página.")

    for mensaje in st.session_state.historial_tutor_abierto:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    if prompt := st.chat_input("Ej. puedes preguntar por resumen o explicación corta de cualquier tema a partir de los ejercicios del curso"):
        with st.spinner("Clasificando tema para estadísticas…"):
            _tema_stats = clasificar_tema_desde_texto(prompt)
        uso_stats.registrar_uso(
            "Tutor Preguntas Abiertas",
            detalle={
                "tipo_evento": "tutor_consulta",
                "tema_catedra": _tema_stats,
                "pregunta_resumen": (prompt or "")[:500],
            },
        )
        st.session_state.historial_tutor_abierto.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consultando guías del curso..."):
                ultimos = st.session_state.historial_tutor_abierto[-MAX_MENSAJES_HISTORIAL_TUTOR:]
                historial_texto = "\n".join([f"{m['role']}: {m['content']}" for m in ultimos])
                respuesta_tutor = generar_respuesta_tutor_abierto(prompt, historial_texto)
                st.markdown(respuesta_tutor)

        st.session_state.historial_tutor_abierto.append({"role": "assistant", "content": respuesta_tutor})

# =======================================================
# LÓGICA E: CORRECCIÓN DE MANUSCRITOS
# =======================================================
elif ruta == "e) Corrección de Manuscritos":
    st.info("Sube una foto de tu resolución escrita. La app identificará el enunciado, valorará tu solución y te dará un juicio (correcto / parcialmente correcto / incorrecto) con sugerencias de ajuste.")

    imagen_manuscrito = st.file_uploader(
        "📸 Sube la foto de tu manuscrito (enunciado + resolución)",
        type=["png", "jpg", "jpeg"],
        key="upload_manuscrito"
    )

    if imagen_manuscrito:
        st.image(imagen_manuscrito, caption="Tu manuscrito", use_container_width=True)

        if st.button("🔍 Evaluar manuscrito", type="primary", use_container_width=True):
            with st.spinner("Analizando enunciado y valorando tu resolución..."):
                try:
                    img_pil = Image.open(imagen_manuscrito)
                    resultado = evaluar_manuscrito(img_pil)
                    if resultado:
                        _tm = temario.normalizar_tema_curso(resultado.get("tema_catedra"))
                        uso_stats.registrar_uso(
                            "Corrección de Manuscritos",
                            detalle={"tema_catedra": _tm},
                        )
                        st.session_state.manuscrito_correccion = resultado
                        st.rerun()
                    else:
                        st.error("No se pudo interpretar la corrección. Intenta con una imagen más clara o con otro manuscrito.")
                except Exception as e:
                    st.error(f"Error al procesar la imagen: {e}")

    if st.session_state.manuscrito_correccion:
        datos = st.session_state.manuscrito_correccion
        st.divider()
        _tc_show = temario.normalizar_tema_curso(datos.get("tema_catedra"))
        if _tc_show:
            st.caption(f"📌 **Tema identificado (temario):** `{_tc_show}`")

        st.subheader("📋 Enunciado identificado")
        enunciado = datos.get("enunciado", "")
        if enunciado:
            s = enunciado.strip().replace("\\\\", "\n")
            # Si es solo una fórmula (sin texto tipo "Calcular..."): un solo bloque $$ sin $ internos
            es_solo_formula = ("\\int" in s or "\\sqrt" in s or "\\frac" in s) and not any(
                w in s.lower() for w in ["calcular", "evalúe", "resuelva", "siguiente", "definida", "indefinida", "con respecto", "variable x", "la integral"]
            )
            if es_solo_formula:
                t = "$$" + s.replace("$", "").strip() + "$$"
            else:
                t = preparar_latex_para_streamlit(enunciado)
            st.markdown(t)
        else:
            st.caption("(No se pudo extraer enunciado)")

        juicio = (datos.get("juicio") or "").strip().lower()
        st.subheader("⚖️ Juicio")
        if juicio == "correcto":
            st.success("✅ **Correcto** — Tu resolución es correcta.")
        elif juicio == "parcialmente_correcto":
            st.warning("⚠️ **Parcialmente correcto** — Hay aspectos a mejorar.")
        elif juicio == "incorrecto":
            st.error("❌ **Incorrecto** — La resolución presenta errores importantes.")
        else:
            st.info(f"**Juicio:** {juicio or 'No especificado'}")

        resumen = datos.get("resumen_valoracion", "")
        if resumen:
            st.markdown("**Valoración:**")
            st.markdown(preparar_latex_para_streamlit(resumen))

        errores = datos.get("errores_detectados") or []
        if errores:
            st.subheader("🔴 Errores detectados")
            for e in errores:
                st.markdown("- " + preparar_latex_para_streamlit(e))

        pasos_omitidos = datos.get("pasos_omitidos") or []
        if pasos_omitidos:
            st.subheader("📌 Pasos omitidos o importantes")
            for p in pasos_omitidos:
                st.markdown("- " + preparar_latex_para_streamlit(p))

        sugerencias = datos.get("sugerencias") or []
        if sugerencias:
            st.subheader("💡 Sugerencias de ajuste")
            for s in sugerencias:
                st.markdown("- " + preparar_latex_para_streamlit(s))

        st.divider()
        if st.button("🔄 Evaluar otro manuscrito", key="btn_nuevo_manuscrito"):
            st.session_state.manuscrito_correccion = None
            st.rerun()

# =======================================================
# LÓGICA F: PLANES DE ESTUDIO OFICIALES
# =======================================================
elif ruta == interfaz.MODO_PLANES_ESTUDIO_OFICIALES:
    interfaz.mostrar_planes_estudio_oficiales()

# --- Pie del panel central: total de interacciones ---
interfaz.mostrar_dudas_resueltas()
