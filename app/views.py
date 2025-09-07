import json
import os
import time
import random
import re
import signal
import PyPDF2
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.cache import cache
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_chrome_options():
    """Crear nueva configuración de Chrome optimizada para Render"""
    options = Options()
    
    # Configuración optimizada para Render
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--window-size=1280,720')
    options.add_argument('--single-process')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--memory-pressure-off')
    options.add_argument('--disable-ipc-flooding-protection')
    
    # Configuración de descargas
    download_folder = os.path.join(settings.BASE_DIR, "descargas_anses")
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        
    prefs = {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 2
    }
    options.add_experimental_option("prefs", prefs)
    
    return options

@csrf_exempt
@require_POST
def consultar_anses(request):
    # Configurar timeout de 25 segundos máximo
    def timeout_handler(signum, frame):
        raise TimeoutError("Tiempo de ejecución excedido")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(25)
    
    try:
        # Obtener datos del request
        data = json.loads(request.body)
        identidad = data.get('dni')
        
        if not identidad:
            return JsonResponse({
                'success': False,
                'error': 'DNI no proporcionado'
            })
        
        # Verificar cache para evitar scraping repetido
        cache_key = f"anses_{identidad}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(cached_data)
        
        # Configurar driver optimizado
        options = get_chrome_options()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        try:
            # Configurar timeouts optimizados
            driver.set_page_load_timeout(15)
            driver.set_script_timeout(12)
            
            # Navegación principal
            driver.get("https://servicioswww.anses.gob.ar/ooss2/")
            
            identidad_limpia = str(identidad).replace("-", "").replace("_", "")
            wait = WebDriverWait(driver, 8)
            
            # Ingresar DNI
            input_dni = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_txtDoc")))
            input_dni.clear()
            input_dni.send_keys(identidad_limpia)
            time.sleep(random.uniform(0.1, 0.3))
            
            # Click en botón
            botonAceptar = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_Button1")))
            botonAceptar.click()
            time.sleep(1.0)
            
            # Obtener datos personales
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            cuit = soup.find("span", id="ContentPlaceHolder1_lblCuil")
            nombre = soup.find("span", id="ContentPlaceHolder1_lblNombre")
            dni_element = soup.find("span", id="ContentPlaceHolder1_lblDoc")
            
            if not all([cuit, nombre, dni_element]):
                raise Exception("No se pudieron obtener los datos personales")
            
            cuit_text = cuit.text.strip()
            nombre_text = nombre.text.strip()
            dni_text = dni_element.text.strip()
            
            # Intentar obtener información adicional del PDF
            cuit_empleador, situacion_revista, empresa = obtener_info_pdf(driver, wait)
            
            # Intentar obtener información de negativa (optimizado)
            tabla_negativa = obtener_info_negativa(driver, cuit_text, dni_text)
            
            # Preparar respuesta
            response_data = {
                'success': True,
                'dni': dni_text,
                'cuit': cuit_text,
                'nombre': nombre_text,
                'cuit_empleador': cuit_empleador,
                'situacion_revista': situacion_revista,
                'empresa': empresa,
                'negativa': tabla_negativa
            }
            
            # Cachear por 1 hora
            cache.set(cache_key, response_data, timeout=3600)
            
            return JsonResponse(response_data)
            
        except TimeoutException:
            return JsonResponse({
                'success': False,
                'error': 'Timeout: El servicio de ANSES está respondiendo lentamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error en el scraping: {str(e)}'
            })
        finally:
            try:
                driver.quit()
            except:
                pass
            
    except TimeoutError:
        return JsonResponse({
            'success': False,
            'error': 'Timeout: La consulta tardó demasiado (más de 25 segundos)'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        })
    finally:
        # Desactivar timeout
        signal.alarm(0)

