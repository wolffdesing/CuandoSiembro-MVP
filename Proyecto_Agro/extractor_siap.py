import pandas as pd
import requests
import io
import time

def extraer_rendimientos_siap():
    print("Iniciando motor de extracción de Datos Abiertos del SIAP...")
    
    # Parámetros de búsqueda para el MVP
    estado_objetivo = "PUEBLA"
    municipios_objetivo = ["TEHUACAN", "TEHUACÁN", "HUIXCOLOTLA", "TEPANCO DE LOPEZ", "TEPANCO DE LÓPEZ"]
    
    # El SIAP oficializa sus bases de datos anuales con un desfase de tiempo normal en agricultura.
    # Consultaremos desde 2019 hasta el último año disponible en su servidor.
    anios = [2019, 2020, 2021, 2022, 2023, 2024]
    datos_consolidados = []
    
    for anio in anios:
        print(f"Conectando al servidor del SIAP para el ciclo agrícola {anio}...")
        
        # URL de la estructura estándar de Datos Abiertos de SAGARPA/SADER
        url_csv = f"http://infosiap.siap.gob.mx/gobmx/datosAbiertos_a/Cierre_agricola_{anio}.csv"
        
        try:
            # Hacer la petición como si fuéramos un navegador para que el servidor no nos bloquee
            headers = {"User-Agent": "Mozilla/5.0"}
            respuesta = requests.get(url_csv, headers=headers, timeout=20)
            
            if respuesta.status_code == 200:
                print(" -> Datos descargados. Filtrando métricas de Tomate Saladette para Tehuacán...")
                # Leer el archivo. Se usa encoding 'latin-1' porque las bases del gobierno tienen acentos (ñ, á, é)
                df = pd.read_csv(io.StringIO(respuesta.text), encoding='latin-1', on_bad_lines='skip', low_memory=False)
                
                # Normalizar los nombres de las columnas a mayúsculas
                df.columns = [col.upper().strip() for col in df.columns]
                
                # Filtrar matemáticamente
                if 'NOMESTADO' in df.columns:
                    # Nos aseguramos de cruzar el tomate rojo en el estado de Puebla
                    df_filtrado = df[
                        (df['NOMESTADO'].str.contains(estado_objetivo, case=False, na=False)) &
                        (df['NOMCULTIVO'].str.contains("Tomate", case=False, na=False))
                    ].copy()
                    
                    # Filtramos por los municipios que nos importan
                    df_filtrado = df_filtrado[df_filtrado['NOMMUNICIPIO'].str.upper().isin(municipios_objetivo)]
                    
                    if not df_filtrado.empty:
                        datos_consolidados.append(df_filtrado)
                        print(f" -> ¡Se aislaron {len(df_filtrado)} registros útiles en {anio}!")
                    else:
                        print(f" -> Sin registros de Saladette en la zona para el año {anio}.")
                else:
                    print(" -> El formato del archivo gubernamental cambió este año.")
            else:
                print(f" -> El año {anio} aún no está cerrado y publicado en Datos Abiertos (Código {respuesta.status_code}).")
                
        except Exception as e:
            print(f" -> Error de conexión en el año {anio}: {type(e).__name__}")
            
        time.sleep(1.5) # Breve pausa para no saturar al servidor del gobierno
        
    # Consolidar, limpiar y exportar
    if datos_consolidados:
        print("\nConsolidando el motor de rendimientos...")
        df_final = pd.concat(datos_consolidados, ignore_index=True)
        
        # Seleccionar estrictamente las columnas que alimentarán tu algoritmo financiero
        columnas_interes = [
            'ANIO', 'NOMESTADO', 'NOMMUNICIPIO', 'NOMCICLO', 'NOMMODALIDAD', 'NOMCULTIVO', 
            'SEMBRADA', 'COSECHADA', 'SINIESTRADA', 'VOLUMENPRODUCCION', 'RENDIMIENTO', 'PRECIOMEDIORURAL'
        ]
        
        # Nos aseguramos de mantener solo las columnas que sí existen
        columnas_finales = [col for col in columnas_interes if col in df_final.columns]
        df_exportar = df_final[columnas_finales]
        
        nombre_archivo = "Historico_Rendimientos_Tehuacan.csv"
        df_exportar.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
        print(f"¡Éxito total! Se guardaron {len(df_exportar)} registros productivos en '{nombre_archivo}'.")
    else:
        print("\nNo se lograron descargar los datos. El servidor del SIAP podría estar en mantenimiento temporal.")

if __name__ == "__main__":
    extraer_rendimientos_siap()