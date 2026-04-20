from .core import ResultadoBeiral


def draw_beiral_svg(espessura_cm: float, largura_cm: float, tem_carga_p: bool) -> str:
    largura_m = largura_cm / 100.0

    svg = '<svg width="100%" height="250" viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 4px;">\n'
    # Hatching for the support
    svg += '<path d="M 30 70 L 50 50 M 30 110 L 50 90 M 30 150 L 50 130 M 30 190 L 50 170" stroke="#718096" stroke-width="1"/>\n'
    # Vertical support line
    svg += '<line x1="50" y1="50" x2="50" y2="200" stroke="#2d3748" stroke-width="2"/>\n'
    # Slab rectangle
    svg += '<rect x="50" y="100" width="200" height="30" fill="#f7fafc" stroke="#2d3748" stroke-width="1.5"/>\n'
    
    # Distributed load (q)
    svg += '<text x="25" y="85" font-family="monospace" font-size="16" font-weight="bold" fill="#2d3748">q</text>\n'
    svg += '<line x1="50" y1="70" x2="250" y2="70" stroke="#2d3748" stroke-width="1"/>\n'
    for x in range(50, 251, 40):
        svg += f'<line x1="{x}" y1="70" x2="{x}" y2="100" stroke="#4a5568" stroke-width="1"/>\n'
        svg += f'<polygon points="{x-2},96 {x+2},96 {x},100" fill="#4a5568"/>\n'

    # Concentrated load (P)
    if tem_carga_p:
        svg += '<text x="255" y="45" font-family="monospace" font-size="16" font-weight="bold" fill="#e53e3e">P</text>\n'
        svg += '<line x1="250" y1="40" x2="250" y2="100" stroke="#e53e3e" stroke-width="2"/>\n'
        svg += '<polygon points="246,92 254,92 250,100" fill="#e53e3e"/>\n'

    # Dimension: Width
    svg += '<line x1="50" y1="160" x2="250" y2="160" stroke="#718096" stroke-width="1"/>\n'
    svg += '<line x1="50" y1="155" x2="50" y2="165" stroke="#718096" stroke-width="1"/>\n'
    svg += '<line x1="250" y1="155" x2="250" y2="165" stroke="#718096" stroke-width="1"/>\n'
    svg += f'<text x="150" y="180" font-family="monospace" font-size="12" text-anchor="middle" fill="#4a5568">{largura_m:.2f} m</text>\n'

    # Dimension: Thickness
    svg += '<line x1="270" y1="100" x2="270" y2="130" stroke="#718096" stroke-width="1"/>\n'
    svg += '<line x1="265" y1="100" x2="275" y2="100" stroke="#718096" stroke-width="1"/>\n'
    svg += '<line x1="265" y1="130" x2="275" y2="130" stroke="#718096" stroke-width="1"/>\n'
    svg += f'<text x="280" y="120" font-family="monospace" font-size="12" fill="#4a5568">{espessura_cm:.0f} cm</text>\n'
    svg += '</svg>'
    return svg


def draw_beiral_svg_from_result(
    espessura_cm: float,
    largura_cm: float,
    resultado: ResultadoBeiral,
) -> str:
    return draw_beiral_svg(espessura_cm, largura_cm, resultado.possui_carga_concentrada)
