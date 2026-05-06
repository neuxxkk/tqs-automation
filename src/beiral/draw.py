from .core import ResultadoBeiral


def draw_beiral_svg(espessura_cm: float, largura_cm: float, tem_carga_p: bool) -> str:
    largura_m = largura_cm / 100.0
    largura_cm = max(largura_cm, 1.0)
    espessura_cm = max(espessura_cm, 1.0)

    view_w = 420
    view_h = 280
    x_suporte = 58
    base_y = 156
    slab_width = min(300.0, max(115.0, 72.0 + largura_cm * 1.55))
    slab_height = min(84.0, max(18.0, 10.0 + espessura_cm * 2.25))
    slab_y = base_y - slab_height / 2.0
    slab_x2 = x_suporte + slab_width
    cota_y = slab_y + slab_height + 42.0
    espessura_x = slab_x2 + 28.0
    q_y = slab_y - 42.0
    q_label_x = x_suporte - 30.0

    svg = (
        f'<svg width="100%" height="280" viewBox="0 0 {view_w} {view_h}" '
        'xmlns="http://www.w3.org/2000/svg" '
        'style="background-color: #ffffff; border: 1px solid #d6d3cb; border-radius: 6px;">\n'
    )
    # Hatching for the support
    hatch_top = slab_y - 42.0
    hatch_bottom = slab_y + slab_height + 64.0
    hatch_y = hatch_top
    while hatch_y <= hatch_bottom:
        svg += (
            f'<path d="M 28 {hatch_y:.1f} L 50 {hatch_y - 20:.1f}" '
            'stroke="#7e837c" stroke-width="1"/>\n'
        )
        hatch_y += 34.0
    # Vertical support line
    svg += (
        f'<line x1="{x_suporte}" y1="{hatch_top:.1f}" x2="{x_suporte}" y2="{hatch_bottom:.1f}" '
        'stroke="#2d3748" stroke-width="2"/>\n'
    )
    # Slab rectangle
    svg += (
        f'<rect x="{x_suporte}" y="{slab_y:.1f}" width="{slab_width:.1f}" height="{slab_height:.1f}" '
        'fill="#f7fafc" stroke="#2d3748" stroke-width="1.5"/>\n'
    )

    # Distributed load (q)
    svg += (
        f'<text x="{q_label_x:.1f}" y="{q_y + 15:.1f}" font-family="monospace" '
        'font-size="16" font-weight="bold" fill="#2d3748">q</text>\n'
    )
    svg += (
        f'<line x1="{x_suporte}" y1="{q_y:.1f}" x2="{slab_x2:.1f}" y2="{q_y:.1f}" '
        'stroke="#2d3748" stroke-width="1"/>\n'
    )
    arrow_count = max(4, min(8, int(round(largura_cm / 25.0))))
    if arrow_count == 1:
        arrow_step = slab_width
    else:
        arrow_step = slab_width / (arrow_count - 1)
    for i in range(arrow_count):
        x = x_suporte + i * arrow_step
        svg += (
            f'<line x1="{x:.1f}" y1="{q_y:.1f}" x2="{x:.1f}" y2="{slab_y:.1f}" '
            'stroke="#4a5568" stroke-width="1"/>\n'
        )
        svg += (
            f'<polygon points="{x - 2:.1f},{slab_y - 4:.1f} {x + 2:.1f},{slab_y - 4:.1f} {x:.1f},{slab_y:.1f}" '
            'fill="#4a5568"/>\n'
        )

    # Concentrated load (P)
    if tem_carga_p:
        svg += (
            f'<text x="{slab_x2 + 8:.1f}" y="{q_y - 8:.1f}" font-family="monospace" '
            'font-size="16" font-weight="bold" fill="#e53e3e">P</text>\n'
        )
        svg += (
            f'<line x1="{slab_x2:.1f}" y1="{q_y - 14:.1f}" x2="{slab_x2:.1f}" y2="{slab_y:.1f}" '
            'stroke="#e53e3e" stroke-width="2"/>\n'
        )
        svg += (
            f'<polygon points="{slab_x2 - 4:.1f},{slab_y - 8:.1f} {slab_x2 + 4:.1f},{slab_y - 8:.1f} {slab_x2:.1f},{slab_y:.1f}" '
            'fill="#e53e3e"/>\n'
        )

    # Dimension: Width
    svg += (
        f'<line x1="{x_suporte}" y1="{cota_y:.1f}" x2="{slab_x2:.1f}" y2="{cota_y:.1f}" '
        'stroke="#718096" stroke-width="1"/>\n'
    )
    svg += (
        f'<line x1="{x_suporte}" y1="{cota_y - 5:.1f}" x2="{x_suporte}" y2="{cota_y + 5:.1f}" '
        'stroke="#718096" stroke-width="1"/>\n'
    )
    svg += (
        f'<line x1="{slab_x2:.1f}" y1="{cota_y - 5:.1f}" x2="{slab_x2:.1f}" y2="{cota_y + 5:.1f}" '
        'stroke="#718096" stroke-width="1"/>\n'
    )
    svg += (
        f'<text x="{x_suporte + slab_width / 2.0:.1f}" y="{cota_y + 20:.1f}" font-family="monospace" '
        f'font-size="12" text-anchor="middle" fill="#4a5568">{largura_m:.2f} m</text>\n'
    )

    # Dimension: Thickness
    svg += (
        f'<line x1="{espessura_x:.1f}" y1="{slab_y:.1f}" x2="{espessura_x:.1f}" y2="{slab_y + slab_height:.1f}" '
        'stroke="#718096" stroke-width="1"/>\n'
    )
    svg += (
        f'<line x1="{espessura_x - 5:.1f}" y1="{slab_y:.1f}" x2="{espessura_x + 5:.1f}" y2="{slab_y:.1f}" '
        'stroke="#718096" stroke-width="1"/>\n'
    )
    svg += (
        f'<line x1="{espessura_x - 5:.1f}" y1="{slab_y + slab_height:.1f}" x2="{espessura_x + 5:.1f}" y2="{slab_y + slab_height:.1f}" '
        'stroke="#718096" stroke-width="1"/>\n'
    )
    svg += (
        f'<text x="{espessura_x + 12:.1f}" y="{slab_y + slab_height / 2.0 + 4:.1f}" font-family="monospace" '
        f'font-size="12" fill="#4a5568">{espessura_cm:.0f} cm</text>\n'
    )
    svg += '</svg>'
    return svg


def draw_beiral_svg_from_result(
    espessura_cm: float,
    largura_cm: float,
    resultado: ResultadoBeiral,
) -> str:
    return draw_beiral_svg(espessura_cm, largura_cm, resultado.possui_carga_concentrada)
