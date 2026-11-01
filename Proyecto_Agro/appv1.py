import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import base64
import os
import plotly.express as px

# --- FUNCIONES AUXILIARES ---
def extraer_kilos(texto, peso_defecto_caja):
    texto = str(texto).lower().strip()
    if 'kilogramo' in texto or texto == 'kg': return 1.0
    numeros = re.findall(r'\d+', texto)
    if numeros: return float(numeros[-1])
    return peso_defecto_caja

def dia_a_fecha(dia_anio):
    fecha_generica = datetime(2024, 1, 1) + timedelta(days=int(dia_anio) - 1)
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    return f"{fecha_generica.day} de {meses[fecha_generica.month - 1]}"

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded_string}"
    return ""

# --- 1. CONFIGURACIÓN DE PÁGINA Y CSS PREMIUM ---
st.set_page_config(page_title="Cuando Siembro | Inteligencia Agrícola", page_icon="🌱", layout="wide", initial_sidebar_state="collapsed")

# Cargar imágenes locales
logo_principal = get_image_base64("logo_principal.png") 
logo_sniim = get_image_base64("image_ae35e8.png")
logo_fira = get_image_base64("image_ae3663.png")
logo_siap = get_image_base64("image_ae39aa.png")
img_dron = get_image_base64("dron.jpg")
img_agricultor = get_image_base64("agricultor.jpg")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Open+Sans:wght@400;600&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Open Sans', sans-serif;
        background-color: #F8F9FA !important;
        color: #4A5568 !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif !important;
        color: #1b3b22 !important;
        font-weight: 800 !important;
    }}

    /* === AJUSTE 1: HEADER MÁS COMPACTO === */
    .header-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 5px 30px; /* Menos espacio arriba y abajo */
        background-color: #FFFFFF; 
        border-bottom: 1px solid #E2E8F0;
        margin: -3rem -3rem 1.5rem -3rem; /* Menos margen inferior */
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }}
    .logo-main {{ height: 75px; object-fit: contain; }} /* Logo más pequeño */
    .nav-links a {{ color: #4A5568; text-decoration: none; margin-right: 25px; font-weight: 600; font-family: 'Inter', sans-serif; }}
    .btn-login {{ padding: 6px 16px; border: 2px solid #1b3b22; border-radius: 6px; color: #1b3b22 !important; font-weight: bold; text-decoration: none; transition: 0.3s; font-size: 0.95rem; }}
    .btn-login:hover {{ background-color: #1b3b22; color: white !important; }}

    /* === AJUSTE 2: HERO SECTION OPTIMIZADA PARA MOSTRAR FORMULARIO === */
    .hero-wrapper {{
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 300px; /* Altura reducida (antes 400px) */
        margin-bottom: 1.5rem; /* Margen inferior reducido */
        overflow: hidden; 
        border-radius: 20px;
        background-color: #E2E8F0; 
    }}
    
    .hero-bg-left {{
        position: absolute;
        left: 0;
        top: 0;
        width: 35%; 
        height: 100%;
        object-fit: cover;
        border-radius: 0 50% 50% 0 / 0 30% 70% 0; 
        z-index: 1;
    }}

    .hero-bg-right {{
        position: absolute;
        right: 0;
        top: 0;
        width: 35%;
        height: 100%;
        object-fit: cover;
        border-radius: 50% 0 0 50% / 30% 0 0 70%; 
        z-index: 1;
    }}

    /* Tarjeta central más delgada y texto ajustado */
    .hero-text-card {{
        position: relative;
        z-index: 2; 
        background-color: rgba(255, 255, 255, 0.95);
        padding: 1.5rem 2rem; /* Menos relleno interno */
        border-radius: 15px;
        max-width: 60%; /* Ligeramente más ancha para evitar saltos de línea */
        text-align: center;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    }}
    
    .hero-title {{ font-size: 2.2rem !important; margin-bottom: 0.6rem; line-height: 1.2; }} /* Título ligeramente más pequeño */
    .hero-subtitle {{ font-size: 1.05rem; color: #4A5568; margin-bottom: 0; font-weight: 400; line-height: 1.4; }} /* Subtítulo ajustado */

    /* Formularios y Botones */
    div.stButton > button:first-child {{
        background-color: #C18E3B !important; color: white !important; font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important; font-size: 1rem !important; padding: 0.6rem 1.5rem !important;
        border-radius: 8px !important; border: none !important; width: 100%; transition: all 0.3s ease;
    }}
    div.stButton > button:first-child:hover {{ background-color: #A67830 !important; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(193, 142, 59, 0.3); }}
    .logos-container {{ display: flex; justify-content: center; align-items: center; gap: 35px; margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0; }}
    .footer-logo {{ height: 40px; object-fit: contain; filter: grayscale(100%); opacity: 0.7; transition: all 0.3s ease; }}
    .footer-logo:hover {{ filter: grayscale(0%); opacity: 1; }}
    .stMetric {{ background-color: #ffffff; padding: 15px; border-radius: 12px; border-left: 5px solid #1b3b22; box-shadow: 0 2px 10px rgba(0,0,0,0.04); }}
    </style>
""", unsafe_allow_html=True)

# --- 2. HEADER ---
if logo_principal:
    st.markdown(f"""
        <div class="header-container">
            <div><img src="{logo_principal}" class="logo-main" alt="Cuando Siembro"></div>
            <div class="nav-links">
                <a href="#">Soporte</a>
                <a href="#" class="btn-login">Iniciar Sesión</a>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. HERO SECTION ---
dron_html = f'<img src="{img_dron}" class="hero-bg-left">' if img_dron else ''
agricultor_html = f'<img src="{img_agricultor}" class="hero-bg-right">' if img_agricultor else ''

st.markdown(f"""
    <div class='hero-wrapper'>
        {dron_html}
        {agricultor_html}
        <div class='hero-text-card'>
            <h1 class='hero-title'>¿Cuándo sembrar para obtener un mejor precio?</h1>
            <p class='hero-subtitle'>Comparamos el histórico de precios del SNIIM con los paquetes tecnológicos de FIRA y el clima de tu región para calcular tu ventana de siembra más rentable.</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 4. CONFIGURACIÓN DEL CULTIVO ---
st.markdown("### Configuración de la Simulación")
col_busq1, col_busq2, col_busq3, col_busq4 = st.columns([2, 2, 2, 2])
with col_busq1:
    cultivo_seleccionado = st.selectbox("1. ¿Qué cultivo?", ["Tomate Saladette", "Girasol amarillo híbrido (Próximamente)", "Lechuga Fernandola (Próximamente)"], index=0)
with col_busq2:
    ubicacion = st.selectbox("2. ¿Dónde estás?", ["Tehuacán, Puebla", "Ajalpan, Puebla", "Tecamachalco, Puebla"], index=0)
with col_busq3:
    meta_mercado = st.selectbox("3. Meta de Mercado", ["Quiero el mejor precio de venta", "Tengo una fecha exacta"])
with col_busq4:
    st.markdown("<br>", unsafe_allow_html=True)
    ejecutar_btn = st.button("CALCULAR VENTANA DE RENTABILIDAD")

st.markdown(f"""
    <div class='logos-container'>
        <span style='color: #718096; font-size: 0.9em;'>Con tecnología e información oficial de:</span>
        <img src='{logo_sniim}' class='footer-logo' alt='SNIIM'>
        <img src='{logo_fira}' class='footer-logo' alt='FIRA'>
        <img src='{logo_siap}' class='footer-logo' alt='SIAP'>
        <span style='font-family: Inter; font-weight: 800; color: #4A5568; font-size: 1.2rem; opacity: 0.7;'>NASA POWER</span>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

# --- 5. BARRA LATERAL ---
st.sidebar.markdown("### ⚙️ Parámetros del Productor")
area_ha = st.sidebar.number_input("Superficie (Hectáreas)", value=1.0, step=0.5)
rendimiento_ton_ha = st.sidebar.number_input("Rendimiento Esperado (Ton/Ha)", value=80)
dias_veg = st.sidebar.number_input("Días de Desarrollo", value=90)
dias_cos = st.sidebar.number_input("Días de Cosecha", value=40)
COSTO_BASE = 7.80 
inflacion_insumos = st.sidebar.slider("Inflación de Insumos (%)", -10, 50, 0)
costo_dinamico = COSTO_BASE * (1 + (inflacion_insumos / 100))
inversion_total = area_ha * rendimiento_ton_ha * 1000 * costo_dinamico

# --- 6. MOTOR ANALÍTICO ---
st.markdown("### 📥 Archivos del Proyecto")
col_data1, col_data2 = st.columns(2)
with col_data1: archivo_precios = st.file_uploader("Sube tu Histórico de Precios (.csv o .xlsx)", type=["csv", "xls", "xlsx"])
with col_data2: archivo_clima = st.file_uploader("Sube tu Histórico Climático (.csv)", type=["csv"])

if ejecutar_btn:
    if archivo_precios is None or archivo_clima is None:
        st.warning("⚠️ Carga los archivos históricos de precios y clima para que el motor pueda calcular la rentabilidad.")
    else:
        with st.spinner("Procesando millones de datos climáticos y comerciales..."):
            df_p_raw = pd.read_csv(archivo_precios, header=None) if archivo_precios.name.endswith('.csv') else pd.read_excel(archivo_precios, header=None)
            df_c_raw = pd.read_csv(archivo_clima)

            df_precios = pd.DataFrame()
            df_precios['Fecha'] = pd.to_datetime(df_p_raw[0], dayfirst=True, errors='coerce')
            df_precios['Presentacion'] = df_p_raw[1].astype(str)
            df_precios['Precio_Caja'] = pd.to_numeric(df_p_raw[5], errors='coerce')
            df_precios = df_precios.dropna(subset=['Fecha', 'Precio_Caja'])
            df_precios['Kilos'] = df_precios['Presentacion'].apply(lambda x: extraer_kilos(x, 14.0))
            df_precios['Precio_Base'] = (df_precios['Precio_Caja'] / df_precios['Kilos']).round(2)
            
            df_clima = pd.DataFrame()
            df_clima['Fecha'] = pd.to_datetime(df_c_raw.iloc[:, 0], errors='coerce')
            for col in df_c_raw.columns[1:]: df_clima[col] = df_c_raw[col]
            df_clima = df_clima.dropna(subset=['Fecha'])
            
            fecha_min = df_precios['Fecha'].min()
            fecha_max = df_clima['Fecha'].max()
            df_maestro = pd.merge(df_clima[(df_clima['Fecha'] >= fecha_min) & (df_clima['Fecha'] <= fecha_max)], df_precios[['Fecha', 'Precio_Base']], on='Fecha', how='left')
            df_maestro = df_maestro.sort_values('Fecha').reset_index(drop=True)
            df_maestro['Precio_Base'] = df_maestro['Precio_Base'].ffill().bfill()

            st.markdown("---")
            if meta_mercado == "Quiero el mejor precio de venta":
                st.markdown("## 🔮 Oráculo de Rentabilidad (Estacionalidad)")
                
                df_maestro['Dia_Anio'] = df_maestro['Fecha'].dt.dayofyear
                perfil_anual = df_maestro.groupby('Dia_Anio').agg({'Precio_Base': 'mean', 'Temp_Max_C': 'mean', 'Temp_Min_C': 'mean'}).reset_index()
                perfil_extendido = pd.concat([perfil_anual, perfil_anual]).reset_index(drop=True)
                
                res = []
                for dia_inicio in range(365):
                    mercado_cos = perfil_extendido.iloc[dia_inicio + dias_veg : dia_inicio + dias_veg + dias_cos]
                    clima_veg = perfil_extendido.iloc[dia_inicio : dia_inicio + dias_veg]
                    precio_esp = mercado_cos['Precio_Base'].mean()
                    ingreso_esp = area_ha * rendimiento_ton_ha * 1000 * precio_esp
                    roi_esp = ((ingreso_esp - inversion_total) / inversion_total) * 100 if inversion_total > 0 else 0
                    riesgo_frio = len(clima_veg[clima_veg['Temp_Min_C'] < 12.0])
                    res.append({'Dia': dia_inicio + 1, 'Fecha': dia_a_fecha(dia_inicio + 1), 'ROI': roi_esp, 'Precio': precio_esp, 'Frio': riesgo_frio})
                
                df_pred = pd.DataFrame(res).sort_values('ROI', ascending=False)
                best = df_pred.iloc[0]
                
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("🥇 Ventana Óptima de Siembra", best['Fecha'], f"ROI Proyectado: {best['ROI']:.1f}%")
                with c2: st.metric("💰 Precio Promedio Esperado", f"${best['Precio']:.2f} / kg", f"Meta FIRA: >${costo_dinamico:.2f}")
                with c3: st.metric("🌡️ Riesgo Agroclimático", f"{best['Frio']} Días", "Días con frío crítico (<12°C)", delta_color="inverse")
                
                st.markdown("### 📈 Curva Estacional de Retorno de Inversión (ROI %)")
                
                df_graf = df_pred.sort_values('Dia').copy()
                df_graf['Fecha_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_graf['Dia'] - 1, unit='D')
                
                fig = px.line(df_graf, x='Fecha_Plot', y='ROI', labels={'Fecha_Plot': 'Día de Trasplante', 'ROI': 'ROI Proyectado (%)'}, hover_data={'Fecha_Plot': '|%d de %b'})
                fig.update_traces(line_color='#1b3b22', line_width=3)
                fig.add_hline(y=0, line_dash="dash", line_color="#F44336", annotation_text="Equilibrio (0%)")
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=True, gridcolor='#E2E8F0', tickformat='%d %b'), yaxis=dict(showgrid=True, gridcolor='#E2E8F0'), hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("## 📊 Análisis Histórico")
                st.dataframe(df_maestro[['Fecha', 'Precio_Base', 'Temp_Max_C', 'Temp_Min_C']].tail(15), use_container_width=True)