import tkinter as tk
from TQS import TQSDwg, TQSEag, TQSJan, TQSGeo


def obter_medidas():
    """Abre uma janela sobreposta para o usuário digitar as 5 medidas."""
    valores = []
    
    def on_ok():
        try:
            # Captura as 7 medidas como floats
            valores.extend([
                int(e1.get()), int(e2.get()), 
                int(e3.get()), int(e4.get()), int(e5.get()),
                float(e_bitola.get()), float(e_espac.get())
            ])
            root.destroy()
        except ValueError:
            pass # Ignora caso o usuário digite letras
            
    root = tk.Tk()
    root.title("Medidas do Ferro Rabo de Porco")
    root.attributes('-topmost', True) # Mantém a janela na frente do TQS
    
    tk.Label(root, text="EspL1: ").grid(row=0, column=0, sticky="e")
    e1 = tk.Entry(root); e1.insert(0, "16"); e1.grid(row=0, column=1)
    
    tk.Label(root, text="EspL2: ").grid(row=1, column=0, sticky="e")
    e2 = tk.Entry(root); e2.insert(0, "12"); e2.grid(row=1, column=1)
    
    tk.Label(root, text="Desnivel: ").grid(row=2, column=0, sticky="e")
    e3 = tk.Entry(root); e3.insert(0, "5"); e3.grid(row=2, column=1)
    
    tk.Label(root, text="L1:").grid(row=3, column=0, sticky="e")
    e4 = tk.Entry(root); e4.insert(0, "100"); e4.grid(row=3, column=1)
    
    tk.Label(root, text="L2:").grid(row=4, column=0, sticky="e")
    e5 = tk.Entry(root); e5.insert(0, "100"); e5.grid(row=4, column=1)

    tk.Label(root, text="Bitola (mm):").grid(row=5, column=0, sticky="e", pady=(10, 0))
    e_bitola = tk.Entry(root); e_bitola.insert(0, "10.0"); e_bitola.grid(row=5, column=1, pady=(10, 0))

    tk.Label(root, text="Espaçamento (cm):").grid(row=6, column=0, sticky="e")
    e_espac = tk.Entry(root); e_espac.insert(0, "15.0"); e_espac.grid(row=6, column=1)

    
    tk.Button(root, text="Desenhar", command=on_ok).grid(row=7, column=0, columnspan=2, pady=10)
    
    root.mainloop()
    return valores if len(valores) == 7 else None


def adicionar_faixa(rebar, eag, tqsjan, espacamento):
    # 5. Adição das Faixas de Distribuição
    # O laço permite inserir quantas faixas precisar. Basta teclar <Esc> para encerrar.
    eag.msg.Print("Posicione as faixas de distribuição.")
    faixa_count = 1
    while faixa_count ==1:
        icod, xf1, yf1 = eag.locate.GetPoint(tqsjan, f"Início da {faixa_count}ª faixa de distribuição (ou <Esc> para pular)")
        if icod != 1: break
            
        icod, xf2, yf2 = eag.locate.GetSecondPoint(tqsjan, xf1, yf1, TQSEag.EAG_RUBLINEAR, TQSEag.EAG_RUBRET_NAOPREEN, f"Fim da {faixa_count}ª faixa")
        if icod != 1: break
            
        icod, xc, yc = eag.locate.GetSecondPoint(tqsjan, xf1, yf1, TQSEag.EAG_RUBLINEAR, TQSEag.EAG_RUBRET_NAOPREEN, f"Posição da cota/texto da {faixa_count}ª faixa")
        if icod != 1: break
            
        ang_faixa = TQSGeo.Angle2p(xf1, yf1, xf2, yf2)
        
        # O parâmetro "NPBEC" garante a identificação de todas as faixas sem supressão
        rebar.RebarDistrAdd(
            TQSDwg.ICPE1P, ang_faixa, 
            xf1, yf1, xf2, yf2, xc, yc, 
            1, 1, 1, 1, 1, 
            TQSDwg.ICPCENTR_CENTRAD, TQSDwg.ICPQUEBR_SEMQUEBRA, 
            "NPBEC", 0, 0, 0, 1, 0, espacamento, 1.0
        )
        faixa_count += 1


