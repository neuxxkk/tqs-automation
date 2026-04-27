import html

import streamlit as st

from beiral.core import (
    EntradaBeiral,
    PESO_ESPECIFICO_ALVENARIA_TF_M3,
    ResultadoBeiral,
    calcular_beiral,
    sanitize_filename_component,
    validar_entrada,
)
from beiral.draw import draw_beiral_svg_from_result


DEFAULT_PROJECT_NAME = "16a Laje - ANIMA MAJOR"
SESSION_INPUT_KEY = "beiral_entrada"
SESSION_RESULT_KEY = "beiral_resultado"
THEME_CSS = """
<style>
    :root {
        --verde-principal:   #5a8a4a;
        --verde-hover:       #3b6d11;
        --verde-claro:       #eaf3de;
        --verde-texto:       #27500a;
        --cinza-900:         #1e1e1c;
        --cinza-800:         #2c2c2a;
        --cinza-600:         #6b6b6b;
        --cinza-300:         #b4b2a9;
        --cinza-100:         #f1efe8;
        --cinza-50:          #f8f7f4;
        --branco:            #ffffff;
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px 0 rgba(0, 0, 0, 0.04);
    }

    [data-testid="stAppViewContainer"] {
        background-color: var(--cinza-100);
        font-family: 'Segoe UI', Arial, sans-serif;
    }

    [data-testid="stAppViewBlockContainer"] {
        max-width: 1100px;
        padding-top: 2rem;
    }

    h1, h2, h3 {
        color: var(--cinza-800);
        font-family: 'Segoe UI Semibold', 'Segoe UI', Arial, sans-serif;
        font-weight: 600;
        letter-spacing: 0.01em;
    }

    [data-testid="stForm"] {
        background: var(--cinza-50);
        border: 1px solid var(--cinza-300);
        border-radius: 2px;
        box-shadow: var(--shadow);
        padding: 1.5rem;
    }

    [data-testid="stMetric"] {
        background: var(--cinza-50);
        border: 1px solid var(--cinza-300);
        border-radius: 2px;
        padding: 1rem;
        box-shadow: var(--shadow);
    }

    [data-testid="stMetricLabel"] {
        color: var(--cinza-600);
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        font-family: 'Segoe UI Semibold', 'Segoe UI', Arial, sans-serif;
    }

    [data-testid="stMetricValue"] {
        color: var(--verde-principal);
        font-weight: 700;
        font-family: 'Consolas', monospace;
    }

    .stButton > button,
    .stDownloadButton > button,
    button[kind="primaryFormSubmit"] {
        border-radius: 2px;
        border: 1px solid var(--verde-principal);
        background-color: var(--verde-principal);
        color: var(--branco);
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: background-color 0.15s;
        font-family: 'Segoe UI', Arial, sans-serif;
    }

    .stButton > button:hover {
        background-color: var(--verde-hover);
        border-color: var(--verde-hover);
    }

    .shell-container {
        background: var(--cinza-50);
        border: 1px solid var(--cinza-300);
        border-radius: 2px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
    }

    .kicker {
        color: var(--verde-principal);
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
        display: block;
        font-family: 'Segoe UI Semibold', 'Segoe UI', Arial, sans-serif;
    }

    .title-large {
        font-size: 1.75rem;
        margin-bottom: 0.5rem;
        color: var(--cinza-800);
        font-family: 'Segoe UI Semibold', 'Segoe UI', Arial, sans-serif;
    }

    .copy-text {
        color: var(--cinza-600);
        font-size: 0.95rem;
        line-height: 1.6;
    }

    .result-box {
        background: var(--verde-claro);
        border-left: 4px solid var(--verde-principal);
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 2px 2px 0;
    }

    .result-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--verde-texto);
        font-family: 'Consolas', monospace;
    }

    .code-block {
        font-family: 'Consolas', monospace;
        background: var(--cinza-100);
        padding: 0.75rem;
        border-radius: 2px;
        border: 1px solid var(--cinza-300);
        font-size: 0.85rem;
        color: var(--cinza-800);
    }
</style>
"""


