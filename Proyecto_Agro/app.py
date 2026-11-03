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

# --- IMPORTACIÓN DEL MOTOR DE CLIMA (La NASA sí permite conexiones en vivo) ---
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
    "dashboard": '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#0F172A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',
    "chart": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    "bars": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect width="4" height="7" x="7" y="14" rx="1"/><rect width="4" height="12" x="15" y="9" rx="1"/></svg>',
    "cloud": '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>'
}

def render_section(icon_key, title):
    return f"""<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
        {ICONS[icon_key]}<h2 style="margin: 0; font-size: 1.8rem; color: #0F172A;">{title}</h2></div>"""

def dia_a_fecha(dia_anio):
    fecha_generica = datetime(2024, 1, 1) + timedelta(days=int(dia_anio) - 1)
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    return f"{fecha_generica.day} de {meses[fecha_generica.month - 1]}"

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Open+Sans:wght@400;600&display=swap');
    html, body, [class*="css"] {{ font-family: 'Open Sans', sans-serif; background-color: #F8F9FA !important; color: #1E293B !important; }}
    h1, h2, h3, h4, h5, h6 {{ font-family: 'Inter', sans-serif !important; color: #0F172A !important; font-weight: 800 !important; letter-spacing: -0.5px; }}

    /* --- ESTILOS GENERALES (PC) --- */
    .header-container {{ display: flex; justify-content: space-between; align-items: center; padding: 5px 30px; background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; margin: -3rem -3rem 1.5rem -3rem; box-shadow: 0 4px 20px rgba(0,0,0,0.03); }}
    .logo-main {{ height: 75px; object-fit: contain; }} 
    .nav-links {{ display: flex; align-items: center; gap: 20px; }}
    .nav-links a {{ color: #475569; text-decoration: none; font-weight: 600; font-family: 'Inter', sans-serif; }}
    .btn-login {{ padding: 6px 16px; border: 2px solid #10B981; border-radius: 8px; color: #10B981 !important; font-weight: bold; transition: 0.3s; white-space: nowrap; }}
    .btn-login:hover {{ background-color: #10B981; color: white !important; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2); }}

    .hero-wrapper {{ position: relative; display: flex; justify-content: center; align-items: center; height: 300px; margin-bottom: 1.5rem; overflow: hidden; border-radius: 20px; background-color: #E2E8F0; }}
    .hero-bg-left {{ position: absolute; left: 0; top: 0; width: 35%; height: 100%; object-fit: cover; border-radius: 0 50% 50% 0 / 0 30% 70% 0; z-index: 1; }}
    .hero-bg-right {{ position: absolute; right: 0; top: 0; width: 35%; height: 100%; object-fit: cover; border-radius: 50% 0 0 50% / 30% 0 0 70%; z-index: 1; }}
    .hero-text-card {{ position: relative; z-index: 2; background-color: rgba(255, 255, 255, 0.95); padding: 1.5rem 2.5rem; border-radius: 16px; max-width: 60%; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.08); backdrop-filter: blur(10px); }}
    .hero-title {{ font-size: 2.3rem !important; margin-bottom: 0.5rem; line-height: 1.2; color: #064E3B !important; }}
    .hero-subtitle {{ font-size: 1.1rem; color: #475569; margin-bottom: 0; font-weight: 400; line-height: 1.5; }}

    div.stButton > button:first-child {{ background: linear-gradient(135deg, #D97706 0%, #B45309 100%) !important; color: white !important; font-family: 'Inter', sans-serif !important; font-weight: 700 !important; font-size: 1.05rem !important; padding: 0.7rem 1.5rem !important; border-radius: 10px !important; border: none !important; width: 100%; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(217, 119, 6, 0.3); }}
    div.stButton > button:first-child:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(217, 119, 6, 0.4); }}
    
    .logos-container {{ display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 40px; margin-top: 15px; padding-top: 20px; border-top: 1px solid #E2E8F0; }}
    .logo-item {{ filter: grayscale(100%); opacity: 0.5; transition: all 0.3s ease; object-fit: contain; }}
    .logo-item:hover {{ filter: grayscale(0%); opacity: 1; }}
    .logo-sniim {{ height: 22px; }}
    .logo-fira {{ height: 38px; }}
    .logo-siap {{ height: 38px; }}
    .logo-nasa {{ font-family: 'Inter', sans-serif; font-weight: 800; color: #64748B; font-size: 1.1rem; letter-spacing: 0.5px; opacity: 0.6; cursor: default; }}
    
    .fira-card {{ background-color: #F8FAFC; padding: 15px; border-radius: 10px; border-left: 4px solid #3B82F6; margin-bottom: 15px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }}
    .fira-card a {{ color: #3B82F6; font-weight: 600; text-decoration: none; display: block; margin-top: 10px; font-size: 0.9rem; }}
    
    div[data-testid="metric-container"] {{ background-color: #FFFFFF; padding: 1rem 1.5rem; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }}
    div[data-testid="metric-container"] label {{ font-family: 'Inter', sans-serif !important; font-weight: 600 !important; color: #64748B !important; font-size: 0.95rem !important; }}

    /* =========================================================
        📱 REGLAS DE RESPONSIVIDAD (SOLO PARA CELULARES)
        ========================================================= */
    @media (max-width: 768px) {{
        /* 1. Arreglar el Menú superior */
        .header-container {{ flex-direction: column; padding: 15px; gap: 15px; margin: -3rem -1.5rem 1.5rem -1.5rem; }}
        .logo-main {{ height: 50px; }} 
        .nav-links {{ width: 100%; justify-content: space-evenly; flex-wrap: wrap; }}
        
        /* 2. Arreglar el colapso del texto en la Tarjeta Principal */
        .hero-wrapper {{ height: auto; padding: 30px 15px; border-radius: 12px; }}
        .hero-bg-left, .hero-bg-right {{ opacity: 0.15; width: 50%; }} /* Atenuamos imágenes de fondo */
        .hero-text-card {{ max-width: 100%; padding: 1.5rem 1rem; }} /* Expandimos la tarjeta al 100% */
        .hero-title {{ font-size: 1.8rem !important; }} /* Reducimos un poco la fuente */
        .hero-subtitle {{ font-size: 1rem; }}
        
        /* 3. Arreglar la asfixia de los Logos */
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
            <h1 class='hero-title'>¿Cuándo sembrar para ganar más?</h1>
            <p class='hero-subtitle'>Algoritmos predictivos que cruzan precios históricos y clima satelital para encontrar tu ventana de máxima rentabilidad.</p>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("### Configuración de la Simulación")
col_busq1, col_busq2, col_busq3, col_busq4 = st.columns([2, 2, 2, 2])
with col_busq1:
    opciones_cultivos = list(PERFILES_AGRONOMICOS.keys())
    indice_defecto = opciones_cultivos.index("Tomate Saladette - Primera") if "Tomate Saladette - Primera" in opciones_cultivos else 0
    cultivo_seleccionado = st.selectbox("1. ¿Qué cultivo?", opciones_cultivos, index=indice_defecto)
with col_busq2:
    ubicacion = st.selectbox("2. ¿Dónde estás?", ["Tehuacán, Puebla", "Ajalpan, Puebla", "Tecamachalco, Puebla"], index=0)
with col_busq3:
    meta_mercado = st.selectbox("3. Horizonte de Análisis", ["3 Años (Recomendado)", "1 Año", "5 Años"])
    anios_historia = int(meta_mercado.split()[0])
with col_busq4:
    st.markdown("<br>", unsafe_allow_html=True)
    ejecutar_btn = st.button("OBTENER DATOS Y CALCULAR")

perfil = PERFILES_AGRONOMICOS.get(cultivo_seleccionado, PERFILES_AGRONOMICOS["DEFAULT"])

st.sidebar.markdown("### 🏦 Módulo de Costos (FIRA)")
st.sidebar.markdown(f"""
    <div class="fira-card">
        <small>Los costos y rendimientos cambian según la región. Consulta el Sistema Agrocostos Oficial para validarlo:</small>
        <a href="https://www.fira.gob.mx/Nd/Agrocostos.jsp" target="_blank">↗ Abrir Portal Agrocostos FIRA</a>
    </div>
""", unsafe_allow_html=True)

costo_usuario = st.sidebar.number_input(f"Costo de Producción (MXN/{perfil['unidad']})", min_value=0.1, max_value=500.0, value=float(perfil["costo_sugerido"]), step=0.5)
area_ha = st.sidebar.number_input("Superficie (Hectáreas)", min_value=0.1, value=1.0, step=0.5)
rendimiento = st.sidebar.number_input(perfil["etiqueta_rend"], min_value=1, value=int(perfil["rend_sugerido"]))
dias_veg = st.sidebar.number_input("Días de Desarrollo", min_value=10, value=int(perfil["veg"]))
dias_cos = st.sidebar.number_input("Días de Cosecha", min_value=5, value=int(perfil["cos"]))

inversion_total = area_ha * rendimiento * perfil["multiplicador"] * costo_usuario

st.markdown(f"""
    <div class='logos-container'>
        <img src='{logo_sniim}' class='logo-item logo-sniim' alt='SNIIM'>
        <img src='{logo_fira}' class='logo-item logo-fira' alt='FIRA'>
        <img src='{logo_siap}' class='logo-item logo-siap' alt='SIAP'>
        <span class='logo-item logo-nasa'>NASA POWER</span>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

if 'df_maestro' not in st.session_state:
    st.session_state.df_maestro = None

if ejecutar_btn:
    with st.status("Analizando bases de datos espaciales y de mercado...", expanded=True) as status:
        st.write("🛰️ Descargando histórico climático de NASA POWER...")
        res_clima = extraer_clima_historico(localidad=ubicacion, anios_historia=anios_historia)
        if res_clima["status"] == "success":
            df_clima = pd.read_csv(res_clima["archivo"])
            df_clima['Fecha'] = pd.to_datetime(df_clima['Fecha'])
        else:
            st.error(res_clima["mensaje"]); st.stop()
            
        st.write("🧠 Sincronizando modelo de mercado local ultrarrápido...")
        nombre_limpio = cultivo_seleccionado.replace(" ", "_").replace("-", "").replace("__", "_")
        nombre_archivo = f"Precios_{nombre_limpio}_Puebla.csv"
        
        # Rastreador inteligente: Busca el CSV tanto en la raíz de GitHub como en subcarpetas
        ruta_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre_archivo)
        ruta_csv = nombre_archivo if os.path.exists(nombre_archivo) else ruta_local
        
        if os.path.exists(ruta_csv):
            df_precios_raw = pd.read_csv(ruta_csv)
            df_precios = pd.DataFrame()
            df_precios['Fecha'] = pd.to_datetime(df_precios_raw.iloc[:, 0], dayfirst=True, errors='coerce')
            df_precios['Presentacion'] = df_precios_raw.iloc[:, 1].astype(str)
            df_precios['Precio_Caja'] = pd.to_numeric(df_precios_raw.iloc[:, 5], errors='coerce')
            df_precios = df_precios.dropna(subset=['Fecha', 'Precio_Caja'])
            
            def calcular_precio_base(row):
                presentacion = str(row['Presentacion']).lower().strip()
                precio_bruto = float(row['Precio_Caja'])
                unidad_perfil = perfil['unidad']
                nums = re.findall(r'\d+', presentacion)
                cantidad_num = float(nums[-1]) if nums else 1.0
                
                if unidad_perfil == 'pieza':
                    return precio_bruto / (cantidad_num * 12.0) if 'docena' in presentacion else precio_bruto / cantidad_num
                elif unidad_perfil == 'docena':
                    return (precio_bruto / cantidad_num) * 12.0 if 'pieza' in presentacion or 'pza' in presentacion else precio_bruto / cantidad_num
                else: 
                    if 'tonelada' in presentacion or 'ton ' in presentacion: return precio_bruto / (cantidad_num * 1000.0)
                    elif 'kilogramo' in presentacion or 'kg' in presentacion or 'kilo' in presentacion: return precio_bruto / cantidad_num
                    elif nums: return precio_bruto / cantidad_num
                    return precio_bruto / 14.0
                    
            df_precios['Precio_Base'] = df_precios.apply(calcular_precio_base, axis=1).round(2)
            
            fecha_min = df_precios['Fecha'].min()
            fecha_max = df_clima['Fecha'].max()
            df_maestro = pd.merge(df_clima[(df_clima['Fecha'] >= fecha_min) & (df_clima['Fecha'] <= fecha_max)], df_precios[['Fecha', 'Precio_Base']], on='Fecha', how='left')
            df_maestro = df_maestro.sort_values('Fecha').reset_index(drop=True)
            df_maestro['Precio_Base'] = df_maestro['Precio_Base'].ffill().bfill()
            st.session_state.df_maestro = df_maestro
            status.update(label="¡Análisis completado en tiempo récord!", state="complete", expanded=False)
        else:
            st.error(f"Falta la base de datos para: {cultivo_seleccionado}. Sincronizando en segundo plano...")
            status.update(label="Sincronización requerida", state="error", expanded=False)
            st.stop()

# --- RESULTADOS (UI PREMIUM CON SVGs) ---
if st.session_state.df_maestro is not None:
    df_maestro = st.session_state.df_maestro.copy()
    
    st.markdown(render_section("dashboard", "Panel de Inteligencia Estratégica"), unsafe_allow_html=True)
    
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
    with c1: st.metric("Ventana Óptima de Siembra", best['Fecha'], f"ROI Proyectado: {best['ROI']:.1f}%")
    with c2: st.metric("Precio Promedio Esperado", f"${best['Precio']:.2f} / {perfil['unidad']}", f"Costo FIRA: ${costo_usuario:.2f}")
    with c3: st.metric("Alertas de Frío en Desarrollo", f"{best['Frio']} Días", "Temperaturas menores a 12°C", delta_color="inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(render_section("chart", "Curva Estacional de Retorno de Inversión (ROI %)"), unsafe_allow_html=True)
    st.caption("Esta gráfica te indica **cuándo sembrar**. El sistema evalúa tu costo de producción y busca las ventanas donde el precio de venta histórico ha sido mayor.")
    
    df_graf_roi = df_pred.sort_values('Dia').copy()
    df_graf_roi['Fecha_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_graf_roi['Dia'] - 1, unit='D')
    
    fig_roi = go.Figure()
    fig_roi.add_trace(go.Scatter(
        x=df_graf_roi['Fecha_Plot'], y=df_graf_roi['ROI'], mode='lines', name='ROI Proyectado',
        line=dict(color='#10B981', width=3.5, shape='spline'), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.15)',
        hovertemplate='<b>%{x|%d de %b}</b><br>ROI: %{y:.1f}%<extra></extra>'
    ))
    fig_roi.add_hline(y=0, line_dash="dash", line_color="#EF4444", annotation_text="Punto de Quiebra (0%)", annotation_position="bottom right")
    fig_roi.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, tickformat='%b'), yaxis=dict(showgrid=True, gridcolor='#F1F5F9', zeroline=False), hovermode="x unified", margin=dict(l=0, r=0, t=20, b=10))
    st.plotly_chart(fig_roi, use_container_width=True)

    col_charts1, col_charts2 = st.columns(2)

    with col_charts1:
        st.markdown(render_section("bars", "Histórico de Mercado"), unsafe_allow_html=True)
        st.caption(f"Comparativa real de precios de venta (MXN/{perfil['unidad']}) en la Central de Abastos.")
        df_historico = df_maestro[['Fecha', 'Precio_Base']].copy()
        df_historico['Año'] = df_historico['Fecha'].dt.year.astype(str)
        df_historico['Dia_Anio'] = df_historico['Fecha'].dt.dayofyear
        df_historico['Mes_Dia_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_historico['Dia_Anio'] - 1, unit='D')
        
        fig_precios = px.line(df_historico, x='Mes_Dia_Plot', y='Precio_Base', color='Año', color_discrete_sequence=['#3B82F6', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6'], render_mode='svg')
        fig_precios.update_traces(line=dict(width=2, shape='spline'), opacity=0.8)
        fig_precios.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(title="", showgrid=False, tickformat='%b'), yaxis=dict(title=f"MXN/{perfil['unidad']}", showgrid=True, gridcolor='#F1F5F9'), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None), hovermode="x unified", margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_precios, use_container_width=True)

    with col_charts2:
        st.markdown(render_section("cloud", "Climatología Local"), unsafe_allow_html=True)
        st.caption("Temperaturas promedio y volumen de precipitación a los que se enfrentará tu cultivo.")
        df_clima_anual = perfil_anual.copy()
        df_clima_anual['Mes_Dia_Plot'] = pd.to_datetime('2024-01-01') + pd.to_timedelta(df_clima_anual['Dia_Anio'] - 1, unit='D')
        
        fig_clima = make_subplots(specs=[[{"secondary_y": True}]])
        fig_clima.add_trace(go.Bar(x=df_clima_anual['Mes_Dia_Plot'], y=df_clima_anual['Precipitacion_mm'], name='Lluvia (mm)', marker_color='rgba(56, 189, 248, 0.4)', hovertemplate='Lluvia: %{y:.1f} mm<extra></extra>'), secondary_y=True)
        fig_clima.add_trace(go.Scatter(x=df_clima_anual['Mes_Dia_Plot'], y=df_clima_anual['Temp_Max_C'], name='Máxima (°C)', line=dict(color='#F43F5E', width=2.5, shape='spline'), hovertemplate='Máx: %{y:.1f}°C<extra></extra>'), secondary_y=False)
        fig_clima.add_trace(go.Scatter(x=df_clima_anual['Mes_Dia_Plot'], y=df_clima_anual['Temp_Min_C'], name='Mínima (°C)', line=dict(color='#3B82F6', width=2.5, shape='spline'), fill='tonexty', fillcolor='rgba(244, 63, 94, 0.05)', hovertemplate='Mín: %{y:.1f}°C<extra></extra>'), secondary_y=False)
        fig_clima.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, tickformat='%b'), yaxis=dict(title="Temperatura (°C)", showgrid=True, gridcolor='#F1F5F9'), yaxis2=dict(title="Precipitación (mm)", showgrid=False, range=[0, df_clima_anual['Precipitacion_mm'].max() * 3]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified", margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_clima, use_container_width=True)
