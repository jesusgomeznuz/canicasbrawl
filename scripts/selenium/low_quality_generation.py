import csv
import os
import subprocess
import time
import pandas as pd
import sys
from glob import glob
from pydub import AudioSegment
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def load_voice_models(csv_path):
    voice_models = {}
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            voice_models[row['nickname']] = row['value']
    return voice_models

def list_subfolders(directory, exclude=None):
    exclude = exclude or []
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir() and f.name not in exclude]
    return sorted(subfolders)

def find_earliest_run_with_video(directory):
    subfolders = [f.path for f in os.scandir(directory) if f.is_dir()]
    for subfolder in sorted(subfolders, key=lambda x: int(os.path.basename(x))):
        mp4_files = glob(os.path.join(subfolder, "*.mp4"))
        if mp4_files:
            return subfolder, mp4_files[0]
    raise FileNotFoundError("No se encontraron subcarpetas con archivos .mp4")

def convert_audio_with_selenium(nickname, audio_file_path, selected_model, output_path):
    driver_path = "C:/chromedriver-win64/chromedriver.exe"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service)
    driver.get("http://127.0.0.1:6969/")

    try:
        dropdown_trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[aria-label='Modelo de voz']"))
        )
        dropdown_trigger.click()
        print("Dropdown encontrado y clicado")

        options_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='listbox']"))
        )
        print("Opciones encontradas")

        options = options_container.find_elements(By.CSS_SELECTOR, "li")
        for option in options:
            print(f"Opción encontrada: {option.text.strip()}")

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

        selected_value = dropdown_trigger.get_attribute("value")
        print(f"Opción seleccionada: {selected_value}")
        if selected_value != selected_model:
            raise ValueError(f"La opción seleccionada no coincide: {selected_value} != {selected_model}")

        time.sleep(2)
        upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        upload_input.send_keys(audio_file_path)
        print(f"Archivo subido: {audio_file_path}")

        time.sleep(5)
        convert_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "component-45"))
        )
        convert_button.click()
        print("Botón de convertir clicado")

        print("Esperando a que aparezca el botón de descarga...")
        download_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Download']"))
        )
        download_button.click()
        print("Botón de descarga clicado")

        download_url = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[download]"))
        ).get_attribute("href")
        print(f"URL del archivo de descarga: {download_url}")

        output_file_path = os.path.join(output_path, f"{nickname}.wav")
        subprocess.run(["curl", "-o", output_file_path, download_url])
        print(f"Archivo descargado y movido a {output_file_path}")

        if not os.path.exists(output_file_path):
            raise FileNotFoundError(f"El archivo {output_file_path} no se encontró después de la conversión.")
    finally:
        driver.quit()

    return output_file_path

def check_all_files_present(participants, output_path):
    missing_files = []
    for nickname in participants:
        nickname_lower = nickname.lower()
        wav_path = os.path.join(output_path, f"{nickname_lower}.wav")
        mp3_path = os.path.join(output_path, f"{nickname_lower}.mp3")
        if not os.path.exists(wav_path) and not os.path.exists(mp3_path):
            missing_files.append(nickname_lower)
    return missing_files

# Main logic
if len(sys.argv) != 2:
    print("Uso: python low_quality_generation.py <nombre_de_la_canción>")
    sys.exit(1)

selected_song = sys.argv[1]

audio_base_path = r"C:\audios"
output_path = os.path.join(audio_base_path, selected_song)

audio_file_path_mp3 = os.path.join(output_path, "voz.mp3")
audio_file_path_wav = os.path.join(output_path, "voz.wav")
if os.path.exists(audio_file_path_mp3):
    audio_file_path = audio_file_path_mp3
elif os.path.exists(audio_file_path_wav):
    audio_file_path = audio_file_path_wav
else:
    raise FileNotFoundError("No se encontró el archivo voz.mp3 o voz.wav en la carpeta seleccionada.")

