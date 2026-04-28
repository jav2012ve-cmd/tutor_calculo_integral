# modules/temario.py
from __future__ import annotations

from typing import Any, Optional

from modules import banco_muestras  # <--- NUEVA LÍNEA IMPORTANTE

# --- LISTAS DE TEMAS ---
# Primer parcial: 1.1.1 → 1.2.3 | Segundo parcial: 1.2.4 → fin (incl. EDO)

TEMAS_PARCIAL_1 = [
    "1.1.1 Integrales Indefinidas Directas",
    "1.1.2 Cambios de variables (Sustitución)",
    "1.1.3 División de Polinomios",
    "1.1.4 Fracciones Simples",
    "1.1.5 Integral por partes",
    "1.2.1 Integral Definida",
    "1.2.2 Áreas entre curvas",
    "1.2.3 Excedentes del consumidor y productor",
]

TEMAS_PARCIAL_2 = [
    "1.2.4 Integrales Impropias",
    "1.2.5 Volúmenes Sólidos de Revolución",
    "1.2.6 Integrales dobles",
    "1.2.7 Funciones de Distribución de probabilidad",
    "2.1.1 ED 1er Orden: Separación de Variables",
    "2.1.2 ED 1er Orden: Homogéneas",
    "2.1.3 ED 1er Orden: Exactas",
    "2.1.4 ED 1er Orden: Lineales",
    "2.1.5 ED 1er Orden: Bernoulli",
    "2.2.1 ED Orden Superior: Homogéneas",
    "2.2.2 ED Orden Superior: No Homogéneas",
    "2.3.1 Aplicaciones de Ecuaciones Diferenciales de primer orden",
    "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
]

# Lista canónica Σigma (banco / prompts actuales): **solo** UCAB · Economía · Matemáticas III.
# El resto de malllas usan ``perfil_curso.lista_temas_activa()`` (átomos de minicurso JSON).
LISTA_TEMAS = TEMAS_PARCIAL_1 + TEMAS_PARCIAL_2
LISTA_TEMAS_UCAB_ECONOMIA_MATEMATICAS_III = LISTA_TEMAS

# --- Gráficos (Plotly) en modo ENTRENAMIENTO ---
# Política: solo algunos temas; el gráfico se muestra si el planteamiento del ejercicio lo permite
# (metadato en banco / enunciado geométrico), no en todos los ítems del tema.
#
# Incluye:
# - 1.2.1: integrales definidas sencillas donde se correlaciona el resultado con el área bajo la curva
#   (p. ej. f ≥ 0 en [a,b], interpretación geométrica explícita).
# - 1.2.7: PDF/CDF; área bajo la densidad ↔ probabilidad de sucesos (intervalos, colas, etc.).
TEMAS_ENTRENAMIENTO_GRAFICO_PLOTLY_OPCIONAL = [
    "1.2.1 Integral Definida",
    "1.2.2 Áreas entre curvas",
    "1.2.3 Excedentes del consumidor y productor",
    "1.2.5 Volúmenes Sólidos de Revolución",
    "1.2.6 Integrales dobles",
    "1.2.7 Funciones de Distribución de probabilidad",
    "2.3.1 Aplicaciones de Ecuaciones Diferenciales de primer orden",
    "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
]

# Resto de temas del temario: no se usa Plotly en entrenamiento (por defecto).
TEMAS_ENTRENAMIENTO_SIN_GRAFICO_PLOTLY = [
    t for t in LISTA_TEMAS if t not in TEMAS_ENTRENAMIENTO_GRAFICO_PLOTLY_OPCIONAL
]


