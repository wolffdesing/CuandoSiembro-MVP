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

# --- BASE DE CONOCIMIENTO (PERFILES AGRONÓMICOS CON EMOJIS) ---
PERFILES_AGRONOMICOS = {
    "Tomate Saladette - Primera": {"emoji": "🍅", "unidad": "kg", "costo_sugerido": 7.80, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 80, "multiplicador": 1000, "veg": 90, "cos": 40},
    "Tomate Verde - Primera": {"emoji": "🍏", "unidad": "kg", "costo_sugerido": 5.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 40, "multiplicador": 1000, "veg": 75, "cos": 30},
    "Cebolla Bola - Primera": {"emoji": "🧅", "unidad": "kg", "costo_sugerido": 4.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 40, "multiplicador": 1000, "veg": 120, "cos": 20},
    "Cebolla Morada - Primera": {"emoji": "🧅", "unidad": "kg", "costo_sugerido": 5.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 35, "multiplicador": 1000, "veg": 120, "cos": 20},
    "Chile Jalapeño - Primera": {"emoji": "🌶️", "unidad": "kg", "costo_sugerido": 6.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 40, "multiplicador": 1000, "veg": 90, "cos": 40},
    "Chile Poblano - Primera": {"emoji": "🫑", "unidad": "kg", "costo_sugerido": 8.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 30, "multiplicador": 1000, "veg": 100, "cos": 40},
    "Chile Serrano - Primera": {"emoji": "🌶️", "unidad": "kg", "costo_sugerido": 7.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 35, "multiplicador": 1000, "veg": 90, "cos": 40},
    "Aguacate Hass - Primera": {"emoji": "🥑", "unidad": "kg", "costo_sugerido": 15.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 10, "multiplicador": 1000, "veg": 180, "cos": 60},
    "Limón s/semilla - Primera": {"emoji": "🍋", "unidad": "kg", "costo_sugerido": 4.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 15, "multiplicador": 1000, "veg": 180, "cos": 60},
    "Papa Alpha - Primera": {"emoji": "🥔", "unidad": "kg", "costo_sugerido": 6.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 35, "multiplicador": 1000, "veg": 100, "cos": 20},
    "Lechuga Romanita grande - Primera": {"emoji": "🥬", "unidad": "pieza", "costo_sugerido": 3.00, "etiqueta_rend": "Rendimiento (Piezas/Ha)", "rend_sugerido": 30000, "multiplicador": 1, "veg": 60, "cos": 15},
    "Zanahoria mediana - Primera": {"emoji": "🥕", "unidad": "kg", "costo_sugerido": 3.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 30, "multiplicador": 1000, "veg": 110, "cos": 20},
    "Brócoli - Primera": {"emoji": "🥦", "unidad": "kg", "costo_sugerido": 5.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 15, "multiplicador": 1000, "veg": 80, "cos": 20},
    "Calabacita Italiana - Primera": {"emoji": "🥒", "unidad": "kg", "costo_sugerido": 4.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 25, "multiplicador": 1000, "veg": 50, "cos": 30},
    "Pepino - Primera": {"emoji": "🥒", "unidad": "kg", "costo_sugerido": 5.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 50, "multiplicador": 1000, "veg": 60, "cos": 30},
    "Fresa - Primera": {"emoji": "🍓", "unidad": "kg", "costo_sugerido": 25.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 40, "multiplicador": 1000, "veg": 120, "cos": 60},
    "Sandía Sangría - Primera": {"emoji": "🍉", "unidad": "kg", "costo_sugerido": 2.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 45, "multiplicador": 1000, "veg": 85, "cos": 20},
    "Papaya Maradol - Primera": {"emoji": "🥭", "unidad": "kg", "costo_sugerido": 4.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 60, "multiplicador": 1000, "veg": 180, "cos": 30},
    "Melón Cantaloupe # 9 - Primera": {"emoji": "🍈", "unidad": "kg", "costo_sugerido": 3.50, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 35, "multiplicador": 1000, "veg": 85, "cos": 20},
    "Plátano Chiapas - Primera": {"emoji": "🍌", "unidad": "kg", "costo_sugerido": 3.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 50, "multiplicador": 1000, "veg": 270, "cos": 30},
    "DEFAULT": {"emoji": "🌱", "unidad": "kg", "costo_sugerido": 5.00, "etiqueta_rend": "Rendimiento (Ton/Ha)", "rend_sugerido": 20, "multiplicador": 1000, "veg": 90, "cos": 30}
}

