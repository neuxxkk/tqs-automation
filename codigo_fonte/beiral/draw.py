from .core import ResultadoBeiral


def draw_beiral_svg(espessura_cm: float, largura_cm: float, tem_carga_p: bool) -> str:
    largura_m = largura_cm / 100.0

    svg = '<svg width="100%" height="250" viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '<path d="M 30 70 L 50 50 M 30 110 L 50 90 M 30 150 L 50 130 M 30 190 L 50 170" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="50" y1="50" x2="50" y2="200" stroke="black" stroke-width="2"/>\n'
    svg += '<rect x="50" y="100" width="200" height="35" fill="none" stroke="black" stroke-width="2"/>\n'
    svg += '<text x="25" y="85" font-family="sans-serif" font-size="18" font-weight="bold">q</text>\n'
    svg += '<line x1="50" y1="70" x2="250" y2="70" stroke="black" stroke-width="1.5"/>\n'

    for x in range(50, 251, 40):
        svg += f'<line x1="{x}" y1="70" x2="{x}" y2="100" stroke="black" stroke-width="1"/>\n'
        svg += f'<polygon points="{x-3},95 {x+3},95 {x},100" fill="black"/>\n'

    if tem_carga_p:
        svg += '<text x="255" y="45" font-family="sans-serif" font-size="18" font-weight="bold" fill="black">P</text>\n'
        svg += '<line x1="250" y1="40" x2="250" y2="100" stroke="black" stroke-width="2"/>\n'
        svg += '<polygon points="245,90 255,90 250,100" fill="black"/>\n'

    svg += '<line x1="50" y1="160" x2="250" y2="160" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="50" y1="155" x2="50" y2="165" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="250" y1="155" x2="250" y2="165" stroke="black" stroke-width="1"/>\n'
    svg += f'<text x="150" y="180" font-family="sans-serif" font-size="14" text-anchor="middle">{largura_m:.2f} m</text>\n'

    svg += '<line x1="270" y1="100" x2="270" y2="135" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="265" y1="100" x2="275" y2="100" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="265" y1="135" x2="275" y2="135" stroke="black" stroke-width="1"/>\n'
    svg += f'<text x="285" y="122" font-family="sans-serif" font-size="14">{espessura_cm:.0f} cm</text>\n'
    svg += '</svg>'
    return svg


def draw_beiral_svg_from_result(
    espessura_cm: float,
    largura_cm: float,
    resultado: ResultadoBeiral,
) -> str:
    return draw_beiral_svg(espessura_cm, largura_cm, resultado.possui_carga_concentrada)