print(f"Archivo de audio encontrado: {audio_file_path}")

# Load voice models
voice_models = load_voice_models(os.path.join(audio_base_path, "selenium", "voices.csv"))

# Path to the runs directory
runs_directory = r"C:\Users\LENOVO\Documents\canicasbrawl\Runs"

# Find the earliest run with an available .mp4 video
run_folder, video_path = find_earliest_run_with_video(runs_directory)

# Path to the WinnerTracker CSV file in the run folder
winner_log_path = os.path.join(run_folder, "winner_log.csv")
winner_csv_path = os.path.join(run_folder, "winner.csv")

# Check if the winner_log.csv file exists
if not os.path.exists(winner_log_path):
    raise FileNotFoundError(f"El archivo {winner_log_path} no existe.")
if not os.path.exists(winner_csv_path):
    raise FileNotFoundError(f"El archivo {winner_csv_path} no existe.")
print(f"Archivos encontrados en el run folder {run_folder}: {video_path}, {winner_log_path}, {winner_csv_path}")

# Load WinnerTracker data
winner_data = pd.read_csv(winner_log_path)
winner = pd.read_csv(winner_csv_path).iloc[0, 0]

# Calculate total time and segments for each player
winner_data['Time_ms'] = winner_data['Time'].apply(lambda x: int(x.split(':')[0]) * 60 * 60 * 1000 + int(x.split(':')[1]) * 60 * 1000 + int(x.split(':')[2]) * 1000 + int(x.split(':')[3]))
winner_data['NextTime_ms'] = winner_data['Time_ms'].shift(-1).fillna(winner_data['Time_ms'].max() + 10000).astype(int)
winner_data['LeadTime_ms'] = winner_data['NextTime_ms'] - winner_data['Time_ms']

total_times = winner_data.groupby('Nickname')['LeadTime_ms'].sum() / 1000
segments = winner_data['Nickname'].value_counts()

# Add the extra 10 seconds for the winner
if winner in total_times:
    total_times[winner] += 10

# Print results
print("Nickname,TotalTime,segments")
for nickname in total_times.index:
    print(f"{nickname},{total_times[nickname]:.3f},{segments[nickname]}")

# Recommend voices to generate manually with better quality
recommended_nicknames = [nickname for nickname, total_time in total_times.items() if total_time > 5]
print("\nRecomendación de voces a generar manualmente con mejor calidad (huggingface):")
for nickname in recommended_nicknames:
    print(nickname)

# Process voices with lower quality
low_quality_nicknames = [nickname for nickname in total_times.index if total_times[nickname] <= 5]

for nickname in low_quality_nicknames:
    nickname_lower = nickname.lower()
    low_quality_file_path = os.path.join(output_path, f"{nickname_lower}.wav")
    if not os.path.exists(low_quality_file_path):
        convert_audio_with_selenium(nickname_lower, audio_file_path, voice_models[nickname_lower], output_path)
    else:
        print(f"El archivo de baja calidad para {nickname} ya existe. Omitiendo generación.")

# Check if all files are present
missing_files = check_all_files_present(total_times.index, output_path)

if missing_files:
    while True:
        print(f"Aún faltan archivos. Por favor, completa la generación de audios manuales. Faltan los siguientes archivos: {', '.join(missing_files)}")
        user_input = input("¿Ya terminaste de generar los audios manualmente? (Y/N): ").strip().lower()
        if user_input == 'y':
            missing_files = check_all_files_present(total_times.index, output_path)
            if not missing_files:
                print("Todos los archivos necesarios están presentes. Proceso completado.")
                break
        elif user_input == 'n':
            print("Por favor, completa la generación de audios manuales y vuelve a ejecutar el script.")
            break
        else:
            print("Entrada no válida. Por favor, responde con 'Y' o 'N'.")
else:
    print("Todos los archivos necesarios están presentes. Proceso completado.")
