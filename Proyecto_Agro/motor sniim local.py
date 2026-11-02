import pandas as pd
import requests
import io
import urllib.parse
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando Motor Anti-Bloqueo para: {cultivo}...")

    id_producto = CATALOGO_SNIIM.get(cultivo, "839")
    fecha_fin_dt = datetime.now()
    fecha_inicio_dt = fecha_fin_dt - relativedelta(years=anios_historia)
    
    fecha_inicio = fecha_inicio_dt.strftime('%d/%m/%Y')
    fecha_fin = fecha_fin_dt.strftime('%d/%m/%Y')
    
    # URL directa de la base de datos del gobierno
    url_directa = (
        f"http://www.economia-sniim.gob.mx/Consultas/MercadosNacionales/PreciosDeMercado/Agricolas/"
        f"ResultadosConsultaFechaFrutasYHortalizas.aspx?"
        f"fechaInicio={fecha_inicio}&fechaFinal={fecha_fin}&ProductoId={id_producto}&"
        f"OrigenId=-1&Origen=Todos&DestinoId=210&Destino=Puebla&PreciosPorId=1&RegistrosPorPagina=5000"
    )
    
    encoded_url = urllib.parse.quote(url_directa, safe='')
    
    # MATRIZ DE TÚNELES: Si uno falla, el sistema salta al siguiente automáticamente
    rutas = [
        {"nombre": "Conexión Directa SNIIM", "url": url_directa, "proxy": False},
        {"nombre": "Túnel Proxy (AllOrigins)", "url": f"https://api.allorigins.win/raw?url={encoded_url}", "proxy": True},
        {"nombre": "Túnel Proxy (CodeTabs)", "url": f"https://api.codetabs.com/v1/proxy?quest={encoded_url}", "proxy": True}
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    for ruta in rutas:
        print(f"-> Probando {ruta['nombre']}...")
        try:
            session = requests.Session()
            
            # Si es conexión directa, simulamos la visita al Home para obtener la "Cookie de Sesión ASP.NET" obligatoria
            if not ruta['proxy']:
                session.get("http://www.economia-sniim.gob.mx/nuevo/Home.aspx", headers=headers, timeout=15)
            
            # Ejecutamos la petición de datos
            response = session.get(ruta['url'], headers=headers, timeout=40)
            response.raise_for_status()
            
            # Verificamos que la respuesta no sea un error del proxy sino la tabla real
            if "Sistema Nacional de Información e Integración de Mercados" in response.text or "Precio" in response.text:
                
                # Pandas extrae la tabla directamente del código fuente (HTML)
                tablas = pd.read_html(io.StringIO(response.text))
                df_final = None
                
                # Buscamos la tabla que tenga las columnas correctas
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
                    return {"status": "success", "archivo": nombre_archivo, "mensaje": f"Sincronización exitosa vía {ruta['nombre']} ({len(df_final)} datos extraídos)."}
                
        except requests.exceptions.RequestException as e:
            print(f"Bloqueo en {ruta['nombre']}: {str(e)}. Saltando a la siguiente ruta...")
            time.sleep(2) # Pausa estratégica antes de usar el siguiente túnel
            continue
        except Exception as e:
            print(f"Error procesando {ruta['nombre']}: {str(e)}")
            continue
            
    return {"status": "error", "mensaje": "El Gobierno de México bloqueó las conexiones. El motor intentó evadirlo mediante 3 túneles proxy pero fue rechazado. Intenta consultar un periodo más corto."}
