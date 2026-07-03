from __future__ import annotations

import os
import tempfile

from .domain import EntradaEscada, ResultadoEscada, formatar_pavimento

try:
    from fpdf import FPDF

    HAS_FPDF = True
except ImportError:
    FPDF = None
    HAS_FPDF = False


def pdf_disponivel() -> bool:
    return HAS_FPDF


def _image_suffix(mime_type: str | None) -> str:
    if mime_type == "image/png":
        return ".png"
    if mime_type in {"image/jpeg", "image/jpg"}:
        return ".jpg"
    return ".img"


def _adicionar_imagem(pdf: FPDF, imagem_bytes: bytes | None, mime_type: str | None, x: float, y: float) -> None:
    if not imagem_bytes:
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(110, 110, 110)
        pdf.set_xy(x + 6, y + 29)
        pdf.cell(73, 6, "Imagem da escada nao informada", 0, 0, "C")
        pdf.set_text_color(0, 0, 0)
        return

    suffix = _image_suffix(mime_type)
    if suffix == ".img":
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(110, 110, 110)
        pdf.set_xy(x + 6, y + 29)
        pdf.cell(73, 6, "Formato de imagem nao suportado no PDF", 0, 0, "C")
        pdf.set_text_color(0, 0, 0)
        return

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_img:
            tmp_img.write(imagem_bytes)
            tmp_path = tmp_img.name
        pdf.image(tmp_path, x=x + 3, y=y + 3, w=79, h=59)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def gerar_pdf_relatorio(
    entrada: EntradaEscada,
    resultado: ResultadoEscada,
    imagem_bytes: bytes | None = None,
    imagem_mime_type: str | None = None,
) -> bytes:
    if not HAS_FPDF:
        raise RuntimeError("A biblioteca fpdf nao esta instalada.")

    pdf = FPDF()
    pdf.set_auto_page_break(False, margin=0)
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, "MEMORIA DE CALCULO ESTRUTURAL: ESCADA", 1, 1, "C", fill=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 8, "PROJETO:", 1, 0, "L", fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f" {entrada.nome_projeto}", 1, 1, "L")

    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 8, "PAVIMENTO:", 1, 0, "L", fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f" {formatar_pavimento(entrada.laje_inicial, entrada.laje_final)}", 1, 1, "L")
    pdf.ln(10)

    y_imagem = pdf.get_y()
    pdf.set_draw_color(180, 180, 180)
    pdf.rect(10, y_imagem, 85, 65)
    _adicionar_imagem(pdf, imagem_bytes, imagem_mime_type, 10, y_imagem)

    x_calc = 105
    pdf.set_xy(x_calc, y_imagem)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "1. CARGAS DISTRIBUIDAS (Q)", 0, 1, "L")
    pdf.ln(1)

    pdf.set_font("Arial", "B", 9)
    pdf.set_x(x_calc)
    pdf.cell(0, 5, "PATAMAR", 0, 1, "L")
    pdf.set_font("Arial", "", 9)
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 5, f"- CP geral: {entrada.carga_permanente_patamar_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 5, f"- CA geral: {entrada.carga_acidental_patamar_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 5, f"- Peso proprio: 2.5 x {resultado.espessura_patamar_m:.2f} = {resultado.peso_proprio_patamar_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.set_font("Arial", "B", 9)
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 7, f"TOTAL Q patamar = {resultado.carga_total_patamar_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.ln(3)

    pdf.set_font("Arial", "B", 9)
    pdf.set_x(x_calc)
    pdf.cell(0, 5, "ESCADA", 0, 1, "L")
    pdf.set_font("Arial", "", 9)
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 5, f"- CP geral: {entrada.carga_permanente_escada_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 5, f"- CA geral: {entrada.carga_acidental_escada_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 5, f"- Peso proprio: 2.5 x {resultado.espessura_escada_m:.2f} = {resultado.peso_proprio_escada_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.set_font("Arial", "B", 9)
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 7, f"TOTAL Q escada = {resultado.carga_total_escada_tf_m2:.3f} tf/m2", 0, 1, "L")

    pdf.set_xy(10, y_imagem + 75)
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(0, 10, f" Q patamar = {resultado.carga_total_patamar_tf_m2:.3f} tf/m2  |  Q escada = {resultado.carga_total_escada_tf_m2:.3f} tf/m2", 1, 1, "L", fill=True)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(32, 9, "As adotado:", 1, 0, "L", fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 9, "", 1, 1, "L")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        pdf_bytes = tmp.read()

    os.remove(tmp.name)
    return pdf_bytes


def gerar_memoria_pdf(
    entrada: EntradaEscada,
    resultado: ResultadoEscada,
    imagem_bytes: bytes | None = None,
    imagem_mime_type: str | None = None,
) -> bytes:
    return gerar_pdf_relatorio(entrada, resultado, imagem_bytes, imagem_mime_type)
