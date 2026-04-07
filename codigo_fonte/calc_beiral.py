import streamlit as st
import tempfile
import os

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

def draw_beiral_svg(esp, larg, tem_p):
    larg_m = larg / 100.0
    
    # Construindo o SVG (para visualização no site)
    svg = '<svg width="100%" height="250" viewBox="0 0 400 250" xmlns="http://www.w3.org/2000/svg">\n'
    svg += '<path d="M 30 70 L 50 50 M 30 110 L 50 90 M 30 150 L 50 130 M 30 190 L 50 170" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="50" y1="50" x2="50" y2="200" stroke="black" stroke-width="2"/>\n'
    svg += '<rect x="50" y="100" width="200" height="35" fill="none" stroke="black" stroke-width="2"/>\n'
    svg += '<text x="25" y="85" font-family="sans-serif" font-size="18" font-weight="bold">q</text>\n'
    svg += '<line x1="50" y1="70" x2="250" y2="70" stroke="black" stroke-width="1.5"/>\n'
    
    # Setinhas do q
    for x in range(50, 251, 40):
        svg += f'<line x1="{x}" y1="70" x2="{x}" y2="100" stroke="black" stroke-width="1"/>\n'
        svg += f'<polygon points="{x-3},95 {x+3},95 {x},100" fill="black"/>\n'
        
    if tem_p:
        svg += '<text x="255" y="45" font-family="sans-serif" font-size="18" font-weight="bold" fill="black">P</text>\n'
        svg += '<line x1="250" y1="40" x2="250" y2="100" stroke="black" stroke-width="2"/>\n'
        svg += '<polygon points="245,90 255,90 250,100" fill="black"/>\n'
        
    # Cotas
    svg += '<line x1="50" y1="160" x2="250" y2="160" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="50" y1="155" x2="50" y2="165" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="250" y1="155" x2="250" y2="165" stroke="black" stroke-width="1"/>\n'
    svg += f'<text x="150" y="180" font-family="sans-serif" font-size="14" text-anchor="middle">{larg_m:.2f} m</text>\n'
    
    svg += '<line x1="270" y1="100" x2="270" y2="135" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="265" y1="100" x2="275" y2="100" stroke="black" stroke-width="1"/>\n'
    svg += '<line x1="265" y1="135" x2="275" y2="135" stroke="black" stroke-width="1"/>\n'
    svg += f'<text x="285" y="122" font-family="sans-serif" font-size="14">{esp:.0f} cm</text>\n'
    svg += '</svg>'
    return svg

