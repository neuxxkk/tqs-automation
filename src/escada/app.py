from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from escada.calculos import carregamento_lance
from escada.defaults import edificio_metallo, escada_metallo
from escada.desenho import desenhar_escada
from escada.domain import Apoio, Edificio, Escada, Lance, Vao
from escada.memoria import gerar_memoria_markdown, gerar_memoria_pdf
from ui import inject_formula_theme, render_page_header, render_sidebar_brand


DEFAULTS_REV = "metallo_imagem_v3"
POSICOES_HORARIAS = ["9h", "12h", "3h", "6h"]


def _descricao_fluxo_horario(n_lances: int) -> str:
    partes = [
        f"{i}o lance -> {POSICOES_HORARIAS[(i - 1) % len(POSICOES_HORARIAS)]}"
        for i in range(1, n_lances + 1)
    ]
    return "; ".join(partes)


def _apoio_para_opcao(apoio: Apoio) -> str:
    if apoio.tipo == "lance":
        return f"lance {apoio.referencia_lance}"
    return apoio.tipo


def _opcao_para_apoio(opcao: str) -> Apoio:
    if opcao.startswith("lance "):
        return Apoio(tipo="lance", referencia_lance=int(opcao.split()[1]))
    return Apoio(tipo=opcao)  # type: ignore[arg-type]


def _opcoes_apoio(indice_lance: int, n_lances: int) -> list[str]:
    opcoes = ["laje", "viga", "pilar"]
    opcoes.extend(f"lance {i}" for i in range(1, n_lances + 1) if i != indice_lance)
    return opcoes


def _default_lance(indice: int) -> Lance:
    padrao = escada_metallo().lances
    if indice <= len(padrao):
        return padrao[indice - 1]
    apoios = [Apoio(tipo="laje"), Apoio(tipo="viga")]
    if indice == 4:
        apoios = [Apoio(tipo="laje"), Apoio(tipo="lance", referencia_lance=3)]
    return Lance(
        indice=indice,
        b=1.20,
        h=0.12,
        apoios=apoios,
        vaos=[Vao(tipo="patamar", L=2.00)],
    )


def _indice_padrao(opcoes: list[str], valor: str) -> int:
    return opcoes.index(valor) if valor in opcoes else 0


def _entrada_lance(indice: int, n_lances: int) -> Lance:
    padrao = _default_lance(indice)
    opcoes = _opcoes_apoio(indice, n_lances)

    apoio1 = st.selectbox(
        "Apoio 1",
        opcoes,
        index=_indice_padrao(opcoes, _apoio_para_opcao(padrao.apoios[0])),
        key=f"{DEFAULTS_REV}_lance_{indice}_apoio_1",
    )
    apoio2 = st.selectbox(
        "Apoio 2",
        opcoes,
        index=_indice_padrao(opcoes, _apoio_para_opcao(padrao.apoios[1])),
        key=f"{DEFAULTS_REV}_lance_{indice}_apoio_2",
    )

    col_b, col_h = st.columns(2)
    b = col_b.number_input(
        f"b{indice} (m)",
        min_value=0.10,
        value=float(padrao.b),
        step=0.01,
        format="%.3f",
        key=f"{DEFAULTS_REV}_lance_{indice}_b",
    )
    h = col_h.number_input(
        f"h{indice} (m)",
        min_value=0.05,
        value=float(padrao.h),
        step=0.01,
        format="%.3f",
        key=f"{DEFAULTS_REV}_lance_{indice}_h",
    )

    n_vaos = st.number_input(
        "Numero de vaos",
        min_value=1,
        max_value=8,
        value=len(padrao.vaos),
        step=1,
        key=f"{DEFAULTS_REV}_lance_{indice}_n_vaos",
    )

    vaos: list[Vao] = []
    for j in range(1, int(n_vaos) + 1):
        default_vao = padrao.vaos[j - 1] if j <= len(padrao.vaos) else Vao("patamar", 1.0)
        col_tipo, col_l = st.columns([1.05, 1])
        tipo = col_tipo.selectbox(
            f"Vao {j}",
            ["patamar", "escada"],
            index=0 if default_vao.tipo == "patamar" else 1,
            key=f"{DEFAULTS_REV}_lance_{indice}_vao_{j}_tipo",
        )
        comprimento = col_l.number_input(
            f"L{indice},{j} (m)",
            min_value=0.05,
            value=float(default_vao.L),
            step=0.05,
            format="%.3f",
            key=f"{DEFAULTS_REV}_lance_{indice}_vao_{j}_L",
        )
        vaos.append(Vao(tipo=tipo, L=comprimento))  # type: ignore[arg-type]

    return Lance(
        indice=indice,
        b=b,
        h=h,
        apoios=[_opcao_para_apoio(apoio1), _opcao_para_apoio(apoio2)],
        vaos=vaos,
    )


