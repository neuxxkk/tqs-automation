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
from beiral.pdf import gerar_pdf_relatorio, pdf_disponivel


DEFAULT_PROJECT_NAME = "16a Laje - ANIMA MAJOR"
SESSION_INPUT_KEY = "beiral_entrada"
SESSION_RESULT_KEY = "beiral_resultado"
THEME_CSS = """
<style>
    :root {
        --page-bg-start: #edf2f7;
        --page-bg-end: #dbe4ee;
        --panel-bg: rgba(255, 255, 255, 0.9);
        --ink-strong: #182534;
        --ink-soft: #5d6c7c;
        --accent: #1d4f7a;
        --accent-strong: #12324d;
        --line: rgba(24, 37, 52, 0.11);
        --result-bg: rgba(29, 79, 122, 0.09);
        --result-line: rgba(29, 79, 122, 0.24);
        --badge-bg: rgba(29, 79, 122, 0.08);
        --shadow: 0 16px 42px rgba(33, 52, 74, 0.08);
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(255, 255, 255, 0.78), transparent 28%),
            linear-gradient(180deg, var(--page-bg-start) 0%, var(--page-bg-end) 100%);
    }

    [data-testid="stAppViewBlockContainer"] {
        max-width: 1180px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: var(--ink-strong);
        font-family: "Trebuchet MS", "Segoe UI", sans-serif;
        letter-spacing: -0.02em;
    }

    p, li, label, .stMarkdown, .stCaption {
        color: var(--ink-soft);
    }

    [data-testid="stForm"] {
        background: var(--panel-bg);
        border: 1px solid var(--line);
        border-radius: 24px;
        box-shadow: var(--shadow);
        padding: 1.15rem 1.15rem 1.35rem 1.15rem;
    }

    [data-testid="stMetric"] {
        background: var(--panel-bg);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 0.65rem 0.9rem;
        box-shadow: 0 12px 28px rgba(66, 50, 34, 0.06);
    }

    [data-testid="stMetricLabel"] {
        color: var(--ink-soft);
        font-size: 0.84rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    [data-testid="stMetricValue"] {
        color: var(--ink-strong);
    }

    .stTextInput input, .stNumberInput input {
        background: rgba(255, 255, 255, 0.85);
    }

    .stButton > button,
    .stDownloadButton > button,
    button[kind="primaryFormSubmit"] {
        border-radius: 999px;
        border: 0;
        background: linear-gradient(135deg, var(--accent), #2f699b);
        color: #f8fbff;
        font-weight: 600;
        box-shadow: 0 16px 34px rgba(29, 79, 122, 0.22);
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--accent-strong), var(--accent));
    }

    .top-shell,
    .report-shell,
    .section-shell,
    .formula-shell,
    .drawing-shell,
    .armacao-shell,
    .badge-shell {
        background: var(--panel-bg);
        border: 1px solid var(--line);
        border-radius: 24px;
        box-shadow: var(--shadow);
    }

    .top-shell {
        padding: 1.25rem 1.45rem;
        margin-bottom: 1rem;
        background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(246, 250, 255, 0.92));
    }

    .report-shell,
    .section-shell,
    .formula-shell,
    .drawing-shell,
    .armacao-shell,
    .badge-shell {
        padding: 1.05rem 1.15rem;
    }

    .top-kicker,
    .section-kicker {
        color: var(--accent);
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }

    .top-title,
    .report-title {
        color: var(--ink-strong);
        font-size: 1.9rem;
        line-height: 1.05;
        font-weight: 700;
        margin: 0;
    }

    .top-copy,
    .report-copy,
    .section-copy {
        color: var(--ink-soft);
        margin-top: 0.7rem;
        line-height: 1.55;
    }

    .top-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
    }

    .top-badge {
        border-radius: 999px;
        border: 1px solid rgba(29, 79, 122, 0.14);
        background: var(--badge-bg);
        color: var(--ink-strong);
        font-size: 0.84rem;
        padding: 0.42rem 0.76rem;
    }

    .report-shell {
        margin-top: 1rem;
        margin-bottom: 0.9rem;
        background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(247, 251, 255, 0.92));
    }

    .result-highlight {
        display: inline-block;
        margin-top: 0.85rem;
        padding: 0.8rem 1rem;
        border-radius: 18px;
        background: var(--result-bg);
        border: 1px solid var(--result-line);
        color: var(--ink-strong);
        font-weight: 700;
        font-size: 1.22rem;
    }

    .section-shell,
    .formula-shell,
    .drawing-shell,
    .armacao-shell {
        height: 100%;
    }

    .section-shell ul {
        margin: 0.5rem 0 0 1rem;
        padding: 0;
    }

    .section-shell li,
    .formula-shell li {
        color: var(--ink-strong);
        margin-bottom: 0.35rem;
    }

    .formula-shell code {
        white-space: pre-wrap;
        color: var(--ink-strong);
        font-size: 0.95rem;
    }

    .inline-note {
        color: var(--ink-soft);
        font-size: 0.92rem;
        margin-top: 0.35rem;
    }

    .armacao-value {
        color: var(--ink-strong);
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: 0.6rem;
    }

    .calc-badge {
        display: inline-block;
        margin-top: 0.55rem;
        padding: 0.42rem 0.76rem;
        border-radius: 999px;
        background: var(--badge-bg);
        border: 1px solid rgba(29, 79, 122, 0.14);
        color: var(--accent-strong);
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
"""


