"""Desenho esquematico da escada.

Para a escada de 3 lances, o layout segue o croqui de entrada:
    - Lance 2: bloco vertical inferior esquerdo
    - Lance 1: bloco vertical inferior direito
    - Lance 3: faixa horizontal superior, subdividida pelos seus vaos

As cotas usam linhas de chamada, linha de cota continua e marcas nas
extremidades. Nao ha linhas tracejadas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .domain import Escada, Lance


Sentido = Literal["up", "right", "down", "left"]
LadoCota = Literal["left", "right", "top", "bottom"]
LayoutDesenho = Literal["auto", "croqui", "horario"]


@dataclass
class PosicaoLance:
    indice: int
    x: float
    y: float
    w: float
    h: float
    sentido: Sentido
    cota_vaos: LadoCota
    cota_b: LadoCota


# ---- Layout -------------------------------------------------------------

def posicionar_lances(
    escada: Escada,
    layout: LayoutDesenho = "horario",
) -> list[PosicaoLance]:
    """Calcula posicao de cada lance para o preview."""
    if layout == "horario":
        posicoes = _posicionar_lances_espiral(escada)
    elif layout == "croqui" and escada.n_lances == 3:
        posicoes = _posicionar_lances_croqui_3(escada)
    elif layout == "auto" and escada.n_lances == 3:
        posicoes = _posicionar_lances_croqui_3(escada)
    else:
        posicoes = _posicionar_lances_espiral(escada)
    return _ajustar_adjacencias_de_apoio(escada, posicoes)


def _posicionar_lances_croqui_3(escada: Escada) -> list[PosicaoLance]:
    """Layout fiel ao croqui: 2 embaixo/esquerda, 1 embaixo/direita, 3 em cima."""
    lance1, lance2, lance3 = escada.lances

    topo_inferior = max(lance1.comprimento_total, lance2.comprimento_total)
    largura_superior = lance3.comprimento_total

    # Mantem os lances inferiores separados mesmo se a faixa superior for curta.
    folga_minima = 0.15
    x_lance2 = 0.0
    x_lance1 = max(
        largura_superior - lance1.b,
        x_lance2 + lance2.b + folga_minima,
    )

    return [
        PosicaoLance(
            indice=lance1.indice,
            x=x_lance1,
            y=topo_inferior - lance1.comprimento_total,
            w=lance1.b,
            h=lance1.comprimento_total,
            sentido="up",
            cota_vaos="right",
            cota_b="bottom",
        ),
        PosicaoLance(
            indice=lance2.indice,
            x=x_lance2,
            y=topo_inferior - lance2.comprimento_total,
            w=lance2.b,
            h=lance2.comprimento_total,
            sentido="up",
            cota_vaos="left",
            cota_b="bottom",
        ),
        PosicaoLance(
            indice=lance3.indice,
            x=0.0,
            y=topo_inferior,
            w=largura_superior,
            h=lance3.b,
            sentido="right",
            cota_vaos="top",
            cota_b="right",
        ),
    ]


def _posicionar_lances_espiral(escada: Escada) -> list[PosicaoLance]:
    """Fallback para exemplos com outras quantidades de lances."""
    posicoes: list[PosicaoLance] = []

    for i, lance in enumerate(escada.lances):
        pos_idx = i % 4
        L = lance.comprimento_total
        b = lance.b

        if pos_idx == 0:  # 9h
            if i == 0:
                x, y = 0.0, 0.0
            else:
                prev = posicoes[-1]
                x = prev.x
                y = prev.y - L
            w, h_rect = b, L
            sentido: Sentido = "up"
            cota_vaos: LadoCota = "left"
            cota_b: LadoCota = "bottom"
        elif pos_idx == 1:  # 12h
            prev = posicoes[-1]
            x = prev.x
            y = prev.y + prev.h
            w, h_rect = L, b
            sentido = "right"
            cota_vaos = "top"
            cota_b = "left"
        elif pos_idx == 2:  # 3h
            prev = posicoes[-1]
            x = prev.x + prev.w - b
            y = prev.y - L
            w, h_rect = b, L
            sentido = "down"
            cota_vaos = "right"
            cota_b = "bottom"
        else:  # 6h
            prev = posicoes[-1]
            x = prev.x - L
            y = prev.y - b
            w, h_rect = L, b
            sentido = "left"
            cota_vaos = "bottom"
            cota_b = "right"

        posicoes.append(
            PosicaoLance(
                lance.indice, x, y, w, h_rect, sentido, cota_vaos, cota_b
            )
        )

    return posicoes


def _ajustar_adjacencias_de_apoio(
    escada: Escada,
    posicoes: list[PosicaoLance],
) -> list[PosicaoLance]:
    """Encosta lances que apoiam em outros lances quando ha alinhamento claro."""
    por_indice = {p.indice: p for p in posicoes}

    for lance in escada.lances:
        pos = por_indice[lance.indice]
        refs = [
            apoio.referencia_lance
            for apoio in lance.apoios
            if apoio.tipo == "lance" and apoio.referencia_lance is not None
        ]
        for ref in refs:
            alvo = por_indice[ref]
            if pos.sentido in ("up", "down") and alvo.sentido in ("right", "left"):
                pos.y = alvo.y - pos.h
                if pos.x + pos.w > alvo.x + alvo.w:
                    pos.x = alvo.x + alvo.w - pos.w
                elif pos.x < alvo.x:
                    pos.x = alvo.x
            elif pos.sentido in ("right", "left") and alvo.sentido in ("up", "down"):
                if pos.sentido == "left" and alvo.sentido == "down":
                    pos.x = alvo.x - pos.w
                    pos.y = alvo.y - pos.h
                    continue
                pos.x = alvo.x + alvo.w
                if pos.y + pos.h > alvo.y + alvo.h:
                    pos.y = alvo.y + alvo.h - pos.h
                elif pos.y < alvo.y:
                    pos.y = alvo.y

    return posicoes


# ---- Helpers de cotagem ------------------------------------------------

_COTA_LW = 0.75
_EXTENSAO_LW = 0.55


def _cota_horizontal(ax, x1: float, x2: float,
                     y_obj: float, y_dim: float,
                     label: str, fontsize: float = 7) -> None:
    """Cota horizontal entre x1 e x2, com chamadas ate o objeto."""
    if x1 > x2:
        x1, x2 = x2, x1
    distancia = abs(y_dim - y_obj)
    lado = 1 if y_dim >= y_obj else -1
    sobra = max(0.025, distancia * 0.08)
    tick = max(0.045, distancia * 0.12)
    y_ext = y_dim + lado * sobra

    ax.plot([x1, x1], [y_obj, y_ext], color="black", linewidth=_EXTENSAO_LW)
    ax.plot([x2, x2], [y_obj, y_ext], color="black", linewidth=_EXTENSAO_LW)
    ax.plot([x1, x2], [y_dim, y_dim], color="black", linewidth=_COTA_LW)
    ax.plot([x1, x1], [y_dim - tick / 2, y_dim + tick / 2],
            color="black", linewidth=_COTA_LW)
    ax.plot([x2, x2], [y_dim - tick / 2, y_dim + tick / 2],
            color="black", linewidth=_COTA_LW)

    label_gap = max(0.035, tick * 0.75)
    ax.text((x1 + x2) / 2, y_dim + lado * label_gap,
            label, ha="center",
            va="bottom" if lado > 0 else "top",
            fontsize=fontsize,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.0))


def _cota_vertical(ax, y1: float, y2: float,
                   x_obj: float, x_dim: float,
                   label: str, fontsize: float = 7) -> None:
    """Cota vertical entre y1 e y2, com chamadas ate o objeto."""
    if y1 > y2:
        y1, y2 = y2, y1
    distancia = abs(x_dim - x_obj)
    lado = 1 if x_dim >= x_obj else -1
    sobra = max(0.025, distancia * 0.08)
    tick = max(0.045, distancia * 0.12)
    x_ext = x_dim + lado * sobra

    ax.plot([x_obj, x_ext], [y1, y1], color="black", linewidth=_EXTENSAO_LW)
    ax.plot([x_obj, x_ext], [y2, y2], color="black", linewidth=_EXTENSAO_LW)
    ax.plot([x_dim, x_dim], [y1, y2], color="black", linewidth=_COTA_LW)
    ax.plot([x_dim - tick / 2, x_dim + tick / 2], [y1, y1],
            color="black", linewidth=_COTA_LW)
    ax.plot([x_dim - tick / 2, x_dim + tick / 2], [y2, y2],
            color="black", linewidth=_COTA_LW)

    label_gap = max(0.035, tick * 0.75)
    ax.text(x_dim + lado * label_gap, (y1 + y2) / 2,
            label, ha="left" if lado > 0 else "right", va="center",
            rotation=90, fontsize=fontsize,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.0))


# ---- Helpers de divis\u00e3o de v\u00e3os --------------------------------------

def _linha_divisor(pos: PosicaoLance, offset: float) -> tuple[float, float, float, float]:
    """Coordenadas (x0, x1, y0, y1) da linha s\u00f3lida que separa dois v\u00e3os."""
    if pos.sentido == "up":
        y = pos.y + offset
        return pos.x, pos.x + pos.w, y, y
    if pos.sentido == "right":
        x = pos.x + offset
        return x, x, pos.y, pos.y + pos.h
    if pos.sentido == "down":
        y = pos.y + pos.h - offset
        return pos.x, pos.x + pos.w, y, y
    # left
    x = pos.x + pos.w - offset
    return x, x, pos.y, pos.y + pos.h


def _retangulo_vao(pos: PosicaoLance, inicio: float, comprimento: float) -> tuple[float, float, float, float]:
    """Retorna x, y, w, h do trecho de um vao dentro do lance."""
    if pos.sentido == "up":
        return pos.x, pos.y + inicio, pos.w, comprimento
    if pos.sentido == "right":
        return pos.x + inicio, pos.y, comprimento, pos.h
    if pos.sentido == "down":
        return pos.x, pos.y + pos.h - inicio - comprimento, pos.w, comprimento
    return pos.x + pos.w - inicio - comprimento, pos.y, comprimento, pos.h


def _hachurar_vao(ax, pos: PosicaoLance, inicio: float, comprimento: float) -> None:
    """Hachura simples para vaos do tipo escada."""
    x, y, w, h = _retangulo_vao(pos, inicio, comprimento)
    passo = max(0.12, min(w, h) * 0.22)
    margem = min(w, h) * 0.10

    if pos.sentido in ("up", "down"):
        yy = y + margem
        while yy < y + h - margem:
            ax.plot(
                [x + margem, x + w - margem],
                [yy, min(yy + passo * 0.65, y + h - margem)],
                color="black",
                linestyle="-",
                linewidth=0.45,
                alpha=0.75,
            )
            yy += passo
    else:
        xx = x + margem
        while xx < x + w - margem:
            ax.plot(
                [xx, min(xx + passo * 0.65, x + w - margem)],
                [y + margem, y + h - margem],
                color="black",
                linestyle="-",
                linewidth=0.45,
                alpha=0.75,
            )
            xx += passo


# ---- R\u00f3tulos -------------------------------------------------------------

def _subscrito(n: int) -> str:
    digitos = "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089"
    return "".join(digitos[int(d)] for d in str(n))


def _fmt_metros(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def _label_vao(lance_idx: int, vao_idx: int, L: float) -> str:
    return (
        f"L{_subscrito(lance_idx)}\u208B{_subscrito(vao_idx)} = "
        f"{_fmt_metros(L)}"
    )


def _label_b(lance_idx: int, b: float) -> str:
    return f"b{_subscrito(lance_idx)} = {_fmt_metros(b)}"


# ---- Cotagens dos v\u00e3os e da largura b ----------------------------------

def _cotar_vaos(ax, lance: Lance, pos: PosicaoLance, offset: float) -> None:
    """Coloca uma cota para cada vao no lado externo definido pelo layout."""
    if pos.sentido in ("up", "down"):
        lado = pos.cota_vaos if pos.cota_vaos in ("left", "right") else "left"
        x_obj = pos.x if lado == "left" else pos.x + pos.w
        x_dim = x_obj - offset if lado == "left" else x_obj + offset
        acumulado = 0.0
        for j, v in enumerate(lance.vaos):
            if pos.sentido == "up":
                y1 = pos.y + acumulado
                y2 = y1 + v.L
            else:
                y2 = pos.y + pos.h - acumulado
                y1 = y2 - v.L
            _cota_vertical(ax, y1, y2, x_obj, x_dim,
                           _label_vao(lance.indice, j + 1, v.L))
            acumulado += v.L
        return

    lado = pos.cota_vaos if pos.cota_vaos in ("top", "bottom") else "top"
    y_obj = pos.y + pos.h if lado == "top" else pos.y
    y_dim = y_obj + offset if lado == "top" else y_obj - offset
    acumulado = 0.0
    for j, v in enumerate(lance.vaos):
        if pos.sentido == "right":
            x1 = pos.x + acumulado
            x2 = x1 + v.L
        else:
            x2 = pos.x + pos.w - acumulado
            x1 = x2 - v.L
        _cota_horizontal(ax, x1, x2, y_obj, y_dim,
                         _label_vao(lance.indice, j + 1, v.L))
        acumulado += v.L


def _cotar_b(ax, lance: Lance, pos: PosicaoLance, offset: float) -> None:
    """Cota a largura b, perpendicular a direcao dos vaos."""
    b_offset = offset * 0.55

    if pos.sentido in ("up", "down"):
        lado = pos.cota_b if pos.cota_b in ("top", "bottom") else "bottom"
        y_obj = pos.y + pos.h if lado == "top" else pos.y
        y_dim = y_obj + b_offset if lado == "top" else y_obj - b_offset
        _cota_horizontal(ax, pos.x, pos.x + pos.w, y_obj, y_dim,
                         _label_b(lance.indice, lance.b))
        return

    lado = pos.cota_b if pos.cota_b in ("left", "right") else "right"
    x_obj = pos.x if lado == "left" else pos.x + pos.w
    x_dim = x_obj - b_offset if lado == "left" else x_obj + b_offset
    _cota_vertical(ax, pos.y, pos.y + pos.h, x_obj, x_dim,
                   _label_b(lance.indice, lance.b))


# ---- Lance individual ---------------------------------------------------

def _desenhar_lance(ax, lance: Lance, pos: PosicaoLance) -> None:
    # Ret\u00e2ngulo externo
    ax.add_patch(
        Rectangle(
            (pos.x, pos.y), pos.w, pos.h,
            fill=False, edgecolor="black", linewidth=1.5,
        )
    )

    # Divisores entre v\u00e3os: linhas s\u00f3lidas
    if len(lance.vaos) > 1:
        offset = 0.0
        for vao in lance.vaos[:-1]:
            offset += vao.L
            x0, x1, y0, y1 = _linha_divisor(pos, offset)
            ax.plot([x0, x1], [y0, y1],
                    color="black", linestyle="-", linewidth=1.0)

    offset = 0.0
    for vao in lance.vaos:
        if vao.tipo == "escada":
            _hachurar_vao(ax, pos, offset, vao.L)
        offset += vao.L

    # N\u00famero do lance no CENTRO do ret\u00e2ngulo
    cx = pos.x + pos.w / 2.0
    cy = pos.y + pos.h / 2.0
    ax.text(
        cx, cy, str(lance.indice),
        fontsize=11, ha="center", va="center",
        bbox=dict(boxstyle="circle,pad=0.35",
                  facecolor="white", edgecolor="black", linewidth=1.0),
        zorder=5,
    )


# ---- API p\u00fablica --------------------------------------------------------

def desenhar_escada(escada: Escada, ax=None, layout: LayoutDesenho = "horario"):
    """Renderiza a escada. Retorna a Figure matplotlib."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 10))
        ajustar_layout = True
    else:
        fig = ax.figure
        ajustar_layout = False

    posicoes = posicionar_lances(escada, layout=layout)

    # Bounding box dos ret\u00e2ngulos para dimensionar o offset das cotas
    xs = [p.x for p in posicoes] + [p.x + p.w for p in posicoes]
    ys = [p.y for p in posicoes] + [p.y + p.h for p in posicoes]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    diagonal = max(xmax - xmin, ymax - ymin)
    cota_offset = diagonal * 0.12

    for lance, pos in zip(escada.lances, posicoes):
        _desenhar_lance(ax, lance, pos)
        _cotar_vaos(ax, lance, pos, cota_offset)
        _cotar_b(ax, lance, pos, cota_offset)

    # Margem extra para acomodar as cotas externas
    margem = diagonal * 0.30
    ax.set_xlim(xmin - margem, xmax + margem)
    ax.set_ylim(ymin - margem, ymax + margem)
    ax.set_aspect("equal")
    ax.axis("off")
    if ajustar_layout:
        fig.tight_layout()
    return fig