def _inject_styles() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def _render_top_shell() -> None:
    st.markdown(
        """
        <div class="shell-container">
            <span class="kicker">Engenharia Estrutural</span>
            <h1 class="title-large">Memorial de Calculo: Beiral</h1>
            <p class="copy-text">
                Analise de esforços solicitantes, majoração normativa e verificação de geometria para beirais em balanço.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_section_intro(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="shell-container">
            <span class="kicker">Parametros de Entrada</span>
            <h3>{html.escape(title)}</h3>
            <p class="copy-text">{html.escape(copy)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_list_card(title: str, kicker: str, items: list[str]) -> None:
    list_html = "".join(f"<li style='margin-bottom: 0.25rem;'>{html.escape(item)}</li>" for item in items)
    st.markdown(
        f"""
        <div class="shell-container">
            <span class="kicker">{html.escape(kicker)}</span>
            <h4 style="margin-top:0; margin-bottom:0.75rem;">{html.escape(title)}</h4>
            <ul style="margin: 0; padding-left: 1.2rem; color: var(--ink-soft); font-size: 0.9rem;">{list_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_formula_card(entrada: EntradaBeiral, resultado: ResultadoBeiral) -> None:
    formula_m = (
        f"M = ({resultado.carga_total_q_tf_m2:.3f} × {resultado.largura_m:.2f}² ÷ 2)"
    )
    if resultado.possui_carga_concentrada:
        formula_m += (
            f" + ({resultado.carga_total_p_tf_m:.3f} × {resultado.largura_m:.2f})"
        )

    st.markdown(
        f"""
        <div class="shell-container">
            <span class="kicker">Memoria de Calculo</span>
            <h4 style="margin-top:0;">Equações de Momento</h4>
            <div class="code-block">
                {html.escape(formula_m)} = {resultado.momento_total_tf_m:.4f} tf.m<br>
                γ_f = 1.95 - 0.05 × {entrada.espessura_cm:.0f} = {resultado.majorador:.2f}<br>
                <strong>Msk = M × γ_f = {resultado.msk_tf_m:.3f} tf.m</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_armacao_card(entrada: EntradaBeiral) -> None:
    st.markdown(
        """
        <div class="shell-container" style="background-color: #f8fafc; border-style: dashed;">
            <span class="kicker">Detalhamento</span>
            <h4 style="margin-top:0;">Armação Mínima Adotada</h4>
            <p class="copy-text" style="font-size: 0.85rem;">Defina a bitola e o espaçamento para inclusão no relatório técnico.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _store_result(entrada: EntradaBeiral, resultado: ResultadoBeiral) -> None:
    st.session_state[SESSION_INPUT_KEY] = entrada
    st.session_state[SESSION_RESULT_KEY] = resultado


def _render_resumo(resultado: ResultadoBeiral) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("q total (tf/m2)", f"{resultado.carga_total_q_tf_m2:.3f}")
    col2.metric("P total (tf/m)", f"{resultado.carga_total_p_tf_m:.3f}")
    col3.metric("Momento (tf.m)", f"{resultado.momento_total_tf_m:.3f}")
    col4.metric("Msk (tf.m)", f"{resultado.msk_tf_m:.2f}")


def _render_relatorio(entrada: EntradaBeiral, resultado: ResultadoBeiral) -> None:
    st.divider()
    safe_project_name = html.escape(entrada.nome_projeto)

    st.markdown(
        f"""
        <div class="shell-container" style="border-top: 4px solid var(--accent-strong);">
            <span class="kicker">Relatorio Tecnico</span>
            <h2 class="title-large">{safe_project_name}</h2>
            <p class="copy-text">
                Beiral com balanço de {entrada.largura_cm:.0f} cm e espessura de {entrada.espessura_cm:.0f} cm.
                O processamento abaixo consolida as cargas e o momento fletor solicitante.
            </p>
            <div class="result-box">
                <span class="kicker">Momento de Calculo</span>
                <div class="result-value">Msk = {resultado.msk_tf_m:.3f} tf.m</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_resumo(resultado)

    if resultado.majorador <= 0:
        st.warning(
            "Atenção: O fator de majoração calculado é inválido (<= 0). Verifique os dados de entrada."
        )

    st.success("Cálculo finalizado. O memorial técnico está pronto para exportação.")

    col_img, col_q = st.columns([1.1, 1], gap="large")

    with col_img:
        st.markdown(
            """
            <div class="shell-container">
                <span class="kicker">Esquema Tecnico</span>
                <h4 style="margin-top:0;">Vista do Balanço</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            draw_beiral_svg_from_result(
                entrada.espessura_cm,
                entrada.largura_cm,
                resultado,
            ),
            unsafe_allow_html=True,
        )

    with col_q:
        _render_list_card(
            title="Cargas Distribuidas (q)",
            kicker="Carregamento",
            items=[
                f"Permanente: {entrada.carga_permanente_tf_m2:.3f} tf/m²",
                f"Acidental: {entrada.carga_acidental_tf_m2:.3f} tf/m²",
                f"Peso Próprio (G1): 2.5 × {resultado.espessura_m:.2f} = {resultado.peso_proprio_laje_tf_m2:.3f} tf/m²",
                f"Total q = {resultado.carga_total_q_tf_m2:.3f} tf/m²",
            ],
        )

    col_p, col_formula = st.columns(2, gap="large")

    carga_p_items: list[str] = []
    if entrada.possui_nervura_borda:
        carga_p_items.append(
            f"Nervura N1 ({entrada.espessura_nervura_cm:.0f}×{entrada.altura_nervura_cm:.0f})"
        )
        carga_p_items.append(
            "Peso Próprio = "
            f"{entrada.espessura_nervura_cm / 100:.2f} × "
            f"{entrada.altura_nervura_cm / 100:.2f} × 2.5 = "
            f"{resultado.peso_proprio_nervura_tf_m:.3f} tf/m"
        )
    if entrada.possui_guarda_corpo:
        carga_p_items.append(
            "Carga Alvenaria = "
            f"{entrada.espessura_alvenaria_cm / 100:.2f} × "
            f"{entrada.altura_alvenaria_cm / 100:.2f} × "
            f"{PESO_ESPECIFICO_ALVENARIA_TF_M3:.1f} = "
            f"{resultado.carga_alvenaria_tf_m:.3f} tf/m"
        )
    if resultado.possui_carga_concentrada:
        carga_p_items.append(f"Total P = {resultado.carga_total_p_tf_m:.3f} tf/m")
    else:
        carga_p_items.append("Sem carga concentrada ativa")

    with col_p:
        _render_list_card(
            title="Cargas na Borda (P)",
            kicker="Carregamento P",
            items=carga_p_items,
        )

    with col_formula:
        _render_formula_card(entrada, resultado)

    _render_armacao_card(entrada)
    
    # Refined layout for minimal reinforcement inputs
    col_arm_icon, col_arm_bitola, col_arm_sep, col_arm_espacamento = st.columns(
        [0.4, 1.2, 0.4, 1.2],
        gap="small"
    )

    with col_arm_icon:
        st.markdown("<div style='margin-top: 2.2rem; font-size: 1.5rem; text-align: center;'>ø</div>", unsafe_allow_html=True)
    
    with col_arm_bitola:
        bitola = st.number_input(
            "Bitola (mm)",
            min_value=0.0,
            value=float(entrada.armacao_minima_bitola_mm) if entrada.armacao_minima_bitola_mm not in (None, 0) else 8.0,
            step=0.5,
            key="armacao_minima_bitola_mm",
        )

    with col_arm_sep:
        st.markdown("<div style='margin-top: 2.4rem; font-size: 1.1rem; text-align: center; color: var(--ink-soft);'>c/</div>", unsafe_allow_html=True)

    with col_arm_espacamento:
        espacamento = st.number_input(
            "Espaçamento (cm)",
            min_value=0.0,
            value=float(entrada.armacao_minima_espacamento_cm)  if entrada.armacao_minima_espacamento_cm not in (None, 0) else 14.0,
            step=1.0,
            key="armacao_minima_espacamento_cm",
        )

    entrada.armacao_minima_bitola_mm = bitola
    entrada.armacao_minima_espacamento_cm = espacamento
    st.session_state[SESSION_INPUT_KEY] = entrada

    st.divider()
    from beiral.pdf import gerar_pdf_relatorio, pdf_disponivel

    if pdf_disponivel():
        pdf_bytes = gerar_pdf_relatorio(entrada, resultado)
        file_name = sanitize_filename_component(entrada.nome_projeto)
        st.download_button(
            label="Baixar PDF do relatorio",
            data=pdf_bytes,
            file_name=f"Calculo_Beiral_{file_name}.pdf",
            mime="application/pdf",
        )
    else:
        st.warning(
            "A biblioteca 'fpdf' nao esta instalada. Para habilitar a exportacao do PDF, execute: `pip install fpdf`"
        )


st.set_page_config(page_title="Calculo de Beiral", layout="wide")
_inject_styles()

_render_top_shell()

st.divider()
st.header("Entrada de Dados")
st.caption(
    "Preencha os campos tecnicos abaixo para gerar a memoria de calculo e o PDF do relatorio."
)

nome_projeto = st.text_input("Nome do projeto / laje", value=DEFAULT_PROJECT_NAME)

col_intro, col_overview = st.columns([1.1, 1], gap="large")

with col_intro:
    _render_section_intro(
        title="Dimensoes e cargas basicas",
        copy="Defina a geometria do beiral e as cargas distribuidas do caso analisado.",
    )

with col_overview:
    st.markdown(
        """
        <div class="shell-container">
            <span class="kicker">Referencia</span>
            <h3>Dados do Projeto</h3>
            <p class="copy-text">
                O processamento considera as cargas permanentes, acidentais e elementos de borda (nervuras e guarda-corpos).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("Geometria da Laje")
    espessura_cm = st.number_input(
        "Espessura do beiral (cm)",
        min_value=1.0,
        value=14.0,
        step=1.0,
    )
    largura_cm = st.number_input(
        "Largura do balanço (cm)",
        min_value=1.0,
        value=110.0,
        step=1.0,
    )

with col2:
    st.subheader("Cargas de Superfície (q)")
    carga_permanente = st.number_input(
        "Carga permanente - G2 (tf/m2)",
        min_value=0.0,
        value=0.3,
        step=0.05,
    )
    carga_acidental = st.number_input(
        "Carga acidental - Q (tf/m2)",
        min_value=0.0,
        value=0.2,
        step=0.05,
    )

st.markdown(
    """
    <div class="shell-container">
        <span class="kicker">Cargas Lineares</span>
        <h3>Elementos de Borda</h3>
        <p class="copy-text">
            Ative os elementos presentes na extremidade do balanço para cálculo da carga concentrada P.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Cargas Concentradas na Borda (P)")
col3, col4 = st.columns(2, gap="large")

with col3:
    possui_nervura_borda = st.checkbox("Possui nervura de borda?", value=True)
    if possui_nervura_borda:
        espessura_nervura_cm = st.number_input(
            "Largura da nervura (cm)",
            min_value=1.0,
            value=14.0,
            step=1.0,
        )
        altura_nervura_cm = st.number_input(
            "Altura da nervura (cm)",
            min_value=1.0,
            value=70.0,
            step=1.0,
        )
    else:
        espessura_nervura_cm = 0.0
        altura_nervura_cm = 0.0

with col4:
    possui_guarda_corpo = st.checkbox("Possui alvenaria (Guarda-corpo)?", value=False)
    if possui_guarda_corpo:
        espessura_alvenaria_cm = st.number_input(
            "Espessura da alvenaria (cm)",
            min_value=0.0,
            value=12.0,
            step=1.0,
        )
        altura_alvenaria_cm = st.number_input(
            "Altura da alvenaria (cm)",
            min_value=0.0,
            value=110.0,
            step=1.0,
        )
        carga_alvenaria = (
            (espessura_alvenaria_cm / 100.0)
            * (altura_alvenaria_cm / 100.0)
            * PESO_ESPECIFICO_ALVENARIA_TF_M3
        )
        st.markdown(
            f"""
            <div class="shell-container" style="background-color: #f1f5f9;">
                <span class="kicker">Calculo Automático</span>
                <p class="copy-text">
                    Carga linear da alvenaria: <strong>{carga_alvenaria:.3f} tf/m</strong><br>
                    <small>(Peso específico considerado: 1.3 tf/m³)</small>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        espessura_alvenaria_cm = 0.0
        altura_alvenaria_cm = 0.0

submitted = st.button(
    "Calcular Memorial de Calculo",
    use_container_width=True,
    type="primary",
)

if submitted:
    entrada = EntradaBeiral(
        nome_projeto=nome_projeto,
        espessura_cm=espessura_cm,
        largura_cm=largura_cm,
        carga_permanente_tf_m2=carga_permanente,
        carga_acidental_tf_m2=carga_acidental,
        possui_nervura_borda=possui_nervura_borda,
        espessura_nervura_cm=espessura_nervura_cm,
        altura_nervura_cm=altura_nervura_cm,
        possui_guarda_corpo=possui_guarda_corpo,
        espessura_alvenaria_cm=espessura_alvenaria_cm,
        altura_alvenaria_cm=altura_alvenaria_cm,
    )
    erros = validar_entrada(entrada)

    if erros:
        for erro in erros:
            st.error(erro)
    else:
        resultado = calcular_beiral(entrada)
        _store_result(entrada, resultado)

entrada_salva = st.session_state.get(SESSION_INPUT_KEY)
resultado_salvo = st.session_state.get(SESSION_RESULT_KEY)

if entrada_salva and resultado_salvo:
    _render_relatorio(entrada_salva, resultado_salvo)
