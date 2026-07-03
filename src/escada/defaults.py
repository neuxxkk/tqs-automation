from __future__ import annotations

from .domain import EntradaEscada


DEFAULT_PROJECT_NAME = "Sudoeste - Ed. Metallo"


def entrada_padrao() -> EntradaEscada:
    return EntradaEscada(
        nome_projeto=DEFAULT_PROJECT_NAME,
        laje_inicial=1,
        laje_final=2,
        espessura_patamar_cm=12.0,
        espessura_escada_cm=22.0,
        carga_permanente_patamar_tf_m2=0.10,
        carga_acidental_patamar_tf_m2=0.25,
        carga_permanente_escada_tf_m2=0.10,
        carga_acidental_escada_tf_m2=0.25,
    )