def _tabela_carregamentos(edificio: Edificio, escada: Escada) -> list[dict[str, object]]:
    linhas: list[dict[str, object]] = []
    for lance in escada.lances:
        carga = carregamento_lance(edificio, lance)
        for vao in carga.vaos:
            linhas.append(
                {
                    "Lance": carga.indice,
                    "Vao": vao.indice,
                    "Tipo": vao.tipo,
                    "L (m)": round(vao.L, 3),
                    "h (m)": round(carga.h, 3),
                    "PP (tF/m2)": round(carga.pp, 3),
                    "q (tF/m2)": round(vao.q, 3),
                    "Apoia em lance": "sim" if lance.apoia_em_lance else "nao",
                }
            )
    return linhas


def _build_sidebar() -> tuple[Edificio, Escada]:
    edificio_padrao = edificio_metallo()
    escada_padrao = escada_metallo()

    render_sidebar_brand(
        tool_name="Calculo de Escadas",
        description="Edite lances, apoios e vaos enquanto o preview e a memoria acompanham cada ajuste.",
    )

    st.sidebar.subheader("Dados do edificio")
    nome = st.sidebar.text_input("Nome", value=edificio_padrao.nome)
    col_li, col_lf = st.sidebar.columns(2)
    laje_inicial = col_li.number_input(
        "Laje inicial",
        min_value=0,
        value=escada_padrao.laje_inicial,
        step=1,
    )
    laje_final = col_lf.number_input(
        "Laje final",
        min_value=1,
        value=escada_padrao.laje_final,
        step=1,
    )
    fck = st.sidebar.number_input("fck (MPa)", min_value=10.0, value=edificio_padrao.fck, step=1.0)
    cp = st.sidebar.number_input(
        "CP (tF/m2)",
        min_value=0.0,
        value=edificio_padrao.cp,
        step=0.01,
        format="%.3f",
    )
    ca = st.sidebar.number_input(
        "CA (tF/m2)",
        min_value=0.0,
        value=edificio_padrao.ca,
        step=0.01,
        format="%.3f",
    )

    st.sidebar.subheader("Ferramentas de desenho")
    n_lances = st.sidebar.number_input(
        "Numero de lances",
        min_value=1,
        max_value=12,
        value=escada_padrao.n_lances,
        step=1,
    )
    st.sidebar.caption("Fluxo horario:")
    st.sidebar.caption(_descricao_fluxo_horario(int(n_lances)))

    st.sidebar.subheader("Lances")
    lances: list[Lance] = []
    for i in range(1, int(n_lances) + 1):
        with st.sidebar.expander(f"Lance {i}", expanded=i <= 2):
            lances.append(_entrada_lance(i, int(n_lances)))

    edificio = Edificio(nome=nome, fck=fck, cp=cp, ca=ca)
    escada = Escada(
        laje_inicial=int(laje_inicial),
        laje_final=int(laje_final),
        lances=lances,
    )
    return edificio, escada


def _render_summary(edificio: Edificio, escada: Escada) -> None:
    comprimento_total = sum(lance.comprimento_total for lance in escada.lances)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Lances", str(escada.n_lances))
    col2.metric("Comprimento total (m)", f"{comprimento_total:.3f}")
    col3.metric("fck (MPa)", f"{edificio.fck:.0f}")
    col4.metric("CP + CA (tF/m2)", f"{(edificio.cp + edificio.ca):.3f}")


def _render_preview(escada: Escada) -> None:
    fig = desenhar_escada(escada, layout="horario")
    st.pyplot(fig, clear_figure=True, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Calculo de Escadas", layout="wide")
    inject_formula_theme()

    render_page_header(
        kicker="Engenharia Estrutural",
        title="Calculo de Escadas",
        description=(
            "Modelagem de lances, patamares e apoios com fluxo horario fixo, preview esquematico, "
            "carregamentos e memoria de calculo acompanhando os controles em tempo real."
        ),
    )

    with st.sidebar:
        try:
            edificio, escada = _build_sidebar()
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

    _render_summary(edificio, escada)

    memoria_md = gerar_memoria_markdown(edificio, escada)
    memoria_pdf = gerar_memoria_pdf(edificio, escada, layout="horario")

    tabs = st.tabs(["Preview", "Carregamentos", "Memoria"])

    with tabs[0]:
        _render_preview(escada)

    with tabs[1]:
        st.dataframe(_tabela_carregamentos(edificio, escada), use_container_width=True)

    with tabs[2]:
        col_md, col_pdf = st.columns(2)
        col_md.download_button(
            "Baixar Markdown",
            data=memoria_md.encode("utf-8"),
            file_name="memoria_escada.md",
            mime="text/markdown",
            use_container_width=True,
        )
        col_pdf.download_button(
            "Exportar PDF",
            data=memoria_pdf,
            file_name="memoria_escada.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.markdown(memoria_md)


if __name__ == "__main__":
    main()
