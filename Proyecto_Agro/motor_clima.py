import requests
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

def extraer_clima_historico(localidad="Tehuacán, Puebla", anios_historia=3):
    """
    Se conecta a NASA POWER, extrae el clima de la localidad dada
    y devuelve la ruta del archivo CSV generado. Incluye un margen
    de seguridad de 7 días para evitar cortes en el satélite.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando motor agroclimático para: {localidad}...")
    
    # 1. Mapeo de Coordenadas por Localidad
    coordenadas = {
        "Tehuacán, Puebla": {"lat": 18.4628, "lon": -97.3927},
        "Ajalpan, Puebla": {"lat": 18.3753, "lon": -97.2570},
        "Tecamachalco, Puebla": {"lat": 18.8828, "lon": -97.7289}
    }
    
    # Si la localidad no está, usa Tehuacán por defecto
    coords = coordenadas.get(localidad, coordenadas["Tehuacán, Puebla"])
    latitud = coords["lat"]
    longitud = coords["lon"]
    
    # 2. Ventana Temporal Dinámica (Hoy menos 7 días de margen)
    fecha_fin_dt = datetime.now() - timedelta(days=7)
    fecha_inicio_dt = fecha_fin_dt - relativedelta(years=anios_historia)
    
    # Formato requerido por la NASA (YYYYMMDD)
    fecha_inicio = fecha_inicio_dt.strftime('%Y%m%d')
    fecha_fin = fecha_fin_dt.strftime('%Y%m%d')
    
    print(f"Periodo de consulta satelital: {fecha_inicio} a {fecha_fin}")
    
    # 3. Petición a la API de Agroclimatología (NASA POWER)
    url_api = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=T2M_MAX,T2M_MIN,PRECTOTCORR&"
        f"community=AG&longitude={longitud}&latitude={latitud}&"
        f"start={fecha_inicio}&end={fecha_fin}&format=JSON"
    )
    
    try:
        # Aumentamos el timeout por si la conexión de la NASA es lenta
        respuesta = requests.get(url_api, timeout=60)
        
        if respuesta.status_code == 200:
            datos_json = respuesta.json()
            
            # 4. Procesamiento ETL
            serie_tmax = datos_json['properties']['parameter']['T2M_MAX']
            serie_tmin = datos_json['properties']['parameter']['T2M_MIN']
            serie_prec = datos_json['properties']['parameter']['PRECTOTCORR']
            
            df_clima = pd.DataFrame({
                'Fecha': list(serie_tmax.keys()),
                'Temp_Max_C': list(serie_tmax.values()),
                'Temp_Min_C': list(serie_tmin.values()),
                'Precipitacion_mm': list(serie_prec.values())
            })
            
            # Formato de Fecha
            df_clima['Fecha'] = pd.to_datetime(df_clima['Fecha'], format='%Y%m%d')
            
            # Limpieza de fallos satelitales (-999 a NaN y rellenar)
            df_clima.replace(-999.0, pd.NA, inplace=True)
            df_clima.interpolate(method='linear', inplace=True)
            
            # Métrica Agronómica
            df_clima['Alerta_Helada'] = df_clima['Temp_Min_C'].apply(lambda x: 1 if x <= 4.0 else 0)
            
            # 5. Exportar a CSV temporal
            # Limpiamos el nombre de la localidad para usarlo en el archivo
            nombre_limpio = localidad.replace(", ", "_").replace(" ", "_")
            nombre_archivo = f"Clima_Descargado_{nombre_limpio}.csv"
            
            df_clima.to_csv(nombre_archivo, index=False)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ¡Éxito! Clima guardado en {nombre_archivo}")
            
            return {
                "status": "success", 
                "archivo": nombre_archivo, 
                "mensaje": f"Se extrajeron {len(df_clima)} días de clima para {localidad}."
            }
            
        else:
            return {"status": "error", "mensaje": f"Error de servidor NASA: HTTP {respuesta.status_code}"}
            
    except Exception as e:
        return {"status": "error", "mensaje": f"Fallo de conexión o timeout con la NASA: {str(e)}"}

# Bloque de prueba
if __name__ == "__main__":
    resultado = extraer_clima_historico(localidad="Tehuacán, Puebla", anios_historia=3)
    print(resultado)