import csv
import os
import subprocess
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import msvcrt

# Función para cargar los modelos de voz desde el archivo CSV
def load_voice_models(csv_path):
    voice_models = {}
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            voice_models[row['nickname']] = row['value']
    return voice_models

# Función para convertir audio usando Selenium y Applio
def convert_audio_with_selenium(nickname, audio_file_path, selected_model, output_path):
    # Configurar el Service con la ruta al chromedriver
    driver_path = "C:/chromedriver-win64/chromedriver.exe"
    service = Service(driver_path)

    # Configurar el WebDriver con el Service
    driver = webdriver.Chrome(service=service)

    # Navegar a la Página Web
    driver.get("http://127.0.0.1:6969/")

    try:
        # Esperar hasta que el dropdown esté presente y hacer clic en él para desplegar las opciones
        dropdown_trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[aria-label='Modelo de voz']"))
        )
        dropdown_trigger.click()
        print("Dropdown encontrado y clicado")

        # Esperar hasta que las opciones del dropdown estén visibles
        options_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='listbox']"))
        )
        print("Opciones encontradas")

        # Listar todas las opciones para verificar
        options = options_container.find_elements(By.CSS_SELECTOR, "li")
        if not options:
            print("No se encontraron opciones en el dropdown.")
        for option in options:
            print(f"Opción encontrada: {option.text.strip()}")

        # Seleccionar el modelo de voz específico
        option_to_select = None
        for option in options:
            if selected_model in option.text:
                option_to_select = option
                break

        if option_to_select:
            option_to_select.click()
            print("Opción coincidente encontrada y clicada")
        else:
            print(f"No se encontró la opción '{selected_model}' en el dropdown.")

        # Confirmar que se seleccionó la opción correcta
        selected_value = dropdown_trigger.get_attribute("value")
        print(f"Opción seleccionada: {selected_value}")
        if selected_value != selected_model:
            raise ValueError(f"La opción seleccionada no coincide: {selected_value} != {selected_model}")

        # Esperar unos segundos para confirmar la selección
        time.sleep(2)
        
        # Subir el archivo de voz
        upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        upload_input.send_keys(audio_file_path)
        print(f"Archivo subido: {audio_file_path}")

        # Esperar unos segundos para confirmar la carga
        time.sleep(5)

        # Hacer clic en el botón de convertir
        convert_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "component-45"))
        )
        convert_button.click()
        print("Botón de convertir clicado")

        # Esperar hasta que el botón de descarga aparezca
        print("Esperando a que aparezca el botón de descarga...")
        download_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Download']"))
        )
        download_button.click()
        print("Botón de descarga clicado")

        # Obtener la URL del archivo de descarga
        download_url = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[download]"))
        ).get_attribute("href")
        print(f"URL del archivo de descarga: {download_url}")

        # Descargar el archivo
        output_file_path = os.path.join(output_path, f"{nickname}.wav")
        subprocess.run(["curl", "-o", output_file_path, download_url])
        print(f"Archivo descargado y movido a {output_file_path}")

        # Verificar que el archivo original aún existe
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"El archivo {audio_file_path} no se encontró después de la conversión.")

    finally:
        # Cerrar el navegador
        driver.quit()

    return output_file_path

# Función para listar subcarpetas en un directorio, excluyendo ciertas carpetas
def list_subfolders(directory, exclude=None):
    exclude = exclude or []
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir() and f.name not in exclude]
    return sorted(subfolders)

# Ruta base de los audios
audio_base_path = r"C:\audios"

# Listar subcarpetas en C:\audios excluyendo las carpetas 'selenium' y 'voice removal'
exclude_folders = ['selenium', 'voice removal']
songs = list_subfolders(audio_base_path, exclude_folders)

# Mostrar las opciones de canciones disponibles
print("Canciones disponibles:")
for song in songs:
    print(song)

# Solicitar al usuario que elija una canción
selected_song = input("Elige una canción: ").strip()
if selected_song not in songs:
    raise ValueError(f"Canción '{selected_song}' no encontrada.")

# Directorio para guardar los archivos convertidos
output_path = os.path.join(audio_base_path, selected_song)
if not os.path.exists(output_path):
    os.makedirs(output_path)

# Buscar el archivo de audio a subir (voz.mp3 o voz.wav)
audio_file_path_mp3 = os.path.join(output_path, "voz.mp3")
audio_file_path_wav = os.path.join(output_path, "voz.wav")
if os.path.exists(audio_file_path_mp3):
    audio_file_path = audio_file_path_mp3
elif os.path.exists(audio_file_path_wav):
    audio_file_path = audio_file_path_wav
else:
    raise FileNotFoundError("No se encontró el archivo voz.mp3 o voz.wav en la carpeta seleccionada.")

print(f"Archivo de audio encontrado: {audio_file_path}")

# Cargar los modelos de voz desde voices.csv
voice_models = load_voice_models(os.path.join(audio_base_path, "selenium", "voices.csv"))

# Cargar los datos de winner_log.csv
winner_log_path = r"C:\Users\LENOVO\AppData\LocalLow\DefaultCompany\HowToMakeAVideoGame\winner_log.csv"
if not os.path.exists(winner_log_path):
    raise FileNotFoundError(f"El archivo {winner_log_path} no existe.")
winner_data = pd.read_csv(winner_log_path)

# Detectar los participantes en la carrera
participants = winner_data['Nickname'].unique()

# Generar las pistas completas para cada participante usando Applio si no existen
all_exist = True
for nickname in participants:
    nickname_lower = nickname.lower()
    player_audio_path_mp3 = os.path.join(output_path, f"{nickname_lower}.mp3")
    player_audio_path_wav = os.path.join(output_path, f"{nickname_lower}.wav")
    if nickname_lower in voice_models:
        if not os.path.exists(player_audio_path_mp3) and not os.path.exists(player_audio_path_wav):
            print(f"Generando audio para {nickname}...")
            convert_audio_with_selenium(nickname_lower, audio_file_path, voice_models[nickname_lower], output_path)
            all_exist = False
        else:
            print(f"El archivo para {nickname} ya existe. Omite la generación.")

if all_exist:
    print("Todas las pistas de audio ya existen. No se generó ninguna nueva pista.")

print("Proceso completado.")
print("Press any key to close this window...")
msvcrt.getch()
