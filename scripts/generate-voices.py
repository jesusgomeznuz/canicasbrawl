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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

log_canciones_path = r"C:\Users\LENOVO\Documents\canicasbrawl\scripts\log_canciones.csv"
runs_directory = r"D:\canicasbrawl\Runs"
voice_URLS = r"D:\canicasbrawl\scripts\jammable.csv"
raw_production_folder = r"D:\canicasbrawl\raw production"
download_dir = "C:/Users/LENOVO/Downloads/"
email = os.environ.get('JAMMABLE_EMAIL')
password = os.environ.get('JAMMABLE_PASSWORD')

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

def sanitize_string(s):
    """Convierte una cadena a minúsculas y elimina espacios."""
    return s.lower().replace(" ", "")

def obtener_canciones_y_personajes(csv_path, runs_directory, used_runs):
    canciones_personajes = []

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre_cancion = row['nombre']

            # Proceder con la búsqueda de run y asignación de personajes
            try:
                run_folder, _, run_number = find_earliest_run_with_video(runs_directory, used_runs)
            except FileNotFoundError:
                log_with_time("No se encontraron más runs disponibles.")
                break

            # Calcular new_video_name y new_video_path como en generate-videos.py
            video_number = run_number + 25
            new_video_name = f"Video{video_number} - Run {run_number} - {nombre_cancion}.mp4"
            new_video_path = os.path.join(raw_production_folder, new_video_name)

            # Verificar si el video ya existe en raw production
            if os.path.exists(new_video_path):
                log_with_time(f"El video '{new_video_name}' ya se encuentra en raw production.")
                used_runs.add(run_number)  # Asegurarse de no reutilizar el run
                continue

            used_runs.add(run_number)

            # Proceder con el resto del código
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
    chrome_options.add_argument("--headless")  # Ejecuta en modo headless
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get("https://www.jammable.com/login")
        time.sleep(1)

        email_field = driver.find_element(By.NAME, "email")
        email_field.send_keys(email)
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
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

                # Interactuar directamente con el elemento de entrada de archivo
                path = f"D:\\canicasbrawl\\canciones\\{song_name}\\voz.mp3"
                if not os.path.exists(path):
                    print(f"El archivo {path} no existe.")
                    continue  # Saltar a la siguiente iteración si el archivo no existe

                # Esperar a que el elemento de entrada de archivo esté presente
                try:
                    file_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                    )
                    file_input.send_keys(path)
                except TimeoutException:
                    print(f"No se pudo encontrar el elemento de carga de archivo para {nickname}.")
                    continue

                # Esperar a que el botón "Next Step" sea clicable
                try:
                    next_step_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Next Step')]"))
                    )
                    next_step_button.click()
                except TimeoutException:
                    print(f"Next Step button not found after uploading file for {nickname}")
                    continue

                # Esperar a que el campo de nombre esté presente
                try:
                    name_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Rename (optional)...']"))
                    )
                    name_field.clear()
                    name_field.send_keys(filename)
                except TimeoutException:
                    print(f"Name field not found for {nickname}")
                    continue

                # Esperar a que el botón "Convert!" sea clicable
                try:
                    convert_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Convert')]"))
                    )
                    convert_button.click()
                except TimeoutException:
                    print(f"Convert button not found after filling the name for {nickname}")
                    # Guardar el código fuente de la página para depuración
                    with open(f'convert_error_{nickname}.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    continue

                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Conversión iniciada para {nickname}")
                
        # Después del bucle que maneja las conversiones
        driver.get("https://www.jammable.com/history")
        time.sleep(1)

        while "PENDING" in driver.page_source.upper() or "CONVERTING" in driver.page_source.upper() or "EXTRACTING" in driver.page_source.upper() or "MIXING" in driver.page_source.upper():
            print("Faltan conversiones por finalizar.")
            time.sleep(15)  # Esperar 15 segundos antes de refrescar
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
                # Buscar el enlace de la conversión finalizada
                conversion_link_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//a[contains(@class, 'Conversion_history-item-container') and contains(., '{filename}')]"))
                )
                conversion_link = conversion_link_element.get_attribute("href")
                driver.get(conversion_link)
                print(f"Abriendo el enlace de la conversión finalizada: {conversion_link}")
                time.sleep(1)
            except TimeoutException:
                print(f"No se pudo abrir el enlace de '{filename}': Enlace no encontrado después de esperar.")
                continue
            except NoSuchElementException:
                print(f"No se pudo abrir el enlace de '{filename}': Elemento no encontrado en el DOM.")
                continue
    
            try:
                # Hacer clic en el botón de "Download" para desplegar la lista
                download_button = WebDriverWait(driver, 120).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'tw-inline-flex') and contains(text(), 'Download')]"))
                )
                download_button.click()
                time.sleep(1)

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

            # Esperar brevemente para permitir que la descarga inicie
            time.sleep(2)

            # Buscar el archivo descargado en la carpeta de descargas
            downloaded_file = None
            files_in_download = [f for f in os.listdir(download_dir) if f.endswith(".mp3")]
            if not files_in_download:
                print(f"No se encontró ningún archivo .mp3 en la carpeta de descargas para {nickname}.")
                continue

            # Identificar el archivo más reciente
            downloaded_file = max(
                [os.path.join(download_dir, f) for f in files_in_download],
                key=os.path.getctime
            )

            # Renombrar el archivo descargado al formato "[nickname] - [song_name].mp3"
            new_filename = f"{nickname} - {song_name}.mp3"
            new_file_path = os.path.join(download_dir, new_filename)
            try:
                os.rename(downloaded_file, new_file_path)
                print(f"Archivo descargado renombrado a: {new_filename}")
            except Exception as e:
                print(f"Error al renombrar el archivo de {nickname}: {e}")
                continue

            # Convertir el archivo .mp3 a .wav y moverlo a la carpeta de destino
            try:
                audio = AudioSegment.from_mp3(new_file_path)
                audio.export(output_path, format="wav")
                os.remove(new_file_path)
                print(f"El archivo de {nickname} se ha convertido y movido a: {output_path}")
            except Exception as e:
                print(f"Error al convertir o mover el archivo de {nickname}: {e}")
                continue

            driver.get("https://www.jammable.com/history")
            time.sleep(1)
    finally:
        driver.quit()

