import requests
import pandas as pd
import datetime

def extraer_clima_historico():
    print("Iniciando motor de extracción agroclimática...")
    
    # 1. Configurar Parámetros Geoespaciales y Temporales
    # Coordenadas promedio de la zona productora (Tehuacán - Huixcolotla)
    latitud = 18.4628   # Latitud de Tehuacán (Puedes cambiarla a 18.9167 para Huixcolotla)
    longitud = -97.3927 # Longitud de Tehuacán (Puedes cambiarla a -97.7750 para Huixcolotla)
    
    # Rango de 5 años para empatar exactamente con el dataset del SNIIM
    fecha_inicio = "20210101"
    fecha_fin = "20261004"
    
    # 2. Construir la petición a la API de Agroclimatología
    # Parámetros: T2M_MAX (Temp Max), T2M_MIN (Temp Min), PRECTOTCORR (Precipitación)
    url_api = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=T2M_MAX,T2M_MIN,PRECTOTCORR&"
        f"community=AG&longitude={longitud}&latitude={latitud}&"
        f"start={fecha_inicio}&end={fecha_fin}&format=JSON"
    )
    
    try:
        print(f"Conectando a satélites/bases de datos para Lat: {latitud}, Lon: {longitud}...")
        respuesta = requests.get(url_api, timeout=30)
        
        if respuesta.status_code == 200:
            datos_json = respuesta.json()
            
            # 3. Procesar y Aplanar el JSON a un DataFrame tabular
            print("Datos recibidos. Transformando formato espacial a tabular (Pandas)...")
            
            # Extraer las series de tiempo del JSON
            serie_tmax = datos_json['properties']['parameter']['T2M_MAX']
            serie_tmin = datos_json['properties']['parameter']['T2M_MIN']
            serie_prec = datos_json['properties']['parameter']['PRECTOTCORR']
            
            # Construir el DataFrame
            df_clima = pd.DataFrame({
                'Fecha': list(serie_tmax.keys()),
                'Temp_Max_C': list(serie_tmax.values()),
                'Temp_Min_C': list(serie_tmin.values()),
                'Precipitacion_mm': list(serie_prec.values())
            })
            
            # 4. Limpieza de Datos (ETL)
            # Convertir el formato de fecha (YYYYMMDD a YYYY-MM-DD)
            df_clima['Fecha'] = pd.to_datetime(df_clima['Fecha'], format='%Y%m%d')
            
            # La API devuelve -999.0 cuando hay un error de lectura satelital. Los reemplazamos por NaN.
            df_clima.replace(-999.0, pd.NA, inplace=True)
            
            # Interpolar (rellenar) los valores faltantes matemáticamente para no tener huecos
            df_clima.interpolate(method='linear', inplace=True)
            
            # Crear una columna de "Alerta de Helada" (1 si la temperatura mínima bajó de 4°C, 0 si no)
            df_clima['Alerta_Helada'] = df_clima['Temp_Min_C'].apply(lambda x: 1 if x <= 4.0 else 0)
            
            # 5. Exportar CSV
            nombre_archivo = "Historico_Clima_Tehuacan_5_Anios.csv"
            df_clima.to_csv(nombre_archivo, index=False)
            
            print(f"¡Éxito! Se extrajeron {len(df_clima)} días de registros meteorológicos.")
            print(f"El dataset está listo para cruzar con precios. Guardado en '{nombre_archivo}'")
            
        else:
            print(f"Error en el servidor de origen. Código HTTP: {respuesta.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión a la API: {e}")

if __name__ == "__main__":
    extraer_clima_historico()