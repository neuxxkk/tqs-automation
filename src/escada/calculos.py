from __future__ import annotations

from .domain import (
    EntradaEscada,
    PESO_ESPECIFICO_CONCRETO_TF_M3,
    ResultadoEscada,
)


def peso_proprio(espessura_cm: float) -> float:
    return PESO_ESPECIFICO_CONCRETO_TF_M3 * (espessura_cm / 100.0)


def calcular_escada(entrada: EntradaEscada) -> ResultadoEscada:
    espessura_patamar_m = entrada.espessura_patamar_cm / 100.0
    espessura_escada_m = entrada.espessura_escada_cm / 100.0
    peso_proprio_patamar = peso_proprio(entrada.espessura_patamar_cm)
    peso_proprio_escada = peso_proprio(entrada.espessura_escada_cm)

    carga_total_patamar = (
        entrada.carga_permanente_patamar_tf_m2
        + entrada.carga_acidental_patamar_tf_m2
        + peso_proprio_patamar
    )
    carga_total_escada = (
        entrada.carga_permanente_escada_tf_m2
        + entrada.carga_acidental_escada_tf_m2
        + peso_proprio_escada
    )

    return ResultadoEscada(
        espessura_patamar_m=espessura_patamar_m,
        espessura_escada_m=espessura_escada_m,
        peso_proprio_patamar_tf_m2=peso_proprio_patamar,
        peso_proprio_escada_tf_m2=peso_proprio_escada,
        carga_total_patamar_tf_m2=carga_total_patamar,
        carga_total_escada_tf_m2=carga_total_escada,
    )
