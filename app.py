import streamlit as st
import math
from datetime import datetime
from io import BytesIO
import pandas as pd

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

st.set_page_config(page_title="AirSide PRO", layout="wide")

# =========================
# FUNÇÕES DE ENGENHARIA
# =========================

def motor_current(cv, voltage=380, eff=0.9, pf=0.85):
    power_w = cv * 736
    current = power_w / (math.sqrt(3) * voltage * eff * pf)
    return round(current, 2)

def resistance_current(kw, voltage=380):
    if kw == 0:
        return 0
    return round((kw * 1000) / (math.sqrt(3) * voltage), 2)

def breaker_select(current):
    standard = [16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160]
    for b in standard:
        if current <= b:
            return b
    return standard[-1]

def cable_size(current):
    if current <= 16:
        return "2.5 mm²"
    elif current <= 25:
        return "4 mm²"
    elif current <= 32:
        return "6 mm²"
    elif current <= 50:
        return "10 mm²"
    elif current <= 63:
        return "16 mm²"
    elif current <= 80:
        return "25 mm²"
    else:
        return "35 mm²"

def busbar_dimension(current):
    density = 1.5
    section = current / density
    width = 20
    thickness = round(section / width, 2)
    return f"{width} x {thickness} mm"

def thermal_calc(num_motors, inverter=False):
    base = num_motors * 30
    if inverter:
        base += num_motors * 60
    return base

def ventilation_recommendation(thermal):
    if thermal < 200:
        return "Ventilação natural suficiente"
    elif thermal < 500:
        return "Instalar ventilador forçado"
    else:
        return "Necessário exaustor ou ar condicionado de painel"

# =========================
# INTERFACE
# =========================

st.title("🏭 AirSide PRO – Plataforma Interna de Engenharia HVAC")

st.sidebar.header("📌 Dados do Projeto")
cliente = st.sidebar.text_input("Cliente")
os = st.sidebar.text_input("Número da OS")
responsavel = st.sidebar.text_input("Responsável Técnico")
modelo = st.sidebar.selectbox("Modelo da Máquina", ["SMALL", "MEDIUM", "LARGE", "SPECIAL"])

st.header("⚙ Configuração de Motores")

num_motores = st.number_input("Quantidade de Motores", 1, 6, 1)

motor_currents = []
inverter_used = False

for i in range(num_motores):
    col1, col2 = st.columns(2)
    cv = col1.number_input(f"Motor {i+1} Potência (CV)", 0.5, 200.0, 5.0)
    partida = col2.selectbox(
        f"Tipo Partida Motor {i+1}",
        ["Direta", "Inversor", "Soft-starter"],
        key=f"partida_{i}"
    )

    current = motor_current(cv)
    motor_currents.append(current)

    if partida == "Inversor":
        inverter_used = True

    st.write(f"Corrente estimada: {current} A")

st.header("🔥 Resistência Trifásica Bifilar")

res_kw = st.number_input("Potência Total Resistência (kW)", 0.0, 500.0, 0.0)
res_current = resistance_current(res_kw)
st.write(f"Corrente resistência: {res_current} A")

# =========================
# CÁLCULOS GERAIS
# =========================

total_current = round(sum(motor_currents) + res_current, 2)
breaker = breaker_select(total_current)
cable = cable_size(total_current)
busbar = busbar_dimension(total_current)
thermal = thermal_calc(num_motores, inverter_used)
ventilation = ventilation_recommendation(thermal)

# =========================
# RESUMO EXECUTIVO
# =========================

st.header("📊 Resumo Executivo")

col1, col2, col3 = st.columns(3)
col1.metric("Corrente Total (A)", total_current)
col2.metric("Disjuntor Geral (A)", breaker)
col3.metric("Carga Térmica (W)", thermal)

st.subheader("🔌 Dimensionamento")
st.write(f"Bitola Recomendada: {cable}")
st.write(f"Barramento: {busbar}")

st.subheader("🌡 Ventilação Painel")
st.write(ventilation)

