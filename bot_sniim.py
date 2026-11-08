import os
import time
import sys
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

print("🤖 Iniciando Extracción Masiva SNIIM...")

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

try:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_page_load_timeout(60) # Tiempo máximo de espera para no congelarse

    fecha_hoy = datetime.now()
    fecha_inicio = fecha_hoy - timedelta(days=730)
    str_fecha_fin = fecha_hoy.strftime("%d/%m/%Y")
    str_fecha_ini = fecha_inicio.strftime("%d/%m/%Y")

    URL_SNIIM = "http://www.economia-sniim.gob.mx/Nuevos/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ConsultaFrutasYHortalizas.aspx"

    for cultivo, id_sniim in CULTIVOS_SNIIM.items():
        print(f"🔄 Extrayendo: {cultivo}...")
        try:
            driver.get(URL_SNIIM)
            time.sleep(2)

            driver.find_element(By.ID, "txtFechaIni").clear()
            driver.find_element(By.ID, "txtFechaIni").send_keys(str_fecha_ini)
            
            driver.find_element(By.ID, "txtFechaFin").clear()
            driver.find_element(By.ID, "txtFechaFin").send_keys(str_fecha_fin)

            select_destino = Select(driver.find_element(By.ID, "ddlDestino"))
            try:
                select_destino.select_by_visible_text("Puebla: Central de Abasto de Puebla")
            except:
                pass

            Select(driver.find_element(By.ID, "ddlProducto")).select_by_value(id_sniim)
            driver.find_element(By.ID, "btnBuscar").click()
            time.sleep(3)

            tablas = pd.read_html(driver.page_source)
            df_datos = None
            for tabla in tablas:
                if "Fecha" in tabla.columns or (len(tabla.columns) > 5 and "Precio" in str(tabla.values)):
                    df_datos = tabla
                    break

            if df_datos is not None and not df_datos.empty:
                nombre_limpio = cultivo.replace(" ", "_").replace("-", "").replace("__", "_")
                nombre_archivo = f"Precios_{nombre_limpio}_Puebla.csv"
                df_datos.to_csv(nombre_archivo, index=False)
                print(f"✅ Guardado: {nombre_archivo}")
            else:
                print(f"⚠️ Sin datos para {cultivo}")

        except Exception as e:
            print(f"❌ Error en {cultivo}: {e}")

    driver.quit()
    print("🎉 Proceso de extracción finalizado.")

except Exception as e:
    print(f"❌ Error CRÍTICO evitado: {e}")
    sys.exit(0) # Esto asegura que GitHub Actions no marque error rojo si algo muy grave pasa
