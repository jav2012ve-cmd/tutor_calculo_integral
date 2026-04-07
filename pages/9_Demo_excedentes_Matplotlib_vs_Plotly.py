"""
PROTOTIPO LOCAL — Comparativa Matplotlib vs Plotly (excedente del consumidor y del productor)
===========================================================================================
Ejercicio: mercado lineal con demanda descendente y oferta creciente; equilibrio, EC y EP.

Cómo ejecutar:
  streamlit run app.py
  y en el menú lateral abre la página «9_Demo_excedentes_Matplotlib_vs_Plotly».

Para DESHACER solo esta prueba (volver al tutor sin gráficas):
  - Borra esta carpeta/archivo bajo pages/
  - Quita de requirements.txt las líneas: numpy, matplotlib, plotly
  - pip uninstall matplotlib plotly numpy  (opcional en tu venv)

Punto de control en git (recomendado):
  git tag -a graficas-excedentes-prototipo -m "Prototipo MPL/Plotly excedentes"
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from matplotlib import pyplot as plt

st.set_page_config(page_title="Demo: Excedentes (MPL vs Plotly)", layout="wide")

# --- Mismo enunciado numérico para ambas figuras ---
# Demanda: P = a - b·Q  |  Oferta: P = c + d·Q
a, b = 10.0, 1.0
c, d = 2.0, 1.0
Q_star = (a - c) / (b + d)
P_star = a - b * Q_star

ENUNCIADO = f"""
En un mercado competitivo, la **curva de demanda** es $P = {a:g} - {b:g}Q$ y la **curva de oferta** es $P = {c:g} + {d:g}Q$  
($P$ en unidades monetarias y $Q$ en unidades del bien).

1. Halle el **precio y la cantidad de equilibrio**.  
2. Represente gráficamente el **excedente del consumidor** y el **excedente del productor** en el equilibrio.
"""

st.title("Comparativa local: Matplotlib vs Plotly")
st.caption("Mismo ejercicio de excedentes; dos librerías, mismos datos.")

with st.expander("Enunciado del ejercicio (referencia)", expanded=True):
    st.markdown(ENUNCIADO)
    st.markdown(
        f"**Equilibrio (referencia):** $Q^* = {Q_star:g}$, $P^* = {P_star:g}$.  \n"
        f"**EC** = área bajo la demanda y sobre $P^*$ hasta $Q^*$.  \n"
        f"**EP** = área sobre la oferta y bajo $P^*$ hasta $Q^*$."
    )


def datos_curvas():
    q_max = min(Q_star * 1.35, (a - c) / b * 1.1 + 0.5)
    Q = np.linspace(0, q_max, 200)
    P_d = a - b * Q
    P_s = c + d * Q
    return Q, P_d, P_s


def figura_matplotlib():
    Q, P_d, P_s = datos_curvas()
    Qf = np.linspace(0, Q_star, 120)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(Q, P_d, "b-", linewidth=2, label=r"Demanda: $P = 10 - Q$")
    ax.plot(Q, P_s, "r-", linewidth=2, label=r"Oferta: $P = 2 + Q$")
    ax.axhline(P_star, color="gray", linestyle="--", linewidth=1, alpha=0.8)
    ax.axvline(Q_star, color="gray", linestyle=":", linewidth=1, alpha=0.6)

    # Excedente del consumidor: entre P* y demanda, 0..Q*
    Pd_f = a - b * Qf
    ax.fill_between(Qf, P_star, Pd_f, alpha=0.35, color="green", label="Excedente consumidor")

    # Excedente del productor: entre oferta y P*, 0..Q*
    Ps_f = c + d * Qf
    ax.fill_between(Qf, Ps_f, P_star, alpha=0.35, color="orange", label="Excedente productor")

    ax.plot(Q_star, P_star, "ko", markersize=7, label="Equilibrio")
    ax.set_xlabel(r"Cantidad $Q$")
    ax.set_ylabel(r"Precio $P$")
    ax.set_title("Matplotlib (estático)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def figura_plotly():
    Q, P_d, P_s = datos_curvas()
    Qf = np.linspace(0, Q_star, 80)
    Pd_f = a - b * Qf
    Ps_f = c + d * Qf

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=Q,
            y=P_d,
            mode="lines",
            name="Demanda",
            line=dict(color="blue", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=Q,
            y=P_s,
            mode="lines",
            name="Oferta",
            line=dict(color="red", width=2),
        )
    )

    # Polígono EC: borde superior demanda, inferior P*
    x_ec = np.concatenate([Qf, Qf[::-1]])
    y_ec = np.concatenate([Pd_f, np.full_like(Qf, P_star)[::-1]])
    fig.add_trace(
        go.Scatter(
            x=x_ec,
            y=y_ec,
            fill="toself",
            fillcolor="rgba(0, 160, 0, 0.25)",
            line=dict(width=0),
            name="Excedente consumidor",
            hoverinfo="skip",
        )
    )

    # Polígono EP: borde superior P*, inferior oferta
    x_ep = np.concatenate([Qf, Qf[::-1]])
    y_ep = np.concatenate([np.full_like(Qf, P_star), Ps_f[::-1]])
    fig.add_trace(
        go.Scatter(
            x=x_ep,
            y=y_ep,
            fill="toself",
            fillcolor="rgba(255, 140, 0, 0.3)",
            line=dict(width=0),
            name="Excedente productor",
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[Q_star],
            y=[P_star],
            mode="markers",
            name="Equilibrio",
            marker=dict(color="black", size=10),
        )
    )

    fig.add_hline(y=P_star, line_dash="dash", line_color="gray", opacity=0.7)
    fig.add_vline(x=Q_star, line_dash="dot", line_color="gray", opacity=0.5)

    fig.update_layout(
        title="Plotly (interactivo: zoom, pan, leyenda)",
        xaxis_title="Cantidad Q",
        yaxis_title="Precio P",
        height=480,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    fig.update_xaxes(range=[0, None], zeroline=True)
    fig.update_yaxes(range=[0, None], zeroline=True)
    return fig


col_mpl, col_pl = st.columns(2, gap="large")

with col_mpl:
    st.subheader("Matplotlib")
    st.pyplot(figura_matplotlib(), clear_figure=True)

with col_pl:
    st.subheader("Plotly")
    st.plotly_chart(figura_plotly(), use_container_width=True)

st.divider()
st.markdown(
    "**Qué comparar:** nitidez al imprimir / PDF (Matplotlib), "
    "exploración y lectura de coordenadas (Plotly), tiempo de carga y tamaño del entorno."
)
