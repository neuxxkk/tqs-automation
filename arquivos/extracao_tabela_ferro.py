import math
import os
from datetime import datetime
from TQS import TQSDwg, TQSGeo, TQSEag, TQSJan
import xlsxwriter
from xlsxwriter.utility import xl_range
from PIL import Image as PILImage

TOLERANCIA = 10
NIVEL_VIGA = 228
NIVEL_PILAR = 227
DEBUG = False  # True para ativar prints de depuração


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
        ok = False
        itipo = dwg.iterator.Next()

        if itipo == TQSDwg.DWGTYPE_EOF:
            break
        if itipo != TQSDwg.DWGTYPE_OBJECT:
            continue
        if dwg.iterator.objectName != "IPOFER":
            continue

        rebar = dwg.iterator.smartRebar
        ferro_tipo = rebar.type

        # Faixas múltiplas (ICPFAIMUL) não são ferros reais — ignorar
        if ferro_tipo == TQSDwg.ICPFAIMUL:
            continue

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
            info_descr.append({"ipos": ipos, "nfer": nfer, "icorrido": icorrido})

        pontos_insercao = []
        if ferro_tipo == TQSDwg.ICPFGN:
            n_pontos = rebar.GetGenRebarPoints()
            n_ins = rebar.GetInsertionNumber()

            for idx_ins in range(n_ins):
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
                ) = rebar.GetInsertionData(idx_ins)

                if escxy == 1.0:
                    ok = True
                    for ipt in range(n_pontos):
                        if ipt not in (0, 1, n_pontos - 2, n_pontos - 1):
                            continue

                        xpt_local, ypt_local, zpt, iarco, identdobr, indfrt = rebar.GetGenRebarPoint(ipt)

                        # Pontos com iarco==1 são centros de arco, não vértices reais — ignorar
                        if iarco == 1:
                            if DEBUG:
                                eag.msg.Print(
                                    f"Ferro da posição {info_descr} - Ponto {ipt} ignorado (centro de arco)"
                                )
                            continue

                        x_rot, y_rot = TQSGeo.Rotate(xpt_local, ypt_local, angins, 0.0, 0.0)
                        pontos_insercao.append(((x_rot * escxy) + xins, (y_rot * escxy) + yins))

                        if DEBUG:
                            eag.msg.Print(
                                f"Ferro da posição {info_descr} - Ponto {ipt}: "
                                f"({pontos_insercao[-1][0]:.2f}, {pontos_insercao[-1][1]:.2f}) "
                                f"Escala: {escxy:.2f}"
                            )

        else:
            if info_descr[0]["icorrido"] != 1:
                ok = True
                n_ins = rebar.GetInsertionNumber()

                for idx_ins in range(n_ins):
                    resultado = rebar.GetInsertionPoints(idx_ins)
                    if isinstance(resultado, tuple):
                        npts, istat = resultado
                    else:
                        npts, istat = resultado, 0

                    if istat != 0:
                        if DEBUG:
                            eag.msg.Print(
                                f"Ferro da posição {info_descr} - inserção {idx_ins} ignorada (istat={istat})"
                            )
                        continue

                    for ipt in range(npts):
                        pt = rebar.GetInsertionPoint(idx_ins, ipt)
                        pontos_insercao.append((pt[0], pt[1]))

            if DEBUG:
                eag.msg.Print(
                    f"Ferro da posição {info_descr} - É corrido: {info_descr[0]['icorrido'] == 1}"
                )

        alternado = rebar.alternatingMode == TQSDwg.ICPCAL

        if ok:
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
    for x1l, y1l, x2l, y2l in segmentos:
        if distancia_ponto_segmento(xp, yp, x1l, y1l, x2l, y2l) <= TOLERANCIA:
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

    f_cinza        = fmt("#D9D9D9", bold=True)
    f_azul         = fmt("#BDD7EE")
    f_verde        = fmt("#C6EFCE", bold=True)
    f_amarelo      = fmt("#FFEB9C")
    f_vermelho     = fmt("#FF9999")
    f_verde_lbl    = fmt("#C6EFCE", bold=True)
    f_amarelo_lbl  = fmt("#FFEB9C", bold=True)
    f_azul_lbl     = fmt("#BDD7EE", bold=True)
    f_vermelho_lbl = fmt("#FF9999", bold=True)
    f_cinza_bold   = fmt("#D9D9D9", bold=True)
    f_bold_plain   = wb.add_format({"bold": True, "align": "center", "valign": "vcenter", "border": 1})

    cores_tipo = {
        "BORDA":     f_vermelho,
        "ALTERNADO": f_amarelo,
        "INTERNO":   f_azul,
    }

    # --- Cabeçalho ---
    cabecalho = ["Posição", "Quantidade", "Espaçamento (cm)", "Compr. Faixa (cm)", "Tipo"]
    for col, h in enumerate(cabecalho):
        ws.write(0, col, h, f_cinza)

    linha = 1
    pos_anterior = None
    linhas_dados = []

    for ferro in ferros_ordenados:
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
            linha += 1  # linha em branco entre posições
        pos_anterior = ipos

        fill = cores_tipo[tipo]
        for info in ferro["info_descr"]:
            for col, value in enumerate([
                f"N{info['ipos']}",
                info["nfer"],
                int(round(espacamento)),
                int(round(comp_faixa_total)),
                tipo,
            ]):
                ws.write(linha, col, value, fill)
            linhas_dados.append(linha)
            linha += 1

    # --- Validação drop-down na coluna Tipo ---
    if linhas_dados:
        primeira_linha_tipo = linhas_dados[0]
        ultima_linha_tipo   = linhas_dados[-1]
        col_tipo_idx = 4  # coluna E (0-indexed)
        tipo_range = xl_range(primeira_linha_tipo, col_tipo_idx, ultima_linha_tipo, col_tipo_idx)
        ws.data_validation(tipo_range, {
            "validate":      "list",
            "source":        ["BORDA", "ALTERNADO", "INTERNO"],
            "input_message": "Selecione o tipo do ferro",
            "error_message": "Valor inválido. Escolha BORDA, ALTERNADO ou INTERNO.",
        })

        # --- Formatação condicional: muda cor da linha inteira ao alterar coluna Tipo ---
        # Formatos para formatação condicional (sem borda, pois a CF não herda borda da célula)
        fc_vermelho = wb.add_format({"bg_color": "#FF9999", "align": "center", "valign": "vcenter"})
        fc_amarelo  = wb.add_format({"bg_color": "#FFEB9C", "align": "center", "valign": "vcenter"})
        fc_azul     = wb.add_format({"bg_color": "#BDD7EE", "align": "center", "valign": "vcenter"})

        for linha_cf in linhas_dados:
            # Intervalo A:E da linha atual (0-indexed)
            linha_range = xl_range(linha_cf, 0, linha_cf, 4)
            # $E usa linha Excel (1-indexed)
            linha_excel = linha_cf + 1

            ws.conditional_format(linha_range, {
                "type":     "formula",
                "criteria": f'=$E{linha_excel}="BORDA"',
                "format":   fc_vermelho,
            })
            ws.conditional_format(linha_range, {
                "type":     "formula",
                "criteria": f'=$E{linha_excel}="ALTERNADO"',
                "format":   fc_amarelo,
            })
            ws.conditional_format(linha_range, {
                "type":     "formula",
                "criteria": f'=$E{linha_excel}="INTERNO"',
                "format":   fc_azul,
            })

    linha += 1  # linha em branco antes dos totais

    # Intervalos para as fórmulas (1-indexed para o Excel)
    primeira_linha = linhas_dados[0] + 1 if linhas_dados else 2
    ultima_linha   = linhas_dados[-1] + 1 if linhas_dados else 2

    total_geral_formula = f"=SUM(D{primeira_linha}:D{ultima_linha})"
    total_borda_formula = f'=SUMIF(E{primeira_linha}:E{ultima_linha},"BORDA",D{primeira_linha}:D{ultima_linha})'
    total_alt_formula   = f'=SUMIF(E{primeira_linha}:E{ultima_linha},"ALTERNADO",D{primeira_linha}:D{ultima_linha})'
    total_simp_formula  = f'=SUMIF(E{primeira_linha}:E{ultima_linha},"INTERNO",D{primeira_linha}:D{ultima_linha})'

    totais = [
        ("Total Geral (cm)",      total_geral_formula, f_verde,    f_verde_lbl),
        ("Total Alternados (cm)", total_alt_formula,   f_amarelo,  f_amarelo_lbl),
        ("Total Simples (cm)",    total_simp_formula,  f_azul,     f_azul_lbl),
        ("Total Borda (cm)",      total_borda_formula, f_vermelho, f_vermelho_lbl),
    ]
    for label, formula, fill_val, fill_lbl in totais:
        ws.merge_range(linha, 0, linha, 2, label, fill_lbl)
        ws.write_formula(linha, 3, formula, fill_val)
        ws.write(linha, 4, "", fill_val)
        linha += 1

    # --- Larguras de colunas ---
    ws.set_column(0, 0, 14)
    ws.set_column(1, 1, 13)
    ws.set_column(2, 2, 18)
    ws.set_column(3, 3, 20)
    ws.set_column(4, 4, 14)

    # --- Bloco auxiliar: imagens detS / detAL ---
    primeira_coluna_imagem = 8   # coluna I (0-indexed)
    primeira_linha_imagem  = 11

    base_dir    = os.path.dirname(__file__)
    imagens_dir = os.path.join(base_dir, "imgs")
    caminho_det_s  = os.path.join(imagens_dir, "detS.png")
    caminho_det_al = os.path.join(imagens_dir, "detAL.png")

    # Referências às linhas dos totais (já escritos acima, linha avançou 4x)
    linha_total_geral = linha - 4
    linha_total_alt   = linha - 3
    linha_total_simp  = linha - 2
    linha_total_borda = linha - 1

    # detS = simples + borda/2  |  detAL = alternados
    # +1 porque xl é 1-indexed e `linha` já é 0-indexed do xlsxwriter
    valor_det_s_formula  = f"=D{linha_total_simp + 1}+D{linha_total_borda + 1}/2"
    valor_det_al_formula = f"=D{linha_total_alt + 1}"

    ALTURA_LINHA_PX = 20
    ESCALA_IMG      = 0.5

    if os.path.exists(caminho_det_s):
        ws.insert_image(primeira_linha_imagem, primeira_coluna_imagem, caminho_det_s,
                        {"x_scale": ESCALA_IMG, "y_scale": ESCALA_IMG})
        with PILImage.open(caminho_det_s) as im:
            _, h_px = im.size
        linhas_ocupadas = max(12, int(h_px * ESCALA_IMG / ALTURA_LINHA_PX))
    else:
        ws.write(primeira_linha_imagem, primeira_coluna_imagem, "Imagem detS nao encontrada")
        linhas_ocupadas = 14

    linha_val_s = primeira_linha_imagem + linhas_ocupadas - 3
    ws.write(linha_val_s,     primeira_coluna_imagem, "Total Simples + Borda", f_cinza_bold)
    ws.write_formula(linha_val_s + 1, primeira_coluna_imagem, valor_det_s_formula, f_bold_plain)

    segunda_linha_imagem = linha_val_s + 4
    if os.path.exists(caminho_det_al):
        ws.insert_image(segunda_linha_imagem, primeira_coluna_imagem, caminho_det_al,
                        {"x_scale": ESCALA_IMG, "y_scale": ESCALA_IMG})
        with PILImage.open(caminho_det_al) as im:
            _, h_px = im.size
        linhas_ocupadas_al = max(12, int(h_px * ESCALA_IMG / ALTURA_LINHA_PX))
    else:
        ws.write(segunda_linha_imagem, primeira_coluna_imagem, "Imagem detAL nao encontrada")
        linhas_ocupadas_al = 14

    linha_val_al = segunda_linha_imagem + linhas_ocupadas_al - 2
    ws.write(linha_val_al,     primeira_coluna_imagem, "Total Alternados", f_cinza_bold)
    ws.write_formula(linha_val_al + 1, primeira_coluna_imagem, valor_det_al_formula, f_bold_plain)

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
    dwg_dir   = os.path.dirname(dwg_path)
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