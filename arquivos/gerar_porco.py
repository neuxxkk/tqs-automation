import math
import tkinter as tk
from TQS import TQSDwg, TQSEag, TQSJan, TQSGeo

# ---------------------------------------------------------------------------
# Constantes globais
# ---------------------------------------------------------------------------
COBRIMENTO_LAJE = 2   # cm
COBRIMENTO_VIGA = 5   # cm

ESP_L1   = 12
ESP_L2   = 12
DESNIVEL = -10
INP1     = 85
INP2     = 76
BITOLA   = 6.3
ESPACAMENTO = 16.0
rebaixo_negativo = False


# ---------------------------------------------------------------------------
# Janela de entrada de medidas
# ---------------------------------------------------------------------------
def obter_medidas():
    """Abre janela tkinter para o usuário digitar as 7 medidas.
    Retorna tupla (ESP_L1, ESP_L2, DESNIVEL, INP1, INP2, BITOLA, ESPACAMENTO)
    ou None se cancelado.
    """
    valores   = []
    labels_erro = {}

    def validar_int(valor, nome):
        try:
            v = int(valor)
            return v, None
        except ValueError:
            return None, f"{nome}: inteiro válido"

    def validar_float(valor, nome):
        try:
            v = float(valor)
            return v, None
        except ValueError:
            return None, f"{nome}: número válido"

    def on_ok():
        for lbl in labels_erro.values():
            lbl.config(text="")

        campos = [
            ("ESP_L1",   e1,       validar_int),
            ("ESP_L2",   e2,       validar_int),
            ("DESNIVEL", e3,       validar_int),
            ("INP1",     e4,       validar_int),
            ("INP2",     e5,       validar_int),
            ("BITOLA",   e_bitola, validar_float),
            ("ESPAC",    e_espac,  validar_float),
        ]
        resultados = []
        valido = True
        for nome, entry, fn in campos:
            v, erro = fn(entry.get(), nome)
            if erro:
                labels_erro[nome].config(text=erro)
                valido = False
            else:
                resultados.append(v)
        if valido:
            valores.extend(resultados)
            root.destroy()

    root = tk.Tk()
    root.title("Medidas do Ferro Rabo de Porco")
    root.attributes("-topmost", True)
    root.resizable(False, False)

    def campo(row, label_txt, default, nome):
        tk.Label(root, text=label_txt).grid(row=row * 2, column=0, sticky="e", padx=6, pady=(4, 0))
        entry = tk.Entry(root, width=10)
        entry.insert(0, str(default))
        entry.grid(row=row * 2, column=1, padx=6, pady=(4, 0))
        lbl_err = tk.Label(root, text="", fg="red", font=("Arial", 8))
        lbl_err.grid(row=row * 2 + 1, column=0, columnspan=2, sticky="w", padx=6)
        labels_erro[nome] = lbl_err
        return entry

    e1       = campo(0, "EspL1 (cm):",        ESP_L1,   "ESP_L1")
    e2       = campo(1, "EspL2 (cm):",        ESP_L2,   "ESP_L2")
    e3       = campo(2, "Desnível (cm):",     DESNIVEL, "DESNIVEL")
    e4       = campo(3, "L1 (cm):",           INP1,     "INP1")
    e5       = campo(4, "L2 (cm):",           INP2,     "INP2")
    e_bitola = campo(5, "Bitola (mm):",       BITOLA,   "BITOLA")
    e_espac  = campo(6, "Espaçamento (cm):",  ESPACAMENTO,    "ESPAC")

    tk.Button(root, text="Desenhar", command=on_ok, width=14).grid(
        row=14, column=0, columnspan=2, pady=12
    )
    root.mainloop()
    return tuple(valores) if len(valores) == 7 else None


