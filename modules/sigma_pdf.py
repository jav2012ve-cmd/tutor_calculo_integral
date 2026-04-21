"""
PDF corporativo Σigma (fpdf): cabecera con logo, título centrado y pie con paginación.
"""

from __future__ import annotations

import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

_ROOT = Path(__file__).resolve().parents[1]

_LOGO_CANDIDATES: tuple[str, ...] = (
    str(_ROOT / "LogoSigma.jpg"),
    str(_ROOT / "assets" / "LogoSigma.jpg"),
    str(_ROOT / "LogoSigma.png"),
    str(_ROOT / "assets" / "LogoSigma.png"),
)


def _resolver_ruta_logo_sigma() -> Optional[str]:
    for p in _LOGO_CANDIDATES:
        if os.path.isfile(p):
            return p
    return None


def _resolver_fuente_sistema_sans() -> Optional[str]:
    """TTF del sistema para rasterizar el pie con Σ (evita incrustar fuente completa en el PDF)."""
    windir = os.environ.get("WINDIR")
    if windir:
        for name in ("arial.ttf", "Arial.ttf", "calibri.ttf", "Calibri.ttf"):
            p = os.path.join(windir, "Fonts", name)
            if os.path.isfile(p):
                return p
    mac = "/Library/Fonts/Arial.ttf"
    if os.path.isfile(mac):
        return mac
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ):
        if os.path.isfile(p):
            return p
    return None


