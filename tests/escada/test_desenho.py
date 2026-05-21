"""Testes do m\u00f3dulo de desenho \u2014 posicionamento e smoke test de render."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sem GUI

import pytest

from escada.defaults import escada_metallo
from escada.desenho import (
    PosicaoLance,
    _validar_sem_sobreposicao,
    desenhar_escada,
    posicionar_lances,
)
from escada.domain import Apoio, Escada, Lance, Vao


# ---- Posicionamento -----------------------------------------------------

def test_posicionamento_lance_unico_na_origem():
    escada = Escada(
        laje_inicial=1, laje_final=2,
        lances=[
            Lance(
                indice=1, b=1.0, h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[Vao(tipo="patamar", L=2.0)],
            ),
        ],
    )
    pos = posicionar_lances(escada)
    assert len(pos) == 1
    assert pos[0].x == pytest.approx(0.0)
    assert pos[0].y == pytest.approx(0.0)
    assert pos[0].w == pytest.approx(1.0)  # b
    assert pos[0].h == pytest.approx(2.0)  # L_total
    assert pos[0].sentido == "up"


def test_posicionamento_2_lances_fica_empilhado_com_lance_1_embaixo():
    escada = Escada(
        laje_inicial=1,
        laje_final=2,
        lances=[
            Lance(
                indice=1,
                b=1.10,
                h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[Vao(tipo="patamar", L=1.50), Vao(tipo="escada", L=0.90)],
            ),
            Lance(
                indice=2,
                b=1.25,
                h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[Vao(tipo="patamar", L=2.20)],
            ),
        ],
    )

    p1, p2 = posicionar_lances(escada, layout="horario")

    assert p1.sentido == "right"
    assert p2.sentido == "right"
    assert p1.x == pytest.approx(0.0)
    assert p2.x == pytest.approx(0.0)
    assert p1.y == pytest.approx(0.0)
    assert p2.y == pytest.approx(p1.y + p1.h)
    assert p1.h == pytest.approx(1.10)
    assert p2.h == pytest.approx(1.25)
    assert p1.cota_vaos == "bottom"
    assert p2.cota_vaos == "top"
    assert p1.cota_b == "left"
    assert p2.cota_b == "right"


def test_posicionamento_metallo_3_lances():
    """Croqui do anexo: 2 embaixo/esquerda, 1 embaixo/direita, 3 em cima."""
    escada = escada_metallo()
    pos = posicionar_lances(escada, layout="croqui")

    p1, p2, p3 = pos

    # Lance 3 e a faixa superior horizontal, subdividida pelos seus vaos.
    assert p3.x == pytest.approx(0.0)
    assert p3.y == pytest.approx(max(p1.h, p2.h))
    assert p3.w == pytest.approx(1.375)
    assert p3.h == pytest.approx(1.250)             # b3 = L2,3
    assert p3.sentido == "right"

    # Lance 2 fica pendurado na esquerda da faixa superior.
    assert p2.x == pytest.approx(0.0)
    assert p2.y + p2.h == pytest.approx(p3.y)
    assert p2.w == pytest.approx(1.215)
    assert p2.h == pytest.approx(3.88)

    # Lance 1 fica pendurado na direita da faixa superior.
    assert p1.x + p1.w == pytest.approx(p3.x + p3.w)
    assert p1.y + p1.h == pytest.approx(p3.y)
    assert p1.w == pytest.approx(1.255)             # b1 = L2,1
    assert p1.h == pytest.approx(0.55)
    assert p1.sentido == "up"

    # As cotas ficam nos mesmos lados do croqui.
    assert p1.cota_vaos == "right"
    assert p2.cota_vaos == "left"
    assert p3.cota_vaos == "top"


def test_posicionamento_metallo_pode_forcar_layout_horario():
    escada = escada_metallo()
    p1, p2, p3 = posicionar_lances(escada, layout="horario")

    assert p1.x == pytest.approx(0.0)
    assert p1.y == pytest.approx(0.0)
    assert p1.sentido == "up"
    assert p2.x == pytest.approx(p1.x)
    assert p2.y == pytest.approx(p1.y + p1.h)
    assert p2.sentido == "right"
    assert p3.x + p3.w == pytest.approx(p2.x + p2.w)
    assert p3.y + p3.h == pytest.approx(p2.y)
    assert p3.sentido == "down"
    assert p3.cota_b == "bottom"


def test_lances_adjacentes_compartilham_borda_com_lance_superior():
    """Os lances inferiores encostam no lance 3 sem invadir sua area."""
    escada = escada_metallo()
    p1, p2, p3 = posicionar_lances(escada, layout="croqui")

    assert p2.y + p2.h == pytest.approx(p3.y)
    assert p1.y + p1.h == pytest.approx(p3.y)
    assert p2.x == pytest.approx(p3.x)
    assert p1.x + p1.w == pytest.approx(p3.x + p3.w)


def test_lances_metallo_nao_sobrepoem_area():
    escada = escada_metallo()
    pos = posicionar_lances(escada, layout="horario")

    for i, a in enumerate(pos):
        for b in pos[i + 1:]:
            x_overlap = max(0.0, min(a.x + a.w, b.x + b.w) - max(a.x, b.x))
            y_overlap = max(0.0, min(a.y + a.h, b.y + b.h) - max(a.y, b.y))
            assert x_overlap * y_overlap == pytest.approx(0.0)


def test_quarto_lance_apoia_no_terceiro_abaixo_e_a_esquerda():
    escada3 = escada_metallo()
    escada = Escada(
        laje_inicial=1,
        laje_final=2,
        lances=[
            *escada3.lances,
            Lance(
                indice=4,
                b=1.20,
                h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="lance", referencia_lance=3)],
                vaos=[Vao(tipo="patamar", L=2.00)],
            ),
        ],
    )

    pos = posicionar_lances(escada, layout="horario")
    p3 = pos[2]
    p4 = pos[3]

    assert p4.sentido == "left"
    assert p4.x + p4.w == pytest.approx(p3.x)
    assert p4.y + p4.h == pytest.approx(p3.y)

    for i, a in enumerate(pos):
        for b in pos[i + 1:]:
            x_overlap = max(0.0, min(a.x + a.w, b.x + b.w) - max(a.x, b.x))
            y_overlap = max(0.0, min(a.y + a.h, b.y + b.h) - max(a.y, b.y))
            assert x_overlap * y_overlap == pytest.approx(0.0)


def test_espiral_com_quatro_lances_desiguais_nao_se_sobrepoe():
    escada = Escada(
        laje_inicial=1,
        laje_final=2,
        lances=[
            Lance(
                indice=1,
                b=1.37,
                h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[Vao(tipo="escada", L=0.55), Vao(tipo="patamar", L=1.95)],
            ),
            Lance(
                indice=2,
                b=1.215,
                h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[
                    Vao(tipo="patamar", L=1.255),
                    Vao(tipo="escada", L=1.375),
                    Vao(tipo="patamar", L=1.250),
                ],
            ),
            Lance(
                indice=3,
                b=1.37,
                h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[Vao(tipo="escada", L=1.375)],
            ),
            Lance(
                indice=4,
                b=1.20,
                h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[Vao(tipo="patamar", L=2.00)],
            ),
        ],
    )

    posicoes = posicionar_lances(escada, layout="horario")

    for i, a in enumerate(posicoes):
        for b in posicoes[i + 1:]:
            x_overlap = max(0.0, min(a.x + a.w, b.x + b.w) - max(a.x, b.x))
            y_overlap = max(0.0, min(a.y + a.h, b.y + b.h) - max(a.y, b.y))
            assert x_overlap * y_overlap == pytest.approx(0.0)


def test_validacao_bloqueia_lances_sobrepostos():
    with pytest.raises(ValueError, match="se sobrepoem"):
        _validar_sem_sobreposicao(
            [
                PosicaoLance(1, 0.0, 0.0, 2.0, 1.0, "right", "top", "left"),
                PosicaoLance(2, 1.0, 0.0, 2.0, 1.0, "right", "top", "right"),
            ]
        )


def test_lance_que_apoia_em_outro_encosta_no_lance_referenciado():
    escada = escada_metallo()
    p1, _, p3 = posicionar_lances(escada, layout="croqui")

    assert p1.y + p1.h == pytest.approx(p3.y)
    assert p3.x <= p1.x <= p3.x + p3.w


def test_hachura_aparece_apenas_em_vao_escada():
    escada_sem_escada = Escada(
        laje_inicial=1, laje_final=2,
        lances=[
            Lance(
                indice=1, b=1.20, h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[Vao(tipo="patamar", L=2.0)],
            ),
        ],
    )
    escada_com_escada = Escada(
        laje_inicial=1, laje_final=2,
        lances=[
            Lance(
                indice=1, b=1.20, h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[Vao(tipo="escada", L=2.0)],
            ),
        ],
    )

    fig_sem = desenhar_escada(escada_sem_escada)
    fig_com = desenhar_escada(escada_com_escada)

    assert len(fig_com.axes[0].lines) > len(fig_sem.axes[0].lines)


# ---- Smoke test de render -----------------------------------------------

def test_render_metallo_gera_png(tmp_path: Path):
    fig = desenhar_escada(escada_metallo())
    out = tmp_path / "metallo.png"
    fig.savefig(out, dpi=120)
    assert out.exists()
    assert out.stat().st_size > 1000  # PNG n\u00e3o-trivial


def test_render_4_lances_nao_falha(tmp_path: Path):
    """Cobre as 4 posi\u00e7\u00f5es da espiral (9h, 12h, 3h, 6h)."""
    escada = Escada(
        laje_inicial=1, laje_final=2,
        lances=[
            Lance(
                indice=i, b=1.20, h=0.12,
                apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
                vaos=[Vao(tipo="patamar", L=2.0)],
            )
            for i in range(1, 5)
        ],
    )
    fig = desenhar_escada(escada)
    out = tmp_path / "quatro.png"
    fig.savefig(out, dpi=120)
    assert out.exists()