# ---------------------------------------------------------------------------
# Faixa de distribuição
# ---------------------------------------------------------------------------
def adicionar_faixa(rebar, eag, tqsjan, espacamento):
    """Permite ao usuário inserir faixas de distribuição clicando no desenho.
    Continua pedindo faixas até o usuário pressionar <Esc>.
    """
    eag.msg.Print("Posicione as faixas de distribuição. <Esc> para encerrar.")
    faixa_count = 1

    # BUG CORRIGIDO: era `while faixa_count == 1` (nunca avançava).
    # Agora é `while True` — o loop quebra apenas quando o usuário aperta <Esc>.
    while True:
        icod, xf1, yf1 = eag.locate.GetPoint(
            tqsjan, f"Início da {faixa_count}ª faixa (ou <Esc> para encerrar)"
        )
        if icod != 1:
            break

        icod, xf2, yf2 = eag.locate.GetSecondPoint(
            tqsjan, xf1, yf1,
            TQSEag.EAG_RUBLINEAR, TQSEag.EAG_RUBRET_NAOPREEN,
            f"Fim da {faixa_count}ª faixa"
        )
        if icod != 1:
            break

        icod, xc, yc = eag.locate.GetSecondPoint(
            tqsjan, xf1, yf1,
            TQSEag.EAG_RUBLINEAR, TQSEag.EAG_RUBRET_NAOPREEN,
            f"Posição da cota/texto da {faixa_count}ª faixa"
        )
        if icod != 1:
            break

        ang_faixa = TQSGeo.Angle2p(xf1, yf1, xf2, yf2)

        rebar.RebarDistrAdd(
            TQSDwg.ICPE1P, ang_faixa,
            xf1, yf1, xf2, yf2, xc, yc,
            1,                              # ifdcotc: cotar comprimento da faixa
            1,                              # iflnfr:  mostrar nº de ferros
            1,                              # iflpos:  mostrar posição
            1,                              # iflbit:  mostrar bitola
            1,                              # iflesp:  mostrar espaçamento
            TQSDwg.ICPCENTR_CENTRAD,        # alinhamento centrado
            TQSDwg.ICPQUEBR_SEMQUEBRA,      # sem quebra de linha
            "NPBEC",                        # ordem dos textos
            0,                              # k32vigas
            0,                              # k41vigas
            0,                              # ilinexten
            1,                              # ilinchama: com linha de chamada
            0,                              # itpponta: flecha
            espacamento,                    # espaçamento
            1.0,                            # escala
        )
        faixa_count += 1

    eag.msg.Print(f"{faixa_count - 1} faixa(s) adicionada(s).")


