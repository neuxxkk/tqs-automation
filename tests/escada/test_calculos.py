"""Valida\u00e7\u00e3o num\u00e9rica do exemplo Ed. Metallo (h=12cm)."""
from __future__ import annotations

import pytest

from escada.calculos import (
    DEGRAU,
    carregamento_lance,
    peso_proprio,
    q_escada,
    q_patamar,
    q_vao,
)
from escada.defaults import edificio_metallo, escada_metallo
from escada.domain import Apoio, Edificio, Escada, Lance, Vao


# ---- Constantes ---------------------------------------------------------

def test_degrau_constante():
    assert DEGRAU == pytest.approx(0.300)


# ---- F\u00f3rmulas b\u00e1sicas ----------------------------------------------------

def test_peso_proprio_h_12cm():
    assert peso_proprio(0.12) == pytest.approx(0.300)


def test_q_patamar_metallo():
    ed = edificio_metallo()
    # CP=0,10 + CA=0,25 + PP=0,300 = 0,650
    assert q_patamar(ed, 0.12) == pytest.approx(0.650)


def test_q_escada_metallo():
    ed = edificio_metallo()
    # 0,650 + 0,300 (degrau) = 0,950
    assert q_escada(ed, 0.12) == pytest.approx(0.950)


# ---- q_vao despacha pelo tipo ------------------------------------------

def test_q_vao_patamar():
    ed = edificio_metallo()
    lance = Lance(
        indice=1, b=1.20, h=0.12,
        apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
        vaos=[Vao(tipo="patamar", L=1.0)],
    )
    assert q_vao(ed, lance, lance.vaos[0]) == pytest.approx(0.650)


def test_q_vao_escada():
    ed = edificio_metallo()
    lance = Lance(
        indice=1, b=1.20, h=0.12,
        apoios=[Apoio(tipo="laje"), Apoio(tipo="viga")],
        vaos=[Vao(tipo="escada", L=1.0)],
    )
    assert q_vao(ed, lance, lance.vaos[0]) == pytest.approx(0.950)


# ---- carregamento_lance agrega tudo ------------------------------------

def test_carregamento_lance2_metallo_tres_vaos():
    ed = edificio_metallo()
    escada = escada_metallo()
    lance2 = escada.lances[1]
    carga = carregamento_lance(ed, lance2)

    assert carga.indice == 2
    assert carga.h == pytest.approx(0.12)
    assert carga.pp == pytest.approx(0.300)
    assert len(carga.vaos) == 3
    assert carga.vaos[0].tipo == "patamar"
    assert carga.vaos[0].q == pytest.approx(0.650)
    assert carga.vaos[1].tipo == "escada"
    assert carga.vaos[1].q == pytest.approx(0.950)
    assert carga.vaos[2].tipo == "patamar"
    assert carga.vaos[2].q == pytest.approx(0.650)


# ---- Valida\u00e7\u00f5es de dom\u00ednio ---------------------------------------------

def test_apoio_lance_exige_referencia():
    with pytest.raises(ValueError, match="referencia_lance"):
        Apoio(tipo="lance")


def test_apoio_nao_lance_nao_aceita_referencia():
    with pytest.raises(ValueError, match="n\u00e3o deve ter referencia_lance"):
        Apoio(tipo="laje", referencia_lance=2)


def test_lance_exige_dois_apoios():
    with pytest.raises(ValueError, match="exatamente 2 apoios"):
        Lance(
            indice=1, b=1.0, h=0.12,
            apoios=[Apoio(tipo="laje")],
            vaos=[Vao(tipo="patamar", L=1.0)],
        )


def test_lance_nao_pode_apoiar_em_si_mesmo():
    with pytest.raises(ValueError, match="apoiar em si mesmo"):
        Escada(
            laje_inicial=1, laje_final=2,
            lances=[
                Lance(
                    indice=1, b=1.0, h=0.12,
                    apoios=[Apoio(tipo="laje"), Apoio(tipo="lance", referencia_lance=1)],
                    vaos=[Vao(tipo="patamar", L=1.0)],
                ),
            ],
        )


def test_apoia_em_lance_property():
    escada = escada_metallo()
    assert escada.lances[0].apoia_em_lance is True   # lance 1 apoia em lance 3
    assert escada.lances[1].apoia_em_lance is False  # lance 2: pilar+viga
    assert escada.lances[2].apoia_em_lance is False  # lance 3: laje+viga


def test_comprimento_total():
    escada = escada_metallo()
    # lance 2: 1,255 + 1,375 + 1,250 = 3,880
    assert escada.lances[1].comprimento_total == pytest.approx(3.88)
