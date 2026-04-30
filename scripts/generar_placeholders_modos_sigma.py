#!/usr/bin/env python3
"""
Genera placeholders estilizados (HUD + icono minimalista) para los 6 modos Σigma.

Los nombres de archivo coinciden con la primera opción de ``_imagen_por_modo``
en ``modules/interfaz.py`` (búsqueda en raíz y en ``assets/``).

Uso:
  python scripts/generar_placeholders_modos_sigma.py

Requiere: Pillow
"""

from __future__ import annotations

import math
import os
from typing import Callable

from PIL import Image, ImageDraw

# --- Paleta (HUD marino + acento cian) ---
NAVY = (6, 18, 42)
NAVY_MID = (12, 32, 58)
ACCENT = (56, 189, 248)  # sky-400
ACCENT_DIM = (30, 100, 140)
ICON = (226, 232, 240)  # slate-200
GRID = (25, 55, 85)

W, H = 1200, 675
BRACKET = 56
BRACKET_THICK = 4
MARGIN = 36


def _assets_dir() -> str:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    return os.path.join(root, "assets")


def _draw_hud_frame(d: ImageDraw.ImageDraw, w: int, h: int) -> None:
    """Bordes tipo HUD: esquinas en L + marco interior sutil."""
    m = MARGIN
    L = BRACKET
    t = BRACKET_THICK

    def corner_l(x0: int, y0: int, dx: int, dy: int) -> None:
        d.line([(x0, y0), (x0 + dx, y0)], fill=ACCENT, width=t)
        d.line([(x0, y0), (x0, y0 + dy)], fill=ACCENT, width=t)

    # Cuatro esquinas
    corner_l(m, m, L, 0)
    corner_l(m, m, 0, L)
    corner_l(w - m - L, m, L, 0)
    corner_l(w - m, m, 0, L)
    corner_l(m, h - m - L, 0, L)
    corner_l(m, h - m, L, 0)
    corner_l(w - m - L, h - m, L, 0)
    corner_l(w - m, h - m, 0, -L)

    inset = m + L // 2
    d.rectangle(
        [inset, inset, w - inset, h - inset],
        outline=ACCENT_DIM,
        width=2,
    )
    # Micro-líneas decorativas (ticks)
    tick = 10
    for i in range(8):
        x = inset + 40 + i * (w - 2 * inset - 80) // 7
        d.line([(x, inset), (x, inset + tick)], fill=ACCENT_DIM, width=1)
        d.line([(x, h - inset), (x, h - inset - tick)], fill=ACCENT_DIM, width=1)


