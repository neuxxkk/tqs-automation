from __future__ import annotations

import re
from dataclasses import dataclass


PESO_ESPECIFICO_CONCRETO_TF_M3 = 2.5


@dataclass(slots=True)
class EntradaEscada:
    """
    Dados de entrada para o memorial simplificado de carregamentos de escada.
    """
    nome_projeto: str
    laje_inicial: int
    laje_final: int
    espessura_patamar_cm: float
    espessura_escada_cm: float
    carga_permanente_patamar_tf_m2: float
    carga_acidental_patamar_tf_m2: float
    carga_permanente_escada_tf_m2: float
    carga_acidental_escada_tf_m2: float


@dataclass(slots=True)
class ResultadoEscada:
    espessura_patamar_m: float
    espessura_escada_m: float
    peso_proprio_patamar_tf_m2: float
    peso_proprio_escada_tf_m2: float
    carga_total_patamar_tf_m2: float
    carga_total_escada_tf_m2: float


def validar_entrada(entrada: EntradaEscada) -> list[str]:
    erros: list[str] = []

    if not entrada.nome_projeto.strip():
        erros.append("Informe o nome do projeto.")

    if entrada.laje_inicial < 0:
        erros.append("A laje inicial nao pode ser negativa.")

    if entrada.laje_final < 0:
        erros.append("A laje final nao pode ser negativa.")

    if entrada.laje_final <= entrada.laje_inicial:
        erros.append("A laje final deve ser pelo menos uma unidade maior que a laje inicial.")

    if entrada.espessura_patamar_cm <= 0:
        erros.append("A espessura do patamar deve ser maior que zero.")

    if entrada.espessura_escada_cm <= 0:
        erros.append("A espessura da escada deve ser maior que zero.")

    if entrada.carga_permanente_patamar_tf_m2 < 0:
        erros.append("A carga permanente do patamar nao pode ser negativa.")

    if entrada.carga_acidental_patamar_tf_m2 < 0:
        erros.append("A carga acidental do patamar nao pode ser negativa.")

    if entrada.carga_permanente_escada_tf_m2 < 0:
        erros.append("A carga permanente da escada nao pode ser negativa.")

    if entrada.carga_acidental_escada_tf_m2 < 0:
        erros.append("A carga acidental da escada nao pode ser negativa.")

    return erros


def sanitize_filename_component(value: str) -> str:
    cleaned = re.sub(r"\s+", "_", value.strip())
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "", cleaned)
    return cleaned or "escada"


def formatar_pavimento(laje_inicial: int, laje_final: int) -> str:
    return f"{laje_inicial}ª laje - {laje_final}ª laje"
