from __future__ import annotations

import html
import sys
from pathlib import Path

import streamlit as st

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from beiral.core import (
    EntradaBeiral,
    PESO_ESPECIFICO_ALVENARIA_TF_M3,
    ResultadoBeiral,
    calcular_beiral,
    sanitize_filename_component,
    validar_entrada,
)
from beiral.draw import draw_beiral_svg_from_result
from beiral.pdf import gerar_pdf_relatorio, pdf_disponivel
from ui import inject_formula_theme, render_page_header, render_sidebar_brand


DEFAULT_PROJECT_NAME = "16a Laje - ANIMA MAJOR"


def _render_card(title: str, kicker: str, body_html: str) -> None:
    st.markdown(
        f"""
        <div class="formula-card">
            <span class="formula-kicker">{html.escape(kicker)}</span>
            <h3>{html.escape(title)}</h3>
            {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_list_card(title: str, kicker: str, items: list[str]) -> None:
    list_html = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    _render_card(title, kicker, f"<ul>{list_html}</ul>")


def _build_sidebar_inputs() -> EntradaBeiral:
    render_sidebar_brand(
        tool_name="Calculo de Beiral",
        description="Ferramenta de memoria estrutural para balancos com cargas distribuidas e de borda.",
    )

    st.sidebar.subheader("Projeto")
    with st.sidebar.form("dados_projeto_form"):
        nome_projeto = st.text_input("Nome do projeto / laje", value=DEFAULT_PROJECT_NAME)
        pavimento = st.text_input("Pavimento", value="")
        elemento = st.text_input("Elemento", value="")
        st.form_submit_button("Aplicar dados do projeto")

    st.sidebar.subheader("Geometria")
    espessura_cm = st.sidebar.number_input(
        "Espessura do beiral (cm)",
        min_value=1.0,
        value=14.0,
        step=1.0,
    )
    largura_cm = st.sidebar.number_input(
        "Largura do balanco (cm)",
        min_value=1.0,
        value=110.0,
        step=1.0,
    )

    st.sidebar.subheader("Cargas de superficie")
    carga_permanente = st.sidebar.number_input(
        "Carga permanente - G2 (tf/m2)",
        min_value=0.0,
        value=0.3,
        step=0.05,
        format="%.3f",
    )
    carga_acidental = st.sidebar.number_input(
        "Carga acidental - Q (tf/m2)",
        min_value=0.0,
        value=0.2,
        step=0.05,
        format="%.3f",
    )

    st.sidebar.subheader("Elementos de borda")
    possui_nervura_borda = st.sidebar.checkbox("Possui nervura de borda", value=True)
    if possui_nervura_borda:
        col_ne, col_na = st.sidebar.columns(2)
        espessura_nervura_cm = col_ne.number_input(
            "Largura (cm)",
            min_value=1.0,
            value=14.0,
            step=1.0,
            key="nervura_largura",
        )
        altura_nervura_cm = col_na.number_input(
            "Altura (cm)",
            min_value=1.0,
            value=70.0,
            step=1.0,
            key="nervura_altura",
        )
    else:
        espessura_nervura_cm = 0.0
        altura_nervura_cm = 0.0

    possui_guarda_corpo = st.sidebar.checkbox("Possui alvenaria / guarda-corpo", value=False)
    if possui_guarda_corpo:
        col_ae, col_aa = st.sidebar.columns(2)
        espessura_alvenaria_cm = col_ae.number_input(
            "Espessura (cm)",
            min_value=0.0,
            value=12.0,
            step=1.0,
            key="alvenaria_espessura",
        )
        altura_alvenaria_cm = col_aa.number_input(
            "Altura (cm)",
            min_value=0.0,
            value=110.0,
            step=1.0,
            key="alvenaria_altura",
        )
        carga_alvenaria = (
            (espessura_alvenaria_cm / 100.0)
            * (altura_alvenaria_cm / 100.0)
            * PESO_ESPECIFICO_ALVENARIA_TF_M3
        )
        st.sidebar.caption(f"Carga linear estimada da alvenaria: {carga_alvenaria:.3f} tf/m")
    else:
        espessura_alvenaria_cm = 0.0
        altura_alvenaria_cm = 0.0

    st.sidebar.subheader("Detalhamento minimo")
    col_bb, col_be = st.sidebar.columns(2)
    armacao_minima_bitola_mm = col_bb.number_input(
        "Bitola (mm)",
        min_value=0.0,
        value=8.0,
        step=0.5,
        format="%.1f",
    )
    armacao_minima_espacamento_cm = col_be.number_input(
        "Espacamento (cm)",
        min_value=0.0,
        value=14.0,
        step=1.0,
        format="%.1f",
    )

    return EntradaBeiral(
        nome_projeto=nome_projeto,
        espessura_cm=espessura_cm,
        largura_cm=largura_cm,
        carga_permanente_tf_m2=carga_permanente,
        carga_acidental_tf_m2=carga_acidental,
        possui_nervura_borda=possui_nervura_borda,
        pavimento=pavimento,
        elemento=elemento,
        espessura_nervura_cm=espessura_nervura_cm,
        altura_nervura_cm=altura_nervura_cm,
        possui_guarda_corpo=possui_guarda_corpo,
        espessura_alvenaria_cm=espessura_alvenaria_cm,
        altura_alvenaria_cm=altura_alvenaria_cm,
        armacao_minima_bitola_mm=armacao_minima_bitola_mm,
        armacao_minima_espacamento_cm=armacao_minima_espacamento_cm,
    )


def _render_formula_card(entrada: EntradaBeiral, resultado: ResultadoBeiral) -> None:
    formula = (
        f"M = ({resultado.carga_total_q_tf_m2:.3f} x {resultado.largura_m:.2f}^2 / 2)"
    )
    if resultado.possui_carga_concentrada:
        formula += f" + ({resultado.carga_total_p_tf_m:.3f} x {resultado.largura_m:.2f})"

    _render_card(
        "Equacoes de momento",
        "Memoria de calculo",
        (
            "<div class='formula-code'>"
            f"{html.escape(formula)} = {resultado.momento_total_tf_m:.4f} tf.m<br>"
            f"gamma_f = 1.95 - 0.05 x {entrada.espessura_cm:.0f} = {resultado.majorador:.2f}<br>"
            f"<strong>Msk = M x gamma_f = {resultado.msk_tf_m:.3f} tf.m</strong>"
            "</div>"
        ),
    )


def _render_resultados(entrada: EntradaBeiral, resultado: ResultadoBeiral) -> None:
    st.markdown(
        f"""
        <div class="formula-note">
            <strong>Momento de calculo pronto.</strong>
            O balanco de {entrada.largura_cm:.0f} cm com espessura de {entrada.espessura_cm:.0f} cm
            resulta em <span class="formula-mono">Msk = {resultado.msk_tf_m:.3f} tf.m</span>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("q total (tf/m2)", f"{resultado.carga_total_q_tf_m2:.3f}")
    col2.metric("P total (tf/m)", f"{resultado.carga_total_p_tf_m:.3f}")
    col3.metric("Momento (tf.m)", f"{resultado.momento_total_tf_m:.3f}")
    col4.metric("Msk (tf.m)", f"{resultado.msk_tf_m:.3f}")

    col_preview, col_memoria = st.columns([1.15, 1], gap="large")

    with col_preview:
        _render_card(
            "Vista do balanco",
            "Esquema tecnico",
            draw_beiral_svg_from_result(
                entrada.espessura_cm,
                entrada.largura_cm,
                resultado,
            ),
        )

    with col_memoria:
        _render_list_card(
            "Cargas distribuidas (q)",
            "Carregamento",
            [
                f"Permanente: {entrada.carga_permanente_tf_m2:.3f} tf/m2",
                f"Acidental: {entrada.carga_acidental_tf_m2:.3f} tf/m2",
                (
                    "Peso proprio (G1): "
                    f"2.5 x {resultado.espessura_m:.2f} = {resultado.peso_proprio_laje_tf_m2:.3f} tf/m2"
                ),
                f"Total q = {resultado.carga_total_q_tf_m2:.3f} tf/m2",
            ],
        )

    col_p, col_formula = st.columns(2, gap="large")
    carga_p_items: list[str] = []
    if entrada.possui_nervura_borda:
        carga_p_items.append(
            f"Nervura ({entrada.espessura_nervura_cm:.0f} x {entrada.altura_nervura_cm:.0f} cm)"
        )
        carga_p_items.append(
            "Peso proprio = "
            f"{entrada.espessura_nervura_cm / 100:.2f} x "
            f"{entrada.altura_nervura_cm / 100:.2f} x 2.5 = "
            f"{resultado.peso_proprio_nervura_tf_m:.3f} tf/m"
        )
    if entrada.possui_guarda_corpo:
        carga_p_items.append(
            "Alvenaria = "
            f"{entrada.espessura_alvenaria_cm / 100:.2f} x "
            f"{entrada.altura_alvenaria_cm / 100:.2f} x "
            f"{PESO_ESPECIFICO_ALVENARIA_TF_M3:.1f} = "
            f"{resultado.carga_alvenaria_tf_m:.3f} tf/m"
        )
    if resultado.possui_carga_concentrada:
        carga_p_items.append(f"Total P = {resultado.carga_total_p_tf_m:.3f} tf/m")
    else:
        carga_p_items.append("Sem carga concentrada ativa")

    with col_p:
        _render_list_card("Cargas na borda (P)", "Carregamento linear", carga_p_items)

    with col_formula:
        _render_formula_card(entrada, resultado)

    if entrada.armacao_minima_bitola_mm > 0:
        _render_card(
            "Armadura minima adotada",
            "Detalhamento",
            (
                "<p>"
                f"Bitola <span class='formula-mono'>o {entrada.armacao_minima_bitola_mm:.1f} mm</span> "
                f"com espacamento <span class='formula-mono'>c/{entrada.armacao_minima_espacamento_cm:.1f} cm</span>."
                "</p>"
            ),
        )

    if pdf_disponivel():
        pdf_bytes = gerar_pdf_relatorio(entrada, resultado)
        file_name = sanitize_filename_component(entrada.nome_projeto)
        st.download_button(
            label="Baixar PDF do relatorio",
            data=pdf_bytes,
            file_name=f"Calculo_Beiral_{file_name}.pdf",
            mime="application/pdf",
            use_container_width=False,
        )
    else:
        st.warning(
            "A biblioteca 'fpdf' nao esta instalada. Para habilitar a exportacao do PDF, execute: pip install fpdf"
        )


def main() -> None:
    st.set_page_config(page_title="Calculo de Beiral", layout="wide")
    inject_formula_theme()

    render_page_header(
        kicker="Engenharia Estrutural",
        title="Calculo de Beiral",
        description=(
            "Analise de cargas distribuidas e lineares para balancos, com memorial visual e "
            "exportacao de relatorio tecnico."
        ),
    )

    with st.sidebar:
        entrada = _build_sidebar_inputs()

    erros = validar_entrada(entrada)
    if erros:
        for erro in erros:
            st.error(erro)
        return

    resultado = calcular_beiral(entrada)
    _render_resultados(entrada, resultado)


if __name__ == "__main__":
    main()
