from __future__ import annotations

import re

from escada.defaults import edificio_metallo, escada_metallo
from escada.memoria import gerar_memoria_markdown, gerar_memoria_pdf


def test_memoria_markdown_contem_dados_principais():
    memoria = gerar_memoria_markdown(edificio_metallo(), escada_metallo())

    assert "# Memória de cálculo da 1ª à 2ª laje - Sudoeste - Ed. Metallo" in memoria
    assert "PP₁ = 2,5 × 0,120 = 0,300 tF·m⁻²" in memoria
    assert "q₃,₁ = 0,100 + 0,250 + PP₃ + 0,300 = 0,950" in memoria
    assert "tF/m2" not in memoria
    assert " * " not in memoria
    assert "Observação" not in memoria
    assert "## Dados de entrada" not in memoria
    assert "## Geometria e apoios" not in memoria
    assert "## Fórmulas adotadas" not in memoria
    assert "| 3 | 1 | escada | 1,375 | 0,300 | 0,950 |" in memoria


def test_memoria_markdown_tem_mesma_ordem_do_pdf():
    memoria = gerar_memoria_markdown(edificio_metallo(), escada_metallo())

    assert memoria.index("# Memória de cálculo") < memoria.index("## Carregamentos")
    assert memoria.index("## Carregamentos") < memoria.index("## Desenvolvimento dos cálculos")


def test_memoria_pdf_gera_bytes_pdf():
    pdf = gerar_memoria_pdf(edificio_metallo(), escada_metallo())

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
    assert len(re.findall(rb"/Type\s*/Page\b", pdf)) == 1


def test_tabela_carregamentos_markdown_nao_e_interrompida():
    memoria = gerar_memoria_markdown(edificio_metallo(), escada_metallo())
    trecho = memoria.split("## Carregamentos", maxsplit=1)[1]
    tabela, _detalhe = trecho.split("## Desenvolvimento dos cálculos", maxsplit=1)
    linhas_tabela = [linha for linha in tabela.splitlines() if linha.startswith("|")]

    assert len(linhas_tabela) >= 3
    assert all(linha.count("|") == linhas_tabela[0].count("|") for linha in linhas_tabela)
