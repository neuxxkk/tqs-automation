"""C\u00e1lculo de carregamentos de lances de escada.

Conven\u00e7\u00f5es (em tF/m\u00b2):
    PP        = 2,5 * h           (peso pr\u00f3prio do concreto, \u03b3 = 25 kN/m\u00b3)
    q_patamar = CP + CA + PP
    q_escada  = CP + CA + PP + DEGRAU
"""
from __future__ import annotations

from dataclasses import dataclass

from .domain import Edificio, Lance, Vao

# Carga adicional do degrau em vaos do tipo "escada" (tF/m\u00b2).
DEGRAU: float = 0.300


def peso_proprio(h: float) -> float:
    """PP = 2,5 * h, com h em metros, retorna tF/m\u00b2."""
    return 2.5 * h


def q_patamar(edificio: Edificio, h: float) -> float:
    return edificio.cp + edificio.ca + peso_proprio(h)


def q_escada(edificio: Edificio, h: float) -> float:
    return edificio.cp + edificio.ca + peso_proprio(h) + DEGRAU


def q_vao(edificio: Edificio, lance: Lance, vao: Vao) -> float:
    if vao.tipo == "patamar":
        return q_patamar(edificio, lance.h)
    if vao.tipo == "escada":
        return q_escada(edificio, lance.h)
    raise ValueError(f"Tipo de v\u00e3o desconhecido: {vao.tipo!r}")


@dataclass
class CarregamentoVao:
    indice: int            # 1-based dentro do lance
    tipo: str              # "patamar" ou "escada"
    L: float
    q: float               # tF/m\u00b2


@dataclass
class CarregamentoLance:
    indice: int            # 1-based
    h: float
    pp: float
    vaos: list[CarregamentoVao]


def carregamento_lance(edificio: Edificio, lance: Lance) -> CarregamentoLance:
    return CarregamentoLance(
        indice=lance.indice,
        h=lance.h,
        pp=peso_proprio(lance.h),
        vaos=[
            CarregamentoVao(
                indice=i + 1,
                tipo=v.tipo,
                L=v.L,
                q=q_vao(edificio, lance, v),
            )
            for i, v in enumerate(lance.vaos)
        ],
    )