def desenhar_box_detalhe(dwg, eag, tqsjan, rebar, x_base, y_base, pontos_concreto, anotacoes):
    """
    Desenha a box 'DETALHE POSIÇÃO Nxx', o contorno de concreto e as setas indicativas (V/L).

    Parâmetros:
    x_base, y_base: Ponto de referência para a inserção do detalhe.
    pontos_concreto: Lista de tuplas (x, y) com os vértices do contorno da viga/laje.
    anotacoes: Lista de tuplas (texto, x_texto, y_texto, x_seta, y_seta).
               (A seta sempre apontará para as coordenadas x_seta, y_seta).
    """
    escala_dwg = dwg.settings.scale
    if escala_dwg <= 0: escala_dwg = 50.0
    h_texto = getattr(rebar, 'textHeigth', 0.2) * escala_dwg

    # Salva o estado atual do DWG para não poluir o restante do seu código
    cor_antiga = dwg.draw.color
    nivel_antigo = dwg.draw.level

    # --- 1. DESENHAR O TÍTULO "DETALHE POSIÇÃO Nxx" ---
    dwg.draw.color = 4 # Ciano para o texto
    titulo = f"DETALHE POSIÇÃO N{rebar.mark}"
    
    # Define as coordenadas do título (ex: 20 unidades acima da base do ferro)
    x_titulo = x_base
    y_titulo = y_base + 100
    
    # Estampa o texto centralizado à esquerda
    dwg.draw.Text(x_titulo, y_titulo, h_texto * 1.2, 0.0, titulo)

    # Desenha o retângulo (box) branco em volta do texto
    dwg.draw.color = 15 # Branco
    largura_box = len(titulo) * (h_texto * 1.2) * 0.75
    altura_box = h_texto * 3.0
    dwg.draw.Rectangle(x_titulo - (h_texto * 1.5), y_titulo - h_texto, 
                       x_titulo + largura_box, y_titulo + altura_box)

    # --- 2. INSERIR A LINHA DO FERRO NO NÍVEL 239 ---
    # RebarLine(xins, yins, angle, scale, identify, identifyBends, ipatas, iexplode, ilevel, iestilo, icolor)
    # identify=0 para não misturar os textos principais no detalhe de concreto
    # ilevel=239 (9º parâmetro) garante a alocação no nível correto pedido
    rebar.RebarLine(x_base, y_base, 0.0, 1.0, 0, 0, 0, 0, 239, -1, -1)

    # --- 3. DESENHAR O CONTORNO DO CONCRETO (Linhas Brancas) ---
    if pontos_concreto:
        dwg.draw.color = 15 # Branco
        dwg.draw.PolyStart()
        for px, py in pontos_concreto:
            dwg.draw.PolyEnterPoint(px, py)
        # Polyline desenha conectando os pontos informados
        dwg.draw.Polyline() 

    # --- 4. DESENHAR SETAS ROXAS (Nível/Cor 239) E AS LABELS DAS VIGAS/LAJES ---
    if anotacoes:
        dwg.draw.color = 239 # Roxo
        dwg.draw.level = 239 
        
        for txt, x_txt, y_txt, x_seta, y_seta in anotacoes:
            # No TQS, a função DimNote gera uma flecha no último ponto acumulado pela PolyStart
            dwg.draw.PolyStart()
            dwg.draw.PolyEnterPoint(x_txt, y_txt)     # Início da linha (perto do texto)
            dwg.draw.PolyEnterPoint(x_seta, y_seta)   # Fim da linha (onde vai a flecha roxa)
            dwg.dim.DimNote()
            
            # Estampa a label (ex: "V15", "L26") logo acima da linha de chamada
            dwg.draw.Text(x_txt, y_txt + (0.5 * escala_dwg), h_texto, 0.0, txt)

    # Restaura as configurações originais do DWG e atualiza a tela
    dwg.draw.color = cor_antiga
    dwg.draw.level = nivel_antigo
    tqsjan.Regen()