# --- LIBRERÍA DE ICONOS SVG PRO ---
ICONS = {
    "dashboard": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',
    "chart": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    "bars": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect width="4" height="7" x="7" y="14" rx="1"/><rect width="4" height="12" x="15" y="9" rx="1"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>',
    "tractor": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F43F5E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 15c0 2.2 1.8 4 4 4s4-1.8 4-4M19 15c0 2.2-1.8 4-4 4s-4-1.8-4-4M11 15h4M1 11h2M7 11h14l-2-6H9l-2 6M11 5v6"/></svg>'
}

def render_section(icon_key, title, subtitle=""):
    return f"""<div style="margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #E2E8F0;">
        <div style="display: flex; align-items: center; gap: 10px;">
            {ICONS[icon_key]}<h3 style="margin: 0; font-size: 1.4rem; font-weight: 600; color: #0F172A; letter-spacing: -0.5px;">{title}</h3>
        </div>
        <p style="margin: 4px 0 0 38px; font-size: 0.9rem; color: #64748B;">{subtitle}</p>
    </div>"""

def dia_a_fecha(dia_anio):
    dia_anio = int(dia_anio)
    while dia_anio > 365:
        dia_anio -= 365
    fecha_generica = datetime(2024, 1, 1) + timedelta(days=dia_anio - 1)
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

    .hero-wrapper {{ position: relative; display: flex; justify-content: center; align-items: center; height: 300px; margin-bottom: 2rem; overflow: hidden; border-radius: 20px; background-color: #E2E8F0; }}
    .hero-bg-left {{ position: absolute; left: 0; top: 0; width: 35%; height: 100%; object-fit: cover; border-radius: 0 50% 50% 0 / 0 30% 70% 0; z-index: 1; }}
    .hero-bg-right {{ position: absolute; right: 0; top: 0; width: 35%; height: 100%; object-fit: cover; border-radius: 50% 0 0 50% / 30% 0 0 70%; z-index: 1; }}
    .hero-text-card {{ position: relative; z-index: 2; background-color: rgba(255, 255, 255, 0.95); padding: 1.5rem 2.5rem; border-radius: 16px; max-width: 60%; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.08); backdrop-filter: blur(10px); }}
    .hero-title {{ font-size: 2.3rem !important; margin-bottom: 0.5rem; line-height: 1.2; color: #064E3B !important; font-weight: 800 !important; letter-spacing: -0.5px; }}
    .hero-subtitle {{ font-size: 1.1rem; color: #475569; margin-bottom: 0; font-weight: 400; line-height: 1.5; }}

    .stSelectbox label, .stNumberInput label {{ font-size: 0.85rem !important; font-weight: 600 !important; color: #64748B !important; text-transform: uppercase; letter-spacing: 0.5px; }}
    .stSelectbox > div > div {{ border-radius: 6px !important; border: 1px solid #CBD5E1 !important; background-color: #FFFFFF !important; box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important; }}
    
    div.stButton > button:first-child {{ background: linear-gradient(135deg, #D97706 0%, #B45309 100%) !important; color: white !important; font-family: 'Inter', sans-serif !important; font-weight: 700 !important; font-size: 1.05rem !important; padding: 0.7rem 1.5rem !important; border-radius: 10px !important; border: none !important; width: 100%; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(217, 119, 6, 0.3); }}
    div.stButton > button:first-child:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(217, 119, 6, 0.4); }}
    
    .btn-scanner > button:first-child {{ background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important; margin-top: 15px; margin-bottom: 15px; }}
    
    .logos-container {{ display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 35px; margin-top: 10px; padding-top: 15px; border-top: 1px solid #E2E8F0; margin-bottom: 30px; }}
    .logo-item {{ filter: grayscale(100%); opacity: 0.4; transition: all 0.3s; object-fit: contain; }}
    .logo-item:hover {{ filter: grayscale(0%); opacity: 0.8; }}
    .logo-sniim {{ height: 18px; }} .logo-fira {{ height: 28px; }} .logo-siap {{ height: 28px; }}
    .logo-nasa {{ font-weight: 700; color: #64748B; font-size: 1rem; opacity: 0.5; }}
    
    div[data-testid="metric-container"] {{ background-color: #FFFFFF; padding: 1.2rem; border-radius: 8px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
    div[data-testid="metric-container"] label {{ font-weight: 600 !important; color: #64748B !important; font-size: 0.85rem !important; text-transform: uppercase; letter-spacing: 0.5px; }}
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{ font-size: 1.5rem !important; font-weight: 700 !important; color: #0F172A !important; letter-spacing: -0.5px; }}
    
    .stTabs [data-baseweb="tab-list"] {{ gap: 20px; margin-bottom: 20px; }}
    .stTabs [data-baseweb="tab"] {{ padding: 10px 15px; background-color: transparent; border-radius: 0; font-weight: 600; color: #64748B; font-size: 1rem; }}
    .stTabs [aria-selected="true"] {{ color: #10B981 !important; border-bottom-color: #10B981 !important; }}
    
    .top-crop-card {{ background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: transform 0.2s; height: 100%; }}
    .top-crop-card:hover {{ transform: translateY(-5px); border-color: #10B981; }}
    .crop-emoji {{ font-size: 3.5rem; margin-bottom: 10px; }}

    @media (max-width: 768px) {{
        .header-container {{ flex-direction: column; padding: 15px; gap: 15px; margin: -3rem -1.5rem 1.5rem -1.5rem; }}
        .logo-main {{ height: 50px; }} 
        .nav-links {{ width: 100%; justify-content: space-evenly; flex-wrap: wrap; }}
        .hero-wrapper {{ height: auto; padding: 25px 15px; border-radius: 12px; }}
        .hero-bg-left, .hero-bg-right {{ opacity: 0.15; width: 50%; }}
        .hero-text-card {{ max-width: 100%; padding: 1rem; }}
        .hero-title {{ font-size: 1.6rem !important; }}
        .hero-subtitle {{ font-size: 0.95rem; }}
        .logos-container {{ gap: 20px; }}
        div[data-testid="metric-container"] {{ padding: 1rem; }}
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{ font-size: 1.25rem !important; }}
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

# ==============================================================
# 📌 FUNCIÓN PRINCIPAL: BÚSQUEDA INDIVIDUAL (DISEÑO ORIGINAL)
# ==============================================================
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

if 'df_maestro' not in st.session_state:
    st.session_state.df_maestro = None
if 'df_precios_crudo' not in st.session_state:
    st.session_state.df_precios_crudo = None

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
            st.session_state.df_precios_crudo = df_precios.copy()
            
            fecha_min = df_precios['Fecha'].min()
            df_maestro = pd.merge(df_clima[df_clima['Fecha'] >= fecha_min], df_precios[['Fecha', 'Precio_Base']], on='Fecha', how='left')
            df_maestro = df_maestro.sort_values('Fecha').reset_index(drop=True)
            df_maestro['Precio_Base'] = df_maestro['Precio_Base'].ffill(limit=7)
            st.session_state.df_maestro = df_maestro
            status.update(label="Algoritmo ejecutado exitosamente.", state="complete", expanded=False)
        else:
            st.error(f"Base de datos de mercado no encontrada para: {cultivo_seleccionado}.")
            status.update(label="Error de conexión a datos", state="error", expanded=False)
            st.stop()

# --- RENDERIZADO DEL ANÁLISIS INDIVIDUAL ---
if st.session_state.df_maestro is not None and st.session_state.df_precios_crudo is not None:
    df_maestro = st.session_state.df_maestro.copy()
    
    df_maestro['Dia_Anio'] = df_maestro['Fecha'].dt.dayofyear
    perfil_anual = df_maestro.groupby('Dia_Anio').agg({'Precio_Base': 'mean', 'Temp_Max_C': 'mean', 'Temp_Min_C': 'mean', 'Precipitacion_mm': 'mean'}).reset_index()
    perfil_extendido = pd.concat([perfil_anual, perfil_anual]).reset_index(drop=True)
    
    res = []
    for dia_inicio in range(365):
        mercado_cos = perfil_extendido.iloc[dia_inicio + dias_veg : dia_inicio + dias_veg + dias_cos]
        clima_veg = perfil_extendido.iloc[dia_inicio : dia_inicio + dias_veg]
        precio_esp = mercado_cos['Precio_Base'].mean()
        if pd.isna(precio_esp): precio_esp = 0
            
        ingreso_esp = area_ha * rendimiento * perfil["multiplicador"] * precio_esp
        roi_esp = ((ingreso_esp - inversion_total) / inversion_total) * 100 if inversion_total > 0 else 0
        riesgo_frio = len(clima_veg[clima_veg['Temp_Min_C'] < 12.0])
        res.append({'Dia': dia_inicio + 1, 'Fecha': dia_a_fecha(dia_inicio + 1), 'ROI': roi_esp, 'Precio': precio_esp, 'Frio': riesgo_frio})
    
    df_pred = pd.DataFrame(res).sort_values('ROI', ascending=False)
    best = df_pred.iloc[0]
    
    volumen_total = area_ha * rendimiento
    unidad_texto = "Toneladas" if "Ton" in perfil["etiqueta_rend"] else "Piezas"
    ingreso_optimo = volumen_total * perfil["multiplicador"] * best["Precio"]
    utilidad_neta = ingreso_optimo - inversion_total

    st.markdown(render_section("dashboard", "Resumen de Inteligencia Agrícola", "Proyección operativa y financiera."), unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("🌱 Ventana de Siembra", best['Fecha'], f"ROI: {best['ROI']:.1f}%")
    with c2: st.metric("💵 Precio Esperado (Spot)", f"$ {best['Precio']:.2f} MXN", f"Costo Base: $ {costo_usuario:.2f}")
    with c3: st.metric("❄️ Riesgo de Heladas", f"{best['Frio']} Días", "Temp. < 12°C", delta_color="inverse")
    with c4: st.metric("💰 Utilidad Neta Estimada", f"$ {utilidad_neta:,.2f}", f"Prod: {volumen_total:,.1f} {unidad_texto}", delta_color="normal")
    st.markdown("<br>", unsafe_allow_html=True)

    tab_dashboard, tab_costos = st.tabs(["📈 Análisis de Mercado y Tendencias", "🚜 Paquete Tecnológico (Costos)"])

    with tab_dashboard:
        st.markdown(render_section("chart", "Curva de Retorno de Inversión (Yield Curve)", "Identifica visualmente el momento exacto para entrar al mercado."), unsafe_allow_html=True)
        df_graf_roi = df_pred.sort_values('Dia').copy()
        df_graf_roi['Fecha_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_graf_roi['Dia'] - 1, unit='D')
        
        fig_roi = go.Figure()
        fig_roi.add_trace(go.Scatter(x=df_graf_roi['Fecha_Plot'], y=df_graf_roi['ROI'], mode='lines', name='ROI', line=dict(color='#089981', width=2, shape='spline'), fill='tozeroy', fillcolor='rgba(8, 153, 129, 0.1)', hovertemplate='<b>%{x|%d %b}</b><br>ROI Estimado: %{y:.1f}%<extra></extra>'))
        fig_roi.add_hline(y=0, line_color="#F23645", line_width=1, line_dash="dash", annotation_text="Punto de Equilibrio", annotation_position="bottom right", annotation_font_color="#F23645")
        fig_roi.update_layout(font=dict(family="Inter", size=12, color="#475569"), plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)', hovermode="x unified", margin=dict(l=0, r=0, t=10, b=10), height=350, xaxis=dict(showgrid=True, gridcolor='#F1F5F9', showspikes=True, spikemode='across', spikethickness=1, spikedash='dot', spikecolor='#94A3B8', tickformat='%b'), yaxis=dict(side='right', showgrid=True, gridcolor='#F1F5F9', zeroline=False, ticksuffix="%"))
        st.plotly_chart(fig_roi, use_container_width=True, config={'displayModeBar': False})

        col_charts1, col_charts2 = st.columns(2)
        with col_charts1:
            st.markdown(render_section("bars", "Acción del Precio Histórico", f"Media móvil en MXN/{perfil['unidad']}."), unsafe_allow_html=True)
            df_historico = st.session_state.df_precios_crudo[['Fecha', 'Precio_Base']].copy().sort_values('Fecha')
            df_historico['Precio_Suavizado'] = df_historico['Precio_Base'].rolling(window=5, min_periods=1).mean()
            df_historico['Año'] = df_historico['Fecha'].dt.year.astype(str)
            df_historico['Mes_Dia_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_historico['Fecha'].dt.dayofyear - 1, unit='D')
            
            fig_precios = px.line(df_historico, x='Mes_Dia_Plot', y='Precio_Suavizado', color='Año', color_discrete_sequence=['#3B82F6', '#F59E0B', '#10B981', '#8B5CF6', '#F43F5E'], render_mode='svg')
            fig_precios.update_traces(line=dict(width=2, shape='spline'), hovertemplate='Año %{data.name}: $%{y:.2f}<extra></extra>')
            fig_precios.update_layout(font=dict(family="Inter", size=11, color="#475569"), plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)', hovermode="x unified", margin=dict(l=0, r=0, t=10, b=10), height=350, xaxis=dict(title="", showgrid=True, gridcolor='#F1F5F9', showspikes=True, spikemode='across', spikethickness=1, spikedash='dot', spikecolor='#94A3B8', tickformat='%b'), yaxis=dict(title="", side='right', showgrid=True, gridcolor='#F1F5F9', tickprefix="$"), legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, title=None))
            st.plotly_chart(fig_precios, use_container_width=True, config={'displayModeBar': False})

        with col_charts2:
            st.markdown(render_section("cloud", "Indicadores Climáticos", "Temperatura (°C) y Lluvia (mm)."), unsafe_allow_html=True)
            df_clima_anual = perfil_anual.copy()
            df_clima_anual['Mes_Dia_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_clima_anual['Dia_Anio'] - 1, unit='D')
            
            fig_clima = make_subplots(specs=[[{"secondary_y": True}]])
            fig_clima.add_trace(go.Bar(x=df_clima_anual['Mes_Dia_Plot'], y=df_clima_anual['Precipitacion_mm'], name='Volumen', marker_color='rgba(148, 163, 184, 0.4)', hovertemplate='%{y:.1f} mm<extra></extra>'), secondary_y=False)
            fig_clima.add_trace(go.Scatter(x=df_clima_anual['Mes_Dia_Plot'], y=df_clima_anual['Temp_Max_C'], name='Temp Máx', line=dict(color='#F23645', width=1.5, shape='spline'), hovertemplate='%{y:.1f}°C<extra></extra>'), secondary_y=True)
            fig_clima.add_trace(go.Scatter(x=df_clima_anual['Mes_Dia_Plot'], y=df_clima_anual['Temp_Min_C'], name='Temp Mín', line=dict(color='#2962FF', width=1.5, shape='spline'), hovertemplate='%{y:.1f}°C<extra></extra>'), secondary_y=True)
            fig_clima.update_layout(font=dict(family="Inter", size=11, color="#475569"), plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)', hovermode="x unified", margin=dict(l=0, r=0, t=10, b=10), height=350, xaxis=dict(showgrid=True, gridcolor='#F1F5F9', showspikes=True, spikemode='across', spikethickness=1, spikedash='dot', spikecolor='#94A3B8', tickformat='%b'), yaxis=dict(showgrid=False, showticklabels=False, range=[0, df_clima_anual['Precipitacion_mm'].max() * 4]), yaxis2=dict(side='right', showgrid=True, gridcolor='#F1F5F9', ticksuffix="°C"), legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
            st.plotly_chart(fig_clima, use_container_width=True, config={'displayModeBar': False})

    with tab_costos:
        st.markdown(render_section("tractor", "Estructura de Costos del Lote", f"Desglose operativo para una inversión de $ {inversion_total:,.2f} MXN."), unsafe_allow_html=True)
        st.info("💡 **Nota Operativa:** Distribución estándar referencial basada en FIRA.")
        conceptos_nombres = ["Preparación del Terreno", "Semilla / Material Vegetativo", "Nutrición y Fertilizantes", "Agroquímicos (Plagas/Enfermedades)", "Labores Culturales (Jornales)", "Cosecha, Flete y Empaque", "Costos Indirectos y Servicios"]
        porcentajes_default = perfil.get("paquete", [0.08, 0.15, 0.28, 0.14, 0.16, 0.14, 0.05])
        df_costos = pd.DataFrame({"Concepto Operativo": conceptos_nombres, "Participación": porcentajes_default, "Monto Asignado (MXN)": [p * inversion_total for p in porcentajes_default]})
        
        col_donut, col_table = st.columns([1.5, 2])
        with col_donut:
            fig_donut = px.pie(df_costos, values='Monto Asignado (MXN)', names='Concepto Operativo', hole=0.6, color_discrete_sequence=['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#F43F5E', '#14B8A6', '#64748B'])
            fig_donut.update_traces(textposition='inside', textinfo='percent', textfont_size=13, textfont_color='white')
            fig_donut.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), height=380)
            fig_donut.add_annotation(text="<b>Estructura</b><br>Financiera", x=0.5, y=0.5, font_size=16, font_color="#0F172A", showarrow=False)
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
            
        with col_table:
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df_costos.style.format({"Participación": "{:.1%}", "Monto Asignado (MXN)": "${:,.2f}"}), use_container_width=True, hide_index=True)


# ==============================================================
# 📌 NUEVAS FUNCIONES: RADAR Y CALENDARIO INTELIGENTE
# ==============================================================
st.markdown("<br><hr style='margin-bottom: 25px;'>", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #E2E8F0;"> 
    <div style="display: flex; align-items: center; gap: 10px;"> 
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/></svg>
        <h3 style="margin: 0; font-size: 1.4rem; font-weight: 600; color: #0F172A; letter-spacing: -0.5px;">Radar de Oportunidades (Calendario Inteligente)</h3> 
    </div> 
    <p style="margin: 4px 0 0 38px; font-size: 0.9rem; color: #64748B;">Descubre qué sembrar hoy explorando todos los cultivos del mercado simultáneamente.</p> 
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='btn-scanner'>", unsafe_allow_html=True)
btn_escaner = st.button("🚀 Escanear todo el mercado para esta semana", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if btn_escaner:
    with st.spinner("Analizando bases de datos y calculando retornos para toda la cartera de cultivos..."):
        dia_actual = datetime.now().timetuple().tm_yday
        fecha_actual_str = datetime.now().strftime("%d de %B")
        
        lista_rankings = []
        datos_matriz = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        for c_nombre, c_perfil in PERFILES_AGRONOMICOS.items():
            if c_nombre == "DEFAULT": continue
            
            nom_arch = f"Precios_{c_nombre.replace(' ', '_').replace('-', '').replace('__', '_')}_Puebla.csv"
            ruta = next((r for r in [os.path.join(base_dir, nom_arch), os.path.join(base_dir, "Proyecto_Agro", nom_arch), nom_arch] if os.path.exists(r)), None)
            
            if ruta:
                df_p = pd.read_csv(ruta)
                df_temp = pd.DataFrame()
                df_temp['Fecha'] = pd.to_datetime(df_p.iloc[:, 0], dayfirst=True, errors='coerce')
                df_temp['Presentacion'] = df_p.iloc[:, 1].astype(str)
                # SOLUCIÓN AL ERROR: Convertimos los precios a numérico limpiamente, ignorando textos ("ND", comas)
                df_temp['Precio_Caja'] = pd.to_numeric(df_p.iloc[:, 5], errors='coerce')
                df_temp = df_temp.dropna(subset=['Fecha', 'Precio_Caja'])
                
                def calcular_precio_base_scanner(row, unidad):
                    presentacion = str(row['Presentacion']).lower().strip()
                    precio = float(row['Precio_Caja'])
                    nums = re.findall(r'\d+', presentacion)
                    cant = float(nums[-1]) if nums else 1.0
                    
                    if unidad == 'pieza': return precio / (cant * 12.0) if 'docena' in presentacion else precio / cant
                    elif unidad == 'docena': return (precio / cant) * 12.0 if 'pieza' in presentacion or 'pza' in presentacion else precio / cant
                    else: 
                        if 'ton' in presentacion: return precio / (cant * 1000.0)
                        elif 'kg' in presentacion or 'kilo' in presentacion: return precio / cant
                        elif nums: return precio / cant
                        return precio / 14.0
                
                if not df_temp.empty:
                    df_temp['Precio'] = df_temp.apply(lambda r: calcular_precio_base_scanner(r, c_perfil['unidad']), axis=1)
                    df_temp['Dia_Anio'] = df_temp['Fecha'].dt.dayofyear
                    
                    perfil_diario = df_temp.groupby('Dia_Anio')['Precio'].mean().reindex(range(1, 366)).ffill().bfill()
                    perfil_extend = pd.concat([perfil_diario, perfil_diario]).reset_index(drop=True)
                    
                    rois_anuales = []
                    for d in range(365):
                        precio_futuro = perfil_extend.iloc[d + c_perfil['veg'] : d + c_perfil['veg'] + c_perfil['cos']].mean()
                        inv = 1.0 * c_perfil['rend_sugerido'] * c_perfil['multiplicador'] * c_perfil['costo_sugerido']
                        gan = 1.0 * c_perfil['rend_sugerido'] * c_perfil['multiplicador'] * precio_futuro
                        roi = ((gan - inv) / inv * 100) if inv > 0 else 0
                        rois_anuales.append(roi)
                    
                    roi_hoy = rois_anuales[dia_actual - 1] if len(rois_anuales) > 0 else 0
                    lista_rankings.append({"Cultivo": c_nombre.split("-")[0].strip(), "Emoji": c_perfil["emoji"], "ROI": roi_hoy})
                    
                    meses_dias = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
                    for m in range(12):
                        segmento = rois_anuales[meses_dias[m]:meses_dias[m+1]]
                        roi_mes = sum(segmento)/len(segmento) if len(segmento) > 0 else 0
                        datos_matriz.append({"Mes": m+1, "Cultivo": f"{c_perfil['emoji']} {c_nombre.split('-')[0].strip()}", "ROI": roi_mes})

        if len(lista_rankings) > 0:
            df_rank = pd.DataFrame(lista_rankings).sort_values("ROI", ascending=False).head(3)
            
            st.success(f"**Análisis completado.** Hoy es {fecha_actual_str}. Estas son las mejores opciones para iniciar la siembra esta semana:")
            st.markdown("<br>", unsafe_allow_html=True)
            
            r1, r2, r3 = st.columns(3)
            tops = df_rank.to_dict('records')
            
            if len(tops) > 0:
                with r1: st.markdown(f"<div class='top-crop-card'><div class='crop-emoji'>{tops[0]['Emoji']}</div><h3 style='margin:0; color:#0F172A;'>{tops[0]['Cultivo']}</h3><p style='color:#10B981; font-weight:bold; margin-top:5px;'>Opción #1 (ROI {tops[0]['ROI']:.0f}%)</p></div>", unsafe_allow_html=True)
            if len(tops) > 1:
                with r2: st.markdown(f"<div class='top-crop-card'><div class='crop-emoji'>{tops[1]['Emoji']}</div><h3 style='margin:0; color:#0F172A;'>{tops[1]['Cultivo']}</h3><p style='color:#3B82F6; font-weight:bold; margin-top:5px;'>Opción #2 (ROI {tops[1]['ROI']:.0f}%)</p></div>", unsafe_allow_html=True)
            if len(tops) > 2:
                with r3: st.markdown(f"<div class='top-crop-card'><div class='crop-emoji'>{tops[2]['Emoji']}</div><h3 style='margin:0; color:#0F172A;'>{tops[2]['Cultivo']}</h3><p style='color:#F59E0B; font-weight:bold; margin-top:5px;'>Opción #3 (ROI {tops[2]['ROI']:.0f}%)</p></div>", unsafe_allow_html=True)
            
            st.markdown("<br><hr><br>", unsafe_allow_html=True)
            
            st.markdown("#### 🗓️ Mapa de Calor Anual de Siembras (Temporadas Altas)")
            st.caption("Los recuadros más verdes indican los meses donde históricamente es más rentable iniciar la siembra para cada cultivo.")
            
            df_heat = pd.DataFrame(datos_matriz)
            meses_labels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            
            matriz_pivot = df_heat.pivot(index='Cultivo', columns='Mes', values='ROI')
            
            fig_hm = go.Figure(data=go.Heatmap(
                z=matriz_pivot.values,
                x=meses_labels,
                y=matriz_pivot.index,
                colorscale='RdYlGn',
                hovertemplate='<b>%{y}</b><br>Siembra en %{x}<br>ROI Esperado: %{z:.1f}%<extra></extra>',
                showscale=False
            ))
            
            fig_hm.update_layout(
                font=dict(family="Inter", size=12, color="#475569"),
                plot_bgcolor='#FFFFFF', paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=10, b=10),
                height=100 + (len(matriz_pivot) * 35),
                xaxis=dict(side="top", showgrid=False),
                yaxis=dict(showgrid=False, autorange="reversed")
            )
            st.plotly_chart(fig_hm, use_container_width=True, config={'displayModeBar': False})
        else:
            st.warning("No se encontraron bases de datos de precios locales para realizar el escaneo masivo.")
