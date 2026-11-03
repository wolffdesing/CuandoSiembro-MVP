import pandas as pd
import io
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Catálogo completo de tus 20 cultivos MVP
CATALOGO_SNIIM = {
    "Tomate Saladette - Primera": "839", "Tomate Verde - Primera": "842", "Cebolla Bola - Primera": "183",
    "Cebolla Morada - Primera": "187", "Chile Jalapeño - Primera": "233", "Chile Poblano - Primera": "242",
    "Chile Serrano - Primera": "246", "Aguacate Hass - Primera": "133", "Limón s/semilla - Primera": "426",
    "Papa Alpha - Primera": "740", "Lechuga Romanita grande - Primera": "405", "Zanahoria mediana - Primera": "880",
    "Brócoli - Primera": "162", "Calabacita Italiana - Primera": "170", "Pepino - Primera": "771",
    "Fresa - Primera": "358", "Sandía Sangría - Primera": "787", "Papaya Maradol - Primera": "609",
    "Melón Cantaloupe # 9 - Primera": "499", "Plátano Chiapas - Primera": "663"
}

def actualizar_base_datos():
    print(f"--- Iniciando actualización masiva de la base de datos: {datetime.now()} ---")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    espera = WebDriverWait(driver, 25)
    
    for cultivo, id_producto in CATALOGO_SNIIM.items():
        print(f"Extrayendo: {cultivo}...")
        try:
            fecha_fin = datetime.now().strftime('%d/%m/%Y')
            fecha_inicio = (datetime.now() - relativedelta(years=3)).strftime('%d/%m/%Y')
            
            driver.get("http://www.economia-sniim.gob.mx/nuevo/Home.aspx?opcion=Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ConsultaFrutasYHortalizas.aspx?SubOpcion=4|0")
            time.sleep(2)
            driver.switch_to.frame("ifraHome")
            
            Select(espera.until(EC.presence_of_element_located((By.ID, "ddlProducto")))).select_by_value(id_producto)
            Select(driver.find_element(By.ID, "ddlDestino")).select_by_value("210") # Puebla
            
            driver.execute_script(f"document.getElementById('txtFechaInicio').value = '{fecha_inicio}';")
            driver.execute_script(f"document.getElementById('txtFechaFinal').value = '{fecha_fin}';")
            driver.find_element(By.ID, "btnBuscar").click()
            time.sleep(6) # Paciencia para que el SNIIM cargue la tabla
            
            tabla = espera.until(EC.presence_of_element_located((By.ID, "tblResultados")))
            df = pd.read_html(io.StringIO(tabla.get_attribute('outerHTML')))[0]
            
            nombre_limpio = cultivo.replace(" ", "_").replace("-", "").replace("__", "_")
            nombre_archivo = f"Precios_{nombre_limpio}_Puebla.csv"
            df.to_csv(nombre_archivo, index=False)
            print(f"✅ Éxito: {nombre_archivo} guardado ({len(df)} registros).")
            
        except Exception as e:
            print(f"❌ Error con {cultivo}: {str(e)}")
            continue # Si uno falla, salta al siguiente sin detener el programa
            
    driver.quit()
    print("--- Actualización finalizada ---")

if __name__ == "__main__":
    actualizar_base_datos()