# =========================
# DIMENSIONAMENTO INTERNO
# =========================

st.header("📐 Dimensionamento Interno da Máquina")

col1, col2, col3 = st.columns(3)
altura = col1.number_input("Altura da Máquina (mm)", 500, 5000, 900)
largura = col2.number_input("Largura da Máquina (mm)", 500, 5000, 800)
profundidade = col3.number_input("Profundidade (mm)", 300, 3000, 600)

tensao = st.selectbox("Tensão de Alimentação", [220, 380])
rota = st.selectbox("Tipo de Roteamento Interno", ["Simples", "Organizado com curvas"])

fator = 1.4 if rota == "Simples" else 1.8
percurso_base = (altura + largura) / 1000
metragem_total = round(percurso_base * fator, 2)

num_condutores = 4 if tensao == 380 else 3
metragem_final = round(metragem_total * num_condutores, 2)

if "2.5" in cable or "4" in cable or "6" in cable:
    terminal = "Olhal M6"
elif "10" in cable or "16" in cable:
    terminal = "Olhal M8"
else:
    terminal = "Olhal M10"

terminais = num_condutores * 2

st.subheader("📊 Resultado do Cabeamento Interno")
st.write(f"Comprimento estimado por condutor: {metragem_total} m")
st.write(f"Metragem total de cabos: {metragem_final} m")
st.write(f"Quantidade de condutores: {num_condutores}")
st.write(f"Tipo de terminal recomendado: {terminal}")
st.write(f"Quantidade total de terminais: {terminais}")

# =========================
# LISTA DE MATERIAIS
# =========================

def gerar_lista_materiais():
    materiais = []

    materiais.append(["Disjuntor Geral", f"{breaker} A", 1])
    materiais.append(["Cabo Alimentação", cable, metragem_final])
    materiais.append(["Barramento Cobre", busbar, 1])
    materiais.append([f"Terminal {terminal}", terminal, terminais])

    for i in range(num_motores):
        materiais.append([f"Contator Motor {i+1}", "Compatível com corrente", 1])
        materiais.append([f"Relé Térmico Motor {i+1}", "Compatível com corrente", 1])
        materiais.append([f"Cabo Motor {i+1}", cable, metragem_total])
        materiais.append([f"Terminais Motor {i+1}", terminal, 6])

    if res_kw > 0:
        materiais.append(["Contator Resistência", "Compatível com potência", 1])
        materiais.append(["Disjuntor Resistência", "Curva C", 1])
        materiais.append(["Cabo Resistência", cable, metragem_total])
        materiais.append(["Terminais Resistência", terminal, 6])

    return pd.DataFrame(materiais, columns=["Item", "Especificação", "Quantidade"])

# =========================
# PDF
# =========================

def gerar_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("MEMORIAL TÉCNICO – AIRSIDE PRO", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    resumo = [
        ["Cliente", cliente],
        ["OS", os],
        ["Responsável", responsavel],
        ["Modelo", modelo],
        ["Corrente Total (A)", total_current],
        ["Disjuntor Geral (A)", breaker],
        ["Bitola Cabo", cable],
        ["Barramento", busbar],
    ]

    elements.append(Table(resumo))
    elements.append(Spacer(1, 0.4 * inch))

    elements.append(Paragraph("Lista de Materiais", styles["Heading2"]))
    df = gerar_lista_materiais()
    data = [df.columns.tolist()] + df.values.tolist()
    elements.append(Table(data))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# EXCEL
# =========================

def gerar_excel():
    df = gerar_lista_materiais()
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer

st.header("📦 Documentação")

if st.button("Gerar Memorial Técnico (PDF)"):
    pdf = gerar_pdf()
    st.download_button("Baixar PDF", pdf, file_name="Memorial_AirSide_PRO.pdf")

if st.button("Gerar Lista de Materiais (Excel)"):
    excel = gerar_excel()
    st.download_button("Baixar Excel", excel, file_name="Lista_Materiais_AirSide_PRO.xlsx")

st.success("AirSide PRO ativo e operacional.")