# ---------------------------------------------------------------------------
# Detalhe do ferro em concreto
# ---------------------------------------------------------------------------
def desenhar_box_detalhe(dwg, eag, tqsjan, rebar, x_base, y_base, pontos_concreto, anotacoes):
    """Desenha o bloco 'DETALHE POSIÇÃO Nxx', o contorno de concreto e setas.

    pontos_concreto: list de (x, y)
    anotacoes: list de (texto, x_texto, y_texto, x_seta, y_seta)
                A flecha do DimNote aponta para (x_seta, y_seta).
    """
    escala_dwg = dwg.settings.scale
    if escala_dwg <= 0:
        escala_dwg = 50.0

    # BUG CORRIGIDO: textHeigth é propriedade do rebar, mas pode não estar definida
    # neste contexto — usando valor fixo seguro calculado pela escala.
    h_texto = 0.2 * escala_dwg

    # Salva estado atual do desenho
    cor_antiga   = dwg.draw.color
    nivel_antigo = dwg.draw.level

    # --- 1. Título "DETALHE POSIÇÃO Nxx" ---
    titulo   = f"DETALHE POSIÇÃO N{rebar.mark}"
    x_titulo = x_base + INP1
    y_titulo = y_base + 100

    dwg.draw.color = 4  # ciano
    dwg.draw.Text(x_titulo, y_titulo, h_texto * 1.2, 0.0, titulo)

    # BUG CORRIGIDO: draw.Rectangle não existe no TQS.
    # Substituído por PolyStart + 4x PolyEnterPoint + Polyline (retângulo manual).
    dwg.draw.color = 15  # branco
    largura_box = len(titulo) * h_texto * 1.3
    altura_box  = h_texto * 3.0
    bx1 = x_titulo - h_texto * 1.5
    by1 = y_titulo - h_texto
    bx2 = x_titulo + largura_box
    by2 = y_titulo + altura_box
    dwg.draw.PolyStart()
    dwg.draw.PolyEnterPoint(bx1, by1)
    dwg.draw.PolyEnterPoint(bx2, by1)
    dwg.draw.PolyEnterPoint(bx2, by2)
    dwg.draw.PolyEnterPoint(bx1, by2)
    dwg.draw.PolyEnterPoint(bx1, by1)  # fecha o retângulo
    dwg.draw.Polyline()

    # --- 2. Linha de ferro no nível 239 (detalhe de concreto, sem identificação) ---
    # BUG CORRIGIDO: este RebarLine inseria uma 3ª linha no mesmo ferro (rebar),
    # que também apareceria na tabela de ferros e na legenda. Para o detalhe de
    # concreto, a representação deve ser uma linha de desenho simples, não uma
    # RebarLine. Substituído por draw.Line usando os pontos do ferro no sistema local.
    if pontos_concreto and len(pontos_concreto) >= 2:
        dwg.draw.color  = 15   # branco
        dwg.draw.level  = 239
        dwg.draw.PolyStart()
        for px, py in pontos_concreto:
            dwg.draw.PolyEnterPoint(px, py)
        dwg.draw.Polyline()

    
     # --- 3. Setas e labels (Desenho Manual 100% Seguro) ---
    if anotacoes:
        dwg.draw.color = 6    # magenta/roxo
        dwg.draw.level = 239
 
        for txt, x_txt, y_txt, x_seta, y_seta in anotacoes:
            # 1. Label descansando sobre a linha
            dwg.draw.Text(x_txt, y_txt + (h_texto * 0.3), h_texto, 0.0, txt)
 
            # Calcula o tamanho do "degrau" horizontal sob o texto
            largura_linha = len(txt) * h_texto * 1.25
 
            if x_seta < x_txt:
                px_inicio = x_txt + largura_linha
                px_dobra = x_txt
            else:
                px_inicio = x_txt
                px_dobra = x_txt + largura_linha
 
            # 2. Desenha a linha de descanso do texto
            dwg.draw.Line(px_inicio, y_txt, px_dobra, y_txt)
 
            # 3. Calcula a distância e desenha a linha da seta
            dx = x_seta - px_dobra
            dy = y_seta - y_txt
            distancia_seta = TQSGeo.Distance(px_dobra, y_txt, x_seta, y_seta)
 
            if distancia_seta > 0.1:
                # Linha diagonal ou reta até o alvo
                dwg.draw.Line(px_dobra, y_txt, x_seta, y_seta)
 
                # --- MATEMÁTICA DA FLECHA ---
                # Calcula os vetores de inclinação da linha
                cos_a = dx / distancia_seta
                sin_a = dy / distancia_seta
 
                # L = Comprimento da ponta da flecha / W = Largura da base da flecha
                L = h_texto * 0.8
                W = L / 3.0
 
                # Coordenadas da base esquerda e direita do triângulo da flecha
                x_left = x_seta - (L * cos_a) - (W * sin_a)
                y_left = y_seta - (L * sin_a) + (W * cos_a)
 
                x_right = x_seta - (L * cos_a) + (W * sin_a)
                y_right = y_seta - (L * sin_a) - (W * cos_a)
 
                # 4. Desenha o triângulo preenchido (Seta) na ponta
                dwg.draw.PolyStart()
                dwg.draw.PolyEnterPoint(x_seta, y_seta)
                dwg.draw.PolyEnterPoint(x_left, y_left)
                dwg.draw.PolyEnterPoint(x_right, y_right)
                dwg.draw.PolyEnterPoint(x_seta, y_seta)
                dwg.draw.PolylineFilled()

 
    # Restaura estado
    dwg.draw.color = cor_antiga
    dwg.draw.level = nivel_antigo
    tqsjan.Regen()


