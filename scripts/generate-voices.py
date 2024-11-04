import os
import csv
import time
import pandas as pd
from glob import glob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pydub import AudioSegment
from pywinauto.application import Application
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

log_canciones_path = r"C:\Users\LENOVO\Documents\canicasbrawl\scripts\log_canciones.csv"
runs_directory = r"D:\canicasbrawl\Runs"
voice_URLS = r"D:\canicasbrawl\scripts\jammable.csv"
raw_production_folder = r"D:\canicasbrawl\raw production"
winner_log_path = r"C:\Users\LENOVO\Documents\canicasbrawl\scripts\winner_log.csv"
download_dir = "C:/Users/LENOVO/Downloads/"

def verificar_y_crear_lock(run_folder):
    """
    Verifica si existe un archivo de bloqueo en la carpeta 'run_folder'.
    Si no existe, lo crea y devuelve True (indicando que se puede trabajar en esta carpeta).
    Si existe, devuelve False (indicando que ya está en uso).
    """
    lock_file_path = os.path.join(run_folder, "lock_file.txt")
    
    if os.path.exists(lock_file_path):
        # Si el archivo de bloqueo existe, significa que otro proceso está trabajando en esta carpeta.
        return False
    else:
        # Si no existe, crea el archivo de bloqueo para indicar que se está trabajando en esta carpeta.
        with open(lock_file_path, 'w') as lock_file:
            lock_file.write("Esta carpeta está siendo procesada.")
        return True

def verificar_archivos_y_lock(cancion, personajes_list):
    """
    Verifica si todos los archivos necesarios están presentes y si existe un lock file en la carpeta de la canción.
    Si no hay lock file y faltan archivos, se puede proceder.
    """
    folder_path = f"D:/canicasbrawl/canciones/{cancion}/"
    lock_file_path = os.path.join(folder_path, "lock_file.txt")
    
    if os.path.exists(lock_file_path):
        log_with_time(f"La carpeta para {cancion} ya está en uso por otro proceso. Saltando.")
        return False

    # Verificar si todos los archivos de los personajes están presentes
    all_files_present = True
    for personaje in personajes_list:
        wav_path = os.path.join(folder_path, f"{personaje}.wav")
        mp3_path = os.path.join(folder_path, f"{personaje}.mp3")
        if not os.path.exists(wav_path) and not os.path.exists(mp3_path):
            all_files_present = False
            break

    if all_files_present:
        log_with_time(f"Todos los archivos necesarios para {cancion} están presentes.")
        return False
    else:
        # Crear el lock file ya que esta carpeta puede ser procesada
        with open(lock_file_path, 'w') as lock_file:
            lock_file.write("Esta carpeta está siendo procesada.")
        return True


def cancion_ya_producida(song_name, raw_production_folder):
    # Revisa si existen archivos relacionados con la canción en la carpeta 'raw production'
    production_path = os.path.join(raw_production_folder, song_name)
    # Verifica si existe la carpeta o si contiene archivos, puedes adaptar esta verificación según el formato que uses.
    return os.path.exists(production_path) and len(os.listdir(production_path)) > 0

