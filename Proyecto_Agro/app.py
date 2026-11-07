import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import base64
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- IMPORTACIÓN DEL MOTOR DE CLIMA ---
try:
    from motor_clima import extraer_clima_historico
except ImportError:
    st.error("Falta el archivo 'motor_clima.py'.")

# --- BASE DE CONOCIMIENTO (PERFILES AGRONÓMICOS) ---
PERFILES_AGRONOMICOS = {
    "Tomate Saladette - Primera": {"unidad": "kg", "costo_sugerido": 7.80, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 80, "multiplicador": 1000, "veg": 90, "cos": 40},
    "Tomate Verde - Primera": {"unidad": "kg", "costo_sugerido": 5.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 40, "multiplicador": 1000, "veg": 75, "cos": 30},
    "Cebolla Bola - Primera": {"unidad": "kg", "costo_sugerido": 4.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 40, "multiplicador": 1000, "veg": 120, "cos": 20},
    "Cebolla Morada - Primera": {"unidad": "kg", "costo_sugerido": 5.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 35, "multiplicador": 1000, "veg": 120, "cos": 20},
    "Chile Jalapeño - Primera": {"unidad": "kg", "costo_sugerido": 6.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 40, "multiplicador": 1000, "veg": 90, "cos": 40},
    "Chile Poblano - Primera": {"unidad": "kg", "costo_sugerido": 8.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 30, "multiplicador": 1000, "veg": 100, "cos": 40},
    "Chile Serrano - Primera": {"unidad": "kg", "costo_sugerido": 7.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 35, "multiplicador": 1000, "veg": 90, "cos": 40},
    "Aguacate Hass - Primera": {"unidad": "kg", "costo_sugerido": 15.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 10, "multiplicador": 1000, "veg": 180, "cos": 60},
    "Limón s/semilla - Primera": {"unidad": "kg", "costo_sugerido": 4.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 15, "multiplicador": 1000, "veg": 180, "cos": 60},
    "Papa Alpha - Primera": {"unidad": "kg", "costo_sugerido": 6.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 35, "multiplicador": 1000, "veg": 100, "cos": 20},
    "Lechuga Romanita grande - Primera": {"unidad": "pieza", "costo_sugerido": 3.00, "etiqueta_rend": "Rendimiento (Piezas/Ha)", "rend_sugerido": 30000, "multiplicador": 1, "veg": 60, "cos": 15},
    "Zanahoria mediana - Primera": {"unidad": "kg", "costo_sugerido": 3.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 30, "multiplicador": 1000, "veg": 110, "cos": 20},
    "Brócoli - Primera": {"unidad": "kg", "costo_sugerido": 5.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 15, "multiplicador": 1000, "veg": 80, "cos": 20},
    "Calabacita Italiana - Primera": {"unidad": "kg", "costo_sugerido": 4.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 25, "multiplicador": 1000, "veg": 50, "cos": 30},
    "Pepino - Primera": {"unidad": "kg", "costo_sugerido": 5.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 50, "multiplicador": 1000, "veg": 60, "cos": 30},
    "Fresa - Primera": {"unidad": "kg", "costo_sugerido": 25.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 40, "multiplicador": 1000, "veg": 120, "cos": 60},
    "Sandía Sangría - Primera": {"unidad": "kg", "costo_sugerido": 2.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 45, "multiplicador": 1000, "veg": 85, "cos": 20},
    "Papaya Maradol - Primera": {"unidad": "kg", "costo_sugerido": 4.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 60, "multiplicador": 1000, "veg": 180, "cos": 30},
    "Melón Cantaloupe # 9 - Primera": {"unidad": "kg", "costo_sugerido": 3.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 35, "multiplicador": 1000, "veg": 85, "cos": 20},
    "Plátano Chiapas - Primera": {"unidad": "kg", "costo_sugerido": 3.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 50, "multiplicador": 1000, "veg": 270, "cos": 30},
    "DEFAULT": {"unidad": "kg", "costo_sugerido": 5.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 20, "multiplicador": 1000, "veg": 90, "cos": 30}
}

# --- LIBRERÍA DE ICONOS SVG PRO ---
ICONS = {
    "dashboard": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',
    "chart": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    "bars": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect width="4" height="7" x="7" y="14" rx="1"/><rect width="4" height="12" x="15" y="9" rx="1"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>'
}