def _logo_para_cabecera_pdf(ruta: str, max_px: int = 240) -> BytesIO:
    """Escala el logo para cabecera (evita incrustar PNG de varios MB en el PDF)."""
    buf = BytesIO()
    with Image.open(ruta) as im:
        im = im.convert("RGBA") if im.mode not in ("RGB", "L") else im.convert("RGB")
        im.thumbnail((max_px, max_px))
        im.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def _bitmap_tagline_pie_sigma() -> BytesIO:
    """Línea raster con la leyenda exacta (incluye Σ y acentos) sin fuentes embebidas en el PDF."""
    texto = "\u03a3igma: Tu Tutor Inteligente de C\u00e1lculo"
    rgb = (158, 165, 175)
    font_path = _resolver_fuente_sistema_sans()
    img = Image.new("RGB", (520, 34), (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    except OSError:
        font = ImageFont.load_default()
    d.text((4, 9), texto, fill=rgb, font=font)
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


class SigmaPDF(FPDF):
    """
    FPDF con cabecera: modo «informe quiz» (logo, banner de calificación, datos) o título clásico.
    El pie usa latin-1; las cadenas de cabecera deben llegar ya seguras para ese encoding.
    """

    _TAGLINE_ASCII = "Sigma: Tu Tutor Inteligente de Calculo"
    _COLOR_LINEA_AZUL = (41, 128, 185)
    _COLOR_PIE_GRIS = (158, 165, 175)
    _HEADER_QUIZ_ALTO = 32.0
    _MARGEN_SUPERIOR_CUERPO_QUIZ = 40.0

    def __init__(self, titulo_reporte: str, **kwargs: Any) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.titulo_reporte = titulo_reporte
        self._logo_path = _resolver_ruta_logo_sigma()
        self._cabecera_informe_quiz: bool = bool(kwargs.get("cabecera_informe_quiz"))
        self._quiz_nombre: str = str(kwargs.get("nombre_estudiante") or "")
        self._quiz_fecha: str = str(kwargs.get("fecha_informe") or "")
        self._quiz_tipo: str = str(kwargs.get("tipo_actividad") or "Simulacro")
        self._quiz_nota: Optional[float] = kwargs.get("nota_final")
        self._quiz_aprobado: str = str(kwargs.get("aprobado_texto") or "")

        self._tmp_logo_header: Optional[str] = None
        self._tmp_tagline_png: Optional[str] = None

        self.alias_nb_pages()
        self.set_auto_page_break(auto=True, margin=22)
        top_m = self._MARGEN_SUPERIOR_CUERPO_QUIZ if self._cabecera_informe_quiz else 34.0
        self.set_margins(12, top_m, 12)

    def _header_modo_informe_quiz(self) -> None:
        """Logo izquierda, banner central con calificación, bloque derecho (nombre, fecha, actividad)."""
        y0 = 4.0
        xl = 10.0
        wl_logo = 28.0
        ancho_logo_mm = 22.0
        xc = xl + wl_logo + 2.0
        wc = 72.0
        xr = xc + wc + 3.0
        wr = max(22.0, self.w - 10.0 - xr)
        zona_h = self._HEADER_QUIZ_ALTO

        if self._logo_path:
            try:
                if not self._tmp_logo_header:
                    mini = _logo_para_cabecera_pdf(self._logo_path)
                    tf = tempfile.NamedTemporaryFile(suffix="_sigma_logo.png", delete=False)
                    tf.write(mini.getvalue())
                    tf.close()
                    self._tmp_logo_header = tf.name
                self.image(self._tmp_logo_header, x=xl, y=y0 + 1.0, w=ancho_logo_mm)
            except Exception:
                try:
                    self.image(self._logo_path, x=xl, y=y0 + 1.0, w=ancho_logo_mm)
                except Exception:
                    pass

        self.set_fill_color(235, 244, 255)
        self.set_draw_color(*self._COLOR_LINEA_AZUL)
        self.set_line_width(0.35)
        self.rect(xc, y0, wc, zona_h, "DF")
        self.set_xy(xc, y0 + 2.0)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(55, 65, 80)
        self.cell(wc, 4, "Calificación Final", align="C", ln=1)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(15, 23, 42)
        if self._quiz_nota is not None:
            self.cell(wc, 9, f"{self._quiz_nota} / 20", align="C", ln=1)
        if self._quiz_aprobado:
            self.set_font("Helvetica", "B", 8)
            if "No" in self._quiz_aprobado:
                self.set_text_color(185, 28, 28)
            else:
                self.set_text_color(22, 120, 60)
            self.cell(wc, 5, self._quiz_aprobado, align="C", ln=1)
        self.set_text_color(0, 0, 0)

        der_txt = "Estudiante:\n"
        der_txt += self._quiz_nombre.strip() if self._quiz_nombre.strip() else "—"
        if self._quiz_fecha.strip():
            der_txt += "\n\nFecha:\n" + self._quiz_fecha.strip()
        if self._quiz_tipo.strip():
            der_txt += "\n\nActividad:\n" + self._quiz_tipo.strip()
        self.set_xy(xr, y0 + 1.0)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(30, 41, 59)
        self.multi_cell(wr, 3.8, der_txt, align="L")
        self.set_text_color(0, 0, 0)

        y_linea = y0 + zona_h + 2.0
        self.set_draw_color(*self._COLOR_LINEA_AZUL)
        self.set_line_width(0.45)
        self.line(10.0, y_linea, self.w - 10.0, y_linea)
        self.set_y(y_linea + 3.0)

    def _header_modo_clasico(self) -> None:
        y_logo = 5.0
        ancho_logo = 20.0
        if self._logo_path:
            try:
                if not self._tmp_logo_header:
                    mini = _logo_para_cabecera_pdf(self._logo_path)
                    tf = tempfile.NamedTemporaryFile(suffix="_sigma_logo.png", delete=False)
                    tf.write(mini.getvalue())
                    tf.close()
                    self._tmp_logo_header = tf.name
                self.image(self._tmp_logo_header, x=10, y=y_logo, w=ancho_logo)
            except Exception:
                try:
                    self.image(self._logo_path, x=10, y=y_logo, w=ancho_logo)
                except Exception:
                    pass
        self.set_font("Helvetica", "B", 14)
        self.set_xy(0, y_logo + 1.5)
        self.cell(0, 10, self.titulo_reporte, ln=1, align="C")
        y_linea = 24.0
        self.set_draw_color(*self._COLOR_LINEA_AZUL)
        self.set_line_width(0.55)
        self.line(10, y_linea, self.w - 10, y_linea)
        self.set_y(y_linea + 4.5)

    def header(self) -> None:
        if self._cabecera_informe_quiz:
            self._header_modo_informe_quiz()
        else:
            self._header_modo_clasico()

    def footer(self) -> None:
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self._COLOR_PIE_GRIS)
        self.cell(0, 5, "Pagina " + str(self.page_no()) + " / {nb}", align="C", ln=1)
        try:
            if not self._tmp_tagline_png:
                buf = _bitmap_tagline_pie_sigma()
                tf = tempfile.NamedTemporaryFile(suffix="_sigma_tagline.png", delete=False)
                tf.write(buf.getvalue())
                tf.close()
                self._tmp_tagline_png = tf.name
            w_img = min(self.w - 20, 118)
            x_img = (self.w - w_img) / 2.0
            self.image(self._tmp_tagline_png, x=x_img, y=self.get_y(), w=w_img)
        except Exception:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*self._COLOR_PIE_GRIS)
            self.cell(0, 5, self._TAGLINE_ASCII, align="C", ln=1)

    def output(self, name: str = "", dest: str = "") -> str | bytes:
        try:
            return super().output(name, dest)
        finally:
            for p in (self._tmp_logo_header, self._tmp_tagline_png):
                if p and os.path.isfile(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass
            self._tmp_logo_header = None
            self._tmp_tagline_png = None
