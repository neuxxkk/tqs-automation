from __future__ import annotations

import html
import base64
import sys
from pathlib import Path
from typing import Any

import streamlit as st

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from escada.calculos import calcular_escada
from escada.defaults import entrada_padrao
from escada.domain import (
    EntradaEscada,
    ResultadoEscada,
    formatar_pavimento,
    sanitize_filename_component,
    validar_entrada,
)
from escada.memoria import gerar_pdf_relatorio, pdf_disponivel
from ui import inject_formula_theme, render_page_header, render_sidebar_brand


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


def _render_cargas_card(entrada: EntradaEscada, resultado: ResultadoEscada) -> None:
    _render_card(
        "Cargas distribuidas (Q)",
        "Carregamento",
        f"""
        <div class="formula-load-grid">
            <div class="formula-load-row">
                <div>
                    <strong>Patamar</strong>
                    <span>CP {entrada.carga_permanente_patamar_tf_m2:.3f} + CA {entrada.carga_acidental_patamar_tf_m2:.3f} + PP {resultado.peso_proprio_patamar_tf_m2:.3f}</span>
                </div>
                <strong>Q = {resultado.carga_total_patamar_tf_m2:.3f} tf/m2</strong>
            </div>
            <div class="formula-load-row">
                <div>
                    <strong>Escada</strong>
                    <span>CP {entrada.carga_permanente_escada_tf_m2:.3f} + CA {entrada.carga_acidental_escada_tf_m2:.3f} + PP {resultado.peso_proprio_escada_tf_m2:.3f}</span>
                </div>
                <strong>Q = {resultado.carga_total_escada_tf_m2:.3f} tf/m2</strong>
            </div>
        </div>
        """,
    )


def _imagem_card_html(imagem: Any | None) -> str:
    if not imagem:
        return "<p>Nenhuma imagem enviada.</p>"

    mime_type = getattr(imagem, "type", "image/png")
    encoded = base64.b64encode(imagem.getvalue()).decode("ascii")
    return (
        "<div class='formula-upload-preview'>"
        f"<img src='data:{html.escape(mime_type)};base64,{encoded}' alt='Imagem da escada'>"
        "</div>"
    )


def _build_sidebar_inputs() -> tuple[EntradaEscada, Any | None]:
    padrao = entrada_padrao()

    render_sidebar_brand(
        tool_name="Calculo de Escadas",
        description="Ferramenta de memoria estrutural para cargas distribuidas de patamares e escadas.",
    )

    st.sidebar.subheader("Projeto")
    nome_projeto = st.sidebar.text_input("Nome do projeto / escada", value=padrao.nome_projeto)
    col_li, col_lf = st.sidebar.columns(2)
    laje_inicial = col_li.number_input(
        "Da laje",
        min_value=0,
        value=padrao.laje_inicial,
        step=1,
    )
    laje_final_minima = int(laje_inicial) + 1
    laje_final_default = max(padrao.laje_final, laje_final_minima)
    laje_final = col_lf.number_input(
        "Ate a laje",
        min_value=laje_final_minima,
        value=laje_final_default,
        step=1,
    )
    st.sidebar.caption(f"Pavimento: {formatar_pavimento(int(laje_inicial), int(laje_final))}")
    imagem = st.sidebar.file_uploader(
        "Imagem da escada",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
    )

    st.sidebar.subheader("Geometria")
    col_ep, col_ee = st.sidebar.columns(2)
    espessura_patamar_cm = col_ep.number_input(
        "Patamar h (cm)",
        min_value=1.0,
        value=padrao.espessura_patamar_cm,
        step=1.0,
        format="%.1f",
    )
    espessura_escada_cm = col_ee.number_input(
        "Escada h (cm)",
        min_value=1.0,
        value=padrao.espessura_escada_cm,
        step=1.0,
        format="%.1f",
    )

    st.sidebar.subheader("Cargas do patamar")
    carga_permanente_patamar = st.sidebar.number_input(
        "CP geral do patamar (tf/m2)",
        min_value=0.0,
        value=padrao.carga_permanente_patamar_tf_m2,
        step=0.01,
        format="%.3f",
    )
    carga_acidental_patamar = st.sidebar.number_input(
        "CA geral do patamar (tf/m2)",
        min_value=0.0,
        value=padrao.carga_acidental_patamar_tf_m2,
        step=0.01,
        format="%.3f",
    )

    st.sidebar.subheader("Cargas da escada")
    carga_permanente_escada = st.sidebar.number_input(
        "CP geral da escada (tf/m2)",
        min_value=0.0,
        value=padrao.carga_permanente_escada_tf_m2,
        step=0.01,
        format="%.3f",
    )
    carga_acidental_escada = st.sidebar.number_input(
        "CA geral da escada (tf/m2)",
        min_value=0.0,
        value=padrao.carga_acidental_escada_tf_m2,
        step=0.01,
        format="%.3f",
    )

    entrada = EntradaEscada(
        nome_projeto=nome_projeto,
        laje_inicial=int(laje_inicial),
        laje_final=int(laje_final),
        espessura_patamar_cm=espessura_patamar_cm,
        espessura_escada_cm=espessura_escada_cm,
        carga_permanente_patamar_tf_m2=carga_permanente_patamar,
        carga_acidental_patamar_tf_m2=carga_acidental_patamar,
        carga_permanente_escada_tf_m2=carga_permanente_escada,
        carga_acidental_escada_tf_m2=carga_acidental_escada,
    )
    return entrada, imagem


