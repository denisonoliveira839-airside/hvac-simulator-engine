import streamlit as st
import math
from datetime import datetime
from io import BytesIO
import pandas as pd

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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
    partida = col2.selectbox(f"Tipo Partida Motor {i+1}", ["Direta", "Inversor", "Soft-starter"], key=i)

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
# GERAR MEMORIAL PDF
# =========================

def gerar_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("MEMORIAL TÉCNICO – AIRSIDE PRO", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    data = [
        ["Cliente", cliente],
        ["OS", os],
        ["Responsável", responsavel],
        ["Data", str(datetime.now().date())],
        ["Modelo", modelo],
        ["Corrente Total (A)", total_current],
        ["Disjuntor Geral (A)", breaker],
        ["Bitola Cabo", cable],
        ["Barramento", busbar],
        ["Carga Térmica (W)", thermal],
        ["Ventilação", ventilation]
    ]

    table = Table(data)
    table.setStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# GERAR EXCEL
# =========================

def gerar_excel():
    df = pd.DataFrame({
        "Item": ["Disjuntor Geral", "Cabo Principal", "Barramento", "Carga Térmica"],
        "Especificação": [f"{breaker} A", cable, busbar, f"{thermal} W"]
    })

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
