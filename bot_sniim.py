import os
import time
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

print("🤖 Iniciando Bot Extractor SNIIM (GitHub Actions)...")

# --- DICCIONARIO DEL TOP 20 MVP CON IDs REALES DEL SNIIM ---
CULTIVOS_SNIIM = {
    "Tomate Saladette - Primera": "839",
    "Tomate Verde - Primera": "842",
    "Cebolla Bola - Primera": "183",
    "Chile Jalapeño - Primera": "233",
    "Chile Poblano - Primera": "242",
    "Chile Serrano - Primera": "246",
    "Aguacate Hass - Primera": "133",
    "Limón s/semilla - Primera": "426",
    "Papa Alpha - Primera": "740",
    "Zanahoria mediana - Primera": "880",
    "Calabacita Italiana - Primera": "170",
    "Pepino - Primera": "771",
    "Lechuga Romanita grande - Primera": "405",
    "Fresa - Primera": "358",
    "Papaya Maradol - Primera": "609",
    "Sandía Sangría - Primera": "787",
    "Melón Cantaloupe # 9 - Primera": "499",
    "Plátano Chiapas - Primera": "663",
    "Mango Ataulfo - Primera": "465",
    "Brócoli - Primera": "162"
}

# Configuración del navegador para GitHub Actions (Sin interfaz gráfica)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Inicializar driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Fechas: Extraer los últimos 2 años de historia para asegurar datos suficientes
fecha_hoy = datetime.now()
fecha_inicio = fecha_hoy - timedelta(days=730)
str_fecha_fin = fecha_hoy.strftime("%d/%m/%Y")
str_fecha_ini = fecha_inicio.strftime("%d/%m/%Y")

URL_SNIIM = "http://www.economia-sniim.gob.mx/Nuevos/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ConsultaFrutasYHortalizas.aspx"

for cultivo, id_sniim in CULTIVOS_SNIIM.items():
    print(f"🔄 Extrayendo datos de: {cultivo} (ID: {id_sniim})...")
    try:
        driver.get(URL_SNIIM)
        time.sleep(2) # Esperar a que cargue la página (.aspx es lento)

        # 1. Seleccionar Fechas
        campo_fecha_ini = driver.find_element(By.ID, "txtFechaIni")
        campo_fecha_ini.clear()
        campo_fecha_ini.send_keys(str_fecha_ini)
        
        campo_fecha_fin = driver.find_element(By.ID, "txtFechaFin")
        campo_fecha_fin.clear()
        campo_fecha_fin.send_keys(str_fecha_fin)

        # 2. Seleccionar Mercado (46 suele ser Central de Abasto de Puebla, ajusta si tu ID era otro)
        select_destino = Select(driver.find_element(By.ID, "ddlDestino"))
        try:
            select_destino.select_by_visible_text("Puebla: Central de Abasto de Puebla")
        except:
            pass # Si no encuentra Puebla, busca el seleccionado por defecto

        # 3. Seleccionar el Cultivo
        select_producto = Select(driver.find_element(By.ID, "ddlProducto"))
        select_producto.select_by_value(id_sniim)
        
        # 4. Hacer clic en "Buscar"
        btn_buscar = driver.find_element(By.ID, "btnBuscar")
        btn_buscar.click()
        time.sleep(3) # Esperar a que la tabla se genere

        # 5. Extraer la tabla con Pandas
        html_pagina = driver.page_source
        tablas = pd.read_html(html_pagina)
        
        # SNIIM genera varias tablas de estructura, la de datos suele ser la 2da o 3ra
        df_datos = None
        for tabla in tablas:
            if "Fecha" in tabla.columns or (len(tabla.columns) > 5 and "Precio" in str(tabla.values)):
                df_datos = tabla
                break

        if df_datos is not None and not df_datos.empty:
            # Limpiar el nombre para guardarlo como lo espera la app
            nombre_limpio = cultivo.replace(" ", "_").replace("-", "").replace("__", "_")
            nombre_archivo = f"Precios_{nombre_limpio}_Puebla.csv"
            
            df_datos.to_csv(nombre_archivo, index=False)
            print(f"✅ ¡Éxito! Guardado como {nombre_archivo}")
        else:
            print(f"⚠️ No se encontraron datos tabulares para {cultivo}.")

    except Exception as e:
        print(f"❌ Error en {cultivo}: {str(e)}")

driver.quit()
print("🎉 Extracción finalizada. El bot ha cerrado sesión.")
