import math
import os
from datetime import datetime
from TQS import TQSDwg, TQSGeo, TQSEag, TQSJan
import xlsxwriter

TOLERANCIA = 10
NIVEL_VIGA = 228
NIVEL_PILAR = 227


def mapear_contorno(dwg):
    segmentos = []

    dwg.iterator.Begin()
    while True:
        itipo = dwg.iterator.Next()

        if itipo == TQSDwg.DWGTYPE_EOF:
            break
        if itipo not in (TQSDwg.DWGTYPE_LINE, TQSDwg.DWGTYPE_POLYLINE):
            continue
        if dwg.iterator.level not in (NIVEL_VIGA, NIVEL_PILAR):
            continue

        if itipo == TQSDwg.DWGTYPE_LINE:
            segmentos.append((dwg.iterator.x1, dwg.iterator.y1, dwg.iterator.x2, dwg.iterator.y2))
            continue

        npts = dwg.iterator.xySize
        if npts < 2:
            continue

        x_ant, y_ant = dwg.iterator.GetPolylinePt(0)
        for ipt in range(1, npts):
            x_cur, y_cur = dwg.iterator.GetPolylinePt(ipt)
            segmentos.append((x_ant, y_ant, x_cur, y_cur))
            x_ant, y_ant = x_cur, y_cur

    return segmentos


def extrair_ferros(dwg, eag=None):
    ferros = []

    dwg.iterator.Begin()
    while True:
        itipo = dwg.iterator.Next()

        if itipo == TQSDwg.DWGTYPE_EOF:
            break
        if itipo != TQSDwg.DWGTYPE_OBJECT:
            continue
        if dwg.iterator.objectName != "IPOFER":
            continue

        rebar = dwg.iterator.smartRebar
        ferro_tipo = rebar.type
        info_descr = []

        numdescr = rebar.RebarScheduleNumDescr()
        for idescr in range(numdescr):
            (
                ipos,
                bitola,
                nfer,
                mult,
                itpcorbar,
                ivar,
                rdval,
                rddsc,
                compr,
                igane,
                igand,
                observ,
                ilance,
                itipo99,
                icftppata,
                icorrido,
                iluvai,
                iluvaf,
            ) = rebar.RebarScheduleInfo(idescr)
            info_descr.append({"ipos": ipos, "nfer": nfer})

        pontos_insercao = []
        if ferro_tipo == TQSDwg.ICPFGN:
            n_pontos = rebar.GetGenRebarPoints()
            (
                xins,
                yins,
                angins,
                escxy,
                identfer,
                identdobr,
                ipatas,
                iexplodir,
                inivel,
                iestilo,
                icor,
            ) = rebar.GetInsertionData(0)

            for ipt in range(n_pontos):
                if ipt not in (0, 1, n_pontos - 2, n_pontos - 1):
                    continue

                xpt_local, ypt_local, zpt, iarco, identdobr, indfrt = rebar.GetGenRebarPoint(ipt)
                x_rot, y_rot = TQSGeo.Rotate(xpt_local, ypt_local, angins, 0.0, 0.0)
                pontos_insercao.append(((x_rot * escxy) + xins, (y_rot * escxy) + yins))
        else:
            n_ins = rebar.GetInsertionNumber()
            for idx_ins in range(n_ins):
                resultado = rebar.GetInsertionPoints(idx_ins)
                npts = resultado[0] if isinstance(resultado, tuple) else resultado
                for ipt in range(npts):
                    pt = rebar.GetInsertionPoint(idx_ins, ipt)
                    pontos_insercao.append((pt[0], pt[1]))

        alternado = rebar.alternatingMode == TQSDwg.ICPCAL

        ferros.append(
            {
                "tipo": ferro_tipo,
                "bitola_mm": rebar.diameter,
                "info_descr": info_descr,
                "pontos": pontos_insercao,
                "espacamento": rebar.spacing,
                "alternado": alternado,
            }
        )

    return ferros