def log_with_time(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def contar_canciones(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return sum(1 for row in reader)

def listar_runs_disponibles(runs_directory):
    return sum(1 for subdir in os.scandir(runs_directory) if subdir.is_dir() and glob(os.path.join(subdir.path, "*.mp4")))

def find_earliest_run_with_video(directory, used_runs):
    subfolders = [f.path for f in os.scandir(directory) if f.is_dir()]
    for subfolder in sorted(subfolders, key=lambda x: int(os.path.basename(x))):
        run_number = int(os.path.basename(subfolder))
        if run_number not in used_runs:
            mp4_files = glob(os.path.join(subfolder, "*.mp4"))
            if mp4_files:
                return subfolder, mp4_files[0], run_number
    raise FileNotFoundError("No se encontraron subcarpetas con archivos .mp4")

def obtener_canciones_y_personajes(csv_path, runs_directory, used_runs):
    canciones_personajes = []

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre_cancion = row['nombre']

            # Verificar si la canción ya está producida en la carpeta 'raw production'
            if cancion_ya_producida(nombre_cancion, raw_production_folder):
                log_with_time(f"La canción '{nombre_cancion}' ya ha sido producida. Saltando.")
                continue

            # Proceder con la búsqueda de run y asignación de personajes
            run_folder, _, run_number = find_earliest_run_with_video(runs_directory, used_runs)
            used_runs.add(run_number)

            personajes = []
            winner_log_path = os.path.join(run_folder, "winner_log.csv")
            if os.path.exists(winner_log_path):
                with open(winner_log_path, newline='', encoding='utf-8') as winner_csv:
                    winner_reader = csv.DictReader(winner_csv)
                    for winner_row in winner_reader:
                        personajes.append(winner_row['Nickname'])

            if personajes:
                personajes = list(set(personajes))
            else:
                personajes = ['N/A']

            personajes = ','.join(sorted([p.lower() for p in personajes]))
            canciones_personajes.append((nombre_cancion, personajes))

    return canciones_personajes


def convert_audio_with_selenium(links_nicknames, song_name):
    service = Service('C:/chromedriver-win64/chromedriver.exe')
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get("https://www.jammable.com/login")
        time.sleep(1)

        email_field = driver.find_element(By.NAME, "email")
        email_field.send_keys("info@canicasbrawl.com")
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys("oi5D9oX4:")
        password_field.send_keys(Keys.RETURN)
        time.sleep(1)

        for link, nickname, filename in links_nicknames:
            if check_existing_conversion(driver, filename):
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - La conversión de {nickname} ya existe.")
            else:
                driver.get(link)
                time.sleep(1)

                conversion_button = driver.find_element(By.XPATH, "//div[contains(@class,'tw-text-lg') and contains(text(),'Create Cover')]")
                conversion_button.click()

                # Directly interact with the file input element
                path = f"D:\\canicasbrawl\\canciones\\{song_name}\\voz.mp3"
                if not os.path.exists(path):
                    print(f"El archivo {path} no existe.")
                    continue  # Skip to the next iteration if the file doesn't exist

                # Wait for the file input element to be present
                try:
                    file_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                    )
                    file_input.send_keys(path)
                except TimeoutException:
                    print(f"No se pudo encontrar el elemento de carga de archivo para {nickname}.")
                    continue

                # Wait for the "Next Step" button to be clickable
                try:
                    next_step_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Next Step')]"))
                    )
                    next_step_button.click()
                except TimeoutException:
                    print(f"Next Step button not found after uploading file for {nickname}")
                    continue

                # Wait for the name field to be present
                try:
                    name_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Rename (optional)...']"))
                    )
                    name_field.clear()
                    name_field.send_keys(filename)
                except TimeoutException:
                    print(f"Name field not found for {nickname}")
                    continue

                # Wait for the "Convert!" button to be clickable
                try:
                    convert_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Convert')]"))
                    )
                    convert_button.click()
                except TimeoutException:
                    print(f"Convert button not found after filling the name for {nickname}")
                    # Save page source for debugging
                    with open(f'convert_error_{nickname}.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    continue

                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Conversión iniciada para {nickname}")
                
        # Después del for loop que maneja las conversiones
        driver.get("https://www.jammable.com/history")
        time.sleep(1)

        while "PENDING" in driver.page_source.upper() or "CONVERTING" in driver.page_source.upper() or "EXTRACTING" in driver.page_source.upper():
            print("Faltan conversiones por finalizar.")
            time.sleep(10)  # Esperar 10 segundos antes de refrescar
            driver.refresh()
        
        print("Todas las conversiones han finalizado.")
        time.sleep(5)

        for link, nickname, filename in links_nicknames:
            output_path = os.path.join(f"D:/canicasbrawl/canciones/{song_name}/", f"{sanitize_string(nickname)}.wav")

            # Verificar si el archivo ya existe
            if os.path.exists(output_path):
                print(f"El archivo de {nickname} ya existe en la carpeta de destino. Se omite la descarga.")
                continue

            try:
                # Buscar el enlace de la conversión finalizada utilizando una espera explícita
                conversion_link_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//a[contains(@class, 'Conversion_history-item-container') and contains(., '{filename}')]"))
                )
                conversion_link = conversion_link_element.get_attribute("href")
                driver.get(conversion_link)
                print(f"Abriendo el enlace de la conversión finalizada: {conversion_link}")
                time.sleep(1)  # Espera un par de segundos para asegurarse de que la página cargue completamente
            except TimeoutException:
                print(f"No se pudo abrir el enlace de '{filename}': Enlace no encontrado después de esperar.")
                continue
            except NoSuchElementException:
                print(f"No se pudo abrir el enlace de '{filename}': Elemento no encontrado en el DOM.")
                continue
    
            try:
                # Hacer clic en el botón de "Download" para desplegar la lista
                download_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'tw-inline-flex') and contains(text(), 'Download')]"))
                )
                download_button.click()
                time.sleep(1)  # Esperar un momento para que la lista se despliegue

                # Hacer clic en "Download Combined"
                download_combined_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Download Combined')]"))
                )
                download_combined_button.click()
                print(f"Se ha hecho clic en 'Download Combined' para {nickname}.")
                time.sleep(2)
            except TimeoutException:
                print(f"No se pudo hacer clic en 'Download Combined' para {nickname}: Tiempo de espera agotado.")
                continue
            except NoSuchElementException:
                print(f"No se pudo hacer clic en 'Download Combined' para {nickname}: Elemento no encontrado en el DOM.")
                continue

            # Buscar el archivo .mp3 descargado que contenga una palabra del `nickname`
            for file in os.listdir(download_dir):
                if file.endswith(".mp3") and (nickname.split()[0].lower() in file.lower() or (len(nickname.split()) > 1 and nickname.split()[1].lower() in file.lower())):
                    downloaded_file = os.path.join(download_dir, file)
                    break
            else:
                print(f"No se encontró el archivo descargado para {nickname}.")
                downloaded_file = None

            # Convertir el archivo .mp3 a .wav y moverlo a la carpeta de destino
            if downloaded_file:
                try:
                    audio = AudioSegment.from_mp3(downloaded_file)
                    audio.export(output_path, format="wav")
                    os.remove(downloaded_file)
                    print(f"El archivo de {nickname} se ha convertido y movido a: {output_path}")
                except Exception as e:
                    print(f"Error al convertir o mover el archivo de {nickname}: {e}")
    
            driver.get("https://www.jammable.com/history")
            time.sleep(1)  # Espera a que la página se cargue completamente

    finally:
        driver.quit()


