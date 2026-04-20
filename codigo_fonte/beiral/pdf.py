from __future__ import annotations

import os
import tempfile

from .core import EntradaBeiral, ResultadoBeiral

try:
    from fpdf import FPDF

    HAS_FPDF = True
except ImportError:
    FPDF = None
    HAS_FPDF = False


def pdf_disponivel() -> bool:
    return HAS_FPDF


def gerar_pdf_relatorio(entrada: EntradaBeiral, resultado: ResultadoBeiral) -> bytes:
    if not HAS_FPDF:
        raise RuntimeError("A biblioteca fpdf nao esta instalada.")

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(150, 0, 0)
    pdf.cell(0, 10, f"# CALCULO DE BEIRAL : {entrada.nome_projeto}", 0, 1, "L")
    pdf.ln(2)

    pdf.set_text_color(0, 0, 100)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"> Beiral 1: secao de {entrada.largura_cm:.0f}cm", 0, 1, "L")
    pdf.set_text_color(0, 0, 0)

    y_inicio_colunas = pdf.get_y() + 5
    bx = 20
    by = y_inicio_colunas + 5

    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(bx, by, bx, by + 42)
    pdf.set_line_width(0.2)
    for i in range(0, 42, 8):
        pdf.line(bx - 4, by + i + 4, bx, by + i)

    w_laje = 60
    h_laje = 10
    pdf.set_line_width(0.5)
    pdf.rect(bx, by + 15, w_laje, h_laje)

    pdf.set_line_width(0.4)
    y_q = by + 5
    pdf.line(bx, y_q, bx + w_laje, y_q)
    pdf.set_font("Arial", "B", 10)
    pdf.text(bx - 5, y_q, "q")

    for dx in range(0, w_laje + 1, 12):
        pdf.line(bx + dx, y_q, bx + dx, by + 15)
        pdf.line(bx + dx, by + 15, bx + dx - 1.5, by + 13)
        pdf.line(bx + dx, by + 15, bx + dx + 1.5, by + 13)

    if resultado.possui_carga_concentrada:
        pdf.set_line_width(0.6)
        x_p = bx + w_laje
        y_p_start = by - 5
        pdf.line(x_p, y_p_start, x_p, by + 15)
        pdf.line(x_p, by + 15, x_p - 2.5, by + 12)
        pdf.line(x_p, by + 15, x_p + 2.5, by + 12)
        pdf.set_font("Arial", "B", 10)
        pdf.text(x_p + 2, y_p_start + 4, "P")

    pdf.set_line_width(0.2)
    y_cota_larg = by + 32
    pdf.line(bx, y_cota_larg, bx + w_laje, y_cota_larg)
    pdf.line(bx, y_cota_larg - 2, bx, y_cota_larg + 2)
    pdf.line(bx + w_laje, y_cota_larg - 2, bx + w_laje, y_cota_larg + 2)
    pdf.set_font("Arial", "", 10)
    pdf.text(bx + w_laje / 2 - 6, y_cota_larg + 5, f"{resultado.largura_m:.2f} m")

    x_cota_esp = bx + w_laje + 8
    pdf.line(x_cota_esp, by + 15, x_cota_esp, by + 15 + h_laje)
    pdf.line(x_cota_esp - 2, by + 15, x_cota_esp + 2, by + 15)
    pdf.line(x_cota_esp - 2, by + 15 + h_laje, x_cota_esp + 2, by + 15 + h_laje)
    pdf.text(x_cota_esp + 3, by + 15 + h_laje / 2 + 2, f"{entrada.espessura_cm:.0f} cm")

    x_text = 110
    pdf.set_xy(x_text, y_inicio_colunas)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, "* Cargas distribuidas (q)", 0, 1, "L")

    pdf.set_font("Arial", "", 11)
    pdf.set_x(x_text + 7)
    pdf.cell(0, 6, f"> Permanente: {entrada.carga_permanente_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.set_x(x_text + 7)
    pdf.cell(0, 6, f"> Acidental: {entrada.carga_acidental_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.set_x(x_text + 7)
    pdf.cell(
        0,
        6,
        f"> Peso proprio: 2.5 x {resultado.espessura_m:.2f} = {resultado.peso_proprio_laje_tf_m2:.3f} tf/m2",
        0,
        1,
        "L",
    )

    pdf.set_font("Arial", "B", 11)
    pdf.set_x(x_text + 10)
    pdf.cell(0, 6, f"E q = {resultado.carga_total_q_tf_m2:.3f} tf/m2", 0, 1, "L")
    pdf.ln(4)

    pdf.set_x(x_text)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, "* Carga concentrada (P)", 0, 1, "L")
    pdf.set_font("Arial", "", 11)

    if entrada.possui_nervura_borda:
        pdf.set_x(x_text + 7)
        pdf.cell(
            0,
            6,
            f"> Nervura N1 ({entrada.espessura_nervura_cm:.0f}x{entrada.altura_nervura_cm:.0f})",
            0,
            1,
            "L",
        )
        pdf.set_x(x_text + 7)
        pdf.cell(
            0,
            6,
            f"> Peso proprio = {entrada.espessura_nervura_cm / 100:.2f} x {entrada.altura_nervura_cm / 100:.2f} x 2.5 = {resultado.peso_proprio_nervura_tf_m:.3f} tf/m",
            0,
            1,
            "L",
        )

    if entrada.possui_guarda_corpo:
        pdf.set_x(x_text + 7)
        pdf.cell(
            0,
            6,
            f"> Alvenaria = {entrada.espessura_alvenaria_cm / 100:.2f} x {entrada.altura_alvenaria_cm / 100:.2f} x 1.3 = {resultado.carga_alvenaria_tf_m:.3f} tf/m",
            0,
            1,
            "L",
        )

    if not resultado.possui_carga_concentrada:
        pdf.set_x(x_text + 7)
        pdf.cell(0, 6, "> Nenhuma", 0, 1, "L")
    else:
        pdf.set_font("Arial", "B", 11)
        pdf.set_x(x_text + 10)
        pdf.cell(0, 6, f"E P = {resultado.carga_total_p_tf_m:.3f} tf/m", 0, 1, "L")

    y_atual = pdf.get_y()
    y_final = max(y_atual, by + 60) + 10
    pdf.set_xy(10, y_final)

    pdf.set_font("Arial", "B", 12)
    formula = f"({resultado.carga_total_q_tf_m2:.3f} x {resultado.largura_m:.2f} x {resultado.largura_m / 2:.2f})"
    if resultado.possui_carga_concentrada:
        formula += f" + ({resultado.carga_total_p_tf_m:.3f} x {resultado.largura_m:.2f})"

    pdf.cell(0, 8, f"> Momento:  {formula} = M", 0, 1, "L")
    pdf.set_x(40)
    pdf.cell(0, 8, f"M = {resultado.momento_total_tf_m:.3f} tf.m", 0, 1, "L")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "> MAJORACAO", 0, 1, "L")
    pdf.set_font("Arial", "", 12)
    pdf.cell(10)
    pdf.cell(0, 8, f"Y = 1.95 - 0.05 x {entrada.espessura_cm:.0f} = {resultado.majorador:.2f}", 0, 1, "L")
    pdf.ln(8)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(10)
    pdf.cell(
        0,
        10,
        f"Msk = {resultado.momento_total_tf_m:.3f} x {resultado.majorador:.2f}  =  {resultado.msk_tf_m:.2f} tf.m",
        0,
        1,
        "L",
    )

    if (
        entrada.armacao_minima_bitola_mm > 0
        and entrada.armacao_minima_espacamento_cm > 0
    ):
        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "> ARMACAO MINIMA", 0, 1, "L")
        pdf.set_font("Arial", "", 12)
        pdf.cell(
            0,
            8,
            f"Bitola {entrada.armacao_minima_bitola_mm:.1f} c/ {entrada.armacao_minima_espacamento_cm:.1f}",
            0,
            1,
            "L",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        pdf_bytes = tmp.read()

    os.remove(tmp.name)
    return pdf_bytes
