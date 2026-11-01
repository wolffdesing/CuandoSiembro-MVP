from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import random
import io
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

# EL TOP 20 MVP: Cultivos de alto valor comercial y demanda
CATALOGO_SNIIM = {
    "Tomate Saladette - Primera": "839",
    "Tomate Verde - Primera": "842",
    "Cebolla Bola - Primera": "183",
    "Cebolla Morada - Primera": "187",
    "Chile Jalapeño - Primera": "233",
    "Chile Poblano - Primera": "242",
    "Chile Serrano - Primera": "246",
    "Aguacate Hass - Primera": "133",
    "Limón s/semilla - Primera": "426",
    "Papa Alpha - Primera": "740",
    "Lechuga Romanita grande - Primera": "405",
    "Zanahoria mediana - Primera": "880",
    "Brócoli - Primera": "162",
    "Calabacita Italiana - Primera": "170",
    "Pepino - Primera": "771",
    "Fresa - Primera": "358",
    "Sandía Sangría - Primera": "787",
    "Papaya Maradol - Primera": "609",
    "Melón Cantaloupe # 9 - Primera": "499",
    "Plátano Chiapas - Primera": "663"
}

def extraer_precios_historicos(cultivo="Tomate Saladette - Primera", anios_historia=3):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando motor de mercado (SNIIM) para: {cultivo}...")

    id_producto = CATALOGO_SNIIM.get(cultivo, "839")

    fecha_fin_dt = datetime.now()
    fecha_inicio_dt = fecha_fin_dt - relativedelta(years=anios_historia)
    fecha_inicio = fecha_inicio_dt.strftime('%d/%m/%Y')
    fecha_fin = fecha_fin_dt.strftime('%d/%m/%Y')
    
    print(f"Periodo de consulta: {fecha_inicio} a {fecha_fin}")

    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # MODO HEADLESS: Oculta la ventana de Chrome
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--log-level=3") 
    
    # --- LÍNEAS DE SEGURIDAD PARA SERVIDORES EN LA NUBE (LINUX) ---
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.binary_location = "/usr/bin/chromium"
driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=chrome_options)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    espera = WebDriverWait(driver, 40) 
    
    try:
        driver.get("http://www.economia-sniim.gob.mx/nuevo/Home.aspx?opcion=Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ConsultaFrutasYHortalizas.aspx?SubOpcion=4|0") 
        time.sleep(random.uniform(3.0, 4.0))
        
        driver.switch_to.frame("ifraHome")
        Select(espera.until(EC.presence_of_element_located((By.ID, "ddlProducto")))).select_by_value(id_producto)
        time.sleep(random.uniform(1.0, 2.0))
        
        Select(driver.find_element(By.ID, "ddlDestino")).select_by_value("210") # 210 = Puebla
        time.sleep(random.uniform(1.0, 2.0))
        
        driver.execute_script(f"document.getElementById('txtFechaInicio').value = '{fecha_inicio}';")
        driver.execute_script(f"document.getElementById('txtFechaFinal').value = '{fecha_fin}';")
        time.sleep(1.0)
        
        driver.find_element(By.ID, "btnBuscar").click()
        time.sleep(random.uniform(4.0, 5.0))
        
        try:
            elemento_paginacion = espera.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Página') and contains(text(), 'de')]")))
            texto_paginacion = elemento_paginacion.text.strip()
            match = re.search(r'de\s+(\d+)', texto_paginacion)
            total_paginas = int(match.group(1)) if match else 1
        except:
            total_paginas = 1
            
        todos_los_datos = []
        
        for pagina_actual in range(1, total_paginas + 1):
            try:
                tabla_elemento = espera.until(EC.presence_of_element_located((By.ID, "tblResultados")))
                tabla_html_actual = tabla_elemento.get_attribute('outerHTML')
                
                df_temp = pd.read_html(io.StringIO(tabla_html_actual))[0]
                todos_los_datos.append(df_temp)
                
                if pagina_actual < total_paginas:
                    btn_siguiente = driver.find_elements(By.ID, "ibtnSiguiente")
                    if len(btn_siguiente) > 0:
                        btn = btn_siguiente[0]
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1.0)
                        try:
                            acciones = ActionChains(driver)
                            acciones.move_to_element(btn).click().perform()
                        except:
                            btn.click()
                        
                        pagina_esperada = pagina_actual + 1
                        def pagina_cambiada(d):
                            try:
                                elem = d.find_element(By.XPATH, "//*[contains(text(), 'Página') and contains(text(), 'de')]")
                                return f"Página {pagina_esperada} de {total_paginas}" in ' '.join(elem.text.split())
                            except: return False
                        
                        espera.until(pagina_cambiada)
                        time.sleep(1.5)
                        
            except Exception as e:
                break 

        if len(todos_los_datos) > 0:
            df_final = pd.concat(todos_los_datos, ignore_index=True)
            df_final.drop_duplicates(inplace=True) 
            
            nombre_limpio = cultivo.replace(" ", "_").replace("-", "").replace("__", "_")
            nombre_archivo = f"Precios_{nombre_limpio}_Puebla.csv"
            
            df_final.to_csv(nombre_archivo, index=False)
            return {"status": "success", "archivo": nombre_archivo, "mensaje": f"Se extrajeron {len(df_final)} precios del mercado."}
        else:
            return {"status": "error", "mensaje": "No se encontraron datos en el SNIIM."}
            
    except Exception as e:
        return {"status": "error", "mensaje": f"Error del robot web: {str(e)}"}
    finally:
        driver.quit()
