import csv
import os
import shutil
import subprocess
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from glob import glob
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip

def log_with_time(message):
    """
    Prints a message with the current timestamp.
    """
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def load_voice_models(csv_path):
    """
    Loads voice models from a CSV file and returns a dictionary mapping nicknames to model values.
    """
    voice_models = {}
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            voice_models[row['nickname']] = row['value']
    return voice_models

def convert_audio_with_selenium(nickname, audio_file_path, selected_model, output_path):
    """
    Uses Selenium to automate audio conversion by interacting with a local web application.
    Uploads the audio file, selects the voice model, initiates the conversion, and downloads the converted file.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    driver_path = "C:/chromedriver-win64/chromedriver.exe"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("http://127.0.0.1:6969/")

    try:
        dropdown_trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[aria-label='Modelo de voz']"))
        )
        dropdown_trigger.click()

        options_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='listbox']"))
        )

        options = options_container.find_elements(By.CSS_SELECTOR, "li")

        option_to_select = None
        for option in options:
            if selected_model in option.text:
                option_to_select = option
                break

        if option_to_select:
            option_to_select.click()
        else:
            log_with_time(f"Option '{selected_model}' not found in the dropdown.")

        selected_value = dropdown_trigger.get_attribute("value")
        if selected_value != selected_model:
            raise ValueError(f"Selected option does not match: {selected_value} != {selected_model}")

        time.sleep(2)
        upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        upload_input.send_keys(audio_file_path)

        time.sleep(5)
        convert_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "component-45"))
        )
        convert_button.click()

        download_button = WebDriverWait(driver, 300).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Download']"))
        )
        download_button.click()

        download_url = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[download]"))
        ).get_attribute("href")

        output_file_path = os.path.join(output_path, f"{nickname}.wav")
        subprocess.run(["curl", "-o", output_file_path, download_url])

        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"The file {audio_file_path} was not found after conversion.")
    finally:
        driver.quit()

    return output_file_path

def list_subfolders(directory, exclude=None):
    """
    Lists subfolders in a directory, excluding specified folders.
    """
    exclude = exclude or []
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir() and f.name not in exclude]
    return sorted(subfolders)

def find_earliest_run_with_video(directory, used_runs):
    """
    Finds the earliest run directory with an available video that hasn't been used yet.
    Returns the run directory path, the video file path, and the run number.
    """
    subfolders = [f.path for f in os.scandir(directory) if f.is_dir()]
    for subfolder in sorted(subfolders, key=lambda x: int(os.path.basename(x))):
        run_number = int(os.path.basename(subfolder))
        if run_number not in used_runs:
            mp4_files = glob(os.path.join(subfolder, "*.mp4"))
            if mp4_files:
                return subfolder, mp4_files[0], run_number
    raise FileNotFoundError("No subfolders with .mp4 files were found")

def time_to_ms(time_str):
    """
    Converts a time string in the format 'hh:mm:ss:ms' to milliseconds.
    """
    h, m, s, ms = map(int, time_str.split(":"))
    return (h * 3600 + m * 60 + s) * 1000 + ms

def create_final_audio(winner_data, normalized_audio, output_path, instrumental_path):
    """
    Creates the final audio by overlaying normalized player audio segments onto the instrumental track.
    Exports the final audio to an MP3 file.
    """
    instrumental_audio = AudioSegment.from_file(instrumental_path)
    instrumental_audio = instrumental_audio.apply_gain(-5)
    max_duration = max(audio.duration_seconds for audio in normalized_audio.values()) * 1000
    output_audio = AudioSegment.silent(duration=max_duration)

    for i, row in winner_data.iterrows():
        start_time = time_to_ms(row['Time'])
        end_time = time_to_ms(winner_data.iloc[i + 1]['Time']) if i + 1 < len(winner_data) else max_duration
        nickname = row['Nickname'].lower()

        if nickname in normalized_audio:
            player_segment = normalized_audio[nickname][start_time:end_time]
            output_audio = output_audio.overlay(player_segment, position=start_time)

    final_audio = instrumental_audio.overlay(output_audio)
    final_audio_path = os.path.join(output_path, "final_output_with_instrumental.mp3")
    final_audio.export(final_audio_path, format="mp3")
    log_with_time(f"Final audio exported at: {final_audio_path}")

    return final_audio_path

def contar_canciones(csv_path):
    """
    Counts the number of songs in the queue by reading the CSV file.
    """
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return sum(1 for row in reader)

def listar_runs_disponibles(runs_directory):
    """
    Counts the number of available runs with video files in the runs directory.
    """
    return sum(1 for subdir in os.scandir(runs_directory) if subdir.is_dir() and glob(os.path.join(subdir.path, "*.mp4")))

def verificar_archivos_cancion(cancion_folder):
    """
    Verifies if the necessary files for a song are present in the song folder.
    Returns True if both voice and instrumental files are found.
    """
    voz_path_mp3 = os.path.join(cancion_folder, "voz.mp3")
    voz_path_wav = os.path.join(cancion_folder, "voz.wav")
    instrumental_path = os.path.join(cancion_folder, "instrumental.mp3")
    if os.path.exists(voz_path_mp3) or os.path.exists(voz_path_wav):
        if os.path.exists(instrumental_path):
            return True
    return False

def verificar_y_convertir_voces(winner_data, cancion_folder, voice_models):
    """
    Verifies if voice files for each player exist; if not, uses Selenium to generate them.
    Returns True if all voice files exist after the process.
    """
    all_exist = True
    for nickname in winner_data['Nickname'].unique():
        nickname_lower = nickname.lower()
        player_audio_path_mp3 = os.path.join(cancion_folder, f"{nickname_lower}.mp3")
        player_audio_path_wav = os.path.join(cancion_folder, f"{nickname_lower}.wav")
        if nickname_lower in voice_models:
            if not os.path.exists(player_audio_path_mp3) and not os.path.exists(player_audio_path_wav):
                log_with_time(f"Voice file for {nickname} is missing. Generating...")
                convert_audio_with_selenium(nickname_lower, os.path.join(cancion_folder, "voz.mp3"), voice_models[nickname_lower], cancion_folder)
                all_exist = False
            else:
                log_with_time(f"Voice file for {nickname} already exists.")
    return all_exist

def main():
    log_canciones_path = r"C:\Users\LENOVO\Documents\canicasbrawl\scripts\log_canciones.csv"
    runs_directory = r"D:\canicasbrawl\Runs"
    voice_models_path = r"D:\canicasbrawl\scripts\selenium\voices.csv"
    voice_models = load_voice_models(voice_models_path)
    raw_production_folder = r"D:\canicasbrawl\raw production"

    num_canciones = contar_canciones(log_canciones_path)
    log_with_time(f"There are {num_canciones} songs in the queue")

    num_runs_disponibles = listar_runs_disponibles(runs_directory)
    log_with_time(f"There are {num_runs_disponibles} runs available for production")

    if num_runs_disponibles < num_canciones:
        log_with_time("There are not enough runs to produce all the songs.")
        return

    used_runs = set()

    with open(log_canciones_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            cancion_nombre = row['nombre']
            cancion_folder = os.path.join(r"D:\canicasbrawl\canciones", cancion_nombre)
            
            run_path, mp4_file, run_number = find_earliest_run_with_video(runs_directory, used_runs)
            video_number = run_number + 25
            new_video_name = f"Video{video_number} - Run {run_number} - {cancion_nombre}.mp4"
            new_video_path = os.path.join(raw_production_folder, new_video_name)
            used_runs.add(run_number)
            
            if os.path.exists(new_video_path):
                log_with_time(f"The video {new_video_name} already exists in raw production.")
                continue

            if verificar_archivos_cancion(cancion_folder):
                log_with_time(f"All necessary files for {cancion_nombre} are present")
            else:
                log_with_time(f"Missing files for {cancion_nombre}.")
                continue

            log_with_time(f"Using {run_path} to produce the song {cancion_nombre}")

            winner_log_path = os.path.join(run_path, "winner_log.csv")
            if not os.path.exists(winner_log_path):
                raise FileNotFoundError(f"The file {winner_log_path} does not exist.")
            winner_data = pd.read_csv(winner_log_path)

            if verificar_y_convertir_voces(winner_data, cancion_folder, voice_models):
                log_with_time(f"All necessary voices for the song {cancion_nombre} already exist.")
            else:
                log_with_time(f"Voice generation for the song {cancion_nombre} completed.")

            # Video production
            log_with_time(f"Producing the video for the song {cancion_nombre} using run {run_path}")
            instrumental_file_path = os.path.join(cancion_folder, "instrumental.mp3")
            player_audio_paths = {
                nickname.lower(): (os.path.join(cancion_folder, f"{nickname.lower()}.mp3") if os.path.exists(os.path.join(cancion_folder, f"{nickname.lower()}.mp3")) else os.path.join(cancion_folder, f"{nickname.lower()}.wav"))
                for nickname in winner_data['Nickname'].unique()
            }

            players_audio = {player: AudioSegment.from_file(path) for player, path in player_audio_paths.items() if os.path.exists(path)}

            # Print original audio levels
            for player, audio in players_audio.items():
                log_with_time(f"Original level of {player}: {audio.dBFS} dBFS")

            # Adjust audio to target level (-20.0 dBFS)
            target_dBFS = -20.0
            normalized_audio = {}

            for player, audio in players_audio.items():
                change_in_dBFS = target_dBFS - audio.dBFS
                normalized_audio[player] = audio.apply_gain(change_in_dBFS)

                # Print levels after normalization
                log_with_time(f"Final level of {player} after normalization: {normalized_audio[player].dBFS} dBFS")

            final_audio_path = create_final_audio(winner_data, normalized_audio, cancion_folder, instrumental_file_path)

            video_path = mp4_file
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"The file {video_path} does not exist.")
            log_with_time(f"Video file found: {video_path}")

            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(final_audio_path)

            video_clip = video_clip.subclip(0, audio_clip.duration)

            final_video = video_clip.set_audio(audio_clip)

            final_video_output_path = os.path.join(cancion_folder, "final_video_with_audio.mp4")
            
            # Check if the final video already exists before exporting
            if os.path.exists(final_video_output_path):
                log_with_time(f"The final video {final_video_output_path} already exists. Skipping export.")
                continue

            final_video.write_videofile(final_video_output_path, codec="libx264", audio_codec="aac")

            log_with_time(f"Final video with audio exported at: {final_video_output_path}")

            os.makedirs(raw_production_folder, exist_ok=True)
            shutil.move(final_video_output_path, new_video_path)
            log_with_time(f"Video moved to: {new_video_path}")

            os.startfile(raw_production_folder)

if __name__ == "__main__":
    main()