def distancia_ponto_segmento(xp, yp, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    comp2 = dx * dx + dy * dy

    if comp2 == 0:
        return math.sqrt((xp - x1) ** 2 + (yp - y1) ** 2)

    t = ((xp - x1) * dx + (yp - y1) * dy) / comp2
    t = max(0.0, min(1.0, t))
    px = x1 + t * dx
    py = y1 + t * dy
    return math.sqrt((xp - px) ** 2 + (yp - py) ** 2)


def ponto_na_borda(xp, yp, segmentos):
    limite_superior = TOLERANCIA

    for x1l, y1l, x2l, y2l in segmentos:
        if distancia_ponto_segmento(xp, yp, x1l, y1l, x2l, y2l) <= limite_superior:
            return True

    return False


def classificar_ferros(ferros, segmentos):
    for ferro in ferros:
        ferro["eh_borda"] = any(
            ponto_na_borda(xp, yp, segmentos) for xp, yp in ferro["pontos"]
        )


def gerar_relatorio(ferros, arquivo_excel):
    ferros_ordenados = sorted(ferros, key=lambda f: f["info_descr"][0]["ipos"] if f["info_descr"] else 999)

    os.makedirs(os.path.dirname(arquivo_excel), exist_ok=True)
    try:
        wb = xlsxwriter.Workbook(arquivo_excel)
    except Exception:
        return None

    ws = wb.add_worksheet("Ferros")

    # --- Formatos ---
    def fmt(bg=None, bold=False):
        props = {"align": "center", "valign": "vcenter", "border": 1}
        if bg:
            props["bg_color"] = bg
        if bold:
            props["bold"] = True
        return wb.add_format(props)

    f_cinza    = fmt("#D9D9D9", bold=True)
    f_azul     = fmt("#BDD7EE")
    f_verde    = fmt("#C6EFCE", bold=True)
    f_amarelo  = fmt("#FFEB9C")
    f_vermelho = fmt("#FF9999")
    f_verde_lbl = fmt("#C6EFCE", bold=True)
    f_amarelo_lbl = fmt("#FFEB9C", bold=True)
    f_azul_lbl    = fmt("#BDD7EE", bold=True)
    f_vermelho_lbl = fmt("#FF9999", bold=True)

    cores_tipo = {
        "BORDA":    f_vermelho,
        "ALTERNADO": f_amarelo,
        "INTERNO":  f_azul,
    }

    # --- Cabeçalho ---
    cabecalho = ["Posição", "Quantidade", "Espaçamento (cm)", "Compr. Faixa (cm)", "Tipo"]
    for col, h in enumerate(cabecalho):
        ws.write(0, col, h, f_cinza)

    linha = 1
    soma_geral = 0.0
    soma_alt   = 0.0
    soma_simp  = 0.0
    soma_borda = 0.0
    pos_anterior = None

    for ferro in ferros_ordenados[0:-2]:
        if ferro["eh_borda"]:
            tipo = "BORDA"
        elif ferro["alternado"]:
            tipo = "ALTERNADO"
        else:
            tipo = "INTERNO"

        nfer = ferro["info_descr"][0]["nfer"] if ferro["info_descr"] else 0
        espacamento = ferro["espacamento"]
        comp_faixa_total = nfer * espacamento

        ipos = ferro["info_descr"][0]["ipos"] if ferro["info_descr"] else None
        if pos_anterior is not None and ipos != pos_anterior:
            linha += 1  # linha em branco entre posicoes
        pos_anterior = ipos

        fill = cores_tipo[tipo]
        for info in ferro["info_descr"]:
            ws.write(linha, 0, f"N{info['ipos']}", fill)
            ws.write(linha, 1, info["nfer"],              fill)
            ws.write(linha, 2, int(round(espacamento)),   fill)
            ws.write(linha, 3, int(round(comp_faixa_total)), fill)
            ws.write(linha, 4, tipo,                      fill)
            linha += 1

        soma_geral += comp_faixa_total
        if ferro["eh_borda"]:
            soma_borda += comp_faixa_total
        elif ferro["alternado"]:
            soma_alt += comp_faixa_total
        else:
            soma_simp += comp_faixa_total

    linha += 1  # linha em branco antes dos totais
    totais = [
        ("Total Geral (cm)",     soma_geral, f_verde,    f_verde_lbl),
        ("Total Alternados (cm)", soma_alt,  f_amarelo,  f_amarelo_lbl),
        ("Total Simples (cm)",   soma_simp,  f_azul,     f_azul_lbl),
        ("Total Borda (cm)",     soma_borda, f_vermelho, f_vermelho_lbl),
    ]
    for label, valor, fill_val, fill_lbl in totais:
        ws.merge_range(linha, 0, linha, 2, label, fill_lbl)
        ws.write(linha, 3, int(round(valor)), fill_val)
        ws.write(linha, 4, "",                fill_val)
        linha += 1

    # --- Larguras de colunas ---
    ws.set_column(0, 0, 14)
    ws.set_column(1, 1, 13)
    ws.set_column(2, 2, 18)
    ws.set_column(3, 3, 20)
    ws.set_column(4, 4, 14)

    # --- Bloco auxiliar: imagens detS / detAL ---
    primeira_coluna_imagem = 8  # coluna I (0-indexed)
    primeira_linha_imagem  = 11

    base_dir   = os.path.dirname(__file__)
    imagens_dir = os.path.join(base_dir, "imgs")
    caminho_det_s  = os.path.join(imagens_dir, "detS.png")
    caminho_det_al = os.path.join(imagens_dir, "detAL.png")

    valor_det_s  = soma_simp + (soma_borda / 2.0)
    valor_det_al = soma_alt

    f_cinza_bold = fmt("#D9D9D9", bold=True)
    f_bold_plain = wb.add_format({"bold": True, "align": "center", "valign": "vcenter", "border": 1})

    ALTURA_LINHA_PX = 20
    ESCALA_IMG      = 0.5

    if os.path.exists(caminho_det_s):
        ws.insert_image(primeira_linha_imagem, primeira_coluna_imagem, caminho_det_s,
                        {"x_scale": ESCALA_IMG, "y_scale": ESCALA_IMG})
        from PIL import Image as PILImage
        with PILImage.open(caminho_det_s) as im:
            _, h_px = im.size
        linhas_ocupadas = max(12, int(h_px * ESCALA_IMG / ALTURA_LINHA_PX))
    else:
        ws.write(primeira_linha_imagem, primeira_coluna_imagem, "Imagem detS nao encontrada")
        linhas_ocupadas = 14

    linha_val_s = primeira_linha_imagem + linhas_ocupadas - 3
    ws.write(linha_val_s,     primeira_coluna_imagem, "Total Simples + Borda", f_cinza_bold)
    ws.write(linha_val_s + 1, primeira_coluna_imagem, int(round(valor_det_s)), f_bold_plain)

    segunda_linha_imagem = linha_val_s + 4
    if os.path.exists(caminho_det_al):
        ws.insert_image(segunda_linha_imagem, primeira_coluna_imagem, caminho_det_al,
                        {"x_scale": ESCALA_IMG, "y_scale": ESCALA_IMG})
        from PIL import Image as PILImage
        with PILImage.open(caminho_det_al) as im:
            _, h_px = im.size
        linhas_ocupadas_al = max(12, int(h_px * ESCALA_IMG / ALTURA_LINHA_PX))
    else:
        ws.write(segunda_linha_imagem, primeira_coluna_imagem, "Imagem detAL nao encontrada")
        linhas_ocupadas_al = 14

    linha_val_al = segunda_linha_imagem + linhas_ocupadas_al - 2
    ws.write(linha_val_al,     primeira_coluna_imagem, "Total Alternados", f_cinza_bold)
    ws.write(linha_val_al + 1, primeira_coluna_imagem, int(round(valor_det_al)), f_bold_plain)

    # Largura da coluna de imagem
    ws.set_column(primeira_coluna_imagem, primeira_coluna_imagem, 28)

    try:
        wb.close()
        return arquivo_excel
    except Exception:
        return None


def rodar_script(eag=None, tqsjan=None):
    if eag is None:
        eag = TQSEag.TQSEag()
    if tqsjan is None:
        tqsjan = TQSJan.TQSJan()

    dwg = tqsjan.dwg
    dwg_path = dwg.file.Name()
    draw_name = os.path.basename(dwg_path)
    dwg_dir = os.path.dirname(dwg_path)
    arquivo_excel = os.path.join(dwg_dir, f"Ferro Corrido - {draw_name}.xlsx")

    segmentos = mapear_contorno(dwg)
    if not segmentos:
        eag.msg.Print("Aviso: Nenhum segmento de contorno encontrado. Verifique a cor/nivel da borda da viga.")
        return

    ferros = extrair_ferros(dwg, eag)
    if not ferros:
        eag.msg.Print("Aviso: Nenhum ferro inteligente encontrado no desenho.")
        return

    classificar_ferros(ferros, segmentos)
    arquivo_salvo = gerar_relatorio(ferros, arquivo_excel)

    if arquivo_salvo == arquivo_excel:
        eag.msg.Print(f"Relatorio gerado com sucesso: {arquivo_salvo}")
    else:
        eag.msg.Print(
            f"ERRO: Tabela está aberta no Excel. Feche o arquivo '{arquivo_excel}' e tente novamente."
        )


if __name__ == "__main__":
    rodar_script()