def obtener_info_pdf(driver, wait):
    """Función optimizada para obtener info del PDF"""
    cuit_empleador = situacion_revista = empresa = None
    
    try:
        # Intentar encontrar botón de imprimir
        imprimir_exitoso = False
        try:
            boton_imprimir = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[img[@src='App_Themes/Imagenes/imprimir2.gif']]")))
            boton_imprimir.click()
            imprimir_exitoso = True
        except:
            try:
                boton_imprimir = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(@href, 'imprimir')]")))
                boton_imprimir.click()
                imprimir_exitoso = True
            except:
                imprimir_exitoso = False
        
        if imprimir_exitoso:
            # Esperar descarga reducida
            time.sleep(4)
            
            # Buscar PDF
            download_folder = os.path.join(settings.BASE_DIR, "descargas_anses")
            downloaded_files = os.listdir(download_folder)
            archivos_pdf = [f for f in downloaded_files if f.lower().endswith('.pdf')]
            
            if archivos_pdf:
                ruta_pdf = os.path.join(download_folder, archivos_pdf[0])
                texto_pdf = extraer_texto_pdf(ruta_pdf)
                
                # Extraer información con regex
                cuit_match = re.search(r'CUIT Empleador:\s*(\d{2}-\d{8}-\d{1})', texto_pdf)
                if cuit_match:
                    cuit_empleador = cuit_match.group(1)
                
                situacion_match = re.search(r'Situación de Revista:\s*([^\n]+)', texto_pdf)
                if situacion_match:
                    situacion_revista = situacion_match.group(1).strip()
                
                # Limpiar archivo
                try:
                    os.remove(ruta_pdf)
                except:
                    pass
    
    except Exception as e:
        print(f"Error al obtener info PDF: {e}")
    
    return cuit_empleador, situacion_revista, empresa

def obtener_info_negativa(driver, cuit, dni):
    """Función optimizada para obtener información de negativa"""
    try:
        # Limpiar y preparar CUIT
        cuit_limpio = str(cuit).replace(" ", "").replace("-", "")
        if len(cuit_limpio) >= 13:
            cuit_part1 = cuit_limpio[:2]
            cuit_part2 = dni
            cuit_part3 = cuit_limpio[10:11]
            
            # Navegar a página de negativa
            driver.get("https://servicioswww.anses.gob.ar/censite/index.aspx")
            
            wait = WebDriverWait(driver, 6)
            
            # Rellenar formulario rápido
            input_part1 = wait.until(EC.presence_of_element_located((By.ID, "txtCuitPre")))
            input_part2 = wait.until(EC.presence_of_element_located((By.ID, "txtCuitDoc")))
            input_part3 = wait.until(EC.presence_of_element_located((By.ID, "txtCuitDV")))
            
            input_part1.send_keys(cuit_part1)
            time.sleep(0.1)
            input_part2.send_keys(cuit_part2)
            time.sleep(0.1)
            input_part3.send_keys(cuit_part3)
            time.sleep(0.1)
            
            # Click y espera reducida
            botonAceptar = wait.until(EC.element_to_be_clickable((By.ID, "btnVerificar")))
            botonAceptar.click()
            time.sleep(0.8)
            
            # Obtener tabla
            try:
                tabla_element = wait.until(EC.presence_of_element_located((By.ID, "Grilla")))
                return tabla_element.text.strip()
            except:
                return "No se pudo obtener información de negativa"
        
    except Exception as e:
        print(f"Error en negativa: {e}")
        return f"Error: {str(e)}"
    
    return "Información no disponible"

def extraer_texto_pdf(ruta_pdf):
    """Extraer texto de PDF optimizado"""
    try:
        with open(ruta_pdf, 'rb') as archivo:
            lector_pdf = PyPDF2.PdfReader(archivo)
            texto = ""
            for i, pagina in enumerate(lector_pdf.pages):
                if i < 2:  # Solo 2 páginas máximo
                    texto += pagina.extract_text() + "\n"
                else:
                    break
            return texto
    except Exception as e:
        return f"Error al leer PDF: {str(e)}"

def ping(request):
    return JsonResponse({"status": "ok", "message": "Servicio funcionando"})