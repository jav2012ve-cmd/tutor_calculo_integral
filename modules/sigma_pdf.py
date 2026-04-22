"""
PDF corporativo Σigma (**fpdf2**, ``from fpdf import FPDF``): cabecera con logo, título y pie.
"""

from __future__ import annotations

import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from fpdf import FPDF  # paquete PyPI: fpdf2
from PIL import Image, ImageDraw, ImageFont

_ROOT = Path(__file__).resolve().parents[1]

# Nombre de familia registrado con ``add_font`` (fpdf); usar siempre este identificador en ``set_font``.
PDF_FONT_FAMILY = "DejaVu"

_DEJAVU_REMOTE_BASE = (
    "https://cdn.jsdelivr.net/gh/dejavu-fonts/dejavu-fonts@version_2_37/ttf/"
)
_DEJAVU_DOWNLOAD_TRIED = False

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


def _ensure_dejavu_font_files() -> None:
    """
    Garantiza DejaVu Sans en ``assets/fonts/`` (Streamlit Cloud y otros entornos sin TTF del sistema).
    Descarga desde jsDelivr (repo dejavu-fonts) solo si faltan archivos.
    """
    global _DEJAVU_DOWNLOAD_TRIED
    d = _ROOT / "assets" / "fonts"
    d.mkdir(parents=True, exist_ok=True)
    sans = d / "DejaVuSans.ttf"
    if sans.is_file():
        return
    if _DEJAVU_DOWNLOAD_TRIED:
        return
    _DEJAVU_DOWNLOAD_TRIED = True
    try:
        import urllib.request

        for fn in (
            "DejaVuSans.ttf",
            "DejaVuSans-Bold.ttf",
            "DejaVuSans-Oblique.ttf",
            "DejaVuSans-BoldOblique.ttf",
        ):
            dest = d / fn
            if dest.is_file():
                continue
            req = urllib.request.Request(
                _DEJAVU_REMOTE_BASE + fn,
                headers={"User-Agent": "SigmaTutor-PDF/1.0"},
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                dest.write_bytes(resp.read())
    except Exception:
        pass


def _resolver_ttf_unicode_sans() -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Rutas TTF (regular, bold, italic, bolditalic) para registrar la familia ``DejaVu``.
    Orden: ``assets/fonts`` (tras intento de descarga), sistema Windows/Linux, FreeSans, Arial.
    """
    _ensure_dejavu_font_files()
    bundled = str(_ROOT / "assets" / "fonts" / "DejaVuSans.ttf")
    if os.path.isfile(bundled):
        d = os.path.dirname(bundled)
        b = os.path.join(d, "DejaVuSans-Bold.ttf")
        i = os.path.join(d, "DejaVuSans-Oblique.ttf")
        bi = os.path.join(d, "DejaVuSans-BoldOblique.ttf")
        return (
            bundled,
            b if os.path.isfile(b) else bundled,
            i if os.path.isfile(i) else bundled,
            bi if os.path.isfile(bi) else (b if os.path.isfile(b) else bundled),
        )
    windir = os.environ.get("WINDIR", "")
    fonts_dir = os.path.join(windir, "Fonts") if windir else ""
    if fonts_dir:
        sets: tuple[tuple[str, str, str, str], ...] = (
            ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf"),
            ("arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf"),
            ("Arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf"),
            ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf"),
        )
        for base, b_name, i_name, bi_name in sets:
            reg = os.path.join(fonts_dir, base)
            if not os.path.isfile(reg):
                continue

            def pick(name: str) -> str:
                p = os.path.join(fonts_dir, name)
                return p if os.path.isfile(p) else reg

            return reg, pick(b_name), pick(i_name), pick(bi_name)
    for e in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ):
        if os.path.isfile(e):
            d = os.path.dirname(e)
            b = os.path.join(d, "DejaVuSans-Bold.ttf")
            i = os.path.join(d, "DejaVuSans-Oblique.ttf")
            bi = os.path.join(d, "DejaVuSans-BoldOblique.ttf")
            return (
                e,
                b if os.path.isfile(b) else e,
                i if os.path.isfile(i) else e,
                bi if os.path.isfile(bi) else (b if os.path.isfile(b) else e),
            )
    for e in ("/usr/share/fonts/truetype/freefont/FreeSans.ttf",):
        if os.path.isfile(e):
            d = os.path.dirname(e)
            b = os.path.join(d, "FreeSansBold.ttf")
            i = os.path.join(d, "FreeSansOblique.ttf")
            bi = os.path.join(d, "FreeSansBoldOblique.ttf")
            return (
                e,
                b if os.path.isfile(b) else e,
                i if os.path.isfile(i) else e,
                bi if os.path.isfile(bi) else (b if os.path.isfile(b) else e),
            )
    return None, None, None, None


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
    font_path = str(_ROOT / "assets" / "fonts" / "DejaVuSans.ttf")
    if not os.path.isfile(font_path):
        _ensure_dejavu_font_files()
    if not os.path.isfile(font_path):
        reg, _, _, _ = _resolver_ttf_unicode_sans()
        if reg and os.path.isfile(reg):
            font_path = reg
        else:
            font_path = _resolver_fuente_sistema_sans() or ""
    img = Image.new("RGB", (520, 34), (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 12) if (font_path and os.path.isfile(font_path)) else ImageFont.load_default()
    except OSError:
        font = ImageFont.load_default()
    d.text((4, 9), texto, fill=rgb, font=font)
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


class SigmaPDF(FPDF):
    """
    **fpdf2** (``FPDF``): cabecera modo informe quiz o título clásico.
    Registra la familia Unicode ``DejaVu`` si existe ``assets/fonts/DejaVuSans.ttf`` (u otro TTF).
    Sin TTF: solo fuentes núcleo; el texto debe pasar por ``limpiar_texto_para_pdf`` + latin-1 al escribir.
    """

    _TAGLINE_ASCII = "Sigma: Tu Tutor Inteligente de Calculo"
    _TAGLINE_PIE_UNICODE = "\u03a3igma: Tu Tutor Inteligente de C\u00e1lculo"
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
        self._quiz_banner_alt: str = str(kwargs.get("texto_banner_central") or "")
        self._banner_titulo_centro: str = str(kwargs.get("banner_titulo_centro") or "Calificación Final")

        self._tmp_logo_header: Optional[str] = None
        self._tmp_tagline_png: Optional[str] = None
        self._uses_dejavu: bool = False
        self._pdf_font_family: str = "Helvetica"
        self._registrar_fuente_dejavu_sans()

        self.alias_nb_pages()
        self.set_auto_page_break(auto=True, margin=22)
        top_m = self._MARGEN_SUPERIOR_CUERPO_QUIZ if self._cabecera_informe_quiz else 34.0
        self.set_margins(12, top_m, 12)

    def _registrar_fuente_dejavu_sans(self) -> None:
        """Registra ``DejaVu`` (fpdf2) si hay ``DejaVuSans.ttf`` en assets o en el sistema."""
        _ensure_dejavu_font_files()
        assets_sans = _ROOT / "assets" / "fonts" / "DejaVuSans.ttf"
        if assets_sans.is_file():
            try:
                self.add_font(PDF_FONT_FAMILY, "", str(assets_sans))
                d = str(assets_sans.parent)
                b = os.path.join(d, "DejaVuSans-Bold.ttf")
                i = os.path.join(d, "DejaVuSans-Oblique.ttf")
                bi = os.path.join(d, "DejaVuSans-BoldOblique.ttf")
                self.add_font(PDF_FONT_FAMILY, "B", b if os.path.isfile(b) else str(assets_sans))
                self.add_font(PDF_FONT_FAMILY, "I", i if os.path.isfile(i) else str(assets_sans))
                self.add_font(PDF_FONT_FAMILY, "BI", bi if os.path.isfile(bi) else (b if os.path.isfile(b) else str(assets_sans)))
                self._uses_dejavu = True
                self._pdf_font_family = PDF_FONT_FAMILY
                return
            except Exception:
                pass
        reg, bd, it, bi = _resolver_ttf_unicode_sans()
        if not reg:
            self._pdf_font_family = "Helvetica"
            return
        try:
            self.add_font(PDF_FONT_FAMILY, "", reg)
            self.add_font(PDF_FONT_FAMILY, "B", bd or reg)
            self.add_font(PDF_FONT_FAMILY, "I", it or reg)
            self.add_font(PDF_FONT_FAMILY, "BI", bi or bd or reg)
            self._uses_dejavu = True
            self._pdf_font_family = PDF_FONT_FAMILY
        except Exception:
            self._uses_dejavu = False
            self._pdf_font_family = "Helvetica"

    def _texto_celda_seguro(self, txt: str) -> str:
        """Texto para ``cell``/``multi_cell``: prioriza ``limpiar_texto_para_pdf``; sin TTF, latin-1."""
        from modules.pdf_text import limpiar_texto_para_pdf

        t = limpiar_texto_para_pdf(txt)
        if not self._uses_dejavu:
            return t.encode("latin-1", errors="replace").decode("latin-1")
        return t

    def _set_font_text(self, style: str = "", size: float = 10) -> None:
        if self._uses_dejavu:
            self.set_font(self._pdf_font_family, style, size)
        else:
            self.set_font("Helvetica", style, size)

    def _pdf_unicode_clean(self, s: str) -> str:
        from modules.pdf_text import finalize_pdf_string, latex_raw_preprocess

        u = self._uses_dejavu
        return finalize_pdf_string(latex_raw_preprocess(s or "", uses_unicode_font=u), uses_unicode_font=u)

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
        self._set_font_text("", 9)
        self.set_text_color(55, 65, 80)
        self.cell(wc, 4, self._pdf_unicode_clean(self._banner_titulo_centro), align="C", ln=1)
        self._set_font_text("B", 16)
        self.set_text_color(15, 23, 42)
        if self._quiz_nota is not None:
            self.cell(wc, 9, f"{self._quiz_nota} / 20", align="C", ln=1)
        else:
            alt = (self._quiz_banner_alt or "").strip() or "Registro de actividad"
            self._set_font_text("B", 11)
            self.cell(wc, 9, self._pdf_unicode_clean(alt[:120]), align="C", ln=1)
        if self._quiz_aprobado:
            self._set_font_text("B", 8)
            if "No" in self._quiz_aprobado:
                self.set_text_color(185, 28, 28)
            else:
                self.set_text_color(22, 120, 60)
            self.cell(wc, 5, self._pdf_unicode_clean(self._quiz_aprobado), align="C", ln=1)
        self.set_text_color(0, 0, 0)

        der_txt = "Estudiante:\n"
        der_txt += self._quiz_nombre.strip() if self._quiz_nombre.strip() else "-"
        if self._quiz_fecha.strip():
            der_txt += "\n\nFecha:\n" + self._quiz_fecha.strip()
        if self._quiz_tipo.strip():
            der_txt += "\n\nActividad:\n" + self._quiz_tipo.strip()
        self.set_xy(xr, y0 + 1.0)
        self._set_font_text("B", 8)
        self.set_text_color(30, 41, 59)
        self.multi_cell(wr, 3.8, self._pdf_unicode_clean(der_txt), align="L")
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
        self._set_font_text("B", 14)
        self.set_xy(0, y_logo + 1.5)
        self.cell(0, 10, self._pdf_unicode_clean(self.titulo_reporte), ln=1, align="C")
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
        self._set_font_text("I", 8)
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
            self._set_font_text("I", 8)
            self.set_text_color(*self._COLOR_PIE_GRIS)
            self.cell(0, 5, self._texto_celda_seguro(self._TAGLINE_PIE_UNICODE), align="C", ln=1)

    def output(self, name: str = "", dest: str = "") -> str | bytes | bytearray:
        try:
            # Compat PyFPDF ``dest='S'``; fpdf2 devuelve ``bytearray`` con ``output()`` sin ruta.
            if dest == "S" or name == "S":
                return super().output()
            if name:
                return super().output(name)
            return super().output()
        finally:
            for p in (self._tmp_logo_header, self._tmp_tagline_png):
                if p and os.path.isfile(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass
            self._tmp_logo_header = None
            self._tmp_tagline_png = None
