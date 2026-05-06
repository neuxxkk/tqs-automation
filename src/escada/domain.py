"""Modelo de dom\u00ednio do c\u00e1lculo de escadas."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


TipoApoio = Literal["laje", "viga", "pilar", "lance"]
TipoVao = Literal["patamar", "escada"]


@dataclass
class Edificio:
    nome: str
    fck: float        # MPa
    cp: float         # tF/m\u00b2 - carga permanente
    ca: float         # tF/m\u00b2 - carga acidental


@dataclass
class Apoio:
    tipo: TipoApoio
    # Quando tipo == "lance", refer\u00eancia 1-based ao lance que serve de apoio.
    referencia_lance: Optional[int] = None

    def __post_init__(self) -> None:
        if self.tipo == "lance" and self.referencia_lance is None:
            raise ValueError("Apoio do tipo 'lance' exige referencia_lance.")
        if self.tipo != "lance" and self.referencia_lance is not None:
            raise ValueError(
                f"Apoio do tipo '{self.tipo}' n\u00e3o deve ter referencia_lance."
            )


@dataclass
class Vao:
    tipo: TipoVao
    L: float          # comprimento em metros


@dataclass
class Lance:
    indice: int                   # 1-based
    b: float                      # largura (m)
    h: float                      # altura da laje (m)
    apoios: list[Apoio]           # exatamente 2
    vaos: list[Vao] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.apoios) != 2:
            raise ValueError(
                f"Lance {self.indice}: deve ter exatamente 2 apoios "
                f"(recebido {len(self.apoios)})."
            )
        if not self.vaos:
            raise ValueError(f"Lance {self.indice}: deve ter pelo menos 1 v\u00e3o.")

    @property
    def comprimento_total(self) -> float:
        return sum(v.L for v in self.vaos)

    @property
    def apoia_em_lance(self) -> bool:
        """True se algum dos apoios deste lance \u00e9 outro lance."""
        return any(a.tipo == "lance" for a in self.apoios)


@dataclass
class Escada:
    laje_inicial: int             # ex.: 1 (1\u00aa laje)
    laje_final: int               # ex.: 2 (2\u00aa laje)
    lances: list[Lance]

    def __post_init__(self) -> None:
        if not self.lances:
            raise ValueError("Escada deve ter pelo menos 1 lance.")
        indices = [l.indice for l in self.lances]
        if indices != list(range(1, len(self.lances) + 1)):
            raise ValueError(
                f"Lances devem ter \u00edndices sequenciais 1..N (recebido {indices})."
            )
        # Valida refer\u00eancias de apoios em lances.
        n = len(self.lances)
        for lance in self.lances:
            for apoio in lance.apoios:
                if apoio.tipo == "lance":
                    ref = apoio.referencia_lance
                    if ref == lance.indice:
                        raise ValueError(
                            f"Lance {lance.indice} n\u00e3o pode apoiar em si mesmo."
                        )
                    if not (1 <= (ref or 0) <= n):
                        raise ValueError(
                            f"Lance {lance.indice}: refer\u00eancia de apoio "
                            f"{ref} fora do intervalo 1..{n}."
                        )

    @property
    def n_lances(self) -> int:
        return len(self.lances)
