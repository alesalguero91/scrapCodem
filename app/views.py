# views.py
import json
import os
import time
import random
import re
import PyPDF2
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@csrf_exempt
@require_POST
def consultar_anses(request):
    try:
        # Obtener datos del request
        data = json.loads(request.body)
        identidad = data.get('dni')
        
        if not identidad:
            return JsonResponse({
                'success': False,
                'error': 'DNI no proporcionado'
            })
        
        # Configurar la carpeta de descarga
        download_folder = os.path.join(settings.BASE_DIR, "descargas_anses")
        
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        # Configurar opciones de Chrome
        options = uc.ChromeOptions()
        prefs = {
            "download.default_directory": download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)
        
   
        driver = uc.Chrome(options=options)
        
        try:
    
            driver.get("https://servicioswww.anses.gob.ar/ooss2/")
            
         
            identidad_limpia = str(identidad).replace("-", "").replace("_", "")
            wait = WebDriverWait(driver, 15)
            
        
            input_dni = wait.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_txtDoc")))
            input_dni.send_keys(identidad_limpia)
            time.sleep(random.uniform(0.1, 0.6))
            
      
            botonAceptar = wait.until(EC.element_to_be_clickable((By.ID, "ContentPlaceHolder1_Button1")))
            botonAceptar.click()
            time.sleep(2)
            
         
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            cuit = soup.find("span", id="ContentPlaceHolder1_lblCuil")
            nombre = soup.find("span", id="ContentPlaceHolder1_lblNombre")
            dni_element = soup.find("span", id="ContentPlaceHolder1_lblDoc")
            
            if not all([cuit, nombre, dni_element]):
                raise Exception("No se pudieron obtener los datos personales")
            
            cuit = cuit.text
            nombre = nombre.text
            dni = dni_element.text
            
        
            cuit_empleador = None
            situacion_revista = None
            empresa = None
            
           
            imprimir_exitoso = False
            try:
                boton_imprimir = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//a[img[@src='App_Themes/Imagenes/imprimir2.gif']]")))
                boton_imprimir.click()
                imprimir_exitoso = True
            except Exception as e:
                try:
                    boton_imprimir = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//a[contains(@href, 'imprimir')]")))
                    boton_imprimir.click()
                    imprimir_exitoso = True
                except Exception:
                    imprimir_exitoso = False
            
            if imprimir_exitoso:
                # Esperar descarga
                time.sleep(8)
                
              
                downloaded_files = os.listdir(download_folder)
                archivos_pdf = [f for f in downloaded_files if f.lower().endswith('.pdf')]
                
                if archivos_pdf:
                    ruta_pdf = os.path.join(download_folder, archivos_pdf[0])
                    
                   
                    texto_pdf = extraer_texto_pdf(ruta_pdf)
                    
                    
                    cuit_pattern = r'CUIT Empleador:\s*(\d{2}-\d{8}-\d{1})'
                    cuit_match = re.search(cuit_pattern, texto_pdf)
                    if cuit_match:
                        cuit_empleador = cuit_match.group(1)
                    
                   
                    situacion_pattern = r'Situación de Revista:\s*([^\n]+)'
                    situacion_match = re.search(situacion_pattern, texto_pdf)
                    if situacion_match:
                        situacion_revista = situacion_match.group(1).strip()
                    
                    
                    if cuit_empleador:
                        try:
                            driver.get(f"https://www.cuitonline.com/search/{cuit_empleador}")
                            time.sleep(2)
                            soup_empresa = BeautifulSoup(driver.page_source, "html.parser")
                            nombre_empresa = soup_empresa.find("div", class_="denominacion")
                            if nombre_empresa:
                                empresa = nombre_empresa.text.strip()
                        except Exception as e:
                            print(f"Error al obtener información de la empresa: {e}")
                    
                    try:
                        os.remove(ruta_pdf)
                    except:
                        pass
            

            try:
                vale = cuit
                vale = str(vale).replace(" ", "")
                vale = str(vale).replace("-","")
                cuit_part1 = vale[:2]    
                cuit_part2 = dni   
                cuit_part3 = vale[10:]   
                driver.get("https://servicioswww.anses.gob.ar/censite/index.aspx")
 
                soup = BeautifulSoup(driver.page_source, "html.parser")
                wait = WebDriverWait(driver, 10)
                input_part1 = wait.until(EC.presence_of_element_located((By.ID, "txtCuitPre")))

                input_part2 = wait.until(EC.presence_of_element_located((By.ID, "txtCuitDoc")))

                input_part3 = wait.until(EC.presence_of_element_located((By.ID, "txtCuitDV")))

                time.sleep(random.uniform(0.1, 0.6))


                input_part1.send_keys(cuit_part1)
                time.sleep(random.uniform(0.1, 0.6))
                input_part1.send_keys(cuit_part2)
                time.sleep(random.uniform(0.1, 0.6))
                input_part3.send_keys(cuit_part3)
                time.sleep(random.uniform(0.1, 0.6))

                botonAceptar = wait.until(EC.element_to_be_clickable((By.ID, "btnVerificar")))
                time.sleep(random.uniform(0.1, 0.6))
                botonAceptar.click()



                time.sleep(random.uniform(1.0, 2.0))  
                new_soup = BeautifulSoup(driver.page_source, "html.parser")

                tabla = wait.until(EC.presence_of_element_located((By.ID, "Grilla"))).text
                tabla = tabla.replace("Si desea obtener el CODEM (Constancia de Empadronamiento a la Obra Social) PRESIONE AQUÍ", "")
                print(tabla)


            except:
                print("FAllo")    
           
            response_data = {
                'success': True,
                'dni': dni,
                'cuit': cuit,
                'nombre': nombre,
                'cuit_empleador': cuit_empleador,
                'situacion_revista': situacion_revista,
                'empresa': empresa,
                'negativa': tabla

            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
            
        finally:
            driver.quit()
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        })

def extraer_texto_pdf(ruta_pdf):
    try:
        with open(ruta_pdf, 'rb') as archivo:
            lector_pdf = PyPDF2.PdfReader(archivo)
            texto = ""
            for pagina in lector_pdf.pages:
                texto += pagina.extract_text() + "\n"
            return texto
    except Exception as e:
        return f"Error al leer el PDF: {str(e)}"
    

@csrf_exempt
def ping(request):
    mensaje= {
        "dato":"allready"
    }
    JsonResponse( mensaje)