def normalizar_tema_curso(valor: Any, temas_validos: Optional[list[str]] = None) -> Optional[str]:
    """
    Convierte texto de la IA (o similar) al string exacto de la lista de temas activa, o None.

    ``temas_validos``: si se omite, usa ``perfil_curso.lista_temas_activa()`` (UCAB Econ Mat III
    → ``LISTA_TEMAS``; resto → átomos del minicurso).
    """
    temas = temas_validos
    if temas is None:
        try:
            from modules.perfil_curso import lista_temas_activa

            temas = lista_temas_activa()
        except Exception:
            temas = list(LISTA_TEMAS)
    if not temas:
        return None
    if valor is None:
        return None
    s = str(valor).strip()
    if not s or s.upper() == "NULL":
        return None
    if s in temas:
        return s
    s_lower = s.lower()
    for t in temas:
        if t.lower() == s_lower:
            return t
    for t in temas:
        if s_lower in t.lower() or t.lower() in s_lower:
            return t
    return None


def tema_admite_grafico_plotly_entrenamiento(tema: Any) -> bool:
    """True si el tema puede mostrar gráfico Plotly en entrenamiento cuando el ejercicio lo amerite."""
    n = normalizar_tema_curso(tema)
    return n is not None and n in TEMAS_ENTRENAMIENTO_GRAFICO_PLOTLY_OPCIONAL