def gerar_pdf(nome, larg, esp, q1, q2, peso_laje, q_total, tem_p, esp_n, alt_n, peso_nerv, guarda_corpo, p_total, m_total, maj, msk):
    pdf = FPDF()
    pdf.add_page()
    
    # --- 1. CABEÇALHO ---
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(150, 0, 0) # Vermelho escuro para o título
    pdf.cell(0, 10, f"# CALCULO DE BEIRAL : {nome}", 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_text_color(0, 0, 100) # Azul escuro para subtítulo
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"> Beiral 1: seçao de {larg:.0f}cm", 0, 1, 'L')
    pdf.set_text_color(0, 0, 0)
    
    y_inicio_colunas = pdf.get_y() + 5

    # --- 2. DESENHO NATIVO NO PDF (ESQUERDA) ---
    bx = 20 # Posição X base do desenho
    by = y_inicio_colunas + 5 # Posição Y base do desenho
    
    # Parede
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.5)
    pdf.line(bx, by, bx, by + 42) # Linha vertical
    pdf.set_line_width(0.2)
    for i in range(0, 42, 8): # Hachuras
        pdf.line(bx - 4, by + i + 4, bx, by + i)
        
    # Laje (Beiral)
    w_laje = 60
    h_laje = 10
    pdf.set_line_width(0.5)
    pdf.rect(bx, by + 15, w_laje, h_laje)
    
    # Carga q
    pdf.set_line_width(0.4)
    y_q = by + 5
    pdf.line(bx, y_q, bx + w_laje, y_q)
    pdf.set_font("Arial", 'B', 10)
    pdf.text(bx - 5, y_q, "q")
    
    # Setinhas do q
    for dx in range(0, w_laje + 1, 12):
        pdf.line(bx + dx, y_q, bx + dx, by + 15)
        pdf.line(bx + dx, by + 15, bx + dx - 1.5, by + 13)
        pdf.line(bx + dx, by + 15, bx + dx + 1.5, by + 13)
        
    # Carga P
    if tem_p:
        pdf.set_line_width(0.6)
        x_p = bx + w_laje
        y_p_start = by - 5
        pdf.line(x_p, y_p_start, x_p, by + 15)
        pdf.line(x_p, by + 15, x_p - 2.5, by + 12)
        pdf.line(x_p, by + 15, x_p + 2.5, by + 12)
        pdf.set_font("Arial", 'B', 10)
        pdf.text(x_p + 2, y_p_start + 4, "P")
        
    # Cotas
    pdf.set_line_width(0.2)
    y_cota_larg = by + 32
    pdf.line(bx, y_cota_larg, bx + w_laje, y_cota_larg)
    pdf.line(bx, y_cota_larg - 2, bx, y_cota_larg + 2)
    pdf.line(bx + w_laje, y_cota_larg - 2, bx + w_laje, y_cota_larg + 2)
    pdf.set_font("Arial", '', 10)
    pdf.text(bx + w_laje/2 - 6, y_cota_larg + 5, f"{larg/100:.2f} m")
    
    x_cota_esp = bx + w_laje + 8
    pdf.line(x_cota_esp, by + 15, x_cota_esp, by + 15 + h_laje)
    pdf.line(x_cota_esp - 2, by + 15, x_cota_esp + 2, by + 15)
    pdf.line(x_cota_esp - 2, by + 15 + h_laje, x_cota_esp + 2, by + 15 + h_laje)
    pdf.text(x_cota_esp + 3, by + 15 + h_laje/2 + 2, f"{esp:.0f} cm")


    # --- 3. TEXTOS DAS CARGAS (DIREITA) ---
    x_text = 110 # Coluna da direita começa no X=100
    pdf.set_xy(x_text, y_inicio_colunas)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "* Cargas distribuidas (q)", 0, 1, 'L')
    
    pdf.set_font("Arial", '', 11)
    pdf.set_x(x_text + 7)
    pdf.cell(0, 6, f"> Permanente: {q1:.3f} tf/m2", 0, 1, 'L')
    pdf.set_x(x_text + 7)
    pdf.cell(0, 6, f"> Acidental: {q2:.3f} tf/m2", 0, 1, 'L')
    pdf.set_x(x_text + 7)
    pdf.cell(0, 6, f"> Peso proprio: 2.5 x {esp/100:.2f} = {peso_laje:.3f} tf/m2", 0, 1, 'L')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.set_x(x_text + 10)
    pdf.cell(0, 6, f"E q = {q_total:.3f} tf/m2", 0, 1, 'L')
    pdf.ln(4)
    
    pdf.set_x(x_text)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "* Carga concentrada (P)", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    
    if tem_p:
        pdf.set_x(x_text + 7)
        pdf.cell(0, 6, f"> Nervura N1 ({esp_n:.0f}x{alt_n:.0f})", 0, 1, 'L')
        pdf.set_x(x_text + 7)
        pdf.cell(0, 6, f"> Peso proprio = {esp_n/100:.2f} x {alt_n/100:.2f} x 2.5 = {peso_nerv:.3f} tf/m", 0, 1, 'L')
    if guarda_corpo > 0:
        pdf.set_x(x_text + 7)
        pdf.cell(0, 6, f"> Guarda-corpos = {guarda_corpo:.3f} tf/m", 0, 1, 'L')
    if not tem_p and guarda_corpo == 0:
        pdf.set_x(x_text + 7)
        pdf.cell(0, 6, "> Nenhuma", 0, 1, 'L')
    else:
        pdf.set_font("Arial", 'B', 11)
        pdf.set_x(x_text + 10)
        pdf.cell(0, 6, f"E P = {p_total:.3f} tf/m", 0, 1, 'L')
    

    # --- 4. RESULTADOS FINAIS (EMBAIXO) ---
    # Garantir que os cálculos finais fiquem abaixo do desenho e do texto
    y_atual = pdf.get_y()
    y_final = max(y_atual, by + 60) + 10
    pdf.set_xy(10, y_final)
    
    # Momento
    pdf.set_font("Arial", 'B', 12)
    formula = f"({q_total:.3f} x {larg/100:.2f} x {larg/200:.2f})"
    if p_total > 0:
        formula += f" + ({p_total:.3f} x {larg/100:.2f})"
    
    pdf.cell(0, 8, f"> Momento:  {formula} = M", 0, 1, 'L')
    pdf.set_x(40)
    pdf.cell(0, 8, f"M = {m_total:.3f} tf.m", 0, 1, 'L')
    pdf.ln(5)
    
    # Majoração
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "> MAJORAÇAO", 0, 1, 'L')
    pdf.set_font("Arial", '', 12)
    pdf.cell(10)
    pdf.cell(0, 8, f"Y = 1.95 - 0.05 x {esp:.0f} = {maj:.2f}", 0, 1, 'L')
    pdf.ln(8)
    
    # Resultado Final (Msk)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(10)
    pdf.cell(0, 10, f"Msk = {m_total:.3f} x {maj:.2f}  =  {msk:.2f} tf.m", 0, 1, 'L')
    
    # Gerar output do PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        pdf_bytes = tmp.read()
    os.remove(tmp.name)
    return pdf_bytes

