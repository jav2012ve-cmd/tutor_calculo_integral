import random

# ==============================================================================
# BANCO DE PREGUNTAS - MATEMÁTICAS III (ECONOMÍA UCAB)
# Versión: 88 Ejercicios (Sintaxis Corregida y Blindada)
# ==============================================================================

BANCO_FIXED = [
    # --- CÁLCULO INTEGRAL: MÉTODOS BÁSICOS ---
    {
        "tema": "1.1.1 Integrales Directas",
        "pregunta": r"Resuelva la siguiente integral con respecto a la variable $x$: $$ \int (3y-2x)^{20} dx $$",
        "opciones": [
            r"A) $-\frac{1}{42}(3y-2x)^{21} + C$",
            r"B) $\frac{1}{21}(3y-2x)^{21} + C$",
            r"C) $\frac{1}{63}(3y-2x)^{21} + C$",
            r"D) $20(3y-2x)^{19} + C$"
        ],
        "respuesta_correcta": r"A) $-\frac{1}{42}(3y-2x)^{21} + C$",
        "explicacion": r"Al integrar respecto a $x$, $3y$ es constante. Usamos sustitución $u = 3y-2x \Rightarrow du = -2dx$."
    },
    {
        "tema": "1.1.1 Integrales Directas",
        "pregunta": r"Resuelva la integral respecto a $y$: $$ \int \frac{e^{3y-2x}}{e^{y+2x}} dy $$",
        "opciones": [
            r"A) $\frac{1}{2}e^{2y-4x} + C$",
            r"B) $e^{2y-4x} + C$",
            r"C) $\frac{1}{2}e^{2y} + C$",
            r"D) $2e^{2y-4x} + C$"
        ],
        "respuesta_correcta": r"A) $\frac{1}{2}e^{2y-4x} + C$",
        "explicacion": r"Simplificamos exponentes: $(3y-2x) - (y+2x) = 2y - 4x$. Integramos $e^{2y-4x}$ respecto a $y$ dividiendo por 2."
    },
    {
        "tema": "1.1.1 Integrales Directas",
        "pregunta": r"Resuelva respecto a $t$: $$ \int \sqrt[3]{x^{-2}t^{-3}} dt $$",
        "opciones": [
            r"A) $x^{-2/3} \ln|t| + C$",
            r"B) $\frac{3}{2} x^{-2/3} t^{2/3} + C$",
            r"C) $-3 x^{-2/3} t^{-2} + C$",
            r"D) $x^{-2/3} \frac{t^{-2}}{-2} + C$"
        ],
        "respuesta_correcta": r"A) $x^{-2/3} \ln|t| + C$",
        "explicacion": r"Reescribimos: $x^{-2/3} t^{-1}$. La integral de $1/t$ es $\ln|t|$."
    },
    {
        "tema": "1.1.1 Integrales Directas",
        "pregunta": r"Calcule la integral definida: $$ \int_{1}^{2} \frac{x^2-1}{x^2} dx $$",
        "opciones": [
            r"A) $0.5$",
            r"B) $1.5$",
            r"C) $2.0$",
            r"D) $\ln(2)$"
        ],
        "respuesta_correcta": r"A) $0.5$",
        "explicacion": r"Separamos: $1 - x^{-2}$. Integral: $[x + 1/x]_1^2 = (2.5) - (2) = 0.5$."
    },
    {
        "tema": "1.1.1 Integrales Directas",
        "pregunta": r"Integral de $(x-2y^2)^2$ respecto a $y$:",
        "opciones": [
            r"A) $x^2y - \frac{4}{3}xy^3 + \frac{4}{5}y^5 + C$",
            r"B) $\frac{1}{3}(x-2y^2)^3 + C$",
            r"C) $- \frac{(x-2y^2)^3}{4y} + C$",
            r"D) $2(x-2y^2) + C$"
        ],
        "respuesta_correcta": r"A) $x^2y - \frac{4}{3}xy^3 + \frac{4}{5}y^5 + C$",
        "explicacion": r"Expandir binomio: $x^2 - 4xy^2 + 4y^4$. Integrar término a término respecto a $y$."
    },
    # --- SUSTITUCIÓN ---
    {
        "tema": "1.1.2 Cambios de variables (Sustitución)",
        "pregunta": r"Resuelva: $$ \int \frac{\sqrt{1-4\ln x}}{x} dx $$",
        "opciones": [
            r"A) $-\frac{1}{6}(1-4\ln x)^{3/2} + C$",
            r"B) $\frac{2}{3}(1-4\ln x)^{3/2} + C$",
            r"C) $-\frac{1}{4}\sqrt{1-4\ln x} + C$",
            r"D) $\ln|1-4\ln x| + C$"
        ],
        "respuesta_correcta": r"A) $-\frac{1}{6}(1-4\ln x)^{3/2} + C$",
        "explicacion": r"Sustitución $u = 1-4\ln x \Rightarrow du = -4/x dx$. Integral $-\frac{1}{4}\int u^{1/2} du$."
    },
    {
        "tema": "1.1.2 Cambios de variables (Sustitución)",
        "pregunta": r"Teoría: Si $z = f(x)$, la integral $\int g(f(x)) f'(x) dx$ es equivalente a:",
        "opciones": [
            r"A) $\int g(z) dz$",
            r"B) $\int g(z) f'(z) dz$",
            r"C) $\int \frac{g(z)}{f'(x)} dz$",
            r"D) Ninguna de las anteriores"
        ],
        "respuesta_correcta": r"A) $\int g(z) dz$",
        "explicacion": r"Definición directa del diferencial $dz = f'(x)dx$."
    },
    {
        "tema": "1.1.2 Cambios de variables (Sustitución)",
        "pregunta": r"Resuelva: $$ \int (1-3x)^{-2} dx $$",
        "opciones": [
            r"A) $\frac{1}{3(1-3x)} + C$",
            r"B) $-\frac{1}{1-3x} + C$",
            r"C) $\frac{3}{1-3x} + C$",
            r"D) $\frac{(1-3x)^{-3}}{-3} + C$"
        ],
        "respuesta_correcta": r"A) $\frac{1}{3(1-3x)} + C$",
        "explicacion": r"$u=1-3x \Rightarrow du=-3dx$. Integral $-\frac{1}{3} \int u^{-2} du = \frac{1}{3}u^{-1}$."
    },
    {
        "tema": "1.1.2 Cambios de variables (Sustitución)",
        "pregunta": r"Evalúe: $$ \int \frac{\cos(1-2\ln x)}{x} dx $$",
        "opciones": [
            r"A) $-\frac{1}{2}\sin(1-2\ln x) + C$",
            r"B) $\sin(1-2\ln x) + C$",
            r"C) $-2\sin(1-2\ln x) + C$",
            r"D) $\cos(1-2\ln x) + C$"
        ],
        "respuesta_correcta": r"A) $-\frac{1}{2}\sin(1-2\ln x) + C$",
        "explicacion": r"$u=1-2\ln x \Rightarrow du = -2/x dx$. Integral $-\frac{1}{2}\int \cos u du$."
    },
    {
        "tema": "1.1.2 Cambios de variables (Sustitución)",
        "pregunta": r"Resuelva: $$ \int \frac{(1-2\sqrt{x})^3}{\sqrt{x}} dx $$",
        "opciones": [
            r"A) $-\frac{1}{4}(1-2\sqrt{x})^4 + C$",
            r"B) $\frac{1}{4}(1-2\sqrt{x})^4 + C$",
            r"C) $-\frac{1}{2}(1-2\sqrt{x})^4 + C$",
            r"D) $4(1-2\sqrt{x})^4 + C$"
        ],
        "respuesta_correcta": r"A) $-\frac{1}{4}(1-2\sqrt{x})^4 + C$",
        "explicacion": r"$u=1-2\sqrt{x} \Rightarrow du = -1/\sqrt{x} dx$. Integral $-\int u^3 du$."
    },
    # --- FRACCIONES SIMPLES ---
    {
        "tema": "1.1.4 Fracciones Simples",
        "pregunta": r"Forma correcta de descomponer $\frac{2x+x^2+2x^3+4}{(x^2+4)(x^2+1)}$:",
        "opciones": [
            r"A) $\frac{Ax+B}{x^2+4} + \frac{Cx+D}{x^2+1}$",
            r"B) $\frac{A}{x^2+4} + \frac{B}{x^2+1}$",
            r"C) $\frac{Ax}{x^2+4} + \frac{Bx}{x^2+1}$",
            r"D) $\frac{A}{(x^2+4)^2} + \frac{B}{x^2+1}$"
        ],
        "respuesta_correcta": r"A) $\frac{Ax+B}{x^2+4} + \frac{Cx+D}{x^2+1}$",
        "explicacion": r"Factores cuadráticos irreducibles requieren numeradores lineales ($Ax+B$)."
    },
    {
        "tema": "1.1.4 Fracciones Simples",
        "pregunta": r"Resuelva (división primero): $$ \int \frac{2x+1}{x-4} dx $$",
        "opciones": [
            r"A) $2x + 9\ln|x-4| + C$",
            r"B) $2x + \ln|x-4| + C$",
            r"C) $x^2 + \ln|x-4| + C$",
            r"D) $2 + 9(x-4)^{-1} + C$"
        ],
        "respuesta_correcta": r"A) $2x + 9\ln|x-4| + C$",
        "explicacion": r"División: $2 + 9/(x-4)$. Integral directa."
    },
    {
        "tema": "1.1.4 Fracciones Simples",
        "pregunta": r"Calcule: $$ \int \frac{1}{x^2 - 5x + 6} dx $$",
        "opciones": [
            r"A) $\ln|x-3| - \ln|x-2| + C$",
            r"B) $\ln|x-2| - \ln|x-3| + C$",
            r"C) $\ln|(x-3)(x-2)| + C$",
            r"D) $\frac{1}{2x-5} + C$"
        ],
        "respuesta_correcta": r"A) $\ln|x-3| - \ln|x-2| + C$",
        "explicacion": r"Factorización $(x-3)(x-2)$. A/(x-3) + B/(x-2). A=1, B=-1."
    },
    {
        "tema": "1.1.4 Fracciones Simples",
        "pregunta": r"Resuelva: $$ \int \left( \frac{2}{x-1} - \frac{4}{x+1} + \frac{2x}{x^2+1} \right) dx $$",
        "opciones": [
            r"A) $2\ln|x-1| - 4\ln|x+1| + \ln(x^2+1) + C$",
            r"B) $2\ln|x-1| - 4\ln|x+1| + 2\arctan x + C$",
            r"C) $\ln \frac{(x-1)^2}{(x+1)^4} + \frac{1}{x^2+1}$",
            r"D) $2(x-1)^{-1} + C$"
        ],
        "respuesta_correcta": r"A) $2\ln|x-1| - 4\ln|x+1| + \ln(x^2+1) + C$",
        "explicacion": r"Integrales logarítmicas directas. El último término tiene la derivada en el numerador."
    },
    {
        "tema": "1.1.4 Fracciones Simples",
        "pregunta": r"Descomposición de $\frac{x^2+1}{x(x-1)^2}$:",
        "opciones": [
            r"A) $\frac{A}{x} + \frac{B}{x-1} + \frac{C}{(x-1)^2}$",
            r"B) $\frac{A}{x} + \frac{Bx+C}{(x-1)^2}$",
            r"C) $\frac{A}{x} + \frac{B}{x-1} + \frac{Cx+D}{(x-1)^2}$",
            r"D) $\frac{A}{x} + \frac{B}{(x-1)^2}$"
        ],
        "respuesta_correcta": r"A) $\frac{A}{x} + \frac{B}{x-1} + \frac{C}{(x-1)^2}$",
        "explicacion": r"Factor lineal $x$ y factor lineal repetido $(x-1)^2$."
    },
    # --- POR PARTES ---
    {
        "tema": "1.1.5 Integral por partes",
        "pregunta": r"Elección $u, dv$ para $\int x^3 \ln(x^2-4) dx$:",
        "opciones": [
            r"A) $u = \ln(x^2-4)$, $dv = x^3 dx$",
            r"B) $u = x^3$, $dv = \ln(x^2-4) dx$",
            r"C) $u = x^2$, $dv = x \ln(...) dx$",
            r"D) $u = 1$, $dv = x^3 \ln(...) dx$"
        ],
        "respuesta_correcta": r"A) $u = \ln(x^2-4)$, $dv = x^3 dx$",
        "explicacion": r"LIATE: Logarítmica va antes que Algebraica para $u$."
    },
    {
        "tema": "1.1.5 Integral por partes",
        "pregunta": r"Resultado de la cíclica $\int e^{-x} \cos x dx$:",
        "opciones": [
            r"A) $\frac{e^{-x}}{2}(\sin x - \cos x) + C$",
            r"B) $e^{-x}(\sin x + \cos x) + C$",
            r"C) $\frac{e^{-x}}{2}(\cos x - \sin x) + C$",
            r"D) $-e^{-x}\sin x + C$"
        ],
        "respuesta_correcta": r"A) $\frac{e^{-x}}{2}(\sin x - \cos x) + C$",
        "explicacion": r"Aplicando partes dos veces y despejando la integral original."
    },
    {
        "tema": "1.1.5 Integral por partes",
        "pregunta": r"Resuelva: $$ \int 6x e^{1-2x} dx $$",
        "opciones": [
            r"A) $-3xe^{1-2x} - \frac{3}{2}e^{1-2x} + C$",
            r"B) $3xe^{1-2x} - 3e^{1-2x} + C$",
            r"C) $6xe^{1-2x} - 6e^{1-2x} + C$",
            r"D) $3x^2 e^{1-2x} + C$"
        ],
        "respuesta_correcta": r"A) $-3xe^{1-2x} - \frac{3}{2}e^{1-2x} + C$",
        "explicacion": r"$u=6x, dv=e^{1-2x}dx$. Fórmula $uv - \int v du$."
    },
    {
        "tema": "1.1.5 Integral por partes",
        "pregunta": r"Resuelva: $$ \int x \ln x dx $$",
        "opciones": [
            r"A) $\frac{x^2}{2}\ln x - \frac{x^2}{4} + C$",
            r"B) $\frac{x^2}{2}\ln x - \frac{x^2}{2} + C$",
            r"C) $x\ln x - x + C$",
            r"D) $\frac{1}{x} + C$"
        ],
        "respuesta_correcta": r"A) $\frac{x^2}{2}\ln x - \frac{x^2}{4} + C$",
        "explicacion": r"$u=\ln x, dv=x dx \Rightarrow v=x^2/2$. $\int v du = \int x/2 dx = x^2/4$."
    },
    {
        "tema": "1.1.5 Integral por partes",
        "pregunta": r"Resuelva: $$ \int \arcsin(x) dx $$",
        "opciones": [
            r"A) $x \arcsin x + \sqrt{1-x^2} + C$",
            r"B) $x \arcsin x - \sqrt{1-x^2} + C$",
            r"C) $\frac{1}{\sqrt{1-x^2}} + C$",
            r"D) $\cos(\arcsin x) + C$"
        ],
        "respuesta_correcta": r"A) $x \arcsin x + \sqrt{1-x^2} + C$",
        "explicacion": r"$u=\arcsin x, dv=dx$. La integral resultante se hace por sustitución $w=1-x^2$."
    },
    {
        "tema": "1.1.5 Integral por partes",
        "pregunta": r"Resuelva: $$ \int x^3 e^{-x} dx $$",
        "opciones": [
            r"A) $-e^{-x}(x^3 + 3x^2 + 6x + 6) + C$",
            r"B) $e^{-x}(x^3 - 3x^2 + 6x - 6) + C$",
            r"C) $-x^3 e^{-x} + 3x^2 e^{-x} + C$",
            r"D) $-\frac{x^4}{4} e^{-x} + C$"
        ],
        "respuesta_correcta": r"A) $-e^{-x}(x^3 + 3x^2 + 6x + 6) + C$",
        "explicacion": r"Método tabular. Signos alternados. Derivadas de $x^3$: $3x^2, 6x, 6, 0$."
    },
    # --- ÁREAS ---
    {
        "tema": "1.2.1 Áreas entre curvas",
        "pregunta": r"Área entre $y=x^2$ y $y=6-x$:",
        "opciones": [
            r"A) $\int_{-3}^{2} (6 - x - x^2) dx$",
            r"B) $\int_{-3}^{2} (x^2 - (6-x)) dx$",
            r"C) $\int_{0}^{6} (6 - x - x^2) dx$",
            r"D) $\int_{-2}^{3} (6 - x - x^2) dx$"
        ],
        "respuesta_correcta": r"A) $\int_{-3}^{2} (6 - x - x^2) dx$",
        "explicacion": r"Cortes en $x=-3, x=2$. La recta está por encima."
    },
    {
        "tema": "1.2.1 Áreas entre curvas",
        "pregunta": r"Integral para área entre $y=4-x^2$ y $y=1+2x$:",
        "opciones": [
            r"A) $\int_{-3}^{1} [(4-x^2) - (1+2x)] dx$",
            r"B) $\int_{-3}^{1} [(1+2x) - (4-x^2)] dx$",
            r"C) $\int_{0}^{4} \dots dx$",
            r"D) $\int_{-1}^{3} \dots dx$"
        ],
        "respuesta_correcta": r"A) $\int_{-3}^{1} [(4-x^2) - (1+2x)] dx$",
        "explicacion": r"Raíces de intersección $x=-3, x=1$. Parábola abre hacia abajo y está arriba."
    },
    {
        "tema": "1.2.1 Áreas entre curvas",
        "pregunta": r"Área entre $y=x^2+x$ y $y=15-x^2/3$:",
        "opciones": [
            r"A) $\int_{-3.75}^{3} [ (15-x^2/3) - (x^2+x) ] dx$",
            r"B) $\int_{-3}^{3} [ (x^2+x) - (15-x^2/3) ] dx$",
            r"C) $\int_{0}^{3} \dots dx$",
            r"D) $\int_{-4}^{4} \dots dx$"
        ],
        "respuesta_correcta": r"A) $\int_{-3.75}^{3} [ (15-x^2/3) - (x^2+x) ] dx$",
        "explicacion": r"Igualando funciones se obtienen los límites. La segunda función es una parábola que abre hacia abajo (techo)."
    },
    {
        "tema": "1.2.1 Áreas entre curvas",
        "pregunta": r"Área región no acotada entre $y=xe^{-x}$ y $y=e^{-x}$ en $[0, \infty)$:",
        "opciones": [
            r"A) $\int_{0}^{1} (e^{-x} - xe^{-x}) dx + \int_{1}^{\infty} (xe^{-x} - e^{-x}) dx$",
            r"B) $\int_{0}^{\infty} (xe^{-x} - e^{-x}) dx$",
            r"C) $\int_{0}^{\infty} (e^{-x} - xe^{-x}) dx$",
            r"D) $\int_{0}^{1} xe^{-x} dx$"
        ],
        "respuesta_correcta": r"A) $\int_{0}^{1} (e^{-x} - xe^{-x}) dx + \int_{1}^{\infty} (xe^{-x} - e^{-x}) dx$",
        "explicacion": r"Las curvas se cruzan en $x=1$. Hay cambio de posición relativa."
    },
    {
        "tema": "1.2.1 Áreas entre curvas",
        "pregunta": r"Calcule área entre $y=e^{-x}$ y $y=-e^{-2x}$ en $[0, \infty)$:",
        "opciones": [
            r"A) $1.5$",
            r"B) $1.0$",
            r"C) $0.5$",
            r"D) $2.0$"
        ],
        "respuesta_correcta": r"A) $1.5$",
        "explicacion": r"No se cruzan. $\int_0^\infty (e^{-x} + e^{-2x}) dx = [ -e^{-x} - 0.5e^{-2x} ]_0^\infty = 0 - (-1.5) = 1.5$."
    },
    {
        "tema": "1.2.1 Áreas entre curvas",
        "pregunta": r"Plantee la integral (SIN RESOLVER) para el área de la región encerrada por $y = x^2$ y $y = 4$:",
        "opciones": [
            r"A) $\int_{-2}^{2} (4 - x^2) dx$", # Correcta
            r"B) $\int_{0}^{2} (x^2 - 4) dx$",  # Error de límites y orden
            r"C) $\int_{-2}^{2} (x^2 - 4) dx$", # Error de orden (piso - techo)
            r"D) $\int_{0}^{4} (4 - x^2) dx$"   # Error de límites (usa valores de y)
        ],
        "respuesta_correcta": r"A) $\int_{-2}^{2} (4 - x^2) dx$",
        "explicacion": r"Los puntos de corte son $x^2=4 \Rightarrow x=\pm 2$. En ese intervalo, la recta $y=4$ está por encima de la parábola."
    },
    {
        "tema": "1.2.1 Áreas entre curvas",
        "pregunta": r"Plantee la integral (SIN RESOLVER) para el área de la región encerrada por $y = 4-x^2$ y $y = 3x$ en el intervalo $x = -5$ $x = 5$:",
        "opciones": [
            r"A) $\int_{-5}^{-4} (3x-4 - x^2) dxint_{-4}^{1} (4 - x^2-3x) dx+int_{1}^{5} (3x-4 - x^2-3x) dx$", # Correcta
            r"B) $\int_{-5}^{5} (4-x^2 - 3x) dx$",  # Error, no toma en cuenta los cambios de posición de las funciones en el intervalo
            r"C) $$\int_{-5}^{-4} (3x-4 - x^2) dxint_{-4}^{1} (3x-4 - x^2) dx+int_{1}^{5} (3x-4 - x^2-3x) dx$", # Error, falla la posición de las funciones en el intervalo central
            r"D) $\int_{-5}^{-4} (4 - x^2-3x) dxint_{-4}^{1} (4 - x^2-3x) dx+int_{1}^{5} (3x-4 - x^2-3x) dx$",   # Error, falla la posición de las funciones en el primer intervalo. 
        ],
        "respuesta_correcta": r"A) $\int_{-5}^{-4} (3x-4 - x^2) dxint_{-4}^{1} (4 - x^2-3x) dx+int_{1}^{5} (3x-4 - x^2-3x) dx$",
        "explicacion": r"Los puntos de corte entre las funciones son $x=-4$ y $x=1$. Se definen tres intervalos: $x \in [-5, -4]; x \in [-4, 1]; x \in [1, 5]$ En cada intervalo debe validarse la posición de las funciones."
    },
    
    # --- EXCEDENTES ---
    {
        "tema": "1.2.2 Excedentes del consumidor y productor",
        "pregunta": r"Demanda $D(q) = 14 - q^2/4$, Oferta $O(q) = 2q + 2$. Calcule EC:",
        "opciones": [
            r"A) $10.67$",
            r"B) $32.00$",
            r"C) $50.66$",
            r"D) $15.50$"
        ],
        "respuesta_correcta": r"A) $10.67$",
        "explicacion": r"Equilibrio $q=4, p=10$. $\int_0^4 (14-q^2/4) dq - 40 = 10.67$."
    },
    {
        "tema": "1.2.2 Excedentes del consumidor y productor",
        "pregunta": r"Demanda $p = 100 - 2q^2$, Oferta $p = 50 + 3q^2$. Calcule EP:",
        "opciones": [
            r"A) $\int_0^{\sqrt{10}} (80 - (50+3q^2)) dq$",
            r"B) $\int_0^{10} ((100-2q^2) - 80) dq$",
            r"C) $100\sqrt{10}$",
            r"D) $\int_0^{\sqrt{10}} (50+3q^2) dq$"
        ],
        "respuesta_correcta": r"A) $\int_0^{\sqrt{10}} (80 - (50+3q^2)) dq$",
        "explicacion": r"Equilibrio $q=\sqrt{10}, p=80$. EP es el área sobre la oferta y bajo el precio."
    },
    {
        "tema": "1.2.2 Excedentes del consumidor y productor",
        "pregunta": r"EC dados Oferta $p = x^2/9 + 4$ y Demanda $p = 11 - 2x$:",
        "opciones": [
            r"A) $9$",
            r"B) $18$",
            r"C) $4.5$",
            r"D) $27$"
        ],
        "respuesta_correcta": r"A) $9$",
        "explicacion": r"Equilibrio $x=3, p=5$. EC = $\int_0^3 (11-2x - 5) dx = 9$."
    },
    {
        "tema": "1.2.2 Excedentes del consumidor y productor",
        "pregunta": r"EP dados Oferta $p = x^2/4 + 4$ y Demanda $p = 12 - x$:",
        "opciones": [
            r"A) $10.67$",
            r"B) $32.00$",
            r"C) $8.00$",
            r"D) $16.33$"
        ],
        "respuesta_correcta": r"A) $10.67$",
        "explicacion": r"Equilibrio $x=4, p=8$. EP = $\int_0^4 (8 - (x^2/4+4)) dx = 10.67$."
    },
    {
        "tema": "1.2.2 Excedentes del consumidor y productor",
        "pregunta": r"Calcule EP con Oferta $p = 4 + 3x^2$ y Demanda $p = 20 - x^2$:",
        "opciones": [
            r"A) $16$",
            r"B) $32$",
            r"C) $12$",
            r"D) $24$"
        ],
        "respuesta_correcta": r"A) $16$",
        "explicacion": r"Equilibrio $x=2, p=16$. EP = $\int_0^2 (16 - (4+3x^2)) dx = 16$."
    },
    # --- IMPROPIAS ---
    {
        "tema": "1.2.3 Integrales Impropias",
        "pregunta": r"Halle $b$ tal que $\int_{b}^{\infty} \frac{dx}{(1+2x)^2} = \frac{1}{4}$",
        "opciones": [
            r"A) $b = 1/2$",
            r"B) $b = 0$",
            r"C) $b = 1$",
            r"D) $b = 2$"
        ],
        "respuesta_correcta": r"A) $b = 1/2$",
        "explicacion": r"Integral da $\frac{1}{2(1+2b)}$. Igualando a 1/4 da $b=1/2$."
    },
    {
        "tema": "1.2.3 Integrales Impropias",
        "pregunta": r"Convergencia de $\int_{0}^{\infty} \frac{x^2}{\sqrt{(x^3+4)^3}} dx$:",
        "opciones": [
            r"A) Converge a $1/3$",
            r"B) Diverge",
            r"C) Converge a $2/3$",
            r"D) Converge a $0$"
        ],
        "respuesta_correcta": r"A) Converge a $1/3$",
        "explicacion": r"Sustitución $u=x^3+4$. Límite finito."
    },
    {
        "tema": "1.2.3 Integrales Impropias",
        "pregunta": r"Convergencia de $\int_{0}^{\infty} x^2 e^{-x} dx$:",
        "opciones": [
            r"A) Converge a 2$",
            r"B) Converge a 1$",
            r"C) Diverge$",
            r"D) Converge a 0$"
        ],
        "respuesta_correcta": r"A) Converge a 2$",
        "explicacion": r"Es $\Gamma(3) = 2!$."
    },
    {
        "tema": "1.2.3 Integrales Impropias",
        "pregunta": r"Halle $k$ para que $f(x) = k x^2(1-x)$ sea PDF en $[0,1]$:",
        "opciones": [
            r"A) $k = 12$",
            r"B) $k = 6$",
            r"C) $k = 1$",
            r"D) $k = 1/12$"
        ],
        "respuesta_correcta": r"A) $k = 12$",
        "explicacion": r"Integral $\int_0^1 k(x^2-x^3)dx = k(1/3-1/4) = k/12 = 1$."
    },
    {
        "tema": "1.2.3 Integrales Impropias",
        "pregunta": r"Halle $k$ para que $f(x) = k e^{-x/2}$ sea PDF en $x>0$:",
        "opciones": [
            r"A) $k = 0.5$",
            r"B) $k = 2$",
            r"C) $k = 1$",
            r"D) $k = -0.5$"
        ],
        "respuesta_correcta": r"A) $k = 0.5$",
        "explicacion": r"Integral $\int_0^\infty k e^{-x/2} dx = 2k = 1$."
    },
    {
        "tema": "1.2.3 Integrales Impropias",
        "pregunta": r"Evalúe $\int_1^{\infty} x^{-3} dx$:",
        "opciones": [
            r"A) $0.5$",
            r"B) $1$",
            r"C) $0.33$",
            r"D) Diverge"
        ],
        "respuesta_correcta": r"A) $0.5$",
        "explicacion": r"$-1/(2x^2)$ evaluado da $0 - (-0.5) = 0.5$."
    },
    {
        "tema": "1.2.3 Integrales Impropias",
        "pregunta": r"Determine la convergencia de $\int_1^{\infty} \frac{1}{x^p} dx$:",
        "opciones": [
            r"A) Converge si $p > 1$",
            r"B) Converge si $p \ge 1$",
            r"C) Converge si $p < 1$",
            r"D) Diverge para todo $p$"
        ],
        "respuesta_correcta": r"A) Converge si $p > 1$",
        "explicacion": r"Es una p-integral básica. Si $p > 1$, el resultado es $\frac{1}{p-1}$. Si $p \le 1$, el área es infinita."
    },
    {
        "tema": "1.2.3 Integrales Impropias",
        "pregunta": r"Evalúe la integral impropia $\int_0^{\infty} e^{-2x} dx$:",
        "opciones": [
            r"A) $1/2$",
            r"B) $1$",
            r"C) $2$",
            r"D) Diverge"
        ],
        "respuesta_correcta": r"A) $1/2$",
        "explicacion": r"$\lim_{b \to \infty} \left[ -\frac{1}{2}e^{-2x} \right]_0^b = 0 - (-\frac{1}{2}) = 1/2$."
    },
    # --- FUNCIONES DE DISTRIBUCIÓN DE PROBABILIDAD ---
    {
        "tema": "1.2.4 Funciones de Distribución de probabilidad",
        "pregunta": r"Sea $f(x) = kx^2$ una función de densidad para $x \in [0, 3]$. Determine el valor de la constante $k$ para que sea una PDF válida:",
        "opciones": [
            r"A) $k = 1/9$",
            r"B) $k = 1/27$",
            r"C) $k = 3$",
            r"D) $k = 1/3$"
        ],
        "respuesta_correcta": r"A) $k = 1/9$",
        "explicacion": r"Para ser PDF: $\int_{0}^{3} kx^2 dx = 1 \Rightarrow k[\frac{x^3}{3}]_0^3 = 1 \Rightarrow 9k = 1 \Rightarrow k=1/9$."
    },
    {
        "tema": "1.2.4 Funciones de Distribución de probabilidad",
        "pregunta": r"Dada la PDF $f(x) = \frac{1}{2}e^{-x/2}$ para $x \ge 0$, plantee la integral (NO RESOLVER) para hallar la probabilidad de que $x$ esté entre 1 y 5, es decir $P(1 \le x \le 5)$:",
        "opciones": [
            r"A) $\int_{1}^{5} \frac{1}{2}e^{-x/2} dx$",
            r"B) $\int_{0}^{5} \frac{1}{2}e^{-x/2} dx$",
            r"C) $1 - \int_{1}^{5} \frac{1}{2}e^{-x/2} dx$",
            r"D) $\int_{1}^{\infty} \frac{1}{2}e^{-x/2} dx$"
        ],
        "respuesta_correcta": r"A) $\int_{1}^{5} \frac{1}{2}e^{-x/2} dx$",
        "explicacion": r"La probabilidad en un intervalo $[a, b]$ para una PDF es siempre la integral definida de la función en dicho intervalo."
    },     
    {
        "tema": "1.2.4 Funciones de Distribución de probabilidad",
        "pregunta": r"Sea $f(x)$ una PDF definida en $[0, 10]$. Plantee la integral para la probabilidad del evento: '$x$ es menor a 3 **O** mayor a 7' (o inclusivo):",
        "opciones": [
            r"A) $\int_{0}^{3} f(x) dx + \int_{7}^{10} f(x) dx$",
            r"B) $\int_{3}^{7} f(x) dx$",
            r"C) $\int_{0}^{10} f(x) dx - (\int_{0}^{3} f(x) dx + \int_{7}^{10} f(x) dx)$",
            r"D) $\int_{3}^{10} f(x) dx$"
        ],
        "respuesta_correcta": r"A) $\int_{0}^{3} f(x) dx + \int_{7}^{10} f(x) dx$",
        "explicacion": r"El conector 'o' inclusivo en eventos disjuntos (como $x<3$ y $x>7$) se traduce como la suma de las áreas de ambos intervalos."
    },
    {
        "tema": "1.2.4 Funciones de Distribución de probabilidad",
        "pregunta": r"Dada una PDF $f(x)$ en el intervalo $[0, 5]$, plantee la probabilidad del evento '$x$ es menor a 4 **Y** mayor a 1':",
        "opciones": [
            r"A) $\int_{1}^{4} f(x) dx$",
            r"B) $\int_{0}^{1} f(x) dx + \int_{4}^{5} f(x) dx$",
            r"C) $\int_{0}^{4} f(x) dx \cdot \int_{1}^{5} f(x) dx$",
            r"D) $\int_{0}^{5} f(x) dx$"
        ],
        "respuesta_correcta": r"A) $\int_{1}^{4} f(x) dx$",
        "explicacion": r"El conector 'y' representa la intersección de los intervalos $x \in [0, 4]$ y $x \in [1, 5]$, lo que resulta en el intervalo común $[1, 4]$."
    },
    {
        "tema": "1.2.4 Funciones de Distribución de probabilidad",
        "pregunta": r"Sea $f(x) = \frac{1}{5}$ para $x \in [0, 5]$. Calcule la probabilidad del evento '$x \leq 2$ **O** $x \geq 4$':",
        "opciones": [
            r"A) $0.60$",
            r"B) $0.40$",
            r"C) $0.20$",
            r"D) $0.80$"
        ],
        "respuesta_correcta": r"A) $0.60$",
        "explicacion": r"Calculamos $P(x \leq 2) = \int_{0}^{2} \frac{1}{5} dx = 0.4$ y $P(x \geq 4) = \int_{4}^{5} \frac{1}{5} dx = 0.2$. Al ser eventos disjuntos, sumamos: $0.4 + 0.2 = 0.6$."
    },
    {
        "tema": "1.2.4 Funciones de Distribución de probabilidad",
        "pregunta": r"Para una PDF en $[a, b]$, el evento 'O exclusivo' entre dos intervalos $A$ y $B$ ($A \triangle B$) se plantea matemáticamente como:",
        "opciones": [
            r"A) $P(A \cup B) - P(A \cap B)$",
            r"B) $P(A) + P(B)$",
            r"C) $P(A \cap B)$",
            r"D) $1 - P(A \cup B)$"
        ],
        "respuesta_correcta": r"A) $P(A \cup B) - P(A \cap B)$",
        "explicacion": r"El 'o exclusivo' incluye los elementos que están en A o en B, pero no en ambos simultáneamente (diferencia simétrica)."
    },
    
    # --- INTEGRALES DOBLES ---
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Calcule $\int_{0}^{1}\int_{1}^{2} (3x^2 - 6z) dx dz$ (orden $dx, dz$):",
        "opciones": [
            r"A) $-2$",
            r"B) $7$",
            r"C) $0$",
            r"D) $-5$"
        ],
        "respuesta_correcta": r"A) $-2$",
        "explicacion": r"Integral interna $x^3-6zx|_1^2 = 7-6z$. Integral externa $7z-3z^2|_0^1 = 4$."
    },
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Calcule $\int_{0}^{1}\int_{1}^{2} (3x^2 - 6z) dx dz$:",
        "opciones": [
            r"A) $4$",
            r"B) $7$",
            r"C) $0$",
            r"D) $-2$"
        ],
        "respuesta_correcta": r"A) $4$",
        "explicacion": r"Evaluación directa: Interna da $7-6z$. Externa da $4$."
    },
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Plantee para región entre parábola $x = y^2 - 4y$ y recta $y = x - 6$:",
        "opciones": [
            r"A) $\int_{-1}^{6} \int_{y^2-4y}^{y+6} f(x,y) dx dy$",
            r"B) $\int_{-1}^{6} \int_{y+6}^{y^2-4y} f(x,y) dx dy$",
            r"C) $\int \dots dy dx$",
            r"D) $\int \dots$"
        ],
        "respuesta_correcta": r"A) $\int_{-1}^{6} \int_{y^2-4y}^{y+6} f(x,y) dx dy$",
        "explicacion": r"Integración tipo II (dx primero). Límites de y $[-1, 6]$."
    },
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Cambie orden $\int_0^4 \int_0^x f(x,y) dy dx$:",
        "opciones": [
            r"A) $\int_0^4 \int_y^4 f(x,y) dx dy$",
            r"B) $\int_0^4 \int_0^y \dots$",
            r"C) $\int_0^x \dots$",
            r"D) $\int_0^4 \int_4^y \dots$"
        ],
        "respuesta_correcta": r"A) $\int_0^4 \int_y^4 f(x,y) dx dy$",
        "explicacion": r"Región triangular $0 \le y \le x \le 4$. En orden inverso $y \le x \le 4$."
    },
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Calcule $\int_0^1 \int_0^2 (x+y) dy dx$:",
        "opciones": [
            r"A) $3$",
            r"B) $1$",
            r"C) $2$",
            r"D) $4$"
        ],
        "respuesta_correcta": r"A) $3$",
        "explicacion": r"Interna $2x+2$. Externa $1+2=3$."
    },
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Volumen bajo $z=1+x-y$ sobre región limitada por $y=x^2$ y $y=8-2x$:",
        "opciones": [
            r"A) $\int_{-4}^{2} \int_{x^2}^{8-2x} (1+x-y) dy dx$",
            r"B) $\int_{-4}^{2} \int_{8-2x}^{x^2} \dots$",
            r"C) $\int \dots dx dy$",
            r"D) $\int \dots$"
        ],
        "respuesta_correcta": r"A) $\int_{-4}^{2} \int_{x^2}^{8-2x} (1+x-y) dy dx$",
        "explicacion": r"Cortes en $x=-4, 2$. Recta por encima de parábola."
    },
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Calcule la integral doble $\iint_R 2xy \, dA$ sobre el rectángulo $R = [0,2] \times [0,1]$:",
        "opciones": [
            r"A) 2",
            r"B) 4",
            r"C) 1",
            r"D) 8"
        ],
        "respuesta_correcta": r"A) 2",
        "explicacion": r"$\int_0^2 \int_0^1 2xy \, dy \, dx = \int_0^2 x [y^2]_0^1 dx = \int_0^2 x dx = [\frac{x^2}{2}]_0^2 = 2$."
    },
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Al cambiar el orden de integración en $\int_0^1 \int_x^1 f(x,y) \, dy \, dx$, la nueva integral es:",
        "opciones": [
            r"A) $\int_0^1 \int_0^y f(x,y) \, dx \, dy$",
            r"B) $\int_0^1 \int_0^x f(x,y) \, dx \, dy$",
            r"C) $\int_x^1 \int_0^1 f(x,y) \, dx \, dy$",
            r"D) $\int_0^y \int_0^1 f(x,y) \, dx \, dy$"
        ],
        "respuesta_correcta": r"A) $\int_0^1 \int_0^y f(x,y) \, dx \, dy$",
        "explicacion": r"La región es un triángulo definido por $0 \le x \le 1$ y $x \le y \le 1$. Al invertir, $y$ va de 0 a 1 y $x$ va de 0 a $y$."
    },
    # --- INTEGRALES DOBLES SOBRE REGIONES IRREGULARES ---
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Sea $R$ la región acotada por la parábola $y = x^2$ y la recta $y = 4$. Plantee la integral doble $\iint_R f(x,y) dA$ en el orden $dy dx$:",
        "opciones": [
            r"A) $\int_{-2}^{2} \int_{x^2}^{4} f(x,y) dy dx$",
            r"B) $\int_{0}^{2} \int_{x^2}^{4} f(x,y) dy dx$",
            r"C) $\int_{-2}^{2} \int_{0}^{x^2} f(x,y) dy dx$",
            r"D) $\int_{0}^{4} \int_{-\sqrt{y}}^{\sqrt{y}} f(x,y) dy dx$"
        ],
        "respuesta_correcta": r"A) $\int_{-2}^{2} \int_{x^2}^{4} f(x,y) dy dx$",
        "explicacion": r"Los puntos de intersección son $x^2=4 \Rightarrow x = \pm 2$. Para un $x$ fijo, $y$ varía desde la curva inferior (parábola $x^2$) hasta la superior (recta $4$)."
    },    
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Considere la región $R$ limitada por $x = y^2$ y $x = y + 2$. Plantee la integral $\iint_R f(x,y) dA$ usando el orden $dx dy$ (Tipo II):",
        "opciones": [
            r"A) $\int_{-1}^{2} \int_{y^2}^{y+2} f(x,y) dx dy$",
            r"B) $\int_{-1}^{2} \int_{y+2}^{y^2} f(x,y) dx dy$",
            r"C) $\int_{0}^{4} \int_{\sqrt{x}}^{x-2} f(x,y) dx dy$",
            r"D) $\int_{-1}^{1} \int_{y^2}^{y+2} f(x,y) dx dy$"
        ],
        "respuesta_correcta": r"A) $\int_{-1}^{2} \int_{y^2}^{y+2} f(x,y) dx dy$",
        "explicacion": r"Igualando: $y^2 = y+2 \Rightarrow y^2-y-2=0 \Rightarrow (y-2)(y+1)=0$. Límites en $y$ de $-1$ a $2$. La recta $x=y+2$ está a la derecha de la parábola $x=y^2$."
    },
    
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Dada la integral $I = \int_{0}^{1} \int_{y}^{1} f(x,y) dx dy$, realice el cambio de orden a $dy dx$:",
        "opciones": [
            r"A) $\int_{0}^{1} \int_{0}^{x} f(x,y) dy dx$",
            r"B) $\int_{0}^{1} \int_{x}^{1} f(x,y) dy dx$",
            r"C) $\int_{0}^{y} \int_{0}^{1} f(x,y) dy dx$",
            r"D) $\int_{0}^{1} \int_{0}^{1} f(x,y) dy dx$"
        ],
        "respuesta_correcta": r"A) $\int_{0}^{1} \int_{0}^{x} f(x,y) dy dx$",
        "explicacion": r"La región original es un triángulo con vértices $(0,0), (1,0)$ y $(1,1)$. Al cambiar el orden, $x$ va de $0$ a $1$, y para cada $x$, $y$ sube desde $0$ hasta la recta $y=x$."
    },
    {
        "tema": "1.2.6 Integrales Dobles",
        "pregunta": r"Sea $R$ la región en el primer cuadrante limitada por $y = x$ y $y = x^3$. Plantee $\iint_R f(x,y) dA$ en orden $dy dx$:",
        "opciones": [
            r"A) $\int_{0}^{1} \int_{x^3}^{x} f(x,y) dy dx$",
            r"B) $\int_{0}^{1} \int_{x}^{x^3} f(x,y) dy dx$",
            r"C) $\int_{-1}^{1} \int_{x^3}^{x} f(x,y) dy dx$",
            r"D) $\int_{0}^{1} \int_{0}^{x} f(x,y) dy dx$"
        ],
        "respuesta_correcta": r"A) $\int_{0}^{1} \int_{x^3}^{x} f(x,y) dy dx$",
        "explicacion": r"En el intervalo $[0, 1]$, la función identidad $y=x$ está por encima de $y=x^3$. La intersección ocurre en $x=0$ y $x=1$."
    },
    # --- VOLÚMENES DE REVOLUCIÓN ---
    {
        "tema": "1.2.5 Volúmenes de Sólido de Revolución",
        "pregunta": r"Volumen de $f(x)=1+x^2$ entre $x=-1, 5$ girando en $y=-1$:",
        "opciones": [
            r"A) $\pi \int_{-1}^{5} (2+x^2)^2 dx$",
            r"B) $\pi \int (1+x^2)^2 dx$",
            r"C) $2\pi \dots$",
            r"D) $\pi \int ((1+x^2)^2-1) dx$"
        ],
        "respuesta_correcta": r"A) $\pi \int_{-1}^{5} (2+x^2)^2 dx$",
        "explicacion": r"Radio $R = (1+x^2) - (-1) = 2+x^2$. No hay hueco (disco)."
    },
    {
        "tema": "1.2.5 Volúmenes de Sólido de Revolución",
        "pregunta": r"Volumen región $y=x^2-4x$, $y=0$ girando en $y=4$:",
        "opciones": [
            r"A) $\pi \int_0^4 [ 4^2 - (4-(x^2-4x))^2 ] dx$",
            r"B) $\pi \int [ (x^2-4x)^2 ] dx$",
            r"C) $\pi \int [ 4^2 - (4-0)^2 ] dx$",
            r"D) $2\pi \dots$"
        ],
        "respuesta_correcta": r"A) $\pi \int_0^4 [ 4^2 - (4-(x^2-4x))^2 ] dx$",
        "explicacion": r"Arandelas. Radio exterior constante 4 (hasta el eje x). Radio interior hasta la curva."
    },
    {
        "tema": "1.2.5 Volúmenes de Sólido de Revolución",
        "pregunta": r"Volumen región $x=y^2+2, x=1$ girando en $x=-2$:",
        "opciones": [
            r"A) $\pi \int_{-2}^{2} [ (y^2+4)^2 - 3^2 ] dy$",
            r"B) $\pi \int [ (y^2+2)^2 ] dy$",
            r"C) $\pi \int \dots$",
            r"D) $\pi \dots$"
        ],
        "respuesta_correcta": r"A) $\pi \int_{-2}^{2} [ (y^2+4)^2 - 3^2 ] dy$",
        "explicacion": r"Radio mayor $R=(y^2+2)-(-2)$. Radio menor $r=1-(-2)$."
    },
    {
        "tema": "1.2.5 Volúmenes de Sólido de Revolución",
        "pregunta": r"Volumen región $y=2+x^2, y=6$ girando en $y=1$:",
        "opciones": [
            r"A) $\pi \int_{-2}^{2} [ (6-1)^2 - (2+x^2-1)^2 ] dx$",
            r"B) $\pi \int \dots$",
            r"C) $\pi \dots$",
            r"D) $\dots$"
        ],
        "respuesta_correcta": r"A) $\pi \int_{-2}^{2} [ (6-1)^2 - (2+x^2-1)^2 ] dx$",
        "explicacion": r"Radio mayor constante $5$. Radio menor variable $1+x^2$."
    },
    {
        "tema": "1.2.5 Volúmenes de Sólido de Revolución",
        "pregunta": r"Volumen región $y=4-x^2, y=3$ girando en $y=2$:",
        "opciones": [
            r"A) $\pi \int_{0}^{1} [ (4-x^2-2)^2 - (3-2)^2 ] dx$",
            r"B) $\pi \int \dots$",
            r"C) $\pi \dots$",
            r"D) $\dots$"
        ],
        "respuesta_correcta": r"A) $\pi \int_{0}^{1} [ (4-x^2-2)^2 - (3-2)^2 ] dx$",
        "explicacion": r"Radio mayor $(4-x^2)-2$. Radio menor $3-2=1$."
    },
    # --- ECUACIONES DIFERENCIALES: SEPARABLES ---
    {
        "tema": "2.1.1 ED 1er Orden: Separación de Variables",
        "pregunta": r"Población $dp/dt = 10(100-p)^2$. Integral separada:",
        "opciones": [
            r"A) $\int (100-p)^{-2} dp = \int 10 dt$",
            r"B) $\int (100-p)^2 dp = \dots$",
            r"C) $\int \dots$",
            r"D) $\dots$"
        ],
        "respuesta_correcta": r"A) $\int (100-p)^{-2} dp = \int 10 dt$",
        "explicacion": r"Pasar término $p$ dividiendo."
    },
    {
        "tema": "2.1.1 ED 1er Orden: Separación de Variables",
        "pregunta": r"Separar $\sqrt{xy} y' = \frac{x+2}{2-y}$:",
        "opciones": [
            r"A) $\int (2-y)\sqrt{y} dy = \int \frac{x+2}{\sqrt{x}} dx$",
            r"B) $\int \frac{\sqrt{y}}{2-y} dy = \dots$",
            r"C) $\int \dots$",
            r"D) $\int \dots$"
        ],
        "respuesta_correcta": r"A) $\int (2-y)\sqrt{y} dy = \int \frac{x+2}{\sqrt{x}} dx$",
        "explicacion": r"Agrupar y con dy, x con dx."
    },
    {
        "tema": "2.1.1 ED 1er Orden: Separación de Variables",
        "pregunta": r"Solución de $(2-y)\sqrt{xy} dy + (x+2) dx = 0$:",
        "opciones": [
            r"A) $\frac{4}{3}y^{3/2} - \frac{2}{5}y^{5/2} = -(\frac{2}{3}x^{3/2} + 4x^{1/2}) + C$",
            r"B) $2y^{1/2} \dots$",
            r"C) $\ln|2-y| \dots$",
            r"D) $y(2-y)^2 \dots$"
        ],
        "respuesta_correcta": r"A) $\frac{4}{3}y^{3/2} - \frac{2}{5}y^{5/2} = -(\frac{2}{3}x^{3/2} + 4x^{1/2}) + C$",
        "explicacion": r"Integración de potencias fraccionarias tras separar."
    },
    {
        "tema": "2.1.1 ED 1er Orden: Separación de Variables",
        "pregunta": r"Resuelva $\frac{dy}{dx} = \frac{(x-1)(y+3)}{(x+4)(y-2)}$:",
        "opciones": [
            r"A) $y - 5\ln|y+3| = x - 5\ln|x+4| + C$",
            r"B) $y + 5\ln \dots$",
            r"C) $(y-2)^2 \dots$",
            r"D) $\dots$"
        ],
        "respuesta_correcta": r"A) $y - 5\ln|y+3| = x - 5\ln|x+4| + C$",
        "explicacion": r"División de polinomios $(y-2)/(y+3) = 1 - 5/(y+3)$."
    },
    # --- HOMOGÉNEAS ---
    {
        "tema": "2.1.2 ED 1er Orden: Homogéneas",
        "pregunta": r"Tipo de ecuación $(x^2 - 2y^2)dx + y dy = 0$:",
        "opciones": [
            r"A) Homogénea de grado 2",
            r"B) Exacta",
            r"C) Lineal",
            r"D) Separable"
        ],
        "respuesta_correcta": r"A) Homogénea de grado 2",
        "explicacion": r"Todos los términos son grado 2."
    },
    {
        "tema": "2.1.2 ED 1er Orden: Homogéneas",
        "pregunta": r"Clasificación $(x+y)dx - y dy = 0$:",
        "opciones": [
            r"A) Homogénea de grado 1",
            r"B) Exacta",
            r"C) Separable",
            r"D) Lineal"
        ],
        "respuesta_correcta": r"A) Homogénea de grado 1",
        "explicacion": r"Grado 1 en coeficientes."
    },
    {
        "tema": "2.1.2 ED 1er Orden: Homogéneas",
        "pregunta": r"Familia de $(x+y)dx + (x-y)dy = 0$:",
        "opciones": [
            r"A) Homogénea",
            r"B) Separable",
            r"C) Lineal",
            r"D) Bernoulli"
        ],
        "respuesta_correcta": r"A) Homogénea",
        "explicacion": r"Coeficientes del mismo grado."
    },
    {
        "tema": "2.1.2 ED 1er Orden: Homogéneas",
        "pregunta": r"Sustitución para $(x-3y)dx + 2y dy = 0$:",
        "opciones": [
            r"A) $y = ux$",
            r"B) $u = x-3y$",
            r"C) $x = y^2$",
            r"D) $\mu = e^{2y}$"
        ],
        "respuesta_correcta": r"A) $y = ux$",
        "explicacion": r"Estándar para homogéneas."
    },# --- ED 1er ORDEN: HOMOGÉNEAS ---
    {
        "tema": "2.1.2 ED 1er Orden: Homogéneas",
        "pregunta": r"Halle la solución general de la ecuación diferencial homogénea: $(x - 2y) dx + y dy = 0$:",
        "opciones": [
            r"A) $(y - x)^2 = Cx e^{-x/y}$",
            r"B) $(y - x) = C e^{x}$",
            r"C) $y^2 - 2xy + x^2 = C$",
            r"D) $\ln|y-x| + \frac{x}{y-x} = C$"
        ],
        "respuesta_correcta": r"A) $(y - x)^2 = Cx e^{-x/y}$",
        "explicacion": r"Usando $y=ux$ y $dy=udx+xdu$, la ecuación se transforma en una de variables separables cuya integración conduce a la forma implícita $(y-x)^2 = Cxe^{-x/y}$."
    },
    {
        "tema": "2.1.2 ED 1er Orden: Homogéneas",
        "pregunta": r"Resuelva la ecuación diferencial: $y^2 dx + (2xy - x^2) dy = 0$:",
        "opciones": [
            r"A) $x y^2 - x^2 y = C$",
            r"B) $y^2 = \frac{x^2}{2 \ln|y| + C}$",
            r"C) $\frac{x}{y} + \ln|y| = C$",
            r"D) $x^2 y - x y^2 = C$"
        ],
        "respuesta_correcta": r"A) $x y^2 - x^2 y = C$",
        "explicacion": r"Al verificar homogeneidad de grado 2 y sustituir $x=vy$ o $y=ux$, la solución simplificada resulta en la relación algebraica $xy^2 - x^2y = C$."
    },
    
    {
        "tema": "2.1.2 ED 1er Orden: Homogéneas",
        "pregunta": r"Determine la solución de la ED: $(x^2 + y^2) dx + 2xy dy = 0$:",
        "opciones": [
            r"A) $3x^2y + x^3 = C$",
            r"B) $x^2 + y^2 = Cx$",
            r"C) $y = \sqrt{Cx - x^2}$",
            r"D) $x^3 + 3xy^2 = C$"
        ],
        "respuesta_correcta": r"D) $x^3 + 3xy^2 = C$",
        "explicacion": r"Esta ecuación es tanto homogénea como exacta. La integración de $M$ respecto a $x$ y la verificación con $N$ nos da la familia de curvas $x^3 + 3xy^2 = C$."
    },
    {
        "tema": "2.1.2 ED 1er Orden: Homogéneas",
        "pregunta": r"¿Cuál es la solución general de $\frac{dy}{dx} = \frac{y-x}{y+x}$?:",
        "opciones": [
            r"A) $\arctan(\frac{y}{x}) + \ln\sqrt{x^2+y^2} = C$",
            r"B) $\frac{1}{2}\ln|x^2+y^2| + \arctan(\frac{y}{x}) = C$",
            r"C) $y^2 + x^2 = C(y-x)$",
            r"D) $\ln|y+x| = \frac{y}{x} + C$"
        ],
        "respuesta_correcta": r"B) $\frac{1}{2}\ln|x^2+y^2| + \arctan(\frac{y}{x}) = C$",
        "explicacion": r"Al sustituir $y=ux$, la integral resultante de $\frac{1+u}{1+u^2} du$ genera un término de logaritmo (para $u$) y uno de arcotangente."
    },
    # --- EXACTAS ---
    {
        "tema": "2.1.3 ED 1er Orden: Exactas",
        "pregunta": r"Clasificación $(x^2-y^2)dx + (y^2-xy)dy = 0$:",
        "opciones": [
            r"A) Homogénea de grado 2",
            r"B) Exacta",
            r"C) Lineal",
            r"D) Separable"
        ],
        "respuesta_correcta": r"A) Homogénea de grado 2",
        "explicacion": r"No cumple condición de exactitud $M_y = N_x$ directametne (-2y vs -y)."
    },
    {
        "tema": "2.1.3 ED 1er Orden: Exactas",
        "pregunta": r"Valor de $k$ para que sea exacta $(y^3 + kxy^4 - 2x)dx + (3xy^2 + 20x^2y^3)dy = 0$:",
        "opciones": [
            r"A) $k = 10$",
            r"B) $k = 5$",
            r"C) $k = 20$",
            r"D) $k = 4$"
        ],
        "respuesta_correcta": r"A) $k = 10$",
        "explicacion": r"$M_y = 3y^2 + 4ky^3x$. $N_x = 3y^2 + 40xy^3$. $4k=40 \Rightarrow k=10$."
    },
    {
        "tema": "2.1.3 ED 1er Orden: Exactas",
        "pregunta": r"Resuelva la ED: $[2(2x+3y)^2 + 3x^2] dx + [3(2x+3y)^2 - 3y^2] dy = 0$:",
        "opciones": [
            r"A) $\frac{(2x+3y)^3}{3} + x^3 - y^3 = C$",
            r"B) $\frac{2(2x+3y)^3}{3} + 3x^2 - 3y^2 = C$",
            r"C) $(2x+3y)^3 + x^3 - y^3 = C$",
            r"D) $\frac{(2x+3y)^3}{2} + x^3 - y^3 = C$"
        ],
        "respuesta_correcta": r"A) $\frac{(2x+3y)^3}{3} + x^3 - y^3 = C$",
        "explicacion": r"Al verificar exactitud $\frac{\partial M}{\partial y} = \frac{\partial N}{\partial x} = 12(2x+3y)$. La integración de $3x^2$ respecto a $x$ da $x^3$, y $-3y^2$ respecto a $y$ da $-y^3$."
    },
    {
        "tema": "2.1.3 ED 1er Orden: Exactas",
        "pregunta": r"Halle la solución de: $(\frac{1}{y}-2x+\ln^2 y + \frac{2y\ln x}{x}) dx + (3y^2 - \frac{x}{y^2} + \ln^2 x + \frac{2x\ln y}{y}) dy = 0$:",
        "opciones": [
            r"A) $\frac{x}{y} - x^2 + x\ln^2 y + y\ln^2 x + y^3 = C$",
            r"B) $\ln x - x^2 + \ln y + x\ln y + y^3 = C$",
            r"C) $\frac{x}{y} - x^2 + 2\ln x \ln y + y^3 = C$",
            r"D) $\frac{x}{y} - x^2 + y\ln^2 x + y^3 = C$"
        ],
        "respuesta_correcta": r"A) $\frac{x}{y} - x^2 + x\ln^2 y + y\ln^2 x + y^3 = C$",
        "explicacion": r"La función potencial $f(x,y)$ contiene los términos mixtos $y\ln^2 x$ (de $\frac{2y\ln x}{x}$) y $x\ln^2 y$ (de $\frac{2x\ln y}{y}$), además de los términos puros $-x^2$ y $y^3$."
    },    
    {
        "tema": "2.1.3 ED 1er Orden: Exactas",
        "pregunta": r"Resuelva: $(10e^x + e^y - \frac{y}{e^x}) dx + (e^{-x} - 12e^y + xe^y) dy = 0$:",
        "opciones": [
            r"A) $10e^x + ye^x - 12e^y + ye^{-x} = C$",
            r"B) $10e^x + xe^y - 12e^y + ye^{-x} = C$",
            r"C) $10e^x + xe^y - 12e^y - ye^{-x} = C$",
            r"D) $10e^x + e^y - 12e^y + xe^y = C$"
        ],
        "respuesta_correcta": r"B) $10e^x + xe^y - 12e^y + ye^{-x} = C$",
        "explicacion": r"Integrando $M$ respecto a $x$: $10e^x + xe^y + ye^{-x} + g(y)$. Derivando respecto a $y$ e igualando a $N$, obtenemos $g'(y) = -12e^y$."
    },
    # --- LINEALES ---
    {
        "tema": "2.1.4 ED 1er Orden: Lineales",
        "pregunta": r"Factor integrante para $y' + \frac{3}{x}y = x^2 + 1$:",
        "opciones": [
            r"A) $\mu(x) = x^3$",
            r"B) $e^{3x}$",
            r"C) $3 \ln x$",
            r"D) $x^{-3}$"
        ],
        "respuesta_correcta": r"A) $\mu(x) = x^3$",
        "explicacion": r"$e^{3 \ln x} = x^3$."
    },
    {
        "tema": "2.1.4 ED 1er Orden: Lineales",
        "pregunta": r"Clasificación de $(x-3y)dx + 2y dy = 0$ vista como $x(y)$:",
        "opciones": [
            r"A) Lineal en $x$",
            r"B) Bernoulli",
            r"C) Separable",
            r"D) Exacta"
        ],
        "respuesta_correcta": r"A) Lineal en $x$",
        "explicacion": r"Se puede escribir como $dx/dy + P(y)x = Q(y)$."
    },
    {
        "tema": "2.1.4 ED 1er Orden: Lineales",
        "pregunta": r"Halle la solución general de la ecuación: $x dy + (2y - x^3 + x\ln x) dx = 0$:",
        "opciones": [
            r"A) $y = \frac{x^3}{5} - \frac{x}{2}\ln x + \frac{x}{4} + \frac{C}{x^2}$",
            r"B) $y = x^3 - \ln x + C$",
            r"C) $y = \frac{x^4}{5} - x^2\ln x + Cx^2$",
            r"D) $y = \frac{x^3}{5} - \frac{1}{2}\ln x + C$"
        ],
        "respuesta_correcta": r"A) $y = \frac{x^3}{5} - \frac{x}{2}\ln x + \frac{x}{4} + \frac{C}{x^2}$",
        "explicacion": r"Llevamos a forma estándar: $y' + \frac{2}{x}y = x^2 - \ln x$. El factor integrante es $\mu(x) = e^{\int \frac{2}{x}dx} = x^2$. La solución es $y = \frac{1}{x^2} \int x^2(x^2 - \ln x) dx$."
    },
    {
        "tema": "2.1.4 ED 1er Orden: Lineales",
        "pregunta": r"Resuelva la ecuación diferencial lineal en $x$: $dx + (x - e^{-y} \cos y) dy = 0$:",
        "opciones": [
            r"A) $x = e^{-y}(\sin y + C)$",
            r"B) $x = e^{y}(\cos y + C)$",
            r"C) $x = \sin y + e^y + C$",
            r"D) $x = e^{-y}\sin y + C e^y$"
        ],
        "respuesta_correcta": r"A) $x = e^{-y}(\sin y + C)$",
        "explicacion": r"La ecuación es $\frac{dx}{dy} + x = e^{-y}\cos y$. El factor integrante es $\mu(y) = e^y$. Al integrar $\int e^y (e^{-y}\cos y) dy = \int \cos y dy = \sin y + C$."
    },
    {
        "tema": "2.1.4 ED 1er Orden: Lineales",
        "pregunta": r"Determine la solución de $y' - y \tan x = \sec x$:",
        "opciones": [
            r"A) $y = x \sec x + C \sec x$",
            r"B) $y = \sin x + C \cos x$",
            r"C) $y = \sec x \tan x + C$",
            r"D) $y = x \cos x + C$"
        ],
        "respuesta_correcta": r"A) $y = x \sec x + C \sec x$",
        "explicacion": r"$\mu(x) = e^{-\int \tan x dx} = e^{\ln|\cos x|} = \cos x$. Multiplicando la ED: $(y \cos x)' = 1 \Rightarrow y \cos x = x + C \Rightarrow y = \frac{x+C}{\cos x}$."
    },
    # --- ED 1er ORDEN: BERNOULLI ---
    {
        "tema": "2.1.5 ED 1er Orden: Bernoulli",
        "pregunta": r"Resuelva la ecuación diferencial de Bernoulli: $xy dy + (2y^2 - x^3 + x\ln x) dx = 0$:",
        "options": [
            r"A) $y^2 = \frac{x^3}{2} - \frac{2x}{5}\ln x + \frac{2x}{25} + \frac{C}{x^4}$",
            r"B) $y^2 = x^3 - \ln x + C$",
            r"C) $y = \sqrt{x^2 - \ln x} + C$",
            r"D) $y^2 = \frac{x^3}{5} - \frac{x}{2}\ln x + \frac{x}{4} + \frac{C}{x^2}$"
        ],
        "respuesta_correcta": r"A) $y^2 = \frac{x^3}{2} - \frac{2x}{5}\ln x + \frac{2x}{25} + \frac{C}{x^4}$",
        "explicacion": r"Dividiendo por $x y$: $y' + \frac{2}{x}y = (x^2 - \ln x)y^{-1}$. Es Bernoulli con $n=-1$. La sustitución $w = y^2$ la transforma en la lineal $w' + \frac{4}{x}w = 2x^2 - 2\ln x$."
    },
    {
        "tema": "2.1.5 ED 1er Orden: Bernoulli",
        "pregunta": r"Determine la solución general de $y' - y = e^x y^2$:",
        "options": [
            r"A) $y = \frac{1}{Ce^{-x} - e^x}$",
            r"B) $y = \frac{e^x}{C - x}$",
            r"C) $y = (Ce^x - e^{2x})^{-1}$",
            r"D) $y = Ce^x + e^{2x}$"
        ],
        "respuesta_correcta": r"C) $y = (Ce^x - e^{2x})^{-1}$",
        "explicacion": r"Bernoulli con $n=2$. Sustituimos $w = y^{-1} \Rightarrow w' + w = -e^x$. El factor integrante es $e^x$, resultando en $w e^x = -\int e^{2x} dx = -\frac{1}{2}e^{2x} + C$."
    },
    {
        "tema": "2.1.5 ED 1er Orden: Bernoulli",
        "pregunta": r"Halle la solución general de la ecuación diferencial: $x \frac{dy}{dx} + y = x^2 y^2 \ln x$:",
        "opciones": [
            r"A) $y = \frac{1}{x^2(1 - \ln x) + Cx}$",
            r"B) $y = \frac{1}{x(1 - x\ln x + x) + C}$",
            r"C) $y = \frac{1}{x(x - x\ln x + C)}$",
            r"D) $y = x^2 \ln x + Cx$"
        ],
        "respuesta_correcta": r"C) $y = \frac{1}{x(x - x\ln x + C)}$",
        "explicacion": r"Es Bernoulli con $n=2$. Dividiendo por $x y^2$ y usando $w = y^{-1}$, obtenemos $w' - \frac{1}{x}w = -x \ln x$. El factor integrante es $1/x$. La integral resultante es $\int -\ln x dx = x - x \ln x + C$."
    },
    {
        "tema": "2.1.5 ED 1er Orden: Bernoulli",
        "pregunta": r"Resuelva la ecuación diferencial (Bernoulli en $x$): $\frac{dx}{dy} + \frac{x}{y} = y^2 x^3$:",
        "opciones": [
            r"A) $x^{-2} = \frac{2}{y} + Cy^2$",
            r"B) $x^2 = \frac{y}{2 + Cy^3}$",
            r"C) $x^{-2} = y^2 - \frac{2}{5}y^5 + C$",
            r"D) $x^{-2} = \frac{2}{5}y^3 + \frac{C}{y^2}$"
        ],
        "respuesta_correcta": r"D) $x^{-2} = \frac{2}{5}y^3 + \frac{C}{y^2}$",
        "explicacion": r"Aquí $n=3$ respecto a $x$. Sustituimos $w = x^{-2} \Rightarrow \frac{dw}{dy} - \frac{2}{y}w = -2y^2$. El factor integrante es $y^{-2}$. La integral es $\int -2 dy = -2y + C$."
    },
    {
        "tema": "2.1.5 ED 1er Orden: Bernoulli",
        "pregunta": r"Determine la solución de la ecuación: $y' - \frac{1}{x}y = \frac{1}{2y}$:",
        "opciones": [
            r"A) $y^2 = x \ln|x| + Cx^2$",
            r"B) $y^2 = -x + Cx^2$",
            r"C) $y = \sqrt{x^2 + Cx}$",
            r"D) $y^2 = \frac{1}{x} + C$"
        ],
        "respuesta_correcta": r"B) $y^2 = -x + Cx^2$",
        "explicacion": r"Bernoulli con $n = -1$ (ya que $1/y = y^{-1}$). Multiplicando por $2y$ obtenemos $2yy' - \frac{2}{x}y^2 = 1$. Con $w = y^2$, la lineal es $w' - \frac{2}{x}w = 1$. El factor integrante es $x^{-2}$."
    },    
    # --- 2.2.1 ED ORDEN SUPERIOR: HOMOGÉNEAS ---
    {
        "tema": "2.2.1 ED Orden Superior: Homogéneas",
        "pregunta": r"Resuelva la ecuación diferencial: $y'' + 4y' + 3y = 0$:",
        "opciones": [
            r"A) $y = C_1 e^{-x} + C_2 e^{-3x}$",
            r"B) $y = C_1 e^{x} + C_2 e^{3x}$",
            r"C) $y = C_1 e^{-x} + C_2 x e^{-x}$",
            r"D) $y = C_1 \cos(3x) + C_2 \sin(x)$"
        ],
        "respuesta_correcta": r"A) $y = C_1 e^{-x} + C_2 e^{-3x}$",
        "explicacion": r"Ecuación característica: $r^2 + 4r + 3 = 0 \Rightarrow (r+3)(r+1)=0$. Raíces reales distintas $r=-3, -1$."
    },
    {
        "tema": "2.2.1 ED Orden Superior: Homogéneas",
        "pregunta": r"Halle la solución general de: $y''' + 6y'' + 12y' + 8y = 0$:",
        "opciones": [
            r"A) $y = (C_1 + C_2 x + C_3 x^2) e^{-2x}$",
            r"B) $y = C_1 e^{-2x} + C_2 e^{2x} + C_3 e^{0}$",
            r"C) $y = C_1 e^{-2x} + C_2 x e^{-2x} + C_3 e^{2x}$",
            r"D) $y = C_1 e^{-2x} + C_2 e^{-3x} + C_3 e^{-4x}$"
        ],
        "respuesta_correcta": r"A) $y = (C_1 + C_2 x + C_3 x^2) e^{-2x}$",
        "explicacion": r"La característica es $(r+2)^3 = 0$. La raíz $r=-2$ tiene multiplicidad 3."
    },
    {
        "tema": "2.2.1 ED Orden Superior: Homogéneas",
        "pregunta": r"Determine la solución de: $y'' - 6y' + 25y = 0$:",
        "opciones": [
            r"A) $y = e^{3x}(C_1 \cos 4x + C_2 \sin 4x)$",
            r"B) $y = e^{-3x}(C_1 \cos 4x + C_2 \sin 4x)$",
            r"C) $y = C_1 e^{3x} + C_2 e^{4x}$",
            r"D) $y = C_1 e^{7x} + C_2 e^{-1x}$"
        ],
        "respuesta_correcta": r"A) $y = e^{3x}(C_1 \cos 4x + C_2 \sin 4x)$",
        "explicacion": r"Raíces complejas: $r = \frac{6 \pm \sqrt{36-100}}{2} = 3 \pm 4i$. La parte real va en la exponencial y la imaginaria en el argumento de trigonométricas."
    },
    {
        "tema": "2.2.1 ED Orden Superior: Homogéneas",
        "pregunta": r"Resuelva la ecuación: $y^{IV} - 16y = 0$:",
        "opciones": [
            r"A) $y = C_1 e^{2x} + C_2 e^{-2x} + C_3 \cos 2x + C_4 \sin 2x$",
            r"B) $y = C_1 e^{2x} + C_2 e^{-2x} + C_3 e^{2ix} + C_4 e^{-2ix}$",
            r"C) $y = (C_1 + C_2 x + C_3 x^2 + C_4 x^3) e^{2x}$",
            r"D) $y = C_1 \cos 4x + C_2 \sin 4x$"
        ],
        "respuesta_correcta": r"A) $y = C_1 e^{2x} + C_2 e^{-2x} + C_3 \cos 2x + C_4 \sin 2x$",
        "explicacion": r"Raíces de $r^4 - 16 = 0 \Rightarrow (r^2-4)(r^2+4)=0$. Raíces: $2, -2, 2i, -2i$."
    },
    {
        "tema": "2.2.1 ED Orden Superior: Homogéneas",
        "pregunta": r"Si la ecuación característica es $r^2(r-5)=0$, la solución general es:",
        "opciones": [
            r"A) $y = C_1 + C_2 x + C_3 e^{5x}$",
            r"B) $y = C_1 e^{5x}$",
            r"C) $y = C_1 x + C_2 e^{5x}$",
            r"D) $y = C_1 \cos 5x + C_2 \sin 5x$"
        ],
        "respuesta_correcta": r"A) $y = C_1 + C_2 x + C_3 e^{5x}$",
        "explicacion": r"La raíz $r=0$ es doble (genera $C_1 e^{0x} + C_2 x e^{0x} \Rightarrow C_1 + C_2 x$) y $r=5$ es simple."
    },
    {
        "tema": "2.2.1 ED Orden Superior: Homogéneas",
        "pregunta": r"Halle la solución de $y'' + 10y' + 25y = 0$:",
        "opciones": [
            r"A) $y = C_1 e^{-5x} + C_2 x e^{-5x}$",
            r"B) $y = C_1 e^{5x} + C_2 x e^{5x}$",
            r"C) $y = C_1 e^{-5x} + C_2 e^{5x}$",
            r"D) $y = C_1 \cos 5x + C_2 \sin 5x$"
        ],
        "respuesta_correcta": r"A) $y = C_1 e^{-5x} + C_2 x e^{-5x}$",
        "explicacion": r"$(r+5)^2 = 0$. Raíz única repetida $r=-5$."
    },
    {
        "tema": "2.2.1 ED Orden Superior: Homogéneas",
        "pregunta": r"Para $y'' + 4y = 0$, la solución es:",
        "opciones": [
            r"A) $y = C_1 \cos 2x + C_2 \sin 2x$",
            r"B) $y = C_1 e^{2x} + C_2 e^{-2x}$",
            r"C) $y = C_1 e^{2ix} + C_2 e^{-2ix}$",
            r"D) $y = C_1 \cos 4x + C_2 \sin 4x$"
        ],
        "respuesta_correcta": r"A) $y = C_1 \cos 2x + C_2 \sin 2x$",
        "explicacion": r"Raíces imaginarias puras $r = \pm 2i$."
    },
    # --- 2.2.2 ED ORDEN SUPERIOR: NO HOMOGÉNEAS ---
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Halle la solución particular $y_p$ de $y'' + 4y' + 3y = x^2 + 12e^x$:",
        "opciones": [
            r"A) $y_p = \frac{1}{3}x^2 - \frac{8}{9}x + \frac{26}{27} + \frac{3}{2}e^x$",
            r"B) $y_p = \frac{1}{3}x^2 + \frac{3}{2}e^x$",
            r"C) $y_p = Ax^2 + Bx + C + De^x$",
            r"D) $y_p = \frac{1}{3}x^2 - \frac{8}{9}x + 2e^x$"
        ],
        "respuesta_correcta": r"A) $y_p = \frac{1}{3}x^2 - \frac{8}{9}x + \frac{26}{27} + \frac{3}{2}e^x$",
        "explicacion": r"Se asume $y_p = Ax^2+Bx+C + De^x$. Al derivar y sustituir, se determinan los coeficientes por igualdad polinómica."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Para $y''' + 6y'' + 12y' + 8y = 4x - 10e^x$, plantee la forma de $y_p$:",
        "opciones": [
            r"A) $y_p = Ax + B + Ce^x$",
            r"B) $y_p = Ax^2 + Bx + Ce^x$",
            r"C) $y_p = Ax + B + Cx^3 e^{-2x}$",
            r"D) $y_p = A + Be^x$"
        ],
        "respuesta_correcta": r"A) $y_p = Ax + B + Ce^x$",
        "explicacion": r"Como las raíces de la homogénea son $r=-2$ (triple) y el lado derecho tiene $e^x$ y $x^1$, no hay resonancia."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Considere $y^{VI} + 4y^V - 3y^{IV} \dots = 4x^2 + 12e^{-x} + 10e^{2x}$. Si la homogénea tiene raíces $r=-2(3), 2(3)$, plantee la forma de $y_p$ para el término $10e^{2x}$:",
        "opciones": [
            r"A) $y_p = Ax^3 e^{2x}$",
            r"B) $y_p = Ae^{2x}$",
            r"C) $y_p = Ax^2 e^{2x}$",
            r"D) $y_p = (Ax^2+Bx+C)e^{2x}$"
        ],
        "respuesta_correcta": r"A) $y_p = Ax^3 e^{2x}$",
        "explicacion": r"Existe resonancia ya que $r=2$ es raíz de la homogénea con multiplicidad 3."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Halle $y_p$ para $y'' - y = 4e^x$:",
        "opciones": [
            r"A) $y_p = 2xe^x$",
            r"B) $y_p = 4e^x$",
            r"C) $y_p = 2e^x$",
            r"D) $y_p = 4xe^x$"
        ],
        "respuesta_correcta": r"A) $y_p = 2xe^x$",
        "explicacion": r"La homogénea tiene raíz $r=1$. Como $g(x)=4e^x$, hay resonancia. Probamos $y_p = Axe^x$."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Para $y'' + 4y = 8x$, la solución particular es:",
        "opciones": [
            r"A) $y_p = 2x$",
            r"B) $y_p = 8x$",
            r"C) $y_p = 4x$",
            r"D) $y_p = 2x + 4$"
        ],
        "respuesta_correcta": r"A) $y_p = 2x$",
        "explicacion": r"Asumiendo $y_p = Ax+B \Rightarrow y_p''=0$. Sustituyendo: $0 + 4(Ax+B) = 8x \Rightarrow 4A=8, 4B=0 \Rightarrow A=2, B=0$."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Determine la forma de $y_p$ para $y'' - 5y' + 6y = e^{2x} + e^{3x}$:",
        "opciones": [
            r"A) $y_p = Axe^{2x} + Bxe^{3x}$",
            r"B) $y_p = Ae^{2x} + Be^{3x}$",
            r"C) $y_p = Ax^2 e^{2x} + Bx^2 e^{3x}$",
            r"D) $y_p = (Ax+B)e^{2x+3x}$"
        ],
        "respuesta_correcta": r"A) $y_p = Axe^{2x} + Bxe^{3x}$",
        "explicacion": r"Las raíces homogéneas son $r=2$ y $r=3$. Ambos términos externos resuenan con la homogénea."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"¿Cuál es el valor de $A$ en $y_p = A \cos x$ para $y'' + 2y' + y = 10 \sin x$?:",
        "opciones": [
            r"A) $A = -5$",
            r"B) $A = 5$",
            r"C) $A = 10$",
            r"D) $A = 0$"
        ],
        "respuesta_correcta": r"A) $A = -5$",
        "explicacion": r"Se debe usar $y_p = A \cos x + B \sin x$. Al sustituir y resolver el sistema, el coeficiente de la función trigonométrica resulta en -5."
    },
    # --- APLICACIONES ---
    {
        "tema": "2.3.1 Aplicaciones de Ecuaciones Diferenciales de primer orden",
        "pregunta": r"Modelo $\frac{dp}{dt} = kp(1000-p)$:",
        "opciones": [
            r"A) Crecimiento Logístico",
            r"B) Malthus",
            r"C) Newton",
            r"D) Desintegración"
        ],
        "respuesta_correcta": r"A) Crecimiento Logístico",
        "explicacion": r"Ecuación verhulst."
    },
    {
        "tema": "2.3.1 Aplicaciones de Ecuaciones Diferenciales de primer orden",
        "pregunta": r"Límite de $\frac{dp}{dt} = kp(200-p)$:",
        "opciones": [
            r"A) 200 unidades",
            r"B) 0",
            r"C) Infinito",
            r"D) 200k"
        ],
        "respuesta_correcta": r"A) 200 unidades",
        "explicacion": r"Capacidad de carga."
    },
    {
        "tema": "2.3.1 Aplicaciones de Ecuaciones Diferenciales de primer orden",
        "pregunta": r"Ley Enfriamiento: $100 \to 80$ en 10 min ($T_a=25$). Temp a los 20 min:",
        "opciones": [
            r"A) $65.33^{\circ}C$",
            r"B) $60$",
            r"C) $70$",
            r"D) $55$"
        ],
        "respuesta_correcta": r"A) $65.33^{\circ}C$",
        "explicacion": r"Cálculo exponencial iterativo."
    },
    {
        "tema": "2.3.1 Aplicaciones de Ecuaciones Diferenciales de primer orden",
        "pregunta": r"Carbono-14, 1/6 remanente. Vida media 5600. Ecuación:",
        "opciones": [
            r"A) $\frac{1}{6} = e^{k t}$ con $k = \frac{\ln(0.5)}{5600}$",
            r"B) $\dots$",
            r"C) $\dots$",
            r"D) $\dots$"
        ],
        "respuesta_correcta": r"A) $\frac{1}{6} = e^{k t}$ con $k = \frac{\ln(0.5)}{5600}$",
        "explicacion": r"Decaimiento radioactivo."
    },
    {
        "tema": "2.3.1 Aplicaciones de Ecuaciones Diferenciales de primer orden",
        "pregunta": r"Solución general enfriamiento $T(t)$:",
        "opciones": [
            r"A) $T(t) = T_a + (T_0 - T_a)e^{kt}$",
            r"B) $\dots$",
            r"C) $\dots$",
            r"D) $\dots$"
        ],
        "respuesta_correcta": r"A) $T(t) = T_a + (T_0 - T_a)e^{kt}$",
        "explicacion": r"Solución analítica estándar."
    },
    {
        "tema": "2.1.5 Aplicaciones de Ecuaciones Diferenciales en Economía",
        "pregunta": r"Si el crecimiento de una inversión $K(t)$ es proporcional a su tamaño actual ($K' = rK$) con una tasa $r=0.05$ y capital inicial $1000$:",
        "opciones": [
            r"A) $K(t) = 1000 e^{0.05t}$",
            r"B) $K(t) = 1000 + 0.05t$",
            r"C) $K(t) = 1000(1.05)^t$",
            r"D) $K(t) = 50 e^{1000t}$"
        ],
        "respuesta_correcta": r"A) $K(t) = 1000 e^{0.05t}$",
        "explicacion": r"Es una ED de variables separables típica de crecimiento continuo. La solución es $K(t) = K_0 e^{rt}$."
    },
    {
        "tema": "2.1.5 Aplicaciones de Ecuaciones Diferenciales en Economía",
        "pregunta": r"La elasticidad precio de la demanda es constante e igual a -2. Si $\frac{dQ}{dp} \frac{p}{Q} = -2$, halle la función de demanda $Q(p)$:",
        "opciones": [
            r"A) $Q = C p^{-2}$",
            r"B) $Q = -2p + C$",
            r"C) $Q = C e^{-2p}$",
            r"D) $Q = p^2 + C$"
        ],
        "respuesta_correcta": r"A) $Q = C p^{-2}$",
        "explicacion": r"Separando variables: $\frac{dQ}{Q} = -2 \frac{dp}{p} \Rightarrow \ln Q = -2 \ln p + c \Rightarrow Q = e^c p^{-2}$."
    },
    {
        "tema": "2.1.5 Aplicaciones de Ecuaciones Diferenciales en Economía",
        "pregunta": r"En un modelo de ajuste de precios, el precio cambia proporcionalmente al exceso de demanda: $P'(t) = \alpha (Q_d - Q_s)$. Si $Q_d = 10-P$ y $Q_s = P-2$, con $\alpha=0.5$:",
        "opciones": [
            r"A) $P' = 6 - P$",
            r"B) $P' = 12 - 2P$",
            r"C) $P' = 0.5(8 - 2P)$",
            r"D) $P' = 5 - 0.5P$"
        ],
        "respuesta_correcta": r"A) $P' = 6 - P$",
        "explicacion": r"$P' = 0.5[(10-P) - (P-2)] = 0.5[12 - 2P] = 6 - P$. Esta es una ED lineal hacia el equilibrio."
    },
    # --------------------------------------------------------------------------
    # AMPLIACIÓN: ED ORDEN SUPERIOR NO HOMOGÉNEAS (Meta: 5 ejercicios)
    # Fuente: Taller 2 - 202525
    # --------------------------------------------------------------------------
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Dada la ecuación $y'' - 2y' - 3y = 4e^{3x}$, ¿cuál es la forma correcta de la solución particular $y_p$ a proponer?",
        "opciones": [
            r"A) $y_p = Ax e^{3x}$",
            r"B) $y_p = A e^{3x}$",
            r"C) $y_p = A x^2 e^{3x}$",
            r"D) $y_p = (Ax+B) e^{3x}$"
        ],
        "respuesta_correcta": r"A) $y_p = Ax e^{3x}$",
        "explicacion": r"La solución homogénea tiene raíces $r=3, r=-1$, por lo que $y_h = c_1 e^{3x} + c_2 e^{-x}$. Como el término $e^{3x}$ ya está en la homogénea (resonancia), multiplicamos la propuesta por $x$."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Encuentre la solución particular de $y'' + y = x^2 + 1$ usando coeficientes indeterminados:",
        "opciones": [
            r"A) $y_p = x^2 - 1$",
            r"B) $y_p = x^2 + 1$",
            r"C) $y_p = Ax^2 + Bx + C$",
            r"D) $y_p = x^2 - 2$"
        ],
        "respuesta_correcta": r"A) $y_p = x^2 - 1$",
        "explicacion": r"Proponemos $y_p = Ax^2 + Bx + C$. Derivando: $y_p'' = 2A$. Sustituyendo: $2A + (Ax^2 + Bx + C) = x^2 + 1$. Igualando coeficientes: $A=1, B=0, 2A+C=1 \Rightarrow C=-1$."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Resuelva la ecuación $y^{\prime\prime\prime} - y'' = 12x$ (Solo la parte particular $y_p$):",
        "opciones": [
            r"A) $y_p = -2x^3 - 6x^2$",
            r"B) $y_p = Ax + B$",
            r"C) $y_p = -6x^2$",
            r"D) $y_p = x^3$"
        ],
        "respuesta_correcta": r"A) $y_p = -2x^3 - 6x^2$",
        "explicacion": r"Raíces homogénea: $r^2(r-1)=0 \Rightarrow 0, 0, 1$. Como 0 es raíz doble, la propuesta para $12x$ (polinomio grado 1) debe multiplicarse por $x^2$. $y_p = x^2(Ax+B) = Ax^3 + Bx^2$."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"Seleccione la solución general de $y'' + 4y = 8$:",
        "opciones": [
            r"A) $y = c_1 \cos 2x + c_2 \sin 2x + 2$",
            r"B) $y = c_1 e^{2x} + c_2 e^{-2x} + 2$",
            r"C) $y = c_1 \cos 2x + c_2 \sin 2x + 4$",
            r"D) $y = \cos 2x + \sin 2x + 8$"
        ],
        "respuesta_correcta": r"A) $y = c_1 \cos 2x + c_2 \sin 2x + 2$",
        "explicacion": r"Homogénea: $r^2+4=0 \Rightarrow r=\pm 2i$. Particular para constante 8: $y_p=A$. Sustitución $4A=8 \Rightarrow A=2$. Suma: $y_h + y_p$."
    },
    {
        "tema": "2.2.2 ED Orden Superior: No Homogéneas",
        "pregunta": r"¿Cuál es la forma de $y_p$ para $y'' + 2y' + 5y = 12e^x - x^2$?",
        "opciones": [
            r"A) $y_p = A e^x + (Bx^2 + Cx + D)$",
            r"B) $y_p = A e^x - x^2$",
            r"C) $y_p = A x e^x + B x^2$",
            r"D) $y_p = (Ax+B) e^x + C x^2$"
        ],
        "respuesta_correcta": r"A) $y_p = A e^x + (Bx^2 + Cx + D)$",
        "explicacion": r"Principio de superposición. Para $12e^x$ proponemos $Ae^x$. Para $-x^2$ proponemos polinomio completo grado 2 ($Bx^2+Cx+D$). No hay conflicto con la homogénea ($r = -1 \pm 2i$)."
    },
    # --- 2.3.1 APLICACIONES DE ED DE PRIMER ORDEN ---
    {
        "tema": "2.3.1 Aplicaciones de ED de primer orden",
        "pregunta": r"Una infección bacteriana se considera curada si se reduce al 10% de la cantidad inicial $P_0$. Si la rapidez de disminución es proporcional a la cantidad presente y la vida media de la bacteria es de 8 días, ¿cuánto dura el tratamiento?:",
        "opciones": [
            r"A) $t = 8 \frac{\ln(0.1)}{\ln(0.5)}$ días",
            r"B) $t = 8 \ln(10)$ días",
            r"C) $t = 24$ días",
            r"D) $t = \frac{\ln(0.5)}{8 \ln(0.1)}$ días"
        ],
        "respuesta_correcta": r"A) $t = 8 \frac{\ln(0.1)}{\ln(0.5)}$ días",
        "explicacion": r"El modelo es $P(t) = P_0 e^{kt}$. Con vida media: $0.5 = e^{8k} \Rightarrow k = \frac{\ln(0.5)}{8}$. Para curar: $0.1 = e^{kt} \Rightarrow t = \frac{\ln(0.1)}{k}$."
    },    
    {
        "tema": "2.3.1 Aplicaciones de ED de primer orden",
        "pregunta": r"Una colonia de bacterias crece según $\frac{dp}{dt} = k \frac{t}{2}(1000 - p)$. Si $p(0) = 50$, ¿cuál es el comportamiento de la población a largo plazo ($t \to \infty$)?",
        "opciones": [
            r"A) La población se estabiliza en 1000 unidades",
            r"B) La población crece infinitamente",
            r"C) La población se extingue",
            r"D) La población oscila alrededor de 500"
        ],
        "respuesta_correcta": r"A) La población se estabiliza en 1000 unidades",
        "explicacion": r"Es un modelo de crecimiento limitado. Al resolver la ED separable, el término exponencial tiende a cero cuando $t \to \infty$, dejando $p(t) = 1000$."
    },
    {
        "tema": "2.3.1 Aplicaciones de ED de primer orden",
        "pregunta": r"En un modelo de mercado, la tasa de cambio del precio es proporcional a la escasez $\frac{dp}{dt} = k(D - S)$. Si $D = 10-p$ y $S = 2+p$, con $p(0)=10$, halle $p(t)$:",
        "opciones": [
            r"A) $p(t) = 4 + 6e^{-2kt}$",
            r"B) $p(t) = 10e^{-kt}$",
            r"C) $p(t) = 4 - 6e^{2kt}$",
            r"D) $p(t) = 6 + 4e^{-2kt}$"
        ],
        "respuesta_correcta": r"A) $p(t) = 4 + 6e^{-2kt}$",
        "explicacion": r"$\frac{dp}{dt} = k[(10-p)-(2+p)] = k(8-2p)$. Separando variables e integrando con $p(0)=10$ se llega a la convergencia hacia el precio de equilibrio $p=4$."
    },
    {
        "tema": "2.3.1 Aplicaciones de ED de primer orden",
        "pregunta": r"Un cultivo de levadura crece a una tasa proporcional a su tamaño. Si inicialmente hay 2 gramos y después de 2 horas hay 4 gramos, ¿cuánta levadura habrá a las 6 horas?:",
        "opciones": [
            r"A) 16 gramos",
            r"B) 12 gramos",
            r"C) 8 gramos",
            r"D) 32 gramos"
        ],
        "respuesta_correcta": r"A) 16 gramos",
        "explicacion": r"La población se duplica cada 2 horas (de 2 a 4). En 6 horas ocurren tres periodos de duplicación: $2 \to 4 \to 8 \to 16$."
    },
    {
        "tema": "2.3.1 Aplicaciones de ED de primer orden",
        "pregunta": r"El modelo de capital $K(t)$ sigue $\frac{dK}{dt} = sY - \delta K$, donde $sY$ es la inversión constante $I_0$. La solución $K(t)$ para este modelo lineal es:",
        "opciones": [
            r"A) $K(t) = \frac{I_0}{\delta} + (K_0 - \frac{I_0}{\delta})e^{-\delta t}$",
            r"B) $K(t) = I_0 e^{\delta t}$",
            r"C) $K(t) = K_0 - \delta t$",
            r"D) $K(t) = \frac{I_0}{\delta} e^{\delta t}$"
        ],
        "respuesta_correcta": r"A) $K(t) = \frac{I_0}{\delta} + (K_0 - \frac{I_0}{\delta})e^{-\delta t}$",
        "explicacion": r"Es una ED lineal de primer orden. El término $I_0/\delta$ representa el nivel de capital de estado estacionario."
    },
    {
        "tema": "2.3.1 Aplicaciones de ED de primer orden",
        "pregunta": r"Un tanque contiene 100L de salmuera. Entra agua pura a 5L/min y sale la mezcla a la misma tasa. Si inicialmente había 20kg de sal, plantee la ED para la cantidad de sal $Q(t)$:",
        "opciones": [
            r"A) $\frac{dQ}{dt} = -\frac{5Q}{100}$",
            r"B) $\frac{dQ}{dt} = 5 - \frac{Q}{100}$",
            r"C) $\frac{dQ}{dt} = 20e^{-0.05t}$",
            r"D) $\frac{dQ}{dt} = -\frac{Q}{5}$"
        ],
        "respuesta_correcta": r"A) $\frac{dQ}{dt} = -\frac{5Q}{100}$",
        "explicacion": r"Tasa de entrada = 0 (agua pura). Tasa de salida = (Concentración) $\times$ (Flujo) = $(Q/100) \times 5$."
    },
    {
        "tema": "2.3.1 Aplicaciones de ED de primer orden",
        "pregunta": r"En el modelo logístico de población $\frac{dP}{dt} = rP(1 - \frac{P}{K})$, si la población actual $P$ es igual a la capacidad de carga $K$, entonces:",
        "opciones": [
            r"A) La tasa de crecimiento es cero",
            r"B) La población crece exponencialmente",
            r"C) La población colapsa",
            r"D) El crecimiento es máximo"
        ],
        "respuesta_correcta": r"A) La tasa de crecimiento es cero",
        "explicacion": r"Si $P=K$, el término $(1 - P/K)$ se hace cero, anulando la derivada. La población ha alcanzado su equilibrio estable."
    },
    # --- APLICACIONES DE ED (ORDEN SUPERIOR) ---
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"Un modelo de dinámica de precios con expectativas genera la ecuación $P'' + 3P' + 2P = 10$. ¿Cuál es el precio de equilibrio a largo plazo ($P_e$)?",
        "opciones": [
            r"A) $P_e = 5$",
            r"B) $P_e = 10$",
            r"C) $P_e = 2$",
            r"D) $P_e = 0$"
        ],
        "respuesta_correcta": r"A) $P_e = 5$",
        "explicacion": r"En el equilibrio, las derivadas se anulan ($P''=0, P'=0$). Queda $2P = 10 \Rightarrow P = 5$. También es la solución particular $y_p$."
    },
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"La ecuación $y'' + 4y = 0$ modela un ciclo económico sin fricción. Su comportamiento es:",
        "opciones": [
            r"A) Oscilatorio perpetuo (Senos y Cosenos)",
            r"B) Convergente (Exponencial decreciente)",
            r"C) Explosivo (Exponencial creciente)",
            r"D) Lineal"
        ],
        "respuesta_correcta": r"A) Oscilatorio perpetuo (Senos y Cosenos)",
        "explicacion": r"Las raíces características son imaginarias puras ($r = \pm 2i$), lo que genera soluciones de la forma $C_1 \cos(2t) + C_2 \sin(2t)$."
    },
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"Si el ingreso nacional $Y(t)$ sigue la ecuación $Y'' - Y' - 6Y = 0$, ¿qué sucede a largo plazo?",
        "opciones": [
            r"A) Crece explosivamente (inestable)",
            r"B) Converge a 0 (estable)",
            r"C) Se mantiene constante",
            r"D) Oscila"
        ],
        "respuesta_correcta": r"A) Crece explosivamente (inestable)",
        "explicacion": r"Raíces: $r^2 - r - 6 = 0 \Rightarrow (r-3)(r+2)=0$. Como hay una raíz positiva ($r=3$), el término $C_1 e^{3t}$ domina y tiende a infinito."
    },
    # --- 2.3.2 APLICACIONES DE ED DE ORDEN SUPERIOR ---
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"Dadas $Q_D = 4p'' - 2p' + 3p - 7t$ y $Q_O = 3p'' - 3p' + 15p - 5$, plantee la ED que rige el precio de equilibrio $p(t)$:",
        "opciones": [
            r"A) $p'' + p' - 12p = 7t - 5$",
            r"B) $p'' - 5p' + 18p = 7t + 5$",
            r"C) $7p'' - 5p' + 18p = 0$",
            r"D) $p'' + p' - 12p = 0$"
        ],
        "respuesta_correcta": r"A) $p'' + p' - 12p = 7t - 5$",
        "explicacion": r"Igualamos $Q_D = Q_O$: $4p'' - 2p' + 3p - 7t = 3p'' - 3p' + 15p - 5$. Al trasponer términos obtenemos $p'' + p' - 12p = 7t - 5$."
    },
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"Para la trayectoria de precios $p'' + p' - 12p = 7t - 5$, con $p(0)=2$ y $p'(0)=4$, halle la solución complementaria $p_h(t)$:",
        "opciones": [
            r"A) $p_h = C_1 e^{3t} + C_2 e^{-4t}$",
            r"B) $p_h = C_1 e^{-3t} + C_2 e^{4t}$",
            r"C) $p_h = C_1 e^{3t} + C_2 x e^{3t}$",
            r"D) $p_h = C_1 \cos(3t) + C_2 \sin(4t)$"
        ],
        "respuesta_correcta": r"A) $p_h = C_1 e^{3t} + C_2 e^{-4t}$",
        "explicacion": r"La ecuación característica es $r^2 + r - 12 = 0 \Rightarrow (r+4)(r-3)=0$. Las raíces son $r=3$ y $r=-4$."
    },
    
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"Considerando la solución del ejercicio anterior $p(t) = C_1 e^{3t} + C_2 e^{-4t} + p_p(t)$, ¿cuál es el comportamiento del precio a largo plazo ($t \to \infty$)?",
        "opciones": [
            r"A) Es inestable (tiende a infinito debido a $e^{3t}$)",
            r"B) Converge al equilibrio (tiende a $p_p$)",
            r"C) Oscila permanentemente",
            r"D) Se mantiene constante en $p(0)$"
        ],
        "respuesta_correcta": r"A) Es inestable (tiende a infinito debido a $e^{3t}$)",
        "explicacion": r"Como una de las raíces de la característica es positiva ($r=3$), el término $C_1 e^{3t}$ domina y hace que el precio se aleje del equilibrio si $C_1 \neq 0$."
    },
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"Halle el precio de equilibrio de mercado (solución particular $p_p$) para $p'' + p' - 12p = 7t - 5$:",
        "opciones": [
            r"A) $p_p = -\frac{7}{12}t + \frac{53}{144}$",
            r"B) $p_p = 7t - 5$",
            r"C) $p_p = \frac{7}{12}t$",
            r"D) $p_p = -\frac{7}{12}t - \frac{67}{144}$"
        ],
        "respuesta_correcta": r"A) $p_p = -\frac{7}{12}t + \frac{53}{144}$",
        "explicacion": r"Asumimos $p_p = At + B$. Al derivar y sustituir: $A - 12(At+B) = 7t - 5$. Comparando coeficientes: $-12A = 7 \Rightarrow A = -7/12$."
    },
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"En un modelo de ciclo económico, el ingreso nacional $Y(t)$ sigue $Y'' + 2Y' + 5Y = 10$. El comportamiento del ingreso a mediano plazo es:",
        "opciones": [
            r"A) Oscilaciones amortiguadas que convergen a $Y=2$",
            r"B) Oscilaciones explosivas",
            r"C) Crecimiento exponencial constante",
            r"D) Convergencia monótona (sin oscilar)"
        ],
        "respuesta_correcta": r"A) Oscilaciones amortiguadas que convergen a $Y=2$",
        "explicacion": r"Las raíces son $-1 \pm 2i$. La parte real negativa (-1) amortigua el sistema, y la parte imaginaria genera las oscilaciones (ciclo)."
    },
    
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"Si un modelo de expectativas de precios genera raíces características $r_1 = 0$ y $r_2 = -5$, el precio a largo plazo:",
        "opciones": [
            r"A) Tiende a una constante $C_1 + p_p$",
            r"B) Converge a cero",
            r"C) Crece linealmente con el tiempo",
            r"D) Es puramente oscilatorio"
        ],
        "respuesta_correcta": r"A) Tiende a una constante $C_1 + p_p$",
        "explicacion": r"La raíz $r=0$ genera un término constante $C_1 e^{0t} = C_1$. El término $e^{-5t}$ desaparece al límite."
    },
    {
        "tema": "2.3.2 Aplicaciones de Ecuaciones Diferenciales de Orden superior",
        "pregunta": r"Para que un sistema de precios $ap'' + bp' + cp = g(t)$ sea estable (converja al equilibrio), las raíces de la ecuación característica deben tener:",
        "opciones": [
            r"A) Partes reales negativas",
            r"B) Solo raíces reales",
            r"C) Partes reales positivas",
            r"D) Determinante igual a cero"
        ],
        "respuesta_correcta": r"A) Partes reales negativas",
        "explicacion": r"Si las partes reales son negativas, todas las soluciones de la homogénea tienden a cero cuando $t \to \infty$, dejando solo el nivel de equilibrio $p_p$."
    },
]

def obtener_preguntas_fijas(temas_solicitados, cantidad):
    candidatas = [p for p in BANCO_FIXED if any(t in p["tema"] for t in temas_solicitados)]
    if not candidatas:
        return []
    num_a_seleccionar = min(len(candidatas), cantidad)

    return random.sample(candidatas, num_a_seleccionar)




