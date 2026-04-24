import math
import tkinter as tk
from TQS import TQSDwg, TQSEag, TQSJan, TQSGeo

# ---------------------------------------------------------------------------
# Constantes globais
# ---------------------------------------------------------------------------
DEBUG = False         # Altere para True para exibir mensagens de depuração no TQS

COBRIMENTO_LAJE = 2   # cm
COBRIMENTO_VIGA = 5   # cm

ESP_L1      = 12
ESP_L2      = 12
DESNIVEL    = -10
INP1        = 85
INP2        = 76
BITOLA      = 6.3
ESPACAMENTO = 16.0

# ---------------------------------------------------------------------------
# Janela de entrada de medidas
# ---------------------------------------------------------------------------
def obter_medidas():
    """Abre janela tkinter para o usuário digitar as 7 medidas.
    Retorna tupla (ESP_L1, ESP_L2, DESNIVEL, INP1, INP2, BITOLA, ESPACAMENTO)
    ou None se cancelado.
    """
    valores = []
    labels_erro = {}

    def validar_int(valor, nome):
        try:
            return int(valor), None
        except ValueError:
            return None, f"{nome}: inteiro válido"

    def validar_float(valor, nome):
        try:
            return float(valor), None
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

    e1       = campo(0, "EspL1 (cm):",        ESP_L1,      "ESP_L1")
    e2       = campo(1, "EspL2 (cm):",        ESP_L2,      "ESP_L2")
    e3       = campo(2, "Desnível (cm):",     DESNIVEL,    "DESNIVEL")
    e4       = campo(3, "L1 (cm):",           INP1,        "INP1")
    e5       = campo(4, "L2 (cm):",           INP2,        "INP2")
    e_bitola = campo(5, "Bitola (mm):",       BITOLA,      "BITOLA")
    e_espac  = campo(6, "Espaçamento (cm):",  ESPACAMENTO, "ESPAC")

    tk.Button(root, text="Desenhar", command=on_ok, width=14).grid(row=14, column=0, columnspan=2, pady=12)
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

    while True:
        icod, xf1, yf1 = eag.locate.GetPoint(tqsjan, f"Início da {faixa_count}ª faixa (ou <Esc> para encerrar)")
        if icod != 1: break

        icod, xf2, yf2 = eag.locate.GetSecondPoint(
            tqsjan, xf1, yf1, TQSEag.EAG_RUBLINEAR, TQSEag.EAG_RUBRET_NAOPREEN, f"Fim da {faixa_count}ª faixa"
        )
        if icod != 1: break

        xc, yc = (xf1 + xf2) / 2, (yf1 + yf2) / 2
        ang_faixa = TQSGeo.Angle2p(xf1, yf1, xf2, yf2)

        rebar.RebarDistrAdd(
            TQSDwg.ICPE1P, ang_faixa,
            xf1, yf1, xf2, yf2, xc, yc,
            0, 1, 1, 0, 1,                  # Flags de exibição (cotar, n ferros, pos, bitola, espac)
            TQSDwg.ICPCENTR_CENTRAD,        # Alinhamento centrado
            TQSDwg.ICPQUEBR_SEMQUEBRA,      # Sem quebra de linha
            "NPBEC", 0, 0, 0, 1, 0,         # Ordem, k32, k41, exten, chamada, flecha
            espacamento, 1.0                # Espaçamento e escala
        )
        faixa_count += 1

    eag.msg.Print(f"{faixa_count - 1} faixa(s) adicionada(s).")


