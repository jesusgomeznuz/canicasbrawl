import csv
import os
import shutil
import subprocess
import time
import pandas as pd
from glob import glob
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip
from playwright.sync_api import sync_playwright, TimeoutError
import requests

public_url = None  # Global variable to store the public URL

def verificar_url_activo(url):
    try:
        response = requests.get(url, timeout=5)
        # Check if the status code is 200 (OK)
        return response.status_code == 200
    except requests.RequestException:
        return False

def log_with_time(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def load_voice_models(csv_path):
    voice_models = {}
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            voice_models[row['nickname']] = row['URL']  # Associate nickname with the model's URL
    return voice_models

def convert_audio_with_playwright(nickname, audio_file_path, download_link, output_path, public_url):
    # Launch Playwright and configure the browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(public_url)
        
        try:
            # Navigate to the "Generate" tab
            print("Navigating to the 'Generate' tab...")
            page.click('button[role="tab"]:has-text("Generate")')

            # Click on "Refresh Models" in the "Generate" tab
            print("Clicking on 'Refresh Models' in the 'Generate' tab...")
            page.click('button:has-text("Refresh Models 🔁")')

            # Check if the model is available in the "Voice Models" list
            print(f"Checking if the model '{nickname}' is available in the 'Voice Models' list...")
            voice_models_input_selector = 'input[aria-label="Voice Models"]'
            voice_models_input = page.wait_for_selector(voice_models_input_selector, timeout=30000)
            voice_models_input.click()

            # Wait for the dropdown options to be available
            options_selector = 'ul[role="listbox"] li[role="option"]'
            try:
                page.wait_for_selector(options_selector, timeout=5000)
                options = page.query_selector_all(options_selector)
                # Extract model names
                model_names = [option.inner_text().strip() for option in options]
                print(f"Available models: {model_names}")
            except TimeoutError:
                # If no options are available, proceed to add the model
                print("No models found in the dropdown. Proceeding to add the model.")
                model_names = []

            if nickname not in model_names:
                print(f"The model '{nickname}' is not available. Proceeding to add it.")

                # Navigate to the "Download model" tab
                print("Navigating to the 'Download model' tab...")
                page.click('button[role="tab"]:has-text("Download model")')

                # Wait for the fields to be available
                print("Waiting for fields to enter the download link and model name...")
                # Selector for "Download link to model" field
                download_link_selector = 'label:has-text("Download link to model") textarea'
                download_link_textarea = page.wait_for_selector(download_link_selector, timeout=30000)
                print("Field 'Download link to model' found.")

                # Selector for "Name your model" field
                model_name_selector = 'label:has-text("Name your model") textarea'
                model_name_textarea = page.wait_for_selector(model_name_selector, timeout=30000)
                print("Field 'Name your model' found.")

                # Fill in the fields with the provided data
                print("Entering the download link...")
                download_link_textarea.fill(download_link)

                print("Entering the model name...")
                model_name_textarea.fill(nickname)

                # Click on "Download 🌐"
                print("Clicking on 'Download 🌐'...")
                download_button_selector = 'button:has-text("Download 🌐")'
                download_button = page.wait_for_selector(download_button_selector, timeout=30000)
                download_button.click()
                print("Download initiated.")

                # Wait for the success message to appear
                print("Waiting for the model to download and load...")
                try:
                    page.wait_for_function(
                        f"""(modelName) => {{
                            const textarea = document.querySelector('textarea[data-testid="textbox"][disabled]');
                            return textarea && textarea.value.includes(`[+] {nickname} Model successfully downloaded!`);
                        }}""",
                        timeout=300000,
                        arg=nickname
                    )
                    print("Model downloaded and loaded successfully.")
                except TimeoutError:
                    print("Did not receive success message within the expected time.")
                    browser.close()
                    return

                # Return to the "Generate" tab and refresh models
                print("Navigating back to the 'Generate' tab...")
                page.click('button[role="tab"]:has-text("Generate")')
                print("Clicking on 'Refresh Models' in the 'Generate' tab...")
                page.click('button:has-text("Refresh Models 🔁")')

                # Attempt to select the model again
                voice_models_input = page.wait_for_selector(voice_models_input_selector, timeout=30000)
                voice_models_input.click()
                page.wait_for_selector(options_selector, timeout=5000)
                options = page.query_selector_all(options_selector)
                model_names = [option.inner_text().strip() for option in options]

                if nickname in model_names:
                    print(f"The model '{nickname}' is now available after adding.")
                else:
                    print(f"Failed to add the model '{nickname}'.")
                    browser.close()
                    return

            else:
                print(f"The model '{nickname}' is available. Proceeding with generation.")

            # Select the model
            voice_models_input.click()
            page.wait_for_selector(options_selector, timeout=5000)
            page.click(f'{options_selector}:has-text("{nickname}")')
            print(f"Option '{nickname}' selected.")

            # Click on "Upload file instead" and upload the file
            print("Clicking on 'Upload file instead'...")
            upload_file_instead_selector = 'button:has-text("Upload file instead")'
            page.click(upload_file_instead_selector)

            # Wait momentarily for the file input to load
            time.sleep(1)

            print(f"Uploading the file '{audio_file_path}'...")
            file_input_selector = 'input[type="file"][accept="audio/*"]'
            file_input = page.locator(file_input_selector)
            file_input.set_input_files(audio_file_path)
            print("File uploaded successfully.")

            # Wait a few seconds to ensure the file is processed
            print("Waiting 5 seconds to ensure the file is processed...")
            time.sleep(5)

            # Click on 'Generate' using the button ID
            print("Clicking on 'Generate'...")
            generate_button_selector = '#component-55'
            page.wait_for_selector(generate_button_selector, timeout=30000)
            page.click(generate_button_selector)
            print("Generation initiated.")

            # Wait for the generated audio to become available
            print("Waiting for the generated audio to become available...")
            # Wait for the 'div.empty' to disappear within the corresponding component
            page.wait_for_selector('div#component-56 div.empty', state='detached', timeout=600000)
            print("Generated audio is now available.")

            # Click on the download button and handle the download
            print("Clicking on the download button to download the generated audio...")
            download_audio_selector = 'div#component-56 a.download-link'
            with page.expect_download() as download_info:
                page.click(download_audio_selector)
            download = download_info.value
            # Save the downloaded file to a specific path
            output_file_path = os.path.join(output_path, f"{nickname}.mp3")
            download.save_as(output_file_path)
            print("Audio download completed.")

        except Exception as e:
            print(f"Error: {e}")
            browser.close()
            return

        print("Process completed successfully.")
        browser.close()

        return output_file_path


def list_subfolders(directory, exclude=None):
    exclude = exclude or []
    subfolders = [f.name for f in os.scandir(directory) if f.is_dir() and f.name not in exclude]
    return sorted(subfolders)

def find_earliest_run_with_video(directory, used_runs):
    subfolders = [f.path for f in os.scandir(directory) if f.is_dir()]
    for subfolder in sorted(subfolders, key=lambda x: int(os.path.basename(x))):
        run_number = int(os.path.basename(subfolder))
        if run_number not in used_runs:
            mp4_files = glob(os.path.join(subfolder, "*.mp4"))
            if mp4_files:
                return subfolder, mp4_files[0], run_number
    raise FileNotFoundError("No subfolders with .mp4 files were found")

def time_to_ms(time_str):
    h, m, s, ms = map(int, time_str.split(":"))
    return (h * 3600 + m * 60 + s) * 1000 + ms

def create_final_audio(winner_data, normalized_audio, output_path, instrumental_path):
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
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return sum(1 for row in reader)

def listar_runs_disponibles(runs_directory):
    return sum(1 for subdir in os.scandir(runs_directory) if subdir.is_dir() and glob(os.path.join(subdir.path, "*.mp4")))

def verificar_archivos_cancion(cancion_folder):
    voz_path_mp3 = os.path.join(cancion_folder, "voz.mp3")
    voz_path_wav = os.path.join(cancion_folder, "voz.wav")
    instrumental_path = os.path.join(cancion_folder, "instrumental.mp3")
    if os.path.exists(voz_path_mp3) or os.path.exists(voz_path_wav):
        if os.path.exists(instrumental_path):
            return True
    return False

def verificar_y_convertir_voces(winner_data, cancion_folder, voice_models):
    global public_url  # Using the global variable to store the URL

    # Path to the file where we'll store the public URL
    url_file_path = 'public_url.txt'

    # Check if the public URL is already stored and valid
    if public_url is None:
        if os.path.exists(url_file_path):
            with open(url_file_path, 'r') as f:
                stored_url = f.read().strip()
                if verificar_url_activo(stored_url):
                    public_url = stored_url
                    log_with_time(f"Using the stored public URL: {public_url}")
                else:
                    log_with_time("The stored public URL is not active.")
        else:
            log_with_time("No stored public URL found.")

    # If the public URL is still None, request a new one
    if public_url is None:
        public_url = input("Please enter the public URL to perform the conversion: ")
        # Verify if the entered URL is valid
        if verificar_url_activo(public_url):
            # Store the new URL in the file
            with open(url_file_path, 'w') as f:
                f.write(public_url)
            log_with_time(f"New public URL stored: {public_url}")
        else:
            log_with_time("The entered public URL is not valid. Please verify and try again.")
            return False  # Exit the function if the URL is not valid

    all_exist = True
    for nickname in winner_data['Nickname'].unique():
        nickname_lower = nickname.lower()
        player_audio_path_mp3 = os.path.join(cancion_folder, f"{nickname_lower}.mp3")
        player_audio_path_wav = os.path.join(cancion_folder, f"{nickname_lower}.wav")
        if nickname_lower in voice_models:
            if not os.path.exists(player_audio_path_mp3) and not os.path.exists(player_audio_path_wav):
                log_with_time(f"Voice file for {nickname} is missing. Generating...")

                # Call the conversion function with Playwright
                convert_audio_with_playwright(
                    nickname_lower,
                    os.path.join(cancion_folder, "voz.mp3"),
                    voice_models[nickname_lower],  # This is the download link
                    cancion_folder,
                    public_url
                )
                all_exist = False
            else:
                log_with_time(f"Voice file for {nickname} already exists.")
    return all_exist


def main():
    log_canciones_path = r"C:\Users\LENOVO\Documents\canicasbrawl\scripts\log_canciones.csv"
    runs_directory = r"D:\canicasbrawl\Runs"
    voice_models_path = r"D:\canicasbrawl\scripts\voices_info.csv"
    voice_models = load_voice_models(voice_models_path)
    raw_production_folder = r"D:\canicasbrawl\raw production"

    num_canciones = contar_canciones(log_canciones_path)
    log_with_time(f"There are {num_canciones} songs in the queue")

    num_runs_disponibles = listar_runs_disponibles(runs_directory)
    log_with_time(f"There are {num_runs_disponibles} runs available for production")

    used_runs = set()

    with open(log_canciones_path, newline='', encoding='utf-8') as csvfile:

        reader = list(csv.DictReader(csvfile))
        # Process only the first 'num_runs_disponibles' songs
        canciones_a_procesar = reader[:num_runs_disponibles]

        for row in canciones_a_procesar:
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

            # Adjust target_dBFS to a specific level (e.g., -20.0 dBFS)
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