def aplic_desenhar(eag, tqsjan):
    """Função principal chamada pelo botão do menu do TQS."""

    # Cota tamanho da viga
    eag.msg.Print("Insercao de Ferro Rabo de Porco - Iniciada")
    eag.msg.Print("Clique para definir o tamanho da viga (linha elástica) ou pressione <Esc> para cancelar.")

    icod1, x1, y1 = eag.locate.GetPoint(tqsjan, "Clique no primeiro ponto da cotagem")
        
    # Verifica se o usuário apertou <Esc> ou cancelou (icod == 1 significa clique normal do mouse)
    if icod1 != 1: 
        eag.msg.Print("Comando de medição cancelado.")
        return
    
    # 2. Solicita o segundo ponto ligando a linha elástica a partir de x1, y1
    icod2, x2, y2 = eag.locate.GetSecondPoint(
        tqsjan, 
        x1, y1, 
        TQSEag.EAG_RUBLINEAR,        # Ativa a linha elástica linear
        TQSEag.EAG_RUBRET_NAOPREEN,  # Sem preenchimento de janela
        "Clique no segundo ponto"
    )
    
    tamanho_viga = TQSGeo.Distance(x1, y1, x2, y2)
    angulo_inclinacao = TQSGeo.Angle2p(x1, y1, x2, y2)  
    
    # abre janela
    medidas = obter_medidas()
    if not medidas:
        eag.msg.Print("Comando cancelado ou medidas inválidas.")
        return
        
    ESP_L1, ESP_L2, DESNIVEL, INP1, INP2, BITOLA, ESPACAMENTO = medidas
    COBRIMENTO_LAJE = 2
    COBRIMENTO_VIGA = 5

    dwg = tqsjan.dwg
    rebar = TQSDwg.SmartRebar(dwg) 
    rebar.type = TQSDwg.ICPFGN #generico

    # Curvatura -> Calculo comprimento total = Soma Simples das medidas
    rebar.bendTotalLengthMode = TQSDwg.ICPSMS

    # Curvatura -> Calculo Dobras = Comprimento do trecho
    rebar.bendBendLengthMode = TQSDwg.ICPDOBSMS

    rebar.straightBarTextDirection = 1 # horizontal
    
    rebar.mark = dwg.globalrebar.FreeMark() # livre
    rebar.spacing = ESPACAMENTO
    rebar.diameter = BITOLA 
    rebar.quantity = 1

    # Calculo dos comprimentos das partes do ferro rabo de porco
    T1 = ESP_L1 - COBRIMENTO_LAJE 
    T2 = INP1 # tamanho variável 
    T3 = DESNIVEL + ESP_L2 - 4 # o que é 4
    T4 = tamanho_viga - COBRIMENTO_VIGA
    T5 = ESP_L2 - 4  # 
    T6 = INP2 
    T7 = ESP_L2 - COBRIMENTO_LAJE
    
    rebar.GenRebarPoint(0.0, 0.0, 0.0, 0, 1, -1)
    
    p1_x = 0.0
    p1_y = T1
    rebar.GenRebarPoint(p1_x, p1_y, 0.0, 0, 1, -1)
    
    p2_x = p1_x + T2
    p2_y = p1_y
    rebar.GenRebarPoint(p2_x, p2_y, 0.0, 0, 1, -1)
    
    p3_x = p2_x
    p3_y = p1_y - T3
    rebar.GenRebarPoint(p3_x, p3_y, 0.0, 0, 1, -1)
    
    p4_x = p3_x - T4
    p4_y = p3_y
    rebar.GenRebarPoint(p4_x, p4_y, 0.0, 0, 1, -1)
    
    p5_x = p4_x 
    p5_y = p4_y + T5
    rebar.GenRebarPoint(p5_x, p5_y, 0.0, 0, 1, -1)

    p6_x = p5_x + T6 
    p6_y = p5_y
    rebar.GenRebarPoint(p6_x, p6_y, 0.0, 0, 1, -1)

    p7_x = p6_x 
    p7_y = p6_y - T7
    rebar.GenRebarPoint(p7_x, p7_y, 0.0, 0, 1, -1)


    
    # adicionar_faixa(rebar, eag, tqsjan, ESPACAMENTO)

    # 3. Engenheiro seleciona posição da legenda do ferro
    icod_leg, x_leg, y_leg = eag.locate.GetPoint(tqsjan, "Clique para posicionar a legenda do ferro")
    
    if icod_leg != 1:
        eag.msg.Print("Posicionamento da legenda cancelado.")
        return

    # Linha `rebar` da legenda
    rebar.RebarLine(x_leg, y_leg, 0.0, 2.0, 1, 1, 0, 0, 220, -1, -1)


    # Calcula pontos de inserção para a linha de ferro com base nas medidas e na linha elástica
    xins = x1 - (T2 - T4 - COBRIMENTO_VIGA/2)
    yins = y2

    # 1. Calcula onde o ponto de inserção (xins, yins) vai parar após rodar ao redor de (x1, y1)
    xins_rot, yins_rot = TQSGeo.Rotate(xins, yins, angulo_inclinacao, x1, y1)

    # xins Ponto de inserção
    # yins Ponto de inserção
    # angle Ângulo de inserção graus
    # scale Escala de inserção
    # identify (1) Identificar o ferro
    # identifyBends (1) Identificar dobras
    # ipatas 0 não 1 sim 2 45° 3 225° 4 invertido 0 e 1 valem para ICPFRT, ICPSTR, ICPSTRGEN e ICPGRA 2, 3 e 4 valem para ICPFRT
    # iexplode (1) Explodir se estribo
    # ilevel Nível 0..255 EAG (-1) padrão
    # iestilo Estilo 0..5 EAG (-1) padrão
    # icolor Cor 0..255 EAG (-1) padrão

    rebar.RebarLine(xins_rot, yins_rot, angulo_inclinacao, 1.0, 0, 0, 0, 0, 201, -1, -1)
    
    tqsjan.Regen()

    rebar.RebarLine(x_leg, y_leg + 200, 0.0, 2.0, 0, 0, 0, 0, 239, -1, -1)

    x_base = x_leg
    y_base = y_leg + 200

    # desenhando pontos
    pontos_concreto = []

    # Separa as coordenadas para poder somar matematicamente
    px = x_base
    py = y_base
    pontos_concreto.append((px, py))

    py += ESP_L1
    pontos_concreto.append((px, py))

    px += INP1
    pontos_concreto.append((px, py))

    py += DESNIVEL
    pontos_concreto.append((px, py))

    px += INP2
    pontos_concreto.append((px, py))

    py -= ESP_L2
    pontos_concreto.append((px, py))

    px -= INP2
    pontos_concreto.append((px, py))

    py -= 100
    pontos_concreto.append((px, py))

    px -= tamanho_viga
    pontos_concreto.append((px, py))

    py -= (100 + T5)
    pontos_concreto.append((px, py))

    px -= (INP2 - tamanho_viga)
    pontos_concreto.append((px, py))

    # --- CORREÇÃO 1: Adiciona apenas o PRIMEIRO PONTO (índice 0) para fechar o polígono ---
    pontos_concreto.append(pontos_concreto[0])

    eag.msg.Print("Pontos do contorno do concreto calculados para o detalhe.")

    for idx, (p_x, p_y) in enumerate(pontos_concreto):
        eag.msg.Print(f"Ponto {idx+1}: ({p_x:.2f}, {p_y:.2f})")

    # --- CORREÇÃO 2: Índices restaurados para passar apenas números para o TQS ---
    desenhar_box_detalhe(
        dwg, eag, tqsjan, rebar, 
        x_base, y_base, 
        pontos_concreto,
        anotacoes=[
            ("LX", pontos_concreto[1], pontos_concreto[1], pontos_concreto[1] + 50, pontos_concreto[1] + 30),
            ("VX", pontos_concreto[2], pontos_concreto[2][1], pontos_concreto[2] + 50, pontos_concreto[2][1])
        ]
    )


    eag.msg.Print(f"Ferro Especial N{rebar.mark} inserido com sucesso!")