def clasificar_tema_hito_ruta(tema: str, *, orden_curricular: Optional[list[str]] = None) -> str:
    """
    Clasifica un tema para la vista «Hitos de Ruta» en tres tramos:
    **Base** (primer parcial canónico), **Intermedio** / **Avanzado** (segundo parcial y EDO).

    Si el texto no coincide con el temario UCAB canónico (p. ej. átomos de otra malla),
    se usan tercios del orden de ``orden_curricular`` (por defecto ``LISTA_TEMAS``).
    """
    t = (tema or "").strip()
    if not t:
        return "Intermedio"
    if t in TEMAS_PARCIAL_1:
        return "Base"
    if t in TEMAS_PARCIAL_2:
        mitad = (len(TEMAS_PARCIAL_2) + 1) // 2
        try:
            idx = TEMAS_PARCIAL_2.index(t)
        except ValueError:
            return "Avanzado"
        return "Intermedio" if idx < mitad else "Avanzado"
    oc = orden_curricular or list(LISTA_TEMAS)
    if t not in oc:
        return "Intermedio"
    n = len(oc)
    if n <= 1:
        return "Intermedio"
    i = oc.index(t)
    a = max(1, n // 3)
    b = max(a + 1, (2 * n) // 3)
    if i < a:
        return "Base"
    if i < b:
        return "Intermedio"
    return "Avanzado"


# --- CONTENIDO TEÓRICO (Resumido para el ejemplo) ---
CONTENIDO_TEORICO = {
    "1.1.1 Integrales Indefinidas Directas": {
        "definicion": r"f(x) = \int g(x) dx \iff \frac{d}{dx}[f(x)] = g(x)",
        "propiedades": [
            r"\int [f(x) \pm g(x)] dx = \int f(x) dx \pm \int g(x) dx",
            r"\int C \cdot f(x) dx = C \int f(x) dx",
        ],
        "tabla_col1": [
            r"\int x^n dx = \frac{x^{n+1}}{n+1}",
            r"\int e^{x} dx = e^{x}",
        ],
        "tabla_col2": [
            r"\int \frac{1}{x} dx = \ln|x|",
            r"\int \sin(x) dx = -\cos(x)",
        ],
    }
    # ... (Puedes ir agregando el resto poco a poco)
}

CONTEXTO_BASE = """
Actúa como un profesor titular de Cálculo Integral para estudiantes de distintas carreras.
Tus pilares son integración (métodos y aplicaciones) y ecuaciones diferenciales.
Sé riguroso pero cercano.
"""


# --- NUEVO: Prompt Estructurado para el Quiz ---
# --- NUEVO: Prompt Estructurado con "Few-Shot Learning" ---
def generar_prompt_quiz(temas_seleccionados, cantidad):
    regla_integrales_directas = ""
    if any("1.1.1 Integrales Indefinidas Directas" in t for t in temas_seleccionados):
        regla_integrales_directas = """
    6. Si el tema incluye "1.1.1 Integrales Indefinidas Directas", TODAS las preguntas de ese tema deben ser de integrales INDEFINIDAS.
       PROHIBIDO en ese tema: límites de integración en el integral (por ejemplo: \\int_{1}^{2}, \\int_0^1), frases como "integral definida" o aplicación del teorema fundamental.
       La pregunta DEBE usar el lenguaje de "integral indefinida" y el integral NO debe llevar subíndices/supíndices de límites.
       PROHIBIDO en ese tema: cambios de variable / sustitución (NUNCA escribas "u =" ni "sustitución" ni du).
       Debes integrar SOLO con métodos directos:
       * regla de la potencia (polinomios ya expandidos y $x^n$),
       * exponenciales $e^{ax}$ y combinaciones lineales,
       * distribución por división para fracciones racionales simples (reducir algebraicamente antes de integrar),
       * suma y multiplicación por constantes.
       Evita integrales que requieran que detectes una derivada interna (tipo $\\int f(g(x))g'(x)dx$) como camino principal.
       Si necesitas usar el integrando de un ejemplo definido, conviértelo a versión indefinida (misma función, sin límites).
    """
    return f"""
    ACTÚA COMO PROFESOR DE CÁLCULO INTEGRAL PARA ESTUDIANTES UNIVERSITARIOS.

    TU TAREA:
    Genera un examen de {cantidad} preguntas de selección simple.

    REGLAS OBLIGATORIAS:
    1. CADA pregunta debe tener EXACTAMENTE 4 OPCIONES (A, B, C, D).
    2. Las opciones deben ser plausibles (distractores matemáticos comunes).
    3. NO incluyas notas aclaratorias o pistas en el enunciado. Sé directo y riguroso.
    4. ALEATORIEDAD TOTAL: La respuesta correcta DEBE estar distribuida equitativamente entre A, B, C y D.
       No permitas que la mayoría de las respuestas sean A o B.
    5. Si el ejercicio es de tipo 'PLANTEAR' (como áreas, volúmenes, excedentes o integrales dobles), las 4 opciones de respuesta (A, B, C, D) deben ser expresiones matemáticas de integrales. Tres de ellas deben tener errores comunes de planteamiento (límites invertidos, signos erróneos, funciones restadas en orden incorrecto) y una debe ser el planteamiento correcto.
    {regla_integrales_directas}
    7. PROHIBICIÓN ESTRICTA DE BACKTICKS EN JSON: no uses ` ni ``` en ningún valor de ninguna clave del JSON.
       Esto aplica a "pregunta", "opciones", "explicacion", "tema" y cualquier otro campo.

    REGLA DE ORO (CRÍTICO, anti-fragmentación y JSON limpio):
    - No fragmentes el LaTeX dentro de una misma fórmula: si vas a escribir una expresión matemática, encierra TODA la expresión en un solo par de símbolos $. No cierres y abras dólares dentro de la misma unidad matemática.
      MAL: $\\int$ $x^2$ $dx$
      BIEN: $\\int x^2 dx$
    - Prohibido escribir un símbolo $ suelto en texto natural. Las únicas apariciones de $ deben corresponder exactamente a fórmulas completas envueltas en el patrón $...$.
    - Para los campos "pregunta" y "opciones": usa SOLO $...$ (no $$...$$).
    - Cada expresión matemática atómica debe tener un único par $...$.

    TEMAS A EVALUAR:
    {", ".join(temas_seleccionados)}.

    ESTILO (Referencia):
    Usa estos ejemplos para calibrar el tono, PERO GENERA TUS PROPIOS EJERCICIOS:
    --- INICIO EJEMPLOS ---
    {banco_muestras.EJEMPLOS_ESTILO}
    --- FIN EJEMPLOS ---

    FORMATO DE SALIDA (JSON PURO):
    Devuelve SOLO el array JSON. No incluyas markdown, ni etiquetas, ni texto fuera del JSON.
    [
        {{
            "tema": "Nombre del tema exacto de esta pregunta (ej. 1.1.1 Integrales Indefinidas Directas)",
            "pregunta": "Enunciado LaTeX...",
            "opciones": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "respuesta_correcta": "La opción correcta literal",
            "explicacion": "Explicación paso a paso..."
        }},
        ...
    ]
    """
