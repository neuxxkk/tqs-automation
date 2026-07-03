from __future__ import annotations

from escada.calculos import calcular_escada
from escada.defaults import entrada_padrao
from escada.memoria import gerar_pdf_relatorio, pdf_disponivel


def test_pdf_disponivel():
    assert pdf_disponivel() is True


def test_pdf_gera_bytes_pdf_sem_imagem():
    entrada = entrada_padrao()
    resultado = calcular_escada(entrada)

    pdf = gerar_pdf_relatorio(entrada, resultado)

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_pdf_aceita_imagem_png_minima():
    entrada = entrada_padrao()
    resultado = calcular_escada(entrada)
    png_1x1 = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
        b"\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
        b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    pdf = gerar_pdf_relatorio(entrada, resultado, png_1x1, "image/png")

    assert pdf.startswith(b"%PDF")