def _inject_styles() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def _render_top_shell() -> None:
    st.markdown(
        """
        <section class="top-shell">
            <div class="top-kicker">Calculo Estrutural</div>
            <h1 class="top-title">Calculo de Beiral</h1>
            <p class="top-copy">
                Ferramenta para lancamento de cargas, verificacao do momento e emissao do relatorio tecnico.
            </p>
            <div class="top-badges">
                <span class="top-badge">Beiral em balanco</span>
                <span class="top-badge">Memoria de calculo</span>
                <span class="top-badge">PDF</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_section_intro(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <section class="section-shell">
            <div class="section-kicker">Entrada</div>
            <h3>{html.escape(title)}</h3>
            <p class="section-copy">{html.escape(copy)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_list_card(title: str, kicker: str, items: list[str]) -> None:
    list_html = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    st.markdown(
        f"""
        <section class="section-shell">
            <div class="section-kicker">{html.escape(kicker)}</div>
            <h3>{html.escape(title)}</h3>
            <ul>{list_html}</ul>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_formula_card(entrada: EntradaBeiral, resultado: ResultadoBeiral) -> None:
    formula_m = (
        f"({resultado.carga_total_q_tf_m2:.3f} x "
        f"{resultado.largura_m:.2f} x {resultado.largura_m / 2:.2f})"
    )
    if resultado.possui_carga_concentrada:
        formula_m += (
            f" + ({resultado.carga_total_p_tf_m:.3f} x "
            f"{resultado.largura_m:.2f})"
        )

    st.markdown(
        f"""
        <section class="formula-shell">
            <div class="section-kicker">Memoria</div>
            <h3>Momento e majoracao</h3>
            <p class="section-copy">A expressao abaixo resume o fechamento principal do relatorio.</p>
            <p><code>M = {html.escape(formula_m)} = {resultado.momento_total_tf_m:.3f} tf.m</code></p>
            <p><code>Y = 1.95 - 0.05 x {entrada.espessura_cm:.0f} = {resultado.majorador:.2f}</code></p>
            <p><code>Msk = {resultado.momento_total_tf_m:.3f} x {resultado.majorador:.2f} = {resultado.msk_tf_m:.2f} tf.m</code></p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_armacao_card(entrada: EntradaBeiral) -> None:
    st.markdown(
        """
        <section class="armacao-shell">
            <div class="section-kicker">Complemento</div>
            <h3>Armacao minima</h3>
            <p class="section-copy">Preencha a armacao minima diretamente na linha abaixo para incluir o detalhe no relatorio.</p>
        </section>
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
        <section class="report-shell">
            <div class="section-kicker">Saida</div>
            <h2 class="report-title">{safe_project_name}</h2>
            <p class="report-copy">
                Beiral com secao de {entrada.largura_cm:.0f} cm e espessura de {entrada.espessura_cm:.0f} cm.
                O relatorio abaixo consolida cargas, momento e fechamento final para exportacao.
            </p>
            <div class="result-highlight">Resultado final: Msk = {resultado.msk_tf_m:.2f} tf.m</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    _render_resumo(resultado)

    if resultado.majorador <= 0:
        st.warning(
            "O majorador ficou menor ou igual a zero. Vale revisar a formula e os dados informados."
        )

    st.success("Calculo efetuado com sucesso. Confira o relatorio abaixo.")

    col_img, col_q = st.columns([1.05, 1.2], gap="large")

    with col_img:
        st.markdown(
            """
            <section class="drawing-shell">
                <div class="section-kicker">Esquema</div>
                <h3>Vista simplificada do beiral</h3>
                <p class="inline-note">O desenho responde aos dados atuais e marca a presenca de carga P quando aplicavel.</p>
            </section>
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
            title="Cargas distribuidas (q)",
            kicker="Cargas",
            items=[
                f"Permanente: {entrada.carga_permanente_tf_m2:.3f} tf/m2",
                f"Acidental: {entrada.carga_acidental_tf_m2:.3f} tf/m2",
                f"Peso proprio: 2.5 x {resultado.espessura_m:.2f} = {resultado.peso_proprio_laje_tf_m2:.3f} tf/m2",
                f"Sigma q = {resultado.carga_total_q_tf_m2:.3f} tf/m2",
            ],
        )

    col_p, col_formula = st.columns(2, gap="large")

    carga_p_items: list[str] = []
    if entrada.possui_nervura_borda:
        carga_p_items.append(
            f"Nervura N1 ({entrada.espessura_nervura_cm:.0f} x {entrada.altura_nervura_cm:.0f})"
        )
        carga_p_items.append(
            "Peso proprio = "
            f"{entrada.espessura_nervura_cm / 100:.2f} x "
            f"{entrada.altura_nervura_cm / 100:.2f} x 2.5 = "
            f"{resultado.peso_proprio_nervura_tf_m:.3f} tf/m"
        )
    if entrada.possui_guarda_corpo:
        carga_p_items.append(
            "Carga da alvenaria = "
            f"{entrada.espessura_alvenaria_cm / 100:.2f} x "
            f"{entrada.altura_alvenaria_cm / 100:.2f} x "
            f"{PESO_ESPECIFICO_ALVENARIA_TF_M3:.1f} = "
            f"{resultado.carga_alvenaria_tf_m:.3f} tf/m"
        )
    if resultado.possui_carga_concentrada:
        carga_p_items.append(f"Sigma P = {resultado.carga_total_p_tf_m:.3f} tf/m")
    else:
        carga_p_items.append("Nenhuma carga concentrada ativa")

    with col_p:
        _render_list_card(
            title="Carga concentrada (P)",
            kicker="Borda",
            items=carga_p_items,
        )

    with col_formula:
        _render_formula_card(entrada, resultado)

    _render_armacao_card(entrada)
    col_label_1, col_bitola, col_label_2, col_espacamento = st.columns(
        [1.6, 1.1, 0.55, 1.1],
        gap="small",
    )

    with col_label_1:
        st.markdown("**Armacao minima**")

    with col_bitola:
        bitola = st.number_input(
            "Bitola",
            min_value=0.0,
            value=float(entrada.armacao_minima_bitola_mm),
            step=0.5,
            key="armacao_minima_bitola_mm",
            label_visibility="collapsed",
        )

    with col_label_2:
        st.markdown("**c/**")

    with col_espacamento:
        espacamento = st.number_input(
            "Espacamento",
            min_value=0.0,
            value=float(entrada.armacao_minima_espacamento_cm),
            step=1.0,
            key="armacao_minima_espacamento_cm",
            label_visibility="collapsed",
        )

    entrada.armacao_minima_bitola_mm = bitola
    entrada.armacao_minima_espacamento_cm = espacamento
    st.session_state[SESSION_INPUT_KEY] = entrada

    st.divider()
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
        <section class="section-shell">
            <div class="section-kicker">Referencia</div>
            <h3>Dados de entrada</h3>
            <p class="section-copy">
                O processamento considera cargas distribuidas, nervura de borda e alvenaria sobre o guarda-corpo quando houver.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("Dimensoes da laje")
    espessura_cm = st.number_input(
        "Espessura do beiral - esp1 (cm)",
        min_value=1.0,
        value=14.0,
        step=1.0,
    )
    largura_cm = st.number_input(
        "Balanco / largura - larg1 (cm)",
        min_value=1.0,
        value=110.0,
        step=1.0,
    )

with col2:
    st.subheader("Cargas distribuidas (q)")
    carga_permanente = st.number_input(
        "Carga permanente - q1 (tf/m2)",
        min_value=0.0,
        value=0.3,
        step=0.05,
    )
    carga_acidental = st.number_input(
        "Carga acidental - q2 (tf/m2)",
        min_value=0.0,
        value=0.2,
        step=0.05,
    )

st.markdown(
    """
    <section class="section-shell">
        <div class="section-kicker">Borda</div>
        <h3>Cargas concentradas</h3>
        <p class="section-copy">
            Ative apenas os elementos presentes no caso real. Quando nao utilizados, os campos permanecem zerados.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.subheader("Cargas concentradas na borda (P)")
col3, col4 = st.columns(2, gap="large")

with col3:
    possui_nervura_borda = st.checkbox("Possui nervura de borda?", value=True)
    if possui_nervura_borda:
        espessura_nervura_cm = st.number_input(
            "Espessura da nervura (cm)",
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
    possui_guarda_corpo = st.checkbox("Possui guarda-corpos?", value=False)
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
            <section class="section-shell">
                <div class="section-kicker">Alvenaria</div>
                <h3>Carga calculada</h3>
                <p class="section-copy">
                    Carga da alvenaria = {espessura_alvenaria_cm / 100:.2f} x {altura_alvenaria_cm / 100:.2f} x {PESO_ESPECIFICO_ALVENARIA_TF_M3:.1f} = <strong>{carga_alvenaria:.3f} tf/m</strong>
                </p>
                <div class="calc-badge">Peso especifico = 1,3 tf/m3</div>
            </section>
            """,
            unsafe_allow_html=True,
        )
    else:
        espessura_alvenaria_cm = 0.0
        altura_alvenaria_cm = 0.0

submitted = st.button(
    "Gerar memoria de calculo",
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