def check_existing_conversion(driver, filename):
    """Verifica si una conversión con el nombre del archivo ya existe en Jammable."""
    driver.get("https://www.jammable.com/history")
    time.sleep(1)
    try:
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

    # Procesar cada canción y sus personajes
    for cancion, personajes in canciones_personajes:
        print(f"Canción a producir: {cancion}")
        print(f"Personajes: {personajes}")
        print()

        personajes_list = personajes.split(',')

        # Verificar archivos existentes y crear lista de faltantes
        folder_path = f"D:/canicasbrawl/canciones/{cancion}/"
        missing_personajes = []

        for personaje in personajes_list:
            mp3_path = os.path.join(folder_path, f"{personaje}.mp3")
            wav_path = os.path.join(folder_path, f"{personaje}.wav")
            if os.path.exists(mp3_path):
                log_with_time(f"El archivo {mp3_path} ya existe.")
            elif os.path.exists(wav_path):
                log_with_time(f"El archivo {wav_path} ya existe.")
            else:
                log_with_time(f"El archivo para {personaje} no existe y será convertido.")
                missing_personajes.append(personaje)

        if not missing_personajes:
            log_with_time(f"Todos los archivos necesarios para {cancion} están presentes.")
        else:
            log_with_time(f"Comenzando la conversión para {cancion} para los personajes faltantes...")
            # Proceder con la conversión

            # Leer los nombres y URLs de jammable.csv
            df = pd.read_csv(voice_URLS)
            selected_characters = df[df['nickname'].isin(missing_personajes)]
            links_nicknames = [
                (row['URL'], row['nickname'], sanitize_string(f"{cancion}-{row['nickname']}"))
                for _, row in selected_characters.iterrows()
            ]

            # Realizar la conversión
            convert_audio_with_selenium(links_nicknames, cancion)
            log_with_time(f"Conversión finalizada para {cancion}")
