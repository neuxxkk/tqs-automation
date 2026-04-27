from .core import (
    EntradaBeiral,
    ResultadoBeiral,
    calcular_beiral,
    sanitize_filename_component,
    validar_entrada,
)


def __getattr__(name: str):
    if name == "draw_beiral_svg":
        from .draw import draw_beiral_svg

        return draw_beiral_svg
    if name in {"gerar_pdf_relatorio", "pdf_disponivel"}:
        from .pdf import gerar_pdf_relatorio, pdf_disponivel

        return {
            "gerar_pdf_relatorio": gerar_pdf_relatorio,
            "pdf_disponivel": pdf_disponivel,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "EntradaBeiral",
    "ResultadoBeiral",
    "calcular_beiral",
    "sanitize_filename_component",
    "validar_entrada",
    "draw_beiral_svg",
    "gerar_pdf_relatorio",
    "pdf_disponivel",
]