# ==================================================
# FRONT-END (INTERFACE STREAMLIT)
# ==================================================

# Configuração da página
st.set_page_config(page_title="Cálculo de Beiral", layout="centered")

# Título Principal
st.title("🏗️ Cálculo de Beiral")
st.markdown("Automação de rotina de cálculo estrutural para balanços/beirais.")

st.divider()

# --- SECÇÃO 1: ENTRADA DE DADOS ---
st.header("1. Entrada de Dados")

nome_projeto = st.text_input("Nome do Projeto / Laje", value="16ª Laje - ÂNIMA MAJOR")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Dimensões da Laje")
    esp1 = st.number_input("Espessura do Beiral - esp1 (cm)", min_value=1.0, value=14.0, step=1.0)
    larg1 = st.number_input("Balanço/Largura - larg1 (cm)", min_value=1.0, value=110.0, step=1.0)

with col2:
    st.subheader("Cargas Distribuídas (q)")
    q1 = st.number_input("Carga Permanente - q1 (tf/m²)", min_value=0.0, value=0.3, step=0.05)
    q2 = st.number_input("Carga Acidental - q2 (tf/m²)", min_value=0.0, value=0.2, step=0.05)

st.subheader("Cargas Concentradas na Borda (P)")
col3, col4 = st.columns(2)

with col3:
    tem_nervura = st.checkbox("Possui Nervura de Borda?", value=True)
    if tem_nervura:
        esp_nervura = st.number_input("Espessura da Nervura (cm)", min_value=1.0, value=14.0, step=1.0)
        alt_nervura = st.number_input("Altura da Nervura (cm)", min_value=1.0, value=70.0, step=1.0)
    else:
        esp_nervura = 0.0
        alt_nervura = 0.0

with col4:
    tem_guarda_corpo = st.checkbox("Possui Guarda-corpos?", value=False)
    if tem_guarda_corpo:
        carga_guarda_corpo = st.number_input("Carga do Guarda-corpos (tf/m)", min_value=0.0, value=0.0, step=0.05)
    else:
        carga_guarda_corpo = 0.0


# --- SECÇÃO 2: PROCESSAMENTO / CÁLCULOS ---

# Conversão de unidades (cm para metros)
esp1_m = esp1 / 100.0
larg1_m = larg1 / 100.0

# 2.1 Cargas Distribuídas (q)
peso_proprio_laje = 2.5 * esp1_m
q_total = q1 + q2 + peso_proprio_laje

# 2.2 Cargas Concentradas (P)
peso_proprio_nervura = 0.0
if tem_nervura:
    # A área da secção transversal da nervura em m² vezes o peso específico do betão (2.5)
    peso_proprio_nervura = (esp_nervura / 100.0) * (alt_nervura / 100.0) * 2.5

p_total = peso_proprio_nervura + carga_guarda_corpo

