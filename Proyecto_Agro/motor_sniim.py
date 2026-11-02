import pandas as pd
import requests
import io
import time
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando conexión directa al SNIIM para: {cultivo}...")

    id_producto = CATALOGO_SNIIM.get(cultivo, "839")
    fecha_fin_dt = datetime.now()
    fecha_inicio_dt = fecha_fin_dt - relativedelta(years=anios_historia)
    
    fecha_inicio = fecha_inicio_dt.strftime('%d/%m/%Y')
    fecha_fin = fecha_fin_dt.strftime('%d/%m/%Y')
    
    # URL directa con los parámetros de búsqueda inyectados
    url_directa = (
        f"http://www.economia-sniim.gob.mx/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/"
        f"ResultadosConsultaFechaFrutasYHortalizas.aspx?"
        f"fechaInicio={fecha_inicio}&fechaFinal={fecha_fin}&ProductoId={id_producto}&"
        f"OrigenId=-1&Origen=Todos&DestinoId=210&Destino=Puebla&PreciosPorId=1&RegistrosPorPagina=5000"
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    intentos_maximos = 3
    session = requests.Session()
    
    for intento in range(intentos_maximos):
        try:
            print(f"Intento {intento + 1} de {intentos_maximos}. Esperando respuesta del SNIIM (puede tardar hasta 120 segundos)...")
            
            # El secreto de la paciencia: 15 seg para conectar, 120 seg para descargar los datos lentos del SNIIM
            respuesta = session.get(url_directa, headers=headers, timeout=(15, 120))
            respuesta.raise_for_status()
            
            # Pandas lee el HTML buscando las tablas de datos
            tablas = pd.read_html(io.StringIO(respuesta.text))
            df_final = None
            
            for df in tablas:
                cols = [str(c).lower() for c in df.columns]
                if 'fecha' in cols and 'presentación' in cols:
                    df_final = df
                    break
                    
            if df_final is None and len(tablas) > 0:
                df_final = max(tablas, key=len)

            if df_final is not None and len(df_final) > 5:
                nombre_limpio = cultivo.replace(" ", "_").replace("-", "").replace("__", "_")
                nombre_archivo = f"Precios_{nombre_limpio}_Puebla.csv"
                df_final.to_csv(nombre_archivo, index=False)
                
                return {"status": "success", "archivo": nombre_archivo, "mensaje": f"Se obtuvieron {len(df_final)} registros históricos pacientemente."}
            else:
                return {"status": "error", "mensaje": "El SNIIM respondió, pero no hay datos de precios para este cultivo en Puebla."}
                
        except requests.exceptions.Timeout:
            print(f"El servidor del SNIIM está demasiado lento. Reintentando en 10 segundos...")
            time.sleep(10) # Pausa estratégica antes de volver a golpear el servidor
        except Exception as e:
            print(f"Error de conexión: {str(e)}. Reintentando en 5 segundos...")
            time.sleep(5)
            
    return {"status": "error", "mensaje": "El servidor del gobierno (SNIIM) no respondió después de 3 intentos. Intenta con 1 Año de historial."}
