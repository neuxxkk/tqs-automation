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

    # --- Header / Project Info ---
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, "MEMÓRIA DE CÁLCULO ESTRUTURAL: BEIRAL EM BALANÇO", 1, 1, "C", fill=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 8, "PROJETO:", 1, 0, "L", fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f" {entrada.nome_projeto}", 1, 1, "L")
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 8, "ELEMENTO:", 1, 0, "L", fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f" Beiral de {entrada.largura_cm:.0f} cm (Espessura: {entrada.espessura_cm:.0f} cm)", 1, 1, "L")
    pdf.ln(10)

    # --- Sketch Area ---
    y_sketch = pdf.get_y()
    pdf.set_draw_color(180, 180, 180)
    pdf.rect(10, y_sketch, 85, 65) # Box for the sketch
    
    bx = 20
    by = y_sketch + 15
    pdf.set_draw_color(0, 0, 0)
    
    # Support
    pdf.set_line_width(0.5)
    pdf.line(bx, by, bx, by + 40)
    pdf.set_line_width(0.2)
    for i in range(0, 40, 8):
        pdf.line(bx - 3, by + i + 3, bx, by + i)

    # Slab
    w_laje = 55
    h_laje = 8
    pdf.set_line_width(0.5)
    pdf.rect(bx, by + 15, w_laje, h_laje)

    # q load
    pdf.set_line_width(0.3)
    y_q = by + 5
    pdf.line(bx, y_q, bx + w_laje, y_q)
    pdf.set_font("Arial", "B", 8)
    pdf.text(bx - 4, y_q, "q")
    for dx in range(0, w_laje + 1, 11):
        pdf.line(bx + dx, y_q, bx + dx, by + 15)
        pdf.line(bx + dx, by + 15, bx + dx - 1, by + 13.5)
        pdf.line(bx + dx, by + 15, bx + dx + 1, by + 13.5)

    # P load
    if resultado.possui_carga_concentrada:
        pdf.set_line_width(0.5)
        pdf.set_draw_color(200, 0, 0) # Subtle red for P to match engineering standards
        x_p = bx + w_laje
        y_p_start = by - 5
        pdf.line(x_p, y_p_start, x_p, by + 15)
        pdf.line(x_p, by + 15, x_p - 2, by + 12)
        pdf.line(x_p, by + 15, x_p + 2, by + 12)
        pdf.text(x_p + 2, y_p_start + 3, "P")
        pdf.set_draw_color(0, 0, 0)

    # Dimensions on sketch
    pdf.set_font("Arial", "", 8)
    pdf.text(bx + w_laje / 2 - 5, by + 30, f"{resultado.largura_m:.2f} m")
    pdf.text(bx + w_laje + 5, by + 15 + h_laje / 2 + 1, f"{entrada.espessura_cm:.0f} cm")

    # --- Calculations Area ---
    x_calc = 105
    pdf.set_xy(x_calc, y_sketch)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "1. CARGAS DISTRIBUIDAS (q)", 0, 1, "L")
    pdf.set_font("Arial", "", 9)
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 5, f"- Carga Permanente: {entrada.carga_permanente_tf_m2:.3f} tf/m²", 0, 1, "L")
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 5, f"- Carga Acidental: {entrada.carga_acidental_tf_m2:.3f} tf/m²", 0, 1, "L")
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 5, f"- Peso Próprio: 2.5 × {resultado.espessura_m:.2f} = {resultado.peso_proprio_laje_tf_m2:.3f} tf/m²", 0, 1, "L")
    pdf.set_font("Arial", "B", 9)
    pdf.set_x(x_calc + 5)
    pdf.cell(0, 7, f"TOTAL q = {resultado.carga_total_q_tf_m2:.3f} tf/m²", 0, 1, "L")
    pdf.ln(2)

    pdf.set_font("Arial", "B", 10)
    pdf.set_x(x_calc)
    pdf.cell(0, 6, "2. CARGAS CONCENTRADAS (P)", 0, 1, "L")
    pdf.set_font("Arial", "", 9)
    if not resultado.possui_carga_concentrada:
        pdf.set_x(x_calc + 5)
        pdf.cell(0, 5, "- Nenhuma carga concentrada", 0, 1, "L")
    else:
        if entrada.possui_nervura_borda:
            pdf.set_x(x_calc + 5)
            pdf.cell(0, 5, f"- Nervura ({entrada.espessura_nervura_cm:.0f}×{entrada.altura_nervura_cm:.0f}): {resultado.peso_proprio_nervura_tf_m:.3f} tf/m", 0, 1, "L")
        if entrada.possui_guarda_corpo:
            pdf.set_x(x_calc + 5)
            pdf.cell(0, 5, f"- Alvenaria ({entrada.espessura_alvenaria_cm:.0f}×{entrada.altura_alvenaria_cm:.0f}): {resultado.carga_alvenaria_tf_m:.3f} tf/m", 0, 1, "L")
        pdf.set_font("Arial", "B", 9)
        pdf.set_x(x_calc + 5)
        pdf.cell(0, 7, f"TOTAL P = {resultado.carga_total_p_tf_m:.3f} tf/m", 0, 1, "L")

    # --- Results ---
    pdf.set_xy(10, y_sketch + 75)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, "3. DETERMINACAO DO MOMENTO SOLICITANTE", "T", 1, "L")
    
    pdf.set_font("Arial", "", 10)
    formula_text = f"M = (q × L² ÷ 2) + (P × L)"
    pdf.cell(0, 6, f"Fórmula: {formula_text}", 0, 1, "L")
    
    calc_text = f"M = ({resultado.carga_total_q_tf_m2:.3f} × {resultado.largura_m:.2f}² ÷ 2)"
    if resultado.possui_carga_concentrada:
        calc_text += f" + ({resultado.carga_total_p_tf_m:.3f} × {resultado.largura_m:.2f})"
    
    pdf.set_font("Courier", "", 9)
    pdf.cell(10)
    pdf.cell(0, 6, f"{calc_text}", 0, 1, "L")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, f"M = {resultado.momento_total_tf_m:.4f} tf.m", 0, 1, "L")
    pdf.ln(2)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, "4. MAJORAÇÃO (NBR 6118 / TQS)", "T", 1, "L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Fator y_f = 1.95 - 0.05 × {entrada.espessura_cm:.0f} = {resultado.majorador:.2f}", 0, 1, "L")
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(0, 10, f" Msk = M × y_f = {resultado.msk_tf_m:.3f} tf.m", 1, 1, "L", fill=True)

    if entrada.armacao_minima_bitola_mm > 0:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, "5. ARMAÇÃO MÍNIMA ADOTADA", "T", 1, "L")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, f"Bitola: ø {entrada.armacao_minima_bitola_mm:.1f} mm  |  Espaçamento: {entrada.armacao_minima_espacamento_cm:.1f} cm", 0, 1, "L")

    # --- Footer ---
    pdf.set_y(-25)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Relatorio gerado automaticamente pelo Sistema de Automacao TQS", 0, 0, "C")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        pdf_bytes = tmp.read()

    os.remove(tmp.name)
    return pdf_bytes