def render_section(icon_key, title, subtitle=""):
    return f"""<div style="margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #E2E8F0;">
        <div style="display: flex; align-items: center; gap: 10px;">
            {ICONS[icon_key]}<h3 style="margin: 0; font-size: 1.4rem; font-weight: 600; color: #0F172A; letter-spacing: -0.5px;">{title}</h3>
        </div>
        <p style="margin: 4px 0 0 38px; font-size: 0.9rem; color: #64748B;">{subtitle}</p>
    </div>"""

def dia_a_fecha(dia_anio):
    fecha_generica = datetime(2024, 1, 1) + timedelta(days=int(dia_anio) - 1)
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    return f"{fecha_generica.day} {meses[fecha_generica.month - 1]}"

def get_image_base64(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, "rb") as image_file: 
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    return ""

st.set_page_config(page_title="Cuando Siembro | Inteligencia Agrícola", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")

logo_principal = get_image_base64("logo_principal.png") 
logo_sniim = get_image_base64("image_ae35e8.png")
logo_fira = get_image_base64("image_ae3663.png")
logo_siap = get_image_base64("image_ae39aa.png")
img_dron = get_image_base64("dron.jpg")
img_agricultor = get_image_base64("agricultor.jpg")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; background-color: #F8FAFC !important; color: #1E293B !important; }}
    
    .header-container {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 30px; background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; margin: -3rem -3rem 1.5rem -3rem; }}
    .logo-main {{ height: 55px; object-fit: contain; }} 
    .nav-links {{ display: flex; align-items: center; gap: 24px; }}
    .nav-links a {{ color: #475569; text-decoration: none; font-weight: 500; font-size: 0.95rem; transition: color 0.2s; }}
    .nav-links a:hover {{ color: #10B981; }}
    .btn-login {{ padding: 6px 18px; border: 1px solid #10B981; border-radius: 6px; color: #10B981 !important; font-weight: 600; transition: all 0.2s; }}
    .btn-login:hover {{ background-color: #10B981; color: white !important; }}

    .hero-wrapper {{ position: relative; display: flex; justify-content: center; align-items: center; height: 300px; margin-bottom: 1.5rem; overflow: hidden; border-radius: 20px; background-color: #E2E8F0; }}
    .hero-bg-left {{ position: absolute; left: 0; top: 0; width: 35%; height: 100%; object-fit: cover; border-radius: 0 50% 50% 0 / 0 30% 70% 0; z-index: 1; }}
    .hero-bg-right {{ position: absolute; right: 0; top: 0; width: 35%; height: 100%; object-fit: cover; border-radius: 50% 0 0 50% / 30% 0 0 70%; z-index: 1; }}
    .hero-text-card {{ position: relative; z-index: 2; background-color: rgba(255, 255, 255, 0.95); padding: 1.5rem 2.5rem; border-radius: 16px; max-width: 60%; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.08); backdrop-filter: blur(10px); }}
    .hero-title {{ font-size: 2.3rem !important; margin-bottom: 0.5rem; line-height: 1.2; color: #064E3B !important; font-weight: 800 !important; letter-spacing: -0.5px; }}
    .hero-subtitle {{ font-size: 1.1rem; color: #475569; margin-bottom: 0; font-weight: 400; line-height: 1.5; }}

    .stSelectbox label, .stNumberInput label {{ font-size: 0.85rem !important; font-weight: 600 !important; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.5px; }}
    .stSelectbox > div > div {{ border-radius: 6px !important; border: 1px solid #CBD5E1 !important; background-color: #FFFFFF !important; box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important; }}
    
    div.stButton > button:first-child {{ background: linear-gradient(135deg, #D97706 0%, #B45309 100%) !important; color: white !important; font-family: 'Inter', sans-serif !important; font-weight: 700 !important; font-size: 1.05rem !important; padding: 0.7rem 1.5rem !important; border-radius: 10px !important; border: none !important; width: 100%; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(217, 119, 6, 0.3); }}
    div.stButton > button:first-child:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(217, 119, 6, 0.4); }}
    
    .logos-container {{ display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 35px; margin-top: 10px; padding-top: 15px; border-top: 1px solid #E2E8F0; }}
    .logo-item {{ filter: grayscale(100%); opacity: 0.4; transition: all 0.3s; object-fit: contain; }}
    .logo-item:hover {{ filter: grayscale(0%); opacity: 0.8; }}
    .logo-sniim {{ height: 18px; }} .logo-fira {{ height: 28px; }} .logo-siap {{ height: 28px; }}
    .logo-nasa {{ font-weight: 700; color: #64748B; font-size: 1rem; opacity: 0.5; }}
    
    div[data-testid="metric-container"] {{ background-color: #FFFFFF; padding: 1.2rem; border-radius: 8px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
    div[data-testid="metric-container"] label {{ font-weight: 600 !important; color: #64748B !important; font-size: 0.85rem !important; text-transform: uppercase; letter-spacing: 0.5px; }}
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{ font-size: 1.8rem !important; font-weight: 700 !important; color: #0F172A !important; letter-spacing: -0.5px; }}
    
    @media (max-width: 768px) {{
        .header-container {{ flex-direction: column; padding: 15px; gap: 15px; margin: -3rem -1.5rem 1.5rem -1.5rem; }}
        .logo-main {{ height: 50px; }} 
        .nav-links {{ width: 100%; justify-content: space-evenly; flex-wrap: wrap; }}
        .hero-wrapper {{ height: auto; padding: 30px 15px; border-radius: 12px; }}
        .hero-bg-left, .hero-bg-right {{ opacity: 0.15; width: 50%; }}
        .hero-text-card {{ max-width: 100%; padding: 1.5rem 1rem; }}
        .hero-title {{ font-size: 1.8rem !important; }}
        .hero-subtitle {{ font-size: 1rem; }}
        .logos-container {{ gap: 20px; }}
    }}
    </style>
""", unsafe_allow_html=True)

if logo_principal:
    st.markdown(f"""
        <div class="header-container">
            <div><img src="{logo_principal}" class="logo-main" alt="Cuando Siembro"></div>
            <div class="nav-links"><a href="#">Soporte</a><a href="#" class="btn-login">Iniciar Sesión</a></div>
        </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class='hero-wrapper'>
        {('<img src="'+img_dron+'" class="hero-bg-left">' if img_dron else '')} 
        {('<img src="'+img_agricultor+'" class="hero-bg-right">' if img_agricultor else '')}
        <div class='hero-text-card'>
            <h1 class='hero-title'>¿Cuándo sembrar para obtener la mejor ganancia?</h1>
            <p class='hero-subtitle'>Algoritmos predictivos que cruzan precios históricos y clima satelital para encontrar tu ventana de máxima rentabilidad.</p>
        </div>
    </div>
""", unsafe_allow_html=True)

col_busq1, col_busq2, col_busq3, col_busq4 = st.columns([2.5, 2, 2, 2])
with col_busq1:
    opciones_cultivos = list(PERFILES_AGRONOMICOS.keys())
    indice_defecto = opciones_cultivos.index("Tomate Saladette - Primera") if "Tomate Saladette - Primera" in opciones_cultivos else 0
    cultivo_seleccionado = st.selectbox("Activo / Cultivo", opciones_cultivos, index=indice_defecto)
with col_busq2:
    ubicacion = st.selectbox("Zona Geográfica", ["Tehuacán, Puebla", "Ajalpan, Puebla", "Tecamachalco, Puebla"], index=0)
with col_busq3:
    meta_mercado = st.selectbox("Horizonte (Backtesting)", ["3 Años Históricos", "1 Año Histórico", "5 Años Históricos"])
    anios_historia = int(meta_mercado.split()[0])
with col_busq4:
    st.markdown("<br>", unsafe_allow_html=True)
    ejecutar_btn = st.button("OBTENER DATOS Y CALCULAR")

perfil = PERFILES_AGRONOMICOS.get(cultivo_seleccionado, PERFILES_AGRONOMICOS["DEFAULT"])

st.sidebar.markdown("### ⚙️ Parámetros de Operación")
st.sidebar.markdown("<p style='font-size:0.85rem; color:#64748B; line-height:1.4;'>Configura tus costos locales para calcular el Punto de Equilibrio.</p>", unsafe_allow_html=True)

costo_usuario = st.sidebar.number_input(f"Costo Producción (MXN/{perfil['unidad']})", min_value=0.1, max_value=500.0, value=float(perfil["costo_sugerido"]), step=0.5)
area_ha = st.sidebar.number_input("Superficie Operativa (Ha)", min_value=0.1, value=1.0, step=0.5)
rendimiento = st.sidebar.number_input(perfil["etiqueta_rend"], min_value=1, value=int(perfil["rend_sugerido"]))
dias_veg = st.sidebar.number_input("Periodo Vegetativo (Días)", min_value=10, value=int(perfil["veg"]))
dias_cos = st.sidebar.number_input("Ventana de Cosecha (Días)", min_value=5, value=int(perfil["cos"]))

inversion_total = area_ha * rendimiento * perfil["multiplicador"] * costo_usuario

st.markdown(f"""
    <div class='logos-container'>
        <img src='{logo_sniim}' class='logo-item logo-sniim' alt='SNIIM'>
        <img src='{logo_fira}' class='logo-item logo-fira' alt='FIRA'>
        <img src='{logo_siap}' class='logo-item logo-siap' alt='SIAP'>
        <span class='logo-item logo-nasa'>NASA POWER API</span>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

if 'df_maestro' not in st.session_state:
    st.session_state.df_maestro = None

if ejecutar_btn:
    with st.status("Procesando datos en la terminal...", expanded=True) as status:
        st.write("Conectando con satélites (NASA POWER)...")
        res_clima = extraer_clima_historico(localidad=ubicacion, anios_historia=anios_historia)
        if res_clima["status"] == "success":
            df_clima = pd.read_csv(res_clima["archivo"])
            df_clima['Fecha'] = pd.to_datetime(df_clima['Fecha'])
        else:
            st.error(res_clima["mensaje"]); st.stop()
            
        st.write("Sincronizando precios spot (SNIIM)...")
        nombre_limpio = cultivo_seleccionado.replace(" ", "_").replace("-", "").replace("__", "_")
        nombre_archivo = f"Precios_{nombre_limpio}_Puebla.csv"
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        rutas_posibles = [os.path.join(base_dir, nombre_archivo), os.path.join(base_dir, "Proyecto_Agro", nombre_archivo), nombre_archivo]
        
        ruta_csv = next((r for r in rutas_posibles if os.path.exists(r)), None)
            
        if ruta_csv:
            df_precios_raw = pd.read_csv(ruta_csv)
            df_precios = pd.DataFrame()
            df_precios['Fecha'] = pd.to_datetime(df_precios_raw.iloc[:, 0], dayfirst=True, errors='coerce')
            df_precios['Presentacion'] = df_precios_raw.iloc[:, 1].astype(str)
            df_precios['Precio_Caja'] = pd.to_numeric(df_precios_raw.iloc[:, 5], errors='coerce')
            df_precios = df_precios.dropna(subset=['Fecha', 'Precio_Caja'])
            
            def calcular_precio_base(row):
                presentacion = str(row['Presentacion']).lower().strip()
                precio = float(row['Precio_Caja'])
                unidad = perfil['unidad']
                nums = re.findall(r'\d+', presentacion)
                cant = float(nums[-1]) if nums else 1.0
                
                if unidad == 'pieza': return precio / (cant * 12.0) if 'docena' in presentacion else precio / cant
                elif unidad == 'docena': return (precio / cant) * 12.0 if 'pieza' in presentacion or 'pza' in presentacion else precio / cant
                else: 
                    if 'ton' in presentacion: return precio / (cant * 1000.0)
                    elif 'kg' in presentacion or 'kilo' in presentacion: return precio / cant
                    elif nums: return precio / cant
                    return precio / 14.0
                    
            df_precios['Precio_Base'] = df_precios.apply(calcular_precio_base, axis=1).round(2)
            
            fecha_min, fecha_max = df_precios['Fecha'].min(), df_clima['Fecha'].max()
            df_maestro = pd.merge(df_clima[(df_clima['Fecha'] >= fecha_min) & (df_clima['Fecha'] <= fecha_max)], df_precios[['Fecha', 'Precio_Base']], on='Fecha', how='left')
            df_maestro = df_maestro.sort_values('Fecha').reset_index(drop=True)
            df_maestro['Precio_Base'] = df_maestro['Precio_Base'].ffill().bfill()
            st.session_state.df_maestro = df_maestro
            status.update(label="Algoritmo ejecutado exitosamente.", state="complete", expanded=False)
        else:
            st.error(f"Base de datos de mercado no encontrada para: {cultivo_seleccionado}.")
            status.update(label="Error de conexión a datos", state="error", expanded=False)
            st.stop()

# --- RESULTADOS (TRADINGVIEW STYLE) ---
if st.session_state.df_maestro is not None:
    df_maestro = st.session_state.df_maestro.copy()
    
    st.markdown(render_section("dashboard", "Resumen de Inteligencia Agrícola", "Proyección financiera basada en el algoritmo predictivo."), unsafe_allow_html=True)
    
    df_maestro['Dia_Anio'] = df_maestro['Fecha'].dt.dayofyear
    perfil_anual = df_maestro.groupby('Dia_Anio').agg({'Precio_Base': 'mean', 'Temp_Max_C': 'mean', 'Temp_Min_C': 'mean', 'Precipitacion_mm': 'mean'}).reset_index()
    perfil_extendido = pd.concat([perfil_anual, perfil_anual]).reset_index(drop=True)
    
    res = []
    for dia_inicio in range(365):
        mercado_cos = perfil_extendido.iloc[dia_inicio + dias_veg : dia_inicio + dias_veg + dias_cos]
        clima_veg = perfil_extendido.iloc[dia_inicio : dia_inicio + dias_veg]
        precio_esp = mercado_cos['Precio_Base'].mean()
        ingreso_esp = area_ha * rendimiento * perfil["multiplicador"] * precio_esp
        roi_esp = ((ingreso_esp - inversion_total) / inversion_total) * 100 if inversion_total > 0 else 0
        riesgo_frio = len(clima_veg[clima_veg['Temp_Min_C'] < 12.0])
        res.append({'Dia': dia_inicio + 1, 'Fecha': dia_a_fecha(dia_inicio + 1), 'ROI': roi_esp, 'Precio': precio_esp, 'Frio': riesgo_frio})
    
    df_pred = pd.DataFrame(res).sort_values('ROI', ascending=False)
    best = df_pred.iloc[0]
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Ventana de Siembra Sugerida", best['Fecha'], f"Retorno (ROI): {best['ROI']:.1f}%")
    with c2: st.metric("Precio Objetivo (Spot)", f"$ {best['Precio']:.2f} MXN", f"Costo Operativo: $ {costo_usuario:.2f}")
    with c3: st.metric("Riesgo Climático (Heladas)", f"{best['Frio']} Días", "Temp. < 12°C en desarrollo", delta_color="inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- GRÁFICA 1: ÁREA DE RENTABILIDAD ---
    st.markdown(render_section("chart", "Curva de Retorno de Inversión (Yield Curve)", "Identifica visualmente el momento exacto para entrar al mercado."), unsafe_allow_html=True)
    
    df_graf_roi = df_pred.sort_values('Dia').copy()
    df_graf_roi['Fecha_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_graf_roi['Dia'] - 1, unit='D')
    
    fig_roi = go.Figure()
    fig_roi.add_trace(go.Scatter(
        x=df_graf_roi['Fecha_Plot'], y=df_graf_roi['ROI'], mode='lines', name='ROI',
        line=dict(color='#089981', width=2, shape='spline'), fill='tozeroy', fillcolor='rgba(8, 153, 129, 0.1)',
        hovertemplate='<b>%{x|%d %b}</b><br>ROI Estimado: %{y:.1f}%<extra></extra>'
    ))
    fig_roi.add_hline(y=0, line_color="#F23645", line_width=1, line_dash="dash", annotation_text="Punto de Equilibrio", annotation_position="bottom right", annotation_font_color="#F23645")
    
    fig_roi.update_layout(
        font=dict(family="Inter", size=12, color="#475569"),
        plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified", margin=dict(l=0, r=0, t=10, b=10), height=350,
        xaxis=dict(showgrid=True, gridcolor='#F1F5F9', showspikes=True, spikemode='across', spikethickness=1, spikedash='dot', spikecolor='#94A3B8', tickformat='%b'),
        yaxis=dict(side='right', showgrid=True, gridcolor='#F1F5F9', zeroline=False, ticksuffix="%")
    )
    st.plotly_chart(fig_roi, use_container_width=True)

    # --- GRÁFICAS 2 Y 3 (LADO A LADO) ---
    col_charts1, col_charts2 = st.columns(2)

    with col_charts1:
        st.markdown(render_section("bars", "Acción del Precio Histórico", f"Media móvil suavizada a 7 días en MXN/{perfil['unidad']}."), unsafe_allow_html=True)
        
        df_historico = df_maestro[['Fecha', 'Precio_Base']].copy().sort_values('Fecha')
        df_historico['Precio_Suavizado'] = df_historico['Precio_Base'].rolling(window=7, min_periods=1).mean()
        df_historico['Año'] = df_historico['Fecha'].dt.year.astype(str)
        df_historico['Mes_Dia_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_historico['Fecha'].dt.dayofyear - 1, unit='D')
        
        # NUEVA PALETA: Colores vibrantes y contrastantes (Azul, Naranja, Verde, Morado, Rosa)
        paleta_alto_contraste = ['#3B82F6', '#F59E0B', '#10B981', '#8B5CF6', '#F43F5E']
        
        fig_precios = px.line(df_historico, x='Mes_Dia_Plot', y='Precio_Suavizado', color='Año', color_discrete_sequence=paleta_alto_contraste, render_mode='svg')
        
        # NUEVA ETIQUETA HOVER: Muestra explícitamente la palabra "Año", seguido del número y luego el precio.
        fig_precios.update_traces(line=dict(width=2, shape='spline'), hovertemplate='Año %{data.name}: $%{y:.2f}<extra></extra>')
        
        fig_precios.update_layout(
            font=dict(family="Inter", size=11, color="#475569"),
            plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified", margin=dict(l=0, r=0, t=10, b=10), height=350,
            xaxis=dict(title="", showgrid=True, gridcolor='#F1F5F9', showspikes=True, spikemode='across', spikethickness=1, spikedash='dot', spikecolor='#94A3B8', tickformat='%b'),
            yaxis=dict(title="", side='right', showgrid=True, gridcolor='#F1F5F9', tickprefix="$"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None)
        )
        st.plotly_chart(fig_precios, use_container_width=True)

    with col_charts2:
        st.markdown(render_section("cloud", "Indicadores Climáticos", "Temperatura (°C) y Volumen de Precipitación (mm)."), unsafe_allow_html=True)
        
        df_clima_anual = perfil_anual.copy()
        df_clima_anual['Mes_Dia_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_clima_anual['Dia_Anio'] - 1, unit='D')
        
        fig_clima = make_subplots(specs=[[{"secondary_y": True}]])
        fig_clima.add_trace(go.Bar(x=df_clima_anual['Mes_Dia_Plot'], y=df_clima_anual['Precipitacion_mm'], name='Volumen (Lluvia)', marker_color='rgba(148, 163, 184, 0.4)', hovertemplate='%{y:.1f} mm<extra></extra>'), secondary_y=False)
        fig_clima.add_trace(go.Scatter(x=df_clima_anual['Mes_Dia_Plot'], y=df_clima_anual['Temp_Max_C'], name='Temp Máx', line=dict(color='#F23645', width=1.5, shape='spline'), hovertemplate='%{y:.1f}°C<extra></extra>'), secondary_y=True)
        fig_clima.add_trace(go.Scatter(x=df_clima_anual['Mes_Dia_Plot'], y=df_clima_anual['Temp_Min_C'], name='Temp Mín', line=dict(color='#2962FF', width=1.5, shape='spline'), hovertemplate='%{y:.1f}°C<extra></extra>'), secondary_y=True)
        
        fig_clima.update_layout(
            font=dict(family="Inter", size=11, color="#475569"),
            plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified", margin=dict(l=0, r=0, t=10, b=10), height=350,
            xaxis=dict(showgrid=True, gridcolor='#F1F5F9', showspikes=True, spikemode='across', spikethickness=1, spikedash='dot', spikecolor='#94A3B8', tickformat='%b'),
            yaxis=dict(showgrid=False, showticklabels=False, range=[0, df_clima_anual['Precipitacion_mm'].max() * 4]),
            yaxis2=dict(side='right', showgrid=True, gridcolor='#F1F5F9', ticksuffix="°C"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
        )
        st.plotly_chart(fig_clima, use_container_width=True)
