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

def extraer_historico_completo():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    # Forzamos una pantalla grande para evitar que elementos tapen el botón
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    # Aumentamos la paciencia del bot a 40 segundos para el servidor gubernamental
    espera = WebDriverWait(driver, 40) 
    
    try:
        print("Conectando al SNIIM...")
        driver.get("http://www.economia-sniim.gob.mx/nuevo/Home.aspx?opcion=Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/ConsultaFrutasYHortalizas.aspx?SubOpcion=4|0") 
        time.sleep(random.uniform(4.0, 5.0))
        
        driver.switch_to.frame("ifraHome")
        print("Configurando parámetros de búsqueda...")
        
        # 1. Producto (Tomate Saladette)
        Select(espera.until(EC.presence_of_element_located((By.ID, "ddlProducto")))).select_by_value("839")
        time.sleep(random.uniform(1.5, 2.5))
        
        # 2. Mercado (Central de Abasto de Puebla = ID 210)
        Select(driver.find_element(By.ID, "ddlDestino")).select_by_value("210")
        print("Mercado detectado: Central de Abasto de Puebla")
        time.sleep(random.uniform(1.5, 2.5))
        
        # 3. Fechas
        driver.execute_script("document.getElementById('txtFechaInicio').value = '01/01/2021';")
        driver.execute_script("document.getElementById('txtFechaFinal').value = '04/10/2026';")
        time.sleep(1.0)
        
        # 4. Buscar
        driver.find_element(By.ID, "btnBuscar").click()
        print("Consultando servidor del gobierno...")
        time.sleep(random.uniform(5.0, 7.0))
        
        # --- DETECTAR TOTAL DE PÁGINAS ---
        try:
            elemento_paginacion = espera.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Página') and contains(text(), 'de')]")))
            texto_paginacion = elemento_paginacion.text.strip()
            match = re.search(r'de\s+(\d+)', texto_paginacion)
            total_paginas = int(match.group(1)) if match else 1
            print(f"¡El bot detectó exitosamente que hay {total_paginas} páginas de información!")
        except:
            print("No se encontró el texto de paginación. Se extraerá 1 sola página.")
            total_paginas = 1
        
        # 5. BUCLE EXACTO Y CONTROLADO
        todos_los_datos = []
        
        for pagina_actual in range(1, total_paginas + 1):
            try:
                # Esperar a que la tabla cargue y obtener su HTML
                tabla_elemento = espera.until(EC.presence_of_element_located((By.ID, "tblResultados")))
                tabla_html_actual = tabla_elemento.get_attribute('outerHTML')
                
                # Extraer datos con Pandas
                df_temp = pd.read_html(io.StringIO(tabla_html_actual))[0]
                print(f"-> Extrayendo página {pagina_actual}/{total_paginas} | Filas detectadas: {len(df_temp)}")
                todos_los_datos.append(df_temp)
                
                # Avanzar solo si NO estamos en la última página
                if pagina_actual < total_paginas:
                    btn_siguiente = driver.find_elements(By.ID, "ibtnSiguiente")
                    if len(btn_siguiente) > 0:
                        btn = btn_siguiente[0]
                        
                        # Hacer scroll hasta que el botón sea visible
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1.0)
                        
                        # SOLUCIÓN CLAVE: Clic simulado de mouse físico usando ActionChains 
                        try:
                            acciones = ActionChains(driver)
                            acciones.move_to_element(btn).click().perform()
                        except:
                            # Respaldo de seguridad en caso de que ActionChains sea bloqueado por la UI
                            btn.click()
                        
                        # LÓGICA DE ESPERA: Aguardar textualmente el número de la siguiente página
                        pagina_esperada = pagina_actual + 1
                        
                        def pagina_cambiada(d):
                            try:
                                elem = d.find_element(By.XPATH, "//*[contains(text(), 'Página') and contains(text(), 'de')]")
                                # Normalizamos el texto (quitamos saltos o espacios raros de ASP.NET)
                                texto_limpio = ' '.join(elem.text.split())
                                return f"Página {pagina_esperada} de {total_paginas}" in texto_limpio
                            except:
                                return False
                        
                        # Esperar hasta que el servidor devuelva la página correcta
                        espera.until(pagina_cambiada)
                        time.sleep(2.0)
                        
            except Exception as e:
                print(f"Fin del recorrido interrumpido en la página {pagina_actual}. Detalle: {type(e).__name__} - {e}")
                break 

        # 6. Unir y exportar
        if len(todos_los_datos) > 0:
            print("\nConsolidando el modelo de datos...")
            df_final = pd.concat(todos_los_datos, ignore_index=True)
            df_final.drop_duplicates(inplace=True) 
            
            nombre_archivo = "Historico_Saladette_Puebla.csv"
            
            try:
                df_final.to_csv(nombre_archivo, index=False)
                print(f"¡Éxito total! Se guardaron {len(df_final)} registros únicos reales en '{nombre_archivo}'.")
            except PermissionError:
                nombre_backup = "Historico_Saladette_Puebla_BACKUP.csv"
                df_final.to_csv(nombre_backup, index=False)
                print(f"\n¡ADVERTENCIA! El archivo principal estaba bloqueado/abierto.")
                print(f"Tus datos NO se perdieron. Se guardaron con éxito en '{nombre_backup}'.")
        else:
            print("No se encontraron datos para guardar.")
            
    except Exception as e:
        print(f"Error crítico general: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    extraer_historico_completo()