def sanitize_string(s):
    """Convierte una cadena a minúsculas y reemplaza espacios con guiones."""
    return s.lower().replace(" ", "")

def check_existing_conversion(driver, filename):
    """Verifica si una conversión con el nombre del archivo ya existe en Jammable."""
    driver.get("https://www.jammable.com/history")
    time.sleep(1)
    try:
        # Busca en la página de historial si el archivo ya fue convertido
        driver.find_element(By.XPATH, f"//div[contains(text(),'{filename}')]")
        return True
    except:
        return False

# Paso 1: Contar el número de canciones en la cola
num_canciones = contar_canciones(log_canciones_path)
log_with_time(f"Hay {num_canciones} canciones en la cola")

# Paso 2: Listar el número de runs disponibles
num_runs_disponibles = listar_runs_disponibles(runs_directory)
log_with_time(f"Hay {num_runs_disponibles} runs disponibles para producción")

# Paso 3: Verificar si hay suficientes runs disponibles
if num_runs_disponibles < num_canciones:
    log_with_time("No hay suficientes runs para producir todas las canciones.")
else:
    # Inicializar used_runs
    used_runs = set()

    # Paso 4: Obtener canciones y personajes
    canciones_personajes = obtener_canciones_y_personajes(log_canciones_path, runs_directory, used_runs)

    # Después de imprimir las canciones y personajes antes de la producción
    for cancion, personajes in canciones_personajes:
        print(f"Canción a producir: {cancion}")
        print(f"Personajes: {personajes}")
        print()  # Línea en blanco para separar cada bloque de salida

        personajes_list = personajes.split(',')

        # Verificar si existe un archivo de bloqueo y si todos los archivos ya están presentes
        folder_path = f"D:/canicasbrawl/canciones/{cancion}/"
        lock_file_path = os.path.join(folder_path, "lock_file.txt")

        if os.path.exists(lock_file_path):
            log_with_time(f"La carpeta para {cancion} ya está en uso por otro proceso. Saltando.")
            continue  # Saltar a la siguiente canción si ya hay un archivo de bloqueo

        all_files_present = True
        for personaje in personajes_list:
            wav_path = os.path.join(folder_path, f"{personaje}.wav")
            mp3_path = os.path.join(folder_path, f"{personaje}.mp3")
            if not os.path.exists(wav_path) and not os.path.exists(mp3_path):
                all_files_present = False
                break

        if all_files_present:
            log_with_time(f"Todos los archivos necesarios para {cancion} están presentes.")
        else:
            # Crear el archivo de bloqueo ya que esta carpeta puede ser procesada
            with open(lock_file_path, 'w') as lock_file:
                lock_file.write("Esta carpeta está siendo procesada.")
            
            log_with_time(f"Comenzando la conversión para {cancion}...")

            # Leer los nombres y URLs de jammable.csv
            df = pd.read_csv(voice_URLS)
            selected_characters = df[df['nickname'].isin(personajes_list)]
            links_nicknames = [(row['URL'], row['nickname'], sanitize_string(f"{cancion}-{row['nickname']}")) for _, row in selected_characters.iterrows()]
        
            # Realizar la conversión
            convert_audio_with_selenium(links_nicknames, cancion)
            log_with_time(f"Conversión finalizada para {cancion}")

            # Eliminar el archivo de bloqueo después de la conversión
            if os.path.exists(lock_file_path):
                os.remove(lock_file_path)
                log_with_time(f"Archivo de bloqueo eliminado para {cancion}.")
