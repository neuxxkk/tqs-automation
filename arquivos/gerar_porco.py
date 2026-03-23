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


def adicionar_faixa(rebar, x1, y1, x2, y2, angulo, espacamento):
    """Adiciona faixa de distribuição embutida ao ferro.

    A faixa é desenhada ao longo da viga (de x1,y1 até x2,y2).
    O ângulo da faixa é perpendicular ao ferro (angulo + 90°).
    A quantidade de ferros é calculada automaticamente pelo TQS
    via ICPE1P (espaçamentos + 1 ferro).
    """
    # Garante que o ângulo gerado fique entre 0 e 360 graus
    angdist = TQSGeo.NormalizeAngle(angulo + 90.0)

    # --- A SOLUÇÃO: CÁLCULO GEOMÉTRICO CORRETO ---
    # 1. Encontra o ponto médio real do segmento
    mid_x = (x1 + x2) / 2.0
    mid_y = (y1 + y2) / 2.0

    # 2. Usa a função nativa ParallelPoint para obter um ponto que cruza
    # o ponto médio (mid_x, mid_y) ortogonalmente em relação à origem (x1, y1),
    # afastado por 10.0 unidades à direita (se quiser para a esquerda, use -10.0)
    xcot, ycot = TQSGeo.ParallelPoint(x1, y1, mid_x, mid_y, 10.0)

    # Chamada original da API, que já estava com os 23 argumentos corretos
    rebar.RebarDistrAdd(
        TQSDwg.ICPE1P,  # espaçamentos + 1 ferro (quantidade calculada automaticamente)
        angdist,        # ângulo da faixa (perpendicular ao ferro)
        x1, y1,         # ponto 1 da faixa
        x2, y2,         # ponto 2 da faixa
        xcot, ycot,     # ponto de passagem geométrico corrigido
        0,              # ifdcotc: não cotar comprimento da faixa
        1,              # iflnfr:  mostrar número de ferros
        1,              # iflpos:  mostrar posição
        1,              # iflbit:  mostrar bitola
        1,              # iflesp:  mostrar espaçamento
        TQSDwg.ICPCENTR_CENTRAD,       # alinhamento centrado
        TQSDwg.ICPQUEBR_SALTOBITO,     # quebra na bitola
        "",             # ordem padrão
        0,              # k32vigas
        0,              # k41vigas
        1,              # ilinexten: linha de extensão automática
        0,              # ilinchama: sem linha de chamada
        1,              # itpponta: círculo
        espacamento,    # espaçamento da faixa
        1.0,            # escala
    )


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

    # 3. Engenheiro seleciona posição da legenda do ferro
    icod_leg, x_leg, y_leg = eag.locate.GetPoint(tqsjan, "Clique para posicionar a legenda do ferro")
    
    if icod_leg != 1:
        eag.msg.Print("Posicionamento da legenda cancelado.")
        return

    # 4. Insere a segunda linha (A legenda do mesmo ferro!)
    # Como o ferro base não sofreu rebar.Rotate(), ele continua retinho na horizontal.
    # O 3º parâmetro (angle) é '0.0'. O 4º parâmetro (scale) é '2.0'.
    # O 5º parâmetro é '1' -> IDENTIFICAR (com texto de descrição).
    rebar.RebarLine(x_leg, y_leg, 0.0, 2.0, 1, 1, 0, 0, -1, -1, -1)


    # Calcula pontos de inserção para a linha de ferro com base nas medidas e na linha elástica
    xins = x1 - (T2 - T4 - COBRIMENTO_VIGA/2)
    yins = y2

    # 1. Calcula onde o ponto de inserção (xins, yins) vai parar após rodar ao redor de (x1, y1)
    xins_rot, yins_rot = TQSGeo.Rotate(xins, yins, angulo_inclinacao, x1, y1)

    # 2. Insere a primeira linha (Ferro na viga)
    # Passamos o angulo_inclinacao diretamente no 3º parâmetro (angle) da RebarLine.
    # O 5º parâmetro é '0' -> NÃO identificar (sem texto de descrição).
    rebar.RebarLine(xins_rot, yins_rot, angulo_inclinacao, 1.0, 0, 0, 0, 0, -1, -1, -1)
    
    tqsjan.Regen()


    tqsjan.Regen()

        

        
    eag.msg.Print(f"Ferro Especial N{rebar.mark} inserido com sucesso!")