# ---------------------------------------------------------------------------
# Função principal chamada pelo menu TQS
# ---------------------------------------------------------------------------
def aplic_desenhar(eag, tqsjan):
    eag.msg.Print("Inserção de Ferro Rabo de Porco - Iniciada")

    # --- 1. Primeiro ponto da viga ---
    icod1, x1, y1 = eag.locate.GetPoint(tqsjan, "Clique no primeiro ponto da viga")
    if icod1 != 1:
        eag.msg.Print("Cancelado.")
        return

    # --- 2. Segundo ponto da viga ---
    icod2, x2, y2 = eag.locate.GetSecondPoint(
        tqsjan, x1, y1,
        TQSEag.EAG_RUBLINEAR, TQSEag.EAG_RUBRET_NAOPREEN,
        "Clique no segundo ponto da viga"
    )
    if icod2 != 1:
        eag.msg.Print("Cancelado.")
        return
    
    if x1 == x2:
        if y2 < y1:
            x1_sup = x1
            y1_sup = y1

            x1 = x2
            y1 = y2

            x2 = x1_sup
            y2 = y1_sup
    elif y1 ==y2:
        if x2 < x1:
            x1_sup = x1
            y1_sup = y1  

            x1 = x2
            y1 = y2

            x2 = x1_sup
            y2 = y1_sup

    tamanho_viga      = TQSGeo.Distance(x1, y1, x2, y2)
    angulo_inclinacao = TQSGeo.Angle2p(x1, y1, x2, y2)

    eag.msg.Print(f"Tamanho da viga: {tamanho_viga:.2f} cm, Ângulo de inclinação: {angulo_inclinacao:.2f}°")

    # --- 3. Janela de medidas ---
    medidas = obter_medidas()
    if not medidas:
        eag.msg.Print("Cancelado ou medidas inválidas.")
        return

    ESP_L1, ESP_L2, DESNIVEL, INP1, INP2, BITOLA, ESPACAMENTO = medidas

    # --- 4. Configurar SmartRebar ---
    dwg   = tqsjan.dwg
    rebar = TQSDwg.SmartRebar(dwg)
    rebar.type     = TQSDwg.ICPFGN
    rebar.mark     = dwg.globalrebar.FreeMark()
    rebar.diameter = BITOLA
    rebar.spacing  = ESPACAMENTO
    # NÃO definir rebar.quantity — calculado automaticamente pela faixa

    rebar.bendTotalLengthMode = TQSDwg.ICPSMS
    rebar.bendBendLengthMode  = TQSDwg.ICPDOBSMS
    

    # --- 5. Calcular trechos e registrar pontos (deve vir ANTES de RebarDistrAdd) ---
    T1 = ESP_L1 - COBRIMENTO_LAJE
    T2 = INP1
    T4 = tamanho_viga - COBRIMENTO_VIGA
    T6 = INP2
    T7 = ESP_L2 - COBRIMENTO_LAJE

    rebaixo_negativo = False
    if  DESNIVEL < 0: 
        rebaixo_negativo = True
        DESNIVEL = - DESNIVEL

    if rebaixo_negativo: #mantem como esta 
        T3 = DESNIVEL + ESP_L2 - 4
        T5 = ESP_L2 - 4


        rebar.GenRebarPoint(0.0,        0.0,        0.0, 0, 1, -1)  # P0
        rebar.GenRebarPoint(0.0,        T1,         0.0, 0, 1, -1)  # P1
        rebar.GenRebarPoint(T2,         T1,         0.0, 0, 1, -1)  # P2
        rebar.GenRebarPoint(T2,         T1 - T3,    0.0, 0, 1, -1)  # P3
        rebar.GenRebarPoint(T2 - T4,    T1 - T3,    0.0, 0, 1, -1)  # P4
        rebar.GenRebarPoint(T2 - T4,    T1 - T3 + T5, 0.0, 0, 1, -1)  # P5
        rebar.GenRebarPoint(T2 - T4 + T6, T1 - T3 + T5, 0.0, 0, 1, -1)  # P6
        rebar.GenRebarPoint(T2 - T4 + T6, T1 - T3 + T5 - T7, 0.0, 0, 1, -1)  # P7
    else: # DESNIVEL positivo
        T3 = DESNIVEL + ESP_L1 - 4
        T5 = ESP_L1 - 4
                        #   X,           Y,          Z,   tipo, face, kf
        rebar.GenRebarPoint(0.0,        0.0,        0.0, 0, 1, -1)  # P0
        rebar.GenRebarPoint(0.0,        T1,         0.0, 0, 1, -1)  # P1
        rebar.GenRebarPoint(T2,         T1,         0.0, 0, 1, -1)  # P2
        rebar.GenRebarPoint(T2,         T1 - T5,    0.0, 0, 1, -1)  # P3
        rebar.GenRebarPoint(T2 - T4,    T1 - T5,    0.0, 0, 1, -1)  # P4
        rebar.GenRebarPoint(T2 - T4,    T1 - T5 + T3, 0.0, 0, 1, -1)  # P5
        rebar.GenRebarPoint(T2 - T4 + T6, T1 - T5 + T3, 0.0, 0, 1, -1)  # P6
        rebar.GenRebarPoint(T2 - T4 + T6, T1 - T5 + T3 - T7, 0.0, 0, 1, -1)  # P7

    

    # --- 6. Faixa de distribuição (deve vir ANTES de RebarLine) ---
    adicionar_faixa(rebar, eag, tqsjan, ESPACAMENTO)

    # --- 7. Legenda do ferro ---
    icod_leg, x_leg, y_leg = eag.locate.GetPoint(
        tqsjan, "Clique para posicionar a legenda do ferro"
    )
    if icod_leg != 1:
        eag.msg.Print("Posicionamento da legenda cancelado.")
        return

    # Linha de legenda: horizontal, escala 2x, com identificação, nível 220
    rebar.RebarLine(x_leg, y_leg, 0.0, 2.0, 1, 1, 0, 0, 220, -1, -1)


    # --- 8. Linha de ferro na viga (sem identificação, nível 201) ---
    xins = x1 - (T2 - T4 - COBRIMENTO_VIGA / 2)# if -angulo_inclinacao <= 90 else x1 - T2 - COBRIMENTO_VIGA/2
    yins = y2
    xins_rot, yins_rot = TQSGeo.Rotate(xins, yins, angulo_inclinacao, x1, y1)

    eag.msg.Print(f"x1: {x1:.2f}, y1: {y1:.2f}, x2: {x2:.2f}, y2: {y2:.2f}")
    eag.msg.Print(f"xins: {xins:.2f}, yins: {yins:.2f}")

    rebar.RebarLine(xins_rot, yins_rot, angulo_inclinacao, 1.0, 0, 0, 0, 0, 201, -1, -1)


    # --- 9. Linha do detalhe de concreto (nível 239, sem identificação) ---
    # Inserida no mesmo ponto de base do detalhe (x_leg, y_leg + 200),
    # horizontal, escala 2x — será o ferro representado dentro do contorno de concreto.
    x_base = x_leg
    y_base = y_leg + 200
    rebar.RebarLine(x_base, y_base, 0.0, 2.0, 0, 0, 0, 0, 239, -1, -1)

    tqsjan.Regen()

    # --- 10. Detalhe de concreto ---
    # Monta polígono do contorno de concreto
    pontos_concreto = []

    # Ponto 0
    px, py = x_base, y_base
    pontos_concreto.append((px, py))

    # Ponto 1
    py += ESP_L1*2
    pontos_concreto.append((px, py))

    # Ponto 2
    px += (INP1 + 2.5)*2 if rebaixo_negativo else (INP1 - (T4 + 2.5))*2
    pontos_concreto.append((px, py))

    # Ponto 3
    py -= DESNIVEL*2 if rebaixo_negativo else -(DESNIVEL*2)
    pontos_concreto.append((px, py))

    # Ponto 4
    px += INP2*2 if rebaixo_negativo else (INP2 +2.5)*2
    pontos_concreto.append((px, py))

    # Ponto 5
    py -= ESP_L2*2 if rebaixo_negativo else (ESP_L2 + DESNIVEL) *2
    pontos_concreto.append((px, py))

    # Ponto 6
    px -= INP2*2 if rebaixo_negativo else (INP2 - T4 - 2.5)*2
    pontos_concreto.append((px, py))

    # Ponto 7
    py -= 100
    pontos_concreto.append((px, py))

    # Ponto 8
    px -= tamanho_viga*2
    pontos_concreto.append((px, py))

    # Ponto 9
    py = y_base
    pontos_concreto.append((px, py))

    # Ponto 10
    px = x_base
    pontos_concreto.append((px, py))

    pontos_concreto.append(pontos_concreto[0])  # fecha o polígono

    if eag:
        for idx, (p_x, p_y) in enumerate(pontos_concreto):
            eag.msg.Print(f"  Ponto {idx}: ({p_x:.2f}, {p_y:.2f})")

    #pontos setas ponto medio entre p1 e p2, p3 e p4 e p6 e p7
    p1_x = (pontos_concreto[1][0] + pontos_concreto[2][0]) / 2
    p1_y = (pontos_concreto[1][1] + pontos_concreto[2][1]) / 2

    p2_x = (pontos_concreto[3][0] + pontos_concreto[4][0]) / 2
    p2_y = (pontos_concreto[3][1] + pontos_concreto[4][1]) / 2

    p3_x = (pontos_concreto[6][0] + pontos_concreto[7][0]) / 2
    p3_y = (pontos_concreto[6][1] + pontos_concreto[7][1]) / 2


    desenhar_box_detalhe(
        dwg, eag, tqsjan, rebar,
        x_base, y_base,
        pontos_concreto,
        anotacoes=[
            # (texto, x_texto, y_texto, x_seta, y_seta)
            ("L1", p1_x + 30, p1_y + 20, p1_x,        p1_y),
            ("V2", p2_x + 30, p2_y + 20, p2_x,        p2_y),
            ("V1", p3_x + 30, p3_y, p3_x,        p3_y),
        ]
    )

    eag.msg.Print(f"Ferro Especial N{rebar.mark} inserido com sucesso!")