# 2.3 Momento Fletor (M)
# Fórmula corrigida para balanço: (q * L^2 / 2) + (P * L)
momento_distribuida = q_total * larg1_m * (larg1_m / 2.0)
momento_concentrada = p_total * larg1_m
momento_total = momento_distribuida + momento_concentrada

# 2.4 Majorador e Msk
majorador = 1.95 - (0.05 * esp1)
msk = momento_total * majorador


# --- SECÇÃO 3: SAÍDA DE DADOS / RELATÓRIO ---
st.divider()
st.header("📄 Relatório de Cálculo (Saída)")

# Botão para simular a geração
if st.button("Gerar Memória de Cálculo"):
    
    st.success("Cálculo efetuado com sucesso! Verifique o relatório abaixo.")
    
    # Criar um container com estilo de documento
    with st.container():
        # --- LAYOUT ESTILO IMAGEM MANUSCRITA ---
        st.markdown(f"## <span style='color: darkred;'># CÁLCULO DE BEIRAL : {nome_projeto}</span>", unsafe_allow_html=True)
        st.markdown(f"### <span style='color: darkblue;'>&rarr; Beiral 1: seção de {larg1:.0f}cm</span>", unsafe_allow_html=True)
        
        col_img, col_calc = st.columns([1, 1])
        
        with col_img:
            # Renderiza o desenho SVG no painel esquerdo
            st.markdown(draw_beiral_svg(esp1, larg1, (p_total > 0)), unsafe_allow_html=True)
            
        with col_calc:
            # Renderiza os cálculos de distribuída no painel direito
            st.markdown("**\* Cargas distribuídas (q)**")
            st.markdown(f"&rarr; Permanente: {q1:.3f} tf/m²")
            st.markdown(f"&rarr; Acidental: {q2:.3f} tf/m²")
            st.markdown(f"&rarr; Peso próprio: 2.5 &times; {esp1_m:.2f} = {peso_proprio_laje:.3f} tf/m²")
            st.markdown(f"**&Sigma;q = {q_total:.3f} tf/m²**")
            
        st.write("---")
        
        st.markdown("**\* Carga concentrada (P)**")
        if tem_nervura:
            st.markdown(f"&rarr; Nervura N1 ({esp_nervura:.0f}x{alt_nervura:.0f})")
            st.markdown(f"&rarr; Peso próprio = {esp_nervura/100:.2f} &times; {alt_nervura/100:.2f} &times; 2.5 = {peso_proprio_nervura:.3f} tf/m")
        if tem_guarda_corpo:
            st.markdown(f"&rarr; Guarda-corpos = {carga_guarda_corpo:.3f} tf/m")
        if p_total > 0:
            st.markdown(f"**&Sigma;P = {p_total:.3f} tf/m**")
        else:
            st.markdown("&rarr; Nenhuma")
            
        st.write("---")
        
        formula_m = f"({q_total:.3f} &times; {larg1_m:.2f} &times; {larg1_m/2:.2f})"
        if p_total > 0:
            formula_m += f" + ({p_total:.3f} &times; {larg1_m:.2f})"
            
        st.markdown(f"**&rarr; Momento &orarr; :** {formula_m} = M")
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**M = {momento_total:.3f} tf.m**")
        
        st.markdown("**MAJORAÇÃO**")
        st.markdown(f"**&gamma;** = 1.95 - 0.05 &times; {esp1:.0f} = **{majorador:.2f}**")
        
        st.markdown(f"### Msk = {momento_total:.3f} &times; {majorador:.2f} = {msk:.2f} tf.m")
        
        # --- EXPORTAR PDF ---
        st.divider()
        if HAS_FPDF:
            pdf_bytes = gerar_pdf(nome_projeto, larg1, esp1, q1, q2, peso_proprio_laje, q_total, 
                                (p_total > 0), esp_nervura, alt_nervura, peso_proprio_nervura, 
                                carga_guarda_corpo, p_total, momento_total, majorador, msk)
                                
            st.download_button(
                label="📥 Baixar PDF do Relatório",
                data=pdf_bytes,
                file_name=f"Calculo_Beiral_{nome_projeto.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ A biblioteca 'fpdf' não está instalada. Para habilitar a exportação do PDF, instale executando o comando no terminal: `pip install fpdf`")