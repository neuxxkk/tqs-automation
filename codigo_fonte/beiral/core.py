from __future__ import annotations

import re
from dataclasses import dataclass

PESO_ESPECIFICO_CONCRETO_TF_M3 = 2.5
PESO_ESPECIFICO_ALVENARIA_TF_M3 = 1.3


@dataclass(slots=True)
class EntradaBeiral:
    nome_projeto: str
    espessura_cm: float
    largura_cm: float
    carga_permanente_tf_m2: float
    carga_acidental_tf_m2: float
    possui_nervura_borda: bool
    espessura_nervura_cm: float = 0.0
    altura_nervura_cm: float = 0.0
    possui_guarda_corpo: bool = False
    espessura_alvenaria_cm: float = 0.0
    altura_alvenaria_cm: float = 0.0
    armacao_minima_bitola_mm: float = 0.0
    armacao_minima_espacamento_cm: float = 0.0


@dataclass(slots=True)
class ResultadoBeiral:
    espessura_m: float
    largura_m: float
    peso_proprio_laje_tf_m2: float
    carga_total_q_tf_m2: float
    peso_proprio_nervura_tf_m: float
    carga_alvenaria_tf_m: float
    carga_total_p_tf_m: float
    momento_distribuido_tf_m: float
    momento_concentrado_tf_m: float
    momento_total_tf_m: float
    majorador: float
    msk_tf_m: float
    possui_carga_concentrada: bool


def validar_entrada(entrada: EntradaBeiral) -> list[str]:
    erros: list[str] = []

    if not entrada.nome_projeto.strip():
        erros.append("Informe o nome do projeto.")

    if entrada.espessura_cm <= 0:
        erros.append("A espessura do beiral deve ser maior que zero.")

    if entrada.largura_cm <= 0:
        erros.append("A largura do beiral deve ser maior que zero.")

    if entrada.carga_permanente_tf_m2 < 0:
        erros.append("A carga permanente nao pode ser negativa.")

    if entrada.carga_acidental_tf_m2 < 0:
        erros.append("A carga acidental nao pode ser negativa.")

    if entrada.possui_nervura_borda:
        if entrada.espessura_nervura_cm <= 0:
            erros.append("A espessura da nervura deve ser maior que zero.")
        if entrada.altura_nervura_cm <= 0:
            erros.append("A altura da nervura deve ser maior que zero.")

    if entrada.possui_guarda_corpo:
        if entrada.espessura_alvenaria_cm <= 0:
            erros.append("A espessura da alvenaria deve ser maior que zero.")
        if entrada.altura_alvenaria_cm <= 0:
            erros.append("A altura da alvenaria deve ser maior que zero.")

    if entrada.armacao_minima_bitola_mm < 0:
        erros.append("A bitola da armacao minima nao pode ser negativa.")

    if entrada.armacao_minima_espacamento_cm < 0:
        erros.append("O espacamento da armacao minima nao pode ser negativo.")

    return erros


def calcular_beiral(entrada: EntradaBeiral) -> ResultadoBeiral:
    espessura_m = entrada.espessura_cm / 100.0
    largura_m = entrada.largura_cm / 100.0

    peso_proprio_laje = PESO_ESPECIFICO_CONCRETO_TF_M3 * espessura_m
    carga_total_q = (
        entrada.carga_permanente_tf_m2
        + entrada.carga_acidental_tf_m2
        + peso_proprio_laje
    )

    esp_nervura = entrada.espessura_nervura_cm if entrada.possui_nervura_borda else 0.0
    alt_nervura = entrada.altura_nervura_cm if entrada.possui_nervura_borda else 0.0
    esp_alvenaria = entrada.espessura_alvenaria_cm if entrada.possui_guarda_corpo else 0.0
    alt_alvenaria = entrada.altura_alvenaria_cm if entrada.possui_guarda_corpo else 0.0
    carga_alvenaria = (
        (esp_alvenaria / 100.0)
        * (alt_alvenaria / 100.0)
        * PESO_ESPECIFICO_ALVENARIA_TF_M3
    )

    peso_proprio_nervura = (
        (esp_nervura / 100.0) * (alt_nervura / 100.0) * PESO_ESPECIFICO_CONCRETO_TF_M3
    )
    carga_total_p = peso_proprio_nervura + carga_alvenaria

    momento_distribuido = carga_total_q * largura_m * (largura_m / 2.0)
    momento_concentrado = carga_total_p * largura_m
    momento_total = momento_distribuido + momento_concentrado

    majorador = 1.95 - (0.05 * entrada.espessura_cm)
    msk = momento_total * majorador

    return ResultadoBeiral(
        espessura_m=espessura_m,
        largura_m=largura_m,
        peso_proprio_laje_tf_m2=peso_proprio_laje,
        carga_total_q_tf_m2=carga_total_q,
        peso_proprio_nervura_tf_m=peso_proprio_nervura,
        carga_alvenaria_tf_m=carga_alvenaria,
        carga_total_p_tf_m=carga_total_p,
        momento_distribuido_tf_m=momento_distribuido,
        momento_concentrado_tf_m=momento_concentrado,
        momento_total_tf_m=momento_total,
        majorador=majorador,
        msk_tf_m=msk,
        possui_carga_concentrada=carga_total_p > 0,
    )


def sanitize_filename_component(value: str) -> str:
    cleaned = re.sub(r"\s+", "_", value.strip())
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "", cleaned)
    return cleaned or "beiral"