def _draw_bg_grid(im: Image.Image, d: ImageDraw.ImageDraw) -> None:
    """Sutil rejilla de perspectiva HUD."""
    w, h = im.size
    step = 48
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=GRID, width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=GRID, width=1)
    # Viñeta (solo mientras el rectángulo sea válido)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    max_i = min(w, h) // 2 - 2
    for i in range(0, max_i, 4):
        if w - i <= i or h - i <= i:
            break
        a = max(0, 28 - i // 10)
        od.rectangle([i, i, w - i, h - i], outline=(0, 0, 0, a), width=2)
    im.alpha_composite(overlay)


def _icon_seguimos_ruta(d: ImageDraw.ImageDraw, cx: int, cy: int, s: int) -> None:
    """Nodos y ruta (mapa)."""
    pts = [
        (cx - s, cy - s // 2),
        (cx, cy + s // 2),
        (cx + s, cy - s // 3),
    ]
    r = s // 5
    d.line([pts[0], pts[1], pts[2]], fill=ICON, width=5)
    for x, y in pts:
        d.ellipse([x - r, y - r, x + r, y + r], outline=ACCENT, width=3)
        d.ellipse([x - r + 2, y - r + 2, x + r - 2, y + r - 2], fill=NAVY_MID)


def _icon_entrenamiento(d: ImageDraw.ImageDraw, cx: int, cy: int, s: int) -> None:
    """Pesa minimalista + sugerencia de 'carga' (rect central)."""
    bw, bh = s // 2, s // 3
    gap = s // 3
    bar_h = s // 10
    lx = cx - gap - bw
    rx = cx + gap
    d.rounded_rectangle([lx, cy - bh // 2, lx + bw, cy + bh // 2], radius=6, outline=ICON, width=4)
    d.rounded_rectangle([rx, cy - bh // 2, rx + bw, cy + bh // 2], radius=6, outline=ICON, width=4)
    d.rectangle([lx + bw, cy - bar_h // 2, rx, cy + bar_h // 2], fill=ACCENT)
    # "cerebro": dos arcos superiores
    d.arc([cx - s // 3, cy - s, cx, cy - s // 4], 20, 160, fill=ICON, width=3)
    d.arc([cx, cy - s, cx + s // 3, cy - s // 4], 20, 160, fill=ICON, width=3)


def _icon_consulta(d: ImageDraw.ImageDraw, cx: int, cy: int, s: int) -> None:
    """Lupa + libro (rect fino detrás)."""
    r = s // 3
    d.rounded_rectangle([cx - s // 2 - 8, cy - r - 6, cx - s // 2 + 14, cy + r + 10], radius=4, outline=ACCENT_DIM, width=2)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ICON, width=5)
    d.pieslice([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], 45, 320, fill=NAVY_MID)
    hx, hy = cx + int(r * 0.65), cy + int(r * 0.65)
    d.line([(hx, hy), (hx + s // 2, hy + s // 2)], fill=ICON, width=6)


def _icon_simulacro(d: ImageDraw.ImageDraw, cx: int, cy: int, s: int) -> None:
    """Trofeo + hoja de examen (rect pequeño)."""
    # Copa
    w_c, h_c = s // 2, s // 2
    top = cy - h_c // 2
    d.pieslice([cx - w_c // 2, top - 10, cx + w_c // 2, top + h_c], 0, 180, fill=ICON, outline=ICON)
    d.rectangle([cx - w_c // 2 - 8, top + h_c // 2, cx + w_c // 2 + 8, top + h_c // 2 + 14], fill=ACCENT)
    d.rectangle([cx - 6, top + h_c // 2 + 14, cx + 6, top + h_c // 2 + 28], fill=ICON)
    # Asas
    d.arc([cx - w_c // 2 - 22, top + 10, cx - w_c // 2 + 6, top + h_c - 8], 90, 270, fill=ACCENT, width=3)
    d.arc([cx + w_c // 2 - 6, top + 10, cx + w_c // 2 + 22, top + h_c - 8], -90, 90, fill=ACCENT, width=3)
    # Mini "examen"
    ex = cx + w_c // 2 + 24
    ey = cy - s // 3
    d.rounded_rectangle([ex, ey, ex + s // 3, ey + s // 2], radius=4, outline=ICON, width=2)
    for i in range(4):
        yy = ey + 14 + i * 14
        d.line([(ex + 10, yy), (ex + s // 3 - 12, yy)], fill=ACCENT_DIM, width=2)


def _icon_tutor_chat(d: ImageDraw.ImageDraw, cx: int, cy: int, s: int) -> None:
    """Bocadillo de chat."""
    w_b, h_b = s, s // 2
    x0, y0 = cx - w_b // 2, cy - h_b // 2
    d.rounded_rectangle([x0, y0, x0 + w_b, y0 + h_b], radius=22, outline=ICON, width=4)
    tail = [
        (x0 + w_b // 4, y0 + h_b),
        (x0 + w_b // 4 - 12, y0 + h_b + 22),
        (x0 + w_b // 4 + 28, y0 + h_b),
    ]
    d.polygon(tail, fill=ICON)
    # Tres puntos
    for i, dx in enumerate((-18, 0, 18)):
        d.ellipse([cx + dx - 4, cy - 4, cx + dx + 4, cy + 4], fill=NAVY_MID)


def _icon_manuscrito_camara(d: ImageDraw.ImageDraw, cx: int, cy: int, s: int) -> None:
    """Cámara minimalista."""
    body_w, body_h = int(s * 1.1), int(s * 0.75)
    x0, y0 = cx - body_w // 2, cy - body_h // 2
    d.rounded_rectangle([x0, y0, x0 + body_w, y0 + body_h], radius=16, outline=ICON, width=4)
    lens_r = s // 3
    d.ellipse(
        [cx - lens_r, cy - lens_r, cx + lens_r, cy + lens_r],
        outline=ACCENT,
        width=4,
    )
    d.ellipse(
        [cx - lens_r + 10, cy - lens_r + 10, cx + lens_r - 10, cy + lens_r - 10],
        fill=NAVY_MID,
    )
    flash_w = body_w // 4
    d.rounded_rectangle(
        [cx - flash_w // 2, y0 - 18, cx + flash_w // 2, y0 - 6],
        radius=4,
        fill=ACCENT_DIM,
        outline=ICON,
        width=2,
    )


def _make_card(draw_icon: Callable[[ImageDraw.ImageDraw, int, int, int], None]) -> Image.Image:
    im = Image.new("RGBA", (W, H), NAVY + (255,))
    d = ImageDraw.Draw(im)
    _draw_bg_grid(im, d)
    # Brillo radial suave en el centro
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(max(W, H) // 2, 0, -8):
        alpha = max(0, 18 - r // 40)
        gd.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], outline=(30, 80, 120, alpha), width=14)
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    _draw_hud_frame(d, W, H)
    draw_icon(d, W // 2, H // 2, 140)
    return im


def main() -> None:
    out_dir = _assets_dir()
    os.makedirs(out_dir, exist_ok=True)

    # Orden y nombres: primera opción en ``interfaz._imagen_por_modo`` por modo (6 modos de la matriz).
    specs: list[tuple[str, Callable[[ImageDraw.ImageDraw, int, int, int], None]]] = [
        ("botonSeguimos.jpg", _icon_seguimos_ruta),
        ("botonApracticar.jpg", _icon_entrenamiento),
        ("BotonVamosPaso.jpg", _icon_consulta),
        ("BotonSimulacro.jpg", _icon_simulacro),
        ("BotonDime.jpg", _icon_tutor_chat),
        ("BotonTeloReviso.jpg", _icon_manuscrito_camara),
    ]

    for filename, drawer in specs:
        img = _make_card(drawer)
        path = os.path.join(out_dir, filename)
        rgb = img.convert("RGB")
        rgb.save(path, "JPEG", quality=92, optimize=True)
        print(f"OK: {path}")


if __name__ == "__main__":
    main()
