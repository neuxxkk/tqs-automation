from __future__ import annotations

import pytest

from escada.calculos import calcular_escada, peso_proprio
from escada.defaults import entrada_padrao
from escada.domain import EntradaEscada, formatar_pavimento, validar_entrada


def test_peso_proprio_h_12cm():
    assert peso_proprio(12.0) == pytest.approx(0.300)


def test_calcular_escada_cargas_distribuidas_padrao():
    entrada = entrada_padrao()
    resultado = calcular_escada(entrada)

    assert resultado.peso_proprio_patamar_tf_m2 == pytest.approx(0.300)
    assert resultado.peso_proprio_escada_tf_m2 == pytest.approx(0.550)
    assert resultado.carga_total_patamar_tf_m2 == pytest.approx(0.650)
    assert resultado.carga_total_escada_tf_m2 == pytest.approx(0.900)


def test_defaults_pavimento_e_h_escada():
    entrada = entrada_padrao()

    assert entrada.laje_inicial == 1
    assert entrada.laje_final == 2
    assert formatar_pavimento(entrada.laje_inicial, entrada.laje_final) == "1ª laje - 2ª laje"
    assert entrada.espessura_escada_cm == pytest.approx(22.0)


def test_calcular_escada_usa_cp_ca_independentes():
    entrada = EntradaEscada(
        nome_projeto="Teste",
        laje_inicial=1,
        laje_final=2,
        espessura_patamar_cm=10.0,
        espessura_escada_cm=14.0,
        carga_permanente_patamar_tf_m2=0.20,
        carga_acidental_patamar_tf_m2=0.15,
        carga_permanente_escada_tf_m2=0.30,
        carga_acidental_escada_tf_m2=0.25,
    )

    resultado = calcular_escada(entrada)

    assert resultado.carga_total_patamar_tf_m2 == pytest.approx(0.600)
    assert resultado.carga_total_escada_tf_m2 == pytest.approx(0.900)


def test_validar_entrada_exige_nome_e_espessuras_positivas():
    entrada = EntradaEscada(
        nome_projeto="",
        laje_inicial=1,
        laje_final=2,
        espessura_patamar_cm=0.0,
        espessura_escada_cm=-1.0,
        carga_permanente_patamar_tf_m2=0.10,
        carga_acidental_patamar_tf_m2=0.25,
        carga_permanente_escada_tf_m2=0.10,
        carga_acidental_escada_tf_m2=0.25,
    )

    erros = validar_entrada(entrada)

    assert "Informe o nome do projeto." in erros
    assert "A espessura do patamar deve ser maior que zero." in erros
    assert "A espessura da escada deve ser maior que zero." in erros


def test_validar_entrada_exige_laje_final_maior_que_inicial():
    entrada = entrada_padrao()
    entrada.laje_final = entrada.laje_inicial

    erros = validar_entrada(entrada)

    assert "A laje final deve ser pelo menos uma unidade maior que a laje inicial." in erros