# ---------------------------------------------------------------------------
# Detalhe do ferro em concreto
# ---------------------------------------------------------------------------
def desenhar_box_detalhe(dwg, eag, tqsjan, rebar, x_base, y_base, pontos_concreto, anotacoes):
    """Desenha o bloco 'DETALHE POSIÇÃO Nxx', o contorno de concreto e setas."""
    escala_dwg = dwg.settings.scale if dwg.settings.scale > 0 else 50.0
    h_texto = 0.2 * escala_dwg

    cor_antiga = dwg.draw.color
    nivel_antigo = dwg.draw.level

    # --- 1. Título "DETALHE POSIÇÃO Nxx" ---
    titulo = f"DETALHE POSIÇÃO N{rebar.mark}"
    x_titulo = x_base + INP1
    y_titulo = y_base + 100

    dwg.draw.color = 4  # ciano
    dwg.draw.Text(x_titulo, y_titulo, h_texto * 1.2, 0.0, titulo)

    dwg.draw.color = 15  # branco
    largura_box = len(titulo) * h_texto * 1.3
    altura_box = h_texto * 3.0
    bx1, by1 = x_titulo - h_texto * 1.5, y_titulo - h_texto
    bx2, by2 = x_titulo + largura_box, y_titulo + altura_box
    
    pontos_box = [(bx1, by1), (bx2, by1), (bx2, by2), (bx1, by2), (bx1, by1)]
    
    dwg.draw.PolyStart()
    for px, py in pontos_box:
        dwg.draw.PolyEnterPoint(px, py)
    dwg.draw.Polyline()

    # --- 2. Vigas de concreto 228 ---
    if pontos_concreto and len(pontos_concreto) >= 2:
        dwg.draw.color = 15  # branco
        dwg.draw.level = 228
        # desloca -45 cm para a esquerda (eixo X) do primeiro ponto
        dwg.draw.PolyStart()
        for px, py in pontos_concreto:
            dwg.draw.PolyEnterPoint(px, py)
        dwg.draw.Polyline()

    # --- 3. Setas e labels ---
    if anotacoes:
        dwg.draw.color = 6  # magenta/roxo
        dwg.draw.level = 239
 
        for txt, x_txt, y_txt, x_seta, y_seta in anotacoes:
            dwg.draw.Text(x_txt, y_txt + (h_texto * 0.3), h_texto, 0.0, txt)
            largura_linha = len(txt) * h_texto * 1.25
 
            px_inicio = x_txt + largura_linha if x_seta < x_txt else x_txt
            px_dobra = x_txt if x_seta < x_txt else x_txt + largura_linha
 
            dwg.draw.Line(px_inicio, y_txt, px_dobra, y_txt)
 
            dx, dy = x_seta - px_dobra, y_seta - y_txt
            distancia_seta = TQSGeo.Distance(px_dobra, y_txt, x_seta, y_seta)
 
            if distancia_seta > 0.1:
                dwg.draw.Line(px_dobra, y_txt, x_seta, y_seta)
 
                cos_a, sin_a = dx / distancia_seta, dy / distancia_seta
                L = h_texto * 0.8
                W = L / 3.0
 
                x_left = x_seta - (L * cos_a) - (W * sin_a)
                y_left = y_seta - (L * sin_a) + (W * cos_a)
                x_right = x_seta - (L * cos_a) + (W * sin_a)
                y_right = y_seta - (L * sin_a) - (W * cos_a)
 
                dwg.draw.PolyStart()
                for p_seta in [(x_seta, y_seta), (x_left, y_left), (x_right, y_right), (x_seta, y_seta)]:
                    dwg.draw.PolyEnterPoint(*p_seta)
                dwg.draw.PolylineFilled()

    dwg.draw.color = cor_antiga
    dwg.draw.level = nivel_antigo
    tqsjan.Regen()


