"""Geracao da memoria de calculo."""
from __future__ import annotations

from io import BytesIO

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .calculos import DEGRAU, carregamento_lance
from .desenho import LayoutDesenho, desenhar_escada
from .domain import Apoio, Edificio, Escada, Lance


def _fmt(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def _subscrito(valor: int | str) -> str:
    mapa = str.maketrans("0123456789-", "₀₁₂₃₄₅₆₇₈₉₋")
    return str(valor).translate(mapa)


def _apoio_texto(apoio: Apoio) -> str:
    if apoio.tipo == "lance":
        return f"lance {apoio.referencia_lance}"
    return apoio.tipo


def _apoios_lance(lance: Lance) -> str:
    return " + ".join(_apoio_texto(apoio) for apoio in lance.apoios)


def _l(lance: int, vao: int) -> str:
    return f"L{_subscrito(f'{lance},{vao}')}"


def _pp(lance: int) -> str:
    return f"PP{_subscrito(lance)}"


def _q(lance: int, vao: int) -> str:
    return f"q{_subscrito(f'{lance},{vao}')}"


def _linhas_carregamento(edificio: Edificio, escada: Escada) -> list[dict[str, str]]:
    linhas: list[dict[str, str]] = []
    for lance in escada.lances:
        carga = carregamento_lance(edificio, lance)
        for vao in carga.vaos:
            parcela_degrau = f" + {_fmt(DEGRAU)}" if vao.tipo == "escada" else ""
            desenvolvimento = (
                f"{_q(carga.indice, vao.indice)} = {_fmt(edificio.cp)} + "
                f"{_fmt(edificio.ca)} + {_pp(carga.indice)}{parcela_degrau} = "
                f"{_fmt(vao.q)}"
            )
            linhas.append(
                {
                    "lance": str(carga.indice),
                    "vao": str(vao.indice),
                    "tipo": vao.tipo,
                    "L": _fmt(vao.L),
                    "pp": _fmt(carga.pp),
                    "q": _fmt(vao.q),
                    "desenvolvimento": desenvolvimento,
                }
            )
    return linhas


def _linhas_desenvolvimento(edificio: Edificio, escada: Escada) -> list[str]:
    linhas: list[str] = []
    for lance in escada.lances:
        carga = carregamento_lance(edificio, lance)
        linhas.append(
            f"{_pp(lance.indice)} = 2,5 × {_fmt(lance.h)} = "
            f"{_fmt(carga.pp)} tF·m⁻²"
        )
        for vao in carga.vaos:
            parcela_degrau = f" + {_fmt(DEGRAU)}" if vao.tipo == "escada" else ""
            linhas.append(
                f"{_q(carga.indice, vao.indice)} = {_fmt(edificio.cp)} + "
                f"{_fmt(edificio.ca)} + {_pp(carga.indice)}{parcela_degrau} = "
                f"{_fmt(vao.q)} tF·m⁻²"
            )
    return linhas


def gerar_memoria_markdown(edificio: Edificio, escada: Escada) -> str:
    """Gera a memoria de calculo em Markdown."""
    linhas: list[str] = [
        f"# Memória de cálculo da {escada.laje_inicial}ª à {escada.laje_final}ª laje - {edificio.nome}",
        "",
        "## Carregamentos",
        "",
        "| Lance | Vão | Tipo | L (m) | PPᵢ (tF·m⁻²) | qᵢ,ⱼ (tF·m⁻²) | Desenvolvimento |",
        "|---:|---:|---|---:|---:|---:|---|",
    ]

    for linha in _linhas_carregamento(edificio, escada):
        linhas.append(
            f"| {linha['lance']} | {linha['vao']} | {linha['tipo']} | "
            f"{linha['L']} | {linha['pp']} | {linha['q']} | "
            f"{linha['desenvolvimento']} |"
        )

    linhas.extend(["", "## Desenvolvimento dos cálculos", ""])
    linhas.extend(f"- {linha}" for linha in _linhas_desenvolvimento(edificio, escada))

    return "\n".join(linhas) + "\n"


def _caixa(ax, titulo: str) -> None:
    ax.axis("off")
    ax.add_patch(
        Rectangle(
            (0, 0),
            1,
            1,
            transform=ax.transAxes,
            facecolor="#fbfbfb",
            edgecolor="#d0d0d0",
            linewidth=0.8,
        )
    )
    ax.text(0.035, 0.93, titulo, fontsize=9.5, weight="bold", va="top")


def _desenhar_textos(ax, linhas: list[str], y0: float = 0.78, fontsize: float = 8.2) -> None:
    y = y0
    for linha in linhas:
        ax.text(0.045, y, linha, fontsize=fontsize, va="top")
        y -= 0.13


def _pagina_resumo_pdf(
    pdf: PdfPages,
    edificio: Edificio,
    escada: Escada,
    layout: LayoutDesenho,
) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    fig.text(
        0.045,
        0.955,
        f"Memória de cálculo da {escada.laje_inicial}ª à {escada.laje_final}ª laje",
        fontsize=16,
        weight="bold",
    )
    fig.text(0.045, 0.925, edificio.nome, fontsize=10, color="#4a4a4a")

    ax_desenho = fig.add_axes([0.60, 0.28, 0.34, 0.56])
    desenhar_escada(escada, ax=ax_desenho, layout=layout)
    ax_desenho.set_title("Desenho esquemático", fontsize=10, pad=8)

    ax_tabela = fig.add_axes([0.045, 0.47, 0.52, 0.38])
    ax_tabela.axis("off")
    rows = _linhas_carregamento(edificio, escada)
    tabela = [
        [r["lance"], r["vao"], r["tipo"], r["L"], r["pp"], r["q"]]
        for r in rows
    ]
    table = ax_tabela.table(
        cellText=tabela,
        colLabels=["Lance", "Vão", "Tipo", "L (m)", "PPᵢ", "qᵢ,ⱼ"],
        loc="upper left",
        cellLoc="center",
        colLoc="center",
        colWidths=[0.12, 0.10, 0.18, 0.15, 0.15, 0.15],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.15)
    for (row, _col), cell in table.get_celld().items():
        cell.set_edgecolor("#c8c8c8")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_facecolor("#eeeeee")
            cell.set_text_props(weight="bold")

    ax_calc = fig.add_axes([0.045, 0.08, 0.90, 0.31])
    _caixa(ax_calc, "Desenvolvimento dos cálculos")
    linhas = _linhas_desenvolvimento(edificio, escada)
    colunas = 2 if len(linhas) > 7 else 1
    linhas_por_coluna = (len(linhas) + colunas - 1) // colunas
    fontsize = 8.1 if len(linhas) <= 10 else 7.2
    for idx, linha in enumerate(linhas):
        coluna = idx // linhas_por_coluna
        linha_idx = idx % linhas_por_coluna
        x = 0.045 + coluna * 0.47
        y = 0.78 - linha_idx * 0.115
        ax_calc.text(x, y, linha, fontsize=fontsize, va="top")

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _pagina_desenvolvimento_pdf(pdf: PdfPages, edificio: Edificio, escada: Escada) -> None:
    linhas = _linhas_desenvolvimento(edificio, escada)
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    fig.text(0.045, 0.955, "Desenvolvimento dos cálculos", fontsize=15, weight="bold")

    ax = fig.add_axes([0.045, 0.08, 0.90, 0.82])
    _caixa(ax, "Expressões por lance e vão")
    y = 0.87
    for linha in linhas:
        ax.text(0.045, y, linha, fontsize=9, va="top")
        y -= 0.065
        if y < 0.08:
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
            fig = plt.figure(figsize=(11.69, 8.27))
            fig.patch.set_facecolor("white")
            fig.text(0.045, 0.955, "Desenvolvimento dos cálculos", fontsize=15, weight="bold")
            ax = fig.add_axes([0.045, 0.08, 0.90, 0.82])
            _caixa(ax, "Expressões por lance e vão")
            y = 0.87

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def gerar_memoria_pdf(
    edificio: Edificio,
    escada: Escada,
    layout: LayoutDesenho = "horario",
) -> bytes:
    """Gera um PDF com resumo, tabela, desenho e desenvolvimento."""
    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        _pagina_resumo_pdf(pdf, edificio, escada, layout)

    return buffer.getvalue()
