from __future__ import annotations

import base64
import html
from functools import lru_cache
from pathlib import Path

import streamlit as st


THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --verde-principal: #5a8a4a;
        --verde-hover: #3b6d11;
        --verde-claro: #eaf3de;
        --verde-texto: #27500a;
        --cinza-900: #1e1e1c;
        --cinza-800: #2c2c2a;
        --cinza-600: #6b6b6b;
        --cinza-300: #b4b2a9;
        --cinza-100: #f1efe8;
        --cinza-50: #f8f7f4;
        --branco: #ffffff;
        --erro: #e24b4a;
        --aviso: #ba7517;
        --shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
    }

    html, body, [class*="css"]  {
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--cinza-100);
        color: var(--cinza-800);
    }

    [data-testid="stAppViewBlockContainer"] {
        max-width: 1280px;
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    section[data-testid="stSidebar"] {
        background: var(--cinza-900);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        min-width: 420px !important;
        max-width: 420px !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        background: var(--cinza-900);
        color: var(--branco);
        padding-left: 1rem;
        padding-right: 1rem;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: var(--branco);
    }

    section[data-testid="stSidebar"] [data-baseweb="input"] input,
    section[data-testid="stSidebar"] [data-baseweb="base-input"] input,
    section[data-testid="stSidebar"] [data-baseweb="select"] input,
    section[data-testid="stSidebar"] [data-baseweb="select"] div {
        color: var(--cinza-800) !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-baseweb="base-input"] > div,
    section[data-testid="stSidebar"] [data-testid="stNumberInput"] [data-baseweb="input"] > div {
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid rgba(255, 255, 255, 0.12);
    }

    section[data-testid="stSidebar"] [data-baseweb="base-input"],
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        border-radius: 6px;
    }

    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] * ,
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] .stCaption * {
        color: rgba(255, 255, 255, 0.88) !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.04);
        overflow: hidden;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] details {
        background: transparent;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] summary,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary:focus-visible,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary > div,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary > div:hover,
    section[data-testid="stSidebar"] [data-testid="stExpander"] details[open] > summary,
    section[data-testid="stSidebar"] [data-testid="stExpander"] details[open] > summary > div {
        background: transparent !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpander"] summary,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary * {
        color: var(--branco) !important;
    }

    section[data-testid="stSidebar"] [data-testid="stExpanderDetails"] {
        background: rgba(255, 255, 255, 0.02);
        padding-top: 0.35rem;
    }

    section[data-testid="stSidebar"] button {
        color: var(--cinza-800);
    }

    section[data-testid="stSidebar"] [data-baseweb="popover"] *,
    section[data-testid="stSidebar"] [role="listbox"] * {
        color: var(--cinza-800) !important;
    }

    h1, h2, h3, h4 {
        font-family: 'Barlow Condensed', sans-serif;
        color: var(--cinza-800);
        letter-spacing: 0;
    }

    [data-testid="stMetric"] {
        background: var(--cinza-50);
        border: 1px solid var(--cinza-300);
        border-radius: 6px;
        box-shadow: var(--shadow);
        padding: 0.85rem 1rem;
    }

    [data-testid="stMetricLabel"] {
        color: var(--cinza-600);
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    [data-testid="stMetricValue"] {
        color: var(--verde-principal);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
    }

    .stButton > button,
    .stDownloadButton > button,
    button[kind="primary"],
    button[kind="secondary"],
    button[kind="primaryFormSubmit"] {
        border-radius: 6px;
        border: 1px solid var(--verde-principal);
        background: var(--verde-principal);
        color: var(--branco);
        font-family: 'DM Sans', sans-serif;
        font-weight: 700;
        min-height: 42px;
        box-shadow: none;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    button[kind="primary"]:hover,
    button[kind="secondary"]:hover,
    button[kind="primaryFormSubmit"]:hover {
        border-color: var(--verde-hover);
        background: var(--verde-hover);
        color: var(--branco);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: var(--cinza-50);
        border: 1px solid var(--cinza-300);
        border-radius: 6px;
        padding: 0.45rem 0.8rem;
        font-family: 'Barlow Condensed', sans-serif;
        color: var(--cinza-600);
    }

    .stTabs [aria-selected="true"] {
        background: var(--verde-claro);
        border-color: var(--verde-principal);
        color: var(--verde-texto);
    }

    .stExpander {
        border: 1px solid var(--cinza-300);
        border-radius: 6px;
        background: var(--cinza-50);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--cinza-300);
        border-radius: 6px;
        overflow: hidden;
    }

    .formula-page-head {
        padding: 1.1rem 0 1.35rem 0;
        border-bottom: 1px solid var(--cinza-300);
        margin-bottom: 1.4rem;
    }

    .formula-kicker {
        display: inline-block;
        color: var(--verde-principal);
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .formula-page-title {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 2.35rem;
        line-height: 1;
        color: var(--cinza-800);
        margin: 0;
    }

    .formula-page-copy {
        color: var(--cinza-600);
        font-size: 0.98rem;
        line-height: 1.6;
        max-width: 72ch;
        margin-top: 0.65rem;
    }

    .formula-card {
        background: var(--cinza-50);
        border: 1px solid var(--cinza-300);
        border-radius: 6px;
        box-shadow: var(--shadow);
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
    }

    .formula-card h3,
    .formula-card h4 {
        margin: 0 0 0.55rem 0;
    }

    .formula-card p,
    .formula-card li {
        color: var(--cinza-600);
        line-height: 1.55;
        margin-bottom: 0.3rem;
    }

    .formula-note {
        background: var(--verde-claro);
        color: var(--verde-texto);
        border-left: 4px solid var(--verde-principal);
        border-radius: 6px;
        padding: 0.9rem 1rem;
        margin-bottom: 1rem;
    }

    .formula-code {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.86rem;
        background: var(--cinza-100);
        border: 1px solid var(--cinza-300);
        border-radius: 6px;
        padding: 0.9rem 1rem;
        color: var(--cinza-800);
        line-height: 1.65;
    }

    .formula-sidebar-brand {
        display: flex;
        gap: 0.85rem;
        align-items: center;
        padding: 0.5rem 0 1rem 0;
        margin-bottom: 0.85rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    .formula-sidebar-brand img {
        width: 40px;
        height: 40px;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.06);
        padding: 6px;
    }

    .formula-sidebar-brand .brand-text strong {
        display: block;
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--branco);
        line-height: 1;
    }

    .formula-sidebar-brand .brand-text span {
        display: block;
        color: rgba(255, 255, 255, 0.72);
        font-size: 0.82rem;
        margin-top: 0.2rem;
    }

    .formula-sidebar-tool {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 6px;
        padding: 0.9rem 0.95rem;
        margin-bottom: 1rem;
    }

    .formula-sidebar-tool strong {
        display: block;
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 1rem;
        margin-bottom: 0.25rem;
        color: var(--branco);
    }

    .formula-sidebar-tool p {
        color: rgba(255, 255, 255, 0.78);
        font-size: 0.86rem;
        line-height: 1.5;
        margin: 0;
    }

    .formula-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.76rem;
        color: var(--verde-claro);
        background: var(--verde-hover);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 999px;
        padding: 0.2rem 0.55rem;
        margin-top: 0.7rem;
    }

    .formula-mono {
        font-family: 'JetBrains Mono', monospace;
    }
</style>
"""


def inject_formula_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


@lru_cache(maxsize=1)
def _logo_data_uri() -> str:
    logo_path = Path(__file__).resolve().parents[2] / "assets" / "imgs" / "engenharia_formula_logo.ico"
    if not logo_path.exists():
        return ""
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/x-icon;base64,{encoded}"


def render_sidebar_brand(tool_name: str, description: str) -> None:
    logo_src = _logo_data_uri()
    logo_html = f'<img src="{logo_src}" alt="Formula Engenharia">' if logo_src else ""
    st.sidebar.markdown(
        f"""
        <div class="formula-sidebar-brand">
            {logo_html}
            <div class="brand-text">
                <strong>FÓRMULA</strong>
                <span>Engenharia e Consultoria</span>
            </div>
        </div>
        <div class="formula-sidebar-tool">
            <strong>{html.escape(tool_name)}</strong>
            <p>{html.escape(description)}</p>
            <span class="formula-badge">Atualizacao em tempo real</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="formula-page-head">
            <span class="formula-kicker">{html.escape(kicker)}</span>
            <h1 class="formula-page-title">{html.escape(title)}</h1>
            <div class="formula-page-copy">{html.escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