# ---------------------------------------------------------------------------
# Função principal chamada pelo menu TQS
# ---------------------------------------------------------------------------
def aplic_desenhar(eag, tqsjan):
    eag.msg.Print("Inserção de Ferro Rabo de Porco - Iniciada")

    # --- 1. Coleta de pontos da viga ---
    icod1, x1, y1 = eag.locate.GetPoint(tqsjan, "Clique no primeiro ponto da viga")
    if icod1 != 1: return eag.msg.Print("Cancelado.")

    icod2, x2, y2 = eag.locate.GetSecondPoint(
        tqsjan, x1, y1, TQSEag.EAG_RUBLINEAR, TQSEag.EAG_RUBRET_NAOPREEN, "Clique no segundo ponto da viga"
    )
    if icod2 != 1: return eag.msg.Print("Cancelado.")
    
    dist_orig_p1 = TQSGeo.Distance(0, 0, x1, y1)
    dist_orig_p2 = TQSGeo.Distance(0, 0, x2, y2)
    if dist_orig_p2 > dist_orig_p1:
        x1, y1, x2, y2 = x2, y2, x1, y1  # Garante que (x1, y1) seja o ponto mais distante da origem

    tamanho_viga = TQSGeo.Distance(x1, y1, x2, y2)
    angulo_inclinacao = TQSGeo.Angle2p(x1, y1, x2, y2)

    if DEBUG:
        eag.msg.Print(f"Tamanho da viga: {tamanho_viga:.2f} cm, Ângulo de inclinação: {angulo_inclinacao:.2f}°")
        eag.msg.Print(f"Distância do ponto 1 à origem: {dist_orig_p1:.2f} cm, Distância do ponto 2 à origem: {dist_orig_p2:.2f} cm\n INVERTE: {dist_orig_p2 > dist_orig_p1}")

    # --- 2. Janela de medidas ---
    medidas = obter_medidas()
    if not medidas: return eag.msg.Print("Cancelado ou medidas inválidas.")
    ESP_L1, ESP_L2, DESNIVEL, INP1, INP2, BITOLA, ESPACAMENTO = medidas

    # --- 3. Configurar SmartRebar ---
    dwg = tqsjan.dwg
    rebar = TQSDwg.SmartRebar(dwg)
    rebar.type = TQSDwg.ICPFGN
    rebar.mark = dwg.globalrebar.FreeMark()
    rebar.diameter = BITOLA
    rebar.spacing = ESPACAMENTO
    rebar.leaderLine = 0
    rebar.bendTotalLengthMode = TQSDwg.ICPSMS
    rebar.bendBendLengthMode = TQSDwg.ICPDOBSMS

    # --- 4. Calcular trechos e registrar pontos ---
    T1 = ESP_L1 - COBRIMENTO_LAJE
    T2 = INP1
    T4 = tamanho_viga - COBRIMENTO_VIGA
    T6 = INP2
    T7 = ESP_L2 - COBRIMENTO_LAJE

    rebaixo_negativo = DESNIVEL < 0
    if rebaixo_negativo:
        DESNIVEL = abs(DESNIVEL)
        T3 = DESNIVEL + ESP_L2 - 4
        T5 = ESP_L2 - 4
        pontos_rebar = [
            (0.0,          0.0,              0.0),
            (0.0,          T1,               0.0),
            (T2,           T1,               0.0),
            (T2,           T1 - T3,          0.0),
            (T2 - T4,      T1 - T3,          0.0),
            (T2 - T4,      T1 - T3 + T5,     0.0),
            (T2 - T4 + T6, T1 - T3 + T5,     0.0),
            (T2 - T4 + T6, T1 - T3 + T5 - T7,0.0),
        ]
    else:
        T3 = DESNIVEL + ESP_L1 - 4
        T5 = ESP_L1 - 4
        pontos_rebar = [
            (0.0,          0.0,              0.0),
            (0.0,          T1,               0.0),
            (T2,           T1,               0.0),
            (T2,           T1 - T5,          0.0),
            (T2 - T4,      T1 - T5,          0.0),
            (T2 - T4,      T1 - T5 + T3,     0.0),
            (T2 - T4 + T6, T1 - T5 + T3,     0.0),
            (T2 - T4 + T6, T1 - T5 + T3 - T7,0.0),
        ]

    for x, y, z in pontos_rebar:
        rebar.GenRebarPoint(x, y, z, 0, 1, -1)

    # --- 5. Faixa de distribuição ---
    adicionar_faixa(rebar, eag, tqsjan, ESPACAMENTO)

    # --- 6. Legenda do ferro ---
    icod_leg, x_leg, y_leg = eag.locate.GetPoint(tqsjan, "Clique para posicionar a legenda do ferro")
    if icod_leg != 1: return eag.msg.Print("Posicionamento da legenda cancelado.")
    rebar.RebarLine(x_leg, y_leg, 0.0, 2.0, 1, 1, 0, 0, 220, -1, -1)

    # --- 7. Linha de ferro na viga ---
    xins = x1 - (T2 - T4 - COBRIMENTO_VIGA / 2)
    yins = y2
    xins_rot, yins_rot = TQSGeo.Rotate(xins, yins, angulo_inclinacao, x1, y1)

    if DEBUG:
        eag.msg.Print(f"x1: {x1:.2f}, y1: {y1:.2f}, x2: {x2:.2f}, y2: {y2:.2f}")
        eag.msg.Print(f"xins: {xins:.2f}, yins: {yins:.2f}")

    rebar.RebarLine(xins_rot, yins_rot, angulo_inclinacao, 1.0, 0, 0, 0, 0, 201, -1, -1)

    # --- 8. Linha do detalhe de concreto ---
    x_base, y_base = x_leg, y_leg + 200
    rebar.RebarLine(x_base, y_base, 0.0, 2.0, 0, 0, 0, 0, 239, -1, -1)
    tqsjan.Regen()

    # --- 9. Detalhe de concreto ---
    DESLOCAMENTO_DETALHE = 22.5
    INP1 += DESLOCAMENTO_DETALHE

    if not rebaixo_negativo: INP2 += DESLOCAMENTO_DETALHE

    px, py = x_base - DESLOCAMENTO_DETALHE*2, y_base
    p_concreto = [(px, py)]

    py += ESP_L1 * 2; p_concreto.append((px, py))
    px += (INP1 + 2.5) * 2 if rebaixo_negativo else (INP1 - (T4 + 2.5)) * 2; p_concreto.append((px, py))
    py -= DESNIVEL * 2 if rebaixo_negativo else -(DESNIVEL * 2); p_concreto.append((px, py))
    px += INP2 * 2 if rebaixo_negativo else (INP2 + 2.5) * 2; p_concreto.append((px, py))
    py -= ESP_L2 * 2 if rebaixo_negativo else (ESP_L2) * 2; p_concreto.append((px, py))
    px -= INP2 * 2 if rebaixo_negativo else (INP2 - T4 - 2.5) * 2; p_concreto.append((px, py))
    py -= 100; p_concreto.append((px, py))
    px -= tamanho_viga * 2; p_concreto.append((px, py))
    py = y_base; p_concreto.append((px, py))
    px = x_base; p_concreto.append((px, py))
    
    p_concreto.append(p_concreto[0])  # fecha o polígono

    if DEBUG and eag:
        for idx, (p_x, p_y) in enumerate(p_concreto):
            eag.msg.Print(f"  Ponto {idx}: ({p_x:.2f}, {p_y:.2f})")

    p1_x, p1_y = (p_concreto[1][0] + p_concreto[2][0]) / 2, (p_concreto[1][1] + p_concreto[2][1]) / 2
    p2_x, p2_y = (p_concreto[3][0] + p_concreto[4][0]) / 2, (p_concreto[3][1] + p_concreto[4][1]) / 2
    p3_x, p3_y = (p_concreto[6][0] + p_concreto[7][0]) / 2, (p_concreto[6][1] + p_concreto[7][1]) / 2

    desenhar_box_detalhe(
        dwg, eag, tqsjan, rebar, x_base, y_base, p_concreto,
        anotacoes=[
            ("L1", p1_x + 30, p1_y + 20, p1_x, p1_y),
            ("V2", p2_x + 30, p2_y + 20, p2_x, p2_y),
            ("V1", p3_x + 30, p3_y,      p3_x, p3_y),
        ]
    )

    eag.msg.Print(f"Ferro Especial N{rebar.mark} inserido com sucesso!")