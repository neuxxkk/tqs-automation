"""Valores-padr\u00e3o de exemplo (Ed. Metallo)."""
from __future__ import annotations

from .domain import Apoio, Edificio, Escada, Lance, Vao


def edificio_metallo() -> Edificio:
    return Edificio(
        nome="Sudoeste - Ed. Metallo",
        fck=35.0,
        cp=0.10,
        ca=0.25,
    )


def escada_metallo() -> Escada:
    """Exemplo did\u00e1tico de escada de 3 lances entre 1\u00aa e 2\u00aa laje.

    Apoios conforme especifica\u00e7\u00e3o:
        Lance 1: laje + lance 3
        Lance 2: pilar + viga
        Lance 3: laje + viga   (n\u00e3o especificado; valor plaus\u00edvel)
    """
    lance1 = Lance(
        indice=1,
        b=1.37,
        h=0.12,
        apoios=[
            Apoio(tipo="laje"),
            Apoio(tipo="lance", referencia_lance=3),
        ],
        vaos=[Vao(tipo="escada", L=0.55)],
    )
    lance2 = Lance(
        indice=2,
        b=1.215,
        h=0.12,
        apoios=[
            Apoio(tipo="pilar"),
            Apoio(tipo="viga"),
        ],
        vaos=[
            Vao(tipo="patamar", L=1.255),
            Vao(tipo="escada", L=1.375),
            Vao(tipo="patamar", L=1.250),
        ],
    )
    lance3 = Lance(
        indice=3,
        b=1.37,
        h=0.12,
        apoios=[
            Apoio(tipo="laje"),
            Apoio(tipo="viga"),
        ],
        vaos=[Vao(tipo="escada", L=1.375)],
    )
    return Escada(laje_inicial=1, laje_final=2, lances=[lance1, lance2, lance3])