def _render_formula_card(entrada: EntradaEscada, resultado: ResultadoEscada) -> None:
    _render_card(
        "Equacoes de carregamento",
        "Memoria de calculo",
        (
            "<div class='formula-code'>"
            f"Q_patamar = {entrada.carga_permanente_patamar_tf_m2:.3f} + "
            f"{entrada.carga_acidental_patamar_tf_m2:.3f} + "
            f"{resultado.peso_proprio_patamar_tf_m2:.3f} = "
            f"{resultado.carga_total_patamar_tf_m2:.3f} tf/m2<br>"
            f"Q_escada = {entrada.carga_permanente_escada_tf_m2:.3f} + "
            f"{entrada.carga_acidental_escada_tf_m2:.3f} + "
            f"{resultado.peso_proprio_escada_tf_m2:.3f} = "
            f"{resultado.carga_total_escada_tf_m2:.3f} tf/m2"
            "</div>"
        ),
    )


def _render_resultados(
    entrada: EntradaEscada,
    resultado: ResultadoEscada,
    imagem: Any | None,
) -> None:
    st.markdown(
        f"""
        <div class="formula-note">
            <strong>Carregamentos distribuidos prontos.</strong>
            O patamar resulta em <span class="formula-mono">Q = {resultado.carga_total_patamar_tf_m2:.3f} tf/m2</span>
            e a escada em <span class="formula-mono">Q = {resultado.carga_total_escada_tf_m2:.3f} tf/m2</span>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("PP patamar (tf/m2)", f"{resultado.peso_proprio_patamar_tf_m2:.3f}")
    col2.metric("Q patamar (tf/m2)", f"{resultado.carga_total_patamar_tf_m2:.3f}")
    col3.metric("PP escada (tf/m2)", f"{resultado.peso_proprio_escada_tf_m2:.3f}")
    col4.metric("Q escada (tf/m2)", f"{resultado.carga_total_escada_tf_m2:.3f}")

    col_preview, col_memoria = st.columns([1.15, 1], gap="large")

    with col_preview:
        _render_card(
            "Imagem da escada",
            "Referencia do usuario",
            _imagem_card_html(imagem),
        )

    with col_memoria:
        _render_cargas_card(entrada, resultado)

    _render_formula_card(entrada, resultado)

    if pdf_disponivel():
        imagem_bytes = imagem.getvalue() if imagem else None
        imagem_mime_type = getattr(imagem, "type", None) if imagem else None
        pdf_bytes = gerar_pdf_relatorio(entrada, resultado, imagem_bytes, imagem_mime_type)
        file_name = sanitize_filename_component(entrada.nome_projeto)
        st.download_button(
            label="Baixar PDF do relatorio",
            data=pdf_bytes,
            file_name=f"Calculo_Escada_{file_name}.pdf",
            mime="application/pdf",
            use_container_width=False,
        )
    else:
        st.warning(
            "A biblioteca 'fpdf' nao esta instalada. Para habilitar a exportacao do PDF, execute: pip install fpdf"
        )


def main() -> None:
    st.set_page_config(page_title="Calculo de Escadas", layout="wide")
    inject_formula_theme()

    render_page_header(
        kicker="Engenharia Estrutural",
        title="Calculo de Escadas",
        description=(
            "Analise de cargas distribuidas para patamares e escadas, com imagem de referencia "
            "fornecida pelo usuario e exportacao de relatorio tecnico."
        ),
    )

    with st.sidebar:
        entrada, imagem = _build_sidebar_inputs()

    erros = validar_entrada(entrada)
    if erros:
        for erro in erros:
            st.error(erro)
        return

    resultado = calcular_escada(entrada)
    _render_resultados(entrada, resultado, imagem)


if __name__ == "__main__":
    main()
