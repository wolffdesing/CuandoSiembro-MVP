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

print("🤖 Iniciando Bot SNIIM Oficial (Modo Robusto)...")

# Diccionario oficial de los 20 cultivos MVP con sus IDs reales del SNIIM
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

# Configuración de opciones para Chrome en GitHub Actions
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# Inicializar driver de forma limpia
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

fecha_hoy = datetime.now()
fecha_inicio = fecha_hoy - timedelta(days=730) # 2 años de historia
str_fecha_fin = fecha_hoy.strftime("%d/%m/%Y")
str_fecha_ini = fecha_inicio.strftime("%d/%m/%Y")

URL_SNIIM = "http://www.economia-sniim.gob.mx/Nuevos/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ConsultaFrutasYHortalizas.aspx"

try:
    for cultivo, id_sniim in CULTIVOS_SNIIM.items():
        print(f"🔄 Consultando en línea: {cultivo}...")
        try:
            driver.get(URL_SNIIM)
            time.sleep(2)

            # Ingresar fechas
            driver.find_element(By.ID, "txtFechaIni").clear()
            driver.find_element(By.ID, "txtFechaIni").send_keys(str_fecha_ini)
            
            driver.find_element(By.ID, "txtFechaFin").clear()
            driver.find_element(By.ID, "txtFechaFin").send_keys(str_fecha_fin)

            # Seleccionar destino (Puebla)
            try:
                Select(driver.find_element(By.ID, "ddlDestino")).select_by_visible_text("Puebla: Central de Abasto de Puebla")
            except:
                pass

            # Seleccionar producto por su ID oficial
            Select(driver.find_element(By.ID, "ddlProducto")).select_by_value(id_sniim)
            
            # Click en buscar
            driver.find_element(By.ID, "btnBuscar").click()
            time.sleep(3)

            # Extraer tabla resultante con Pandas
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
                print(f"✅ Descargado y guardado: {nombre_archivo}")
            else:
                print(f"⚠️ Sin registros actuales para {cultivo}.")

        except Exception as e:
            print(f"❌ Error puntual en {cultivo}: {str(e)[:80]}")
            continue

finally:
    driver.quit()
    print("🎉 Proceso del bot finalizado.")
