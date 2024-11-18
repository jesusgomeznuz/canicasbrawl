import os
import csv
import time
import shutil
import subprocess
import pandas as pd
from glob import glob
from pydub import AudioSegment
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from moviepy.editor import VideoFileClip, AudioFileClip

log_canciones_path = r"C:\Users\LENOVO\Documents\canicasbrawl\scripts\log_canciones.csv"
runs_directory = r"D:\canicasbrawl\Runs"
voice_URLS = r"D:\canicasbrawl\scripts\jammable.csv"
raw_production_folder = r"D:\canicasbrawl\raw production"
download_dir = "C:/Users/LENOVO/Downloads/"
email = os.environ.get('JAMMABLE_EMAIL')
password = os.environ.get('JAMMABLE_PASSWORD')

def time_to_ms(time_str):
    """
    Converts a time string in the format 'h:m:s:ms' to milliseconds.
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
    max_duration = instrumental_audio.duration_seconds * 1000
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
    log_with_time(f"Final audio exported to: {final_audio_path}")

    return final_audio_path

def log_with_time(message):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def contar_canciones(csv_path):
    """
    Counts the number of songs in the queue by reading the CSV file.
    """
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return sum(1 for row in reader)

def listar_runs_disponibles(runs_directory):
    """
    Lists the number of available runs by scanning the runs directory.
    """
    return sum(1 for subdir in os.scandir(runs_directory) if subdir.is_dir() and glob(os.path.join(subdir.path, "*.mp4")))

def find_earliest_run_with_video(directory, used_runs):
    """
    Finds the earliest available run with a video that hasn't been used yet.
    Returns the run folder, video file, and run number.
    """
    subfolders = [f.path for f in os.scandir(directory) if f.is_dir()]
    for subfolder in sorted(subfolders, key=lambda x: int(os.path.basename(x))):
        run_number = int(os.path.basename(subfolder))
        if run_number not in used_runs:
            mp4_files = glob(os.path.join(subfolder, "*.mp4"))
            if mp4_files:
                return subfolder, mp4_files[0], run_number
    raise FileNotFoundError("No subfolders with .mp4 files were found")

def sanitize_string(s):
    """Converts a string to lowercase and removes spaces."""
    return s.lower().replace(" ", "")

def obtener_canciones_y_personajes(csv_path, runs_directory, used_runs):
    """
    Retrieves song names and associated characters, matches them with available runs,
    and returns a list of song-character-run associations.
    """
    canciones_personajes = []

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nombre_cancion = row['nombre']

            # Find the earliest available run with video that hasn't been used
            try:
                run_folder, mp4_file, run_number = find_earliest_run_with_video(runs_directory, used_runs)
            except FileNotFoundError:
                log_with_time("No more available runs found.")
                break

            # Calculate new_video_name and new_video_path
            video_number = run_number + 25
            new_video_name = f"Video{video_number} - Run {run_number} - {nombre_cancion}.mp4"
            new_video_path = os.path.join(raw_production_folder, new_video_name)

            # Check if the video already exists in raw production
            if os.path.exists(new_video_path):
                log_with_time(f"The video '{new_video_name}' already exists in raw production.")
                used_runs.add(run_number)  # Ensure not to reuse the run
                continue

            used_runs.add(run_number)

            # Proceed with gathering character nicknames from winner_log.csv
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
            canciones_personajes.append((
                nombre_cancion,
                personajes,
                run_folder,
                mp4_file,
                run_number,
                new_video_name,
                new_video_path
            ))

    return canciones_personajes

def convert_audio_with_selenium(links_nicknames, song_name):
    """
    Automates the process of converting audio files using Selenium to interact with Jammable.com.
    Logs into the site, uploads audio files, initiates conversions, waits for completion, and downloads results.
    """
    service = Service('C:/chromedriver-win64/chromedriver.exe')
    chrome_options = Options()
    #chrome_options.add_argument("--headless")  # Runs in headless mode
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
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - The conversion for {nickname} already exists.")
            else:
                driver.get(link)
                time.sleep(1)

                conversion_button = driver.find_element(By.XPATH, "//div[contains(@class,'tw-text-lg') and contains(text(),'Create Cover')]")
                conversion_button.click()

                # Interact directly with the file input element
                path = f"D:\\canicasbrawl\\canciones\\{song_name}\\voz.mp3"
                if not os.path.exists(path):
                    print(f"The file {path} does not exist.")
                    continue  # Skip to the next iteration if the file does not exist

                # Wait for the file input element to be present
                try:
                    file_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                    )
                    file_input.send_keys(path)
                except TimeoutException:
                    print(f"Could not find the file upload element for {nickname}.")
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
                    # Save the page source for debugging
                    with open(f'convert_error_{nickname}.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    continue

                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Conversion started for {nickname}")
                
        # After processing all conversions
        driver.get("https://www.jammable.com/history")
        time.sleep(1)

        while "PENDING" in driver.page_source.upper() or "CONVERTING" in driver.page_source.upper() or "EXTRACTING" in driver.page_source.upper() or "MIXING" in driver.page_source.upper():
            print("Conversions are still pending.")
            time.sleep(15)  # Wait 15 seconds before refreshing
            driver.refresh()
        
        print("All conversions have completed.")
        time.sleep(5)

        for link, nickname, filename in links_nicknames:
            output_path = os.path.join(f"D:/canicasbrawl/canciones/{song_name}/", f"{sanitize_string(nickname)}.wav")

            # Check if the file already exists
            if os.path.exists(output_path):
                print(f"The file for {nickname} already exists in the destination folder. Skipping download.")
                continue

            try:
                # Find the link to the completed conversion
                conversion_link_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//a[contains(@class, 'Conversion_history-item-container') and contains(., '{filename}')]"))
                )
                conversion_link = conversion_link_element.get_attribute("href")
                driver.get(conversion_link)
                print(f"Opening the link to the completed conversion: {conversion_link}")
                time.sleep(1)
            except TimeoutException:
                print(f"Could not open the link for '{filename}': Link not found after waiting.")
                continue
            except NoSuchElementException:
                print(f"Could not open the link for '{filename}': Element not found in the DOM.")
                continue
    
            try:
                # Click the "Download" button to display the list
                download_button = WebDriverWait(driver, 120).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'tw-inline-flex') and contains(text(), 'Download')]"))
                )
                download_button.click()
                time.sleep(1)

                # Click on "Download Combined"
                download_combined_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Download Combined')]"))
                )
                download_combined_button.click()
                print(f"Clicked 'Download Combined' for {nickname}.")
                time.sleep(2)
            except TimeoutException:
                print(f"Could not click 'Download Combined' for {nickname}: Timed out.")
                continue
            except NoSuchElementException:
                print(f"Could not click 'Download Combined' for {nickname}: Element not found in the DOM.")
                continue

            # Wait briefly to allow the download to start
            time.sleep(2)

            # Search for the downloaded file in the downloads folder
            downloaded_file = None
            files_in_download = [f for f in os.listdir(download_dir) if f.endswith(".mp3")]
            if not files_in_download:
                print(f"No .mp3 files found in the downloads folder for {nickname}.")
                continue

            # Identify the most recent file
            downloaded_file = max(
                [os.path.join(download_dir, f) for f in files_in_download],
                key=os.path.getctime
            )

            # Rename the downloaded file to "[nickname] - [song_name].mp3"
            new_filename = f"{nickname} - {song_name}.mp3"
            new_file_path = os.path.join(download_dir, new_filename)
            try:
                os.rename(downloaded_file, new_file_path)
                print(f"Downloaded file renamed to: {new_filename}")
            except Exception as e:
                print(f"Error renaming the file for {nickname}: {e}")
                continue

            # Convert the .mp3 file to .wav and move it to the destination folder
            try:
                audio = AudioSegment.from_mp3(new_file_path)
                audio.export(output_path, format="wav")
                os.remove(new_file_path)
                print(f"The file for {nickname} has been converted and moved to: {output_path}")
            except Exception as e:
                print(f"Error converting or moving the file for {nickname}: {e}")
                continue

            driver.get("https://www.jammable.com/history")
            time.sleep(1)
    finally:
        driver.quit()

def check_existing_conversion(driver, filename):
    """Checks if a conversion with the given filename already exists on Jammable."""
    driver.get("https://www.jammable.com/history")
    time.sleep(1)
    try:
        driver.find_element(By.XPATH, f"//div[contains(text(),'{filename}')]")
        return True
    except:
        return False

# Step 1: Count the number of songs in the queue
num_canciones = contar_canciones(log_canciones_path)
log_with_time(f"There are {num_canciones} songs in the queue")

# Step 2: List the number of available runs
num_runs_disponibles = listar_runs_disponibles(runs_directory)
log_with_time(f"There are {num_runs_disponibles} runs available for production")

# Step 3: Check if there are enough available runs
if num_runs_disponibles < num_canciones:
    log_with_time("There are not enough runs to produce all songs.")
else:
    # Initialize used_runs
    used_runs = set()

    # Step 4: Obtain songs and characters
    canciones_personajes = obtener_canciones_y_personajes(log_canciones_path, runs_directory, used_runs)

    # Process each song and its characters
    for cancion, personajes, run_folder, mp4_file, run_number, new_video_name, new_video_path in canciones_personajes:
        print(f"Song to produce: {cancion}")
        print(f"Characters: {personajes}")
        print()

        personajes_list = personajes.split(',')

        # Check existing files and create a list of missing ones
        folder_path = f"D:/canicasbrawl/canciones/{cancion}/"
        missing_personajes = []

        for personaje in personajes_list:
            mp3_path = os.path.join(folder_path, f"{personaje}.mp3")
            wav_path = os.path.join(folder_path, f"{personaje}.wav")
            if os.path.exists(mp3_path):
                log_with_time(f"The file {mp3_path} already exists.")
            elif os.path.exists(wav_path):
                log_with_time(f"The file {wav_path} already exists.")
            else:
                log_with_time(f"The file for {personaje} does not exist and will be converted.")
                missing_personajes.append(personaje)

        if not missing_personajes:
            log_with_time(f"All necessary files for {cancion} are present.")
        else:
            log_with_time(f"Starting conversion for {cancion} for the missing characters...")
            # Proceed with the conversion

            # Read names and URLs from jammable.csv
            df = pd.read_csv(voice_URLS)
            selected_characters = df[df['nickname'].isin(missing_personajes)]
            links_nicknames = [
                (row['URL'], row['nickname'], sanitize_string(f"{cancion}-{row['nickname']}"))
                for _, row in selected_characters.iterrows()
            ]

            # Perform the conversion
            convert_audio_with_selenium(links_nicknames, cancion)
            log_with_time(f"Conversion completed for {cancion}")

        # **Begin integration of video generation**
        # Verify if the voice and instrumental files are present
        voz_path_mp3 = os.path.join(folder_path, "voz.mp3")
        voz_path_wav = os.path.join(folder_path, "voz.wav")
        instrumental_path = os.path.join(folder_path, "instrumental.mp3")
        if os.path.exists(voz_path_mp3) or os.path.exists(voz_path_wav):
            if os.path.exists(instrumental_path):
                log_with_time(f"All necessary files for {cancion} are present for video generation.")
            else:
                log_with_time(f"The instrumental file is missing for {cancion}. Skipping video generation.")
                continue
        else:
            log_with_time(f"The voice file is missing for {cancion}. Skipping video generation.")
            continue

        # Load the data from winner_log.csv
        winner_log_path = os.path.join(run_folder, "winner_log.csv")
        if not os.path.exists(winner_log_path):
            raise FileNotFoundError(f"The file {winner_log_path} does not exist.")
        winner_data = pd.read_csv(winner_log_path)

        # Prepare the paths of the player audio files
        player_audio_paths = {
            nickname.lower(): (os.path.join(folder_path, f"{nickname.lower()}.mp3") if os.path.exists(os.path.join(folder_path, f"{nickname.lower()}.mp3")) else os.path.join(folder_path, f"{nickname.lower()}.wav"))
            for nickname in winner_data['Nickname'].unique()
        }

        # Load the player audio files
        players_audio = {player: AudioSegment.from_file(path) for player, path in player_audio_paths.items() if os.path.exists(path)}

        # Normalize audio levels
        target_dBFS = -20.0
        normalized_audio = {}
        for player, audio in players_audio.items():
            change_in_dBFS = target_dBFS - audio.dBFS
            normalized_audio[player] = audio.apply_gain(change_in_dBFS)

        # Create the final audio by combining normalized voices and instrumental
        final_audio_path = create_final_audio(winner_data, normalized_audio, folder_path, instrumental_path)

        # Get the path of the video corresponding to the run
        video_path = mp4_file
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"The file {video_path} does not exist.")
        log_with_time(f"Video file found: {video_path}")

        # Load the video and the final audio
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(final_audio_path)

        # Adjust the video duration to the audio
        video_clip = video_clip.subclip(0, audio_clip.duration)

        # Combine the audio with the video
        final_video = video_clip.set_audio(audio_clip)

        # Export the final video
        final_video_output_path = os.path.join(folder_path, "final_video_with_audio.mp4")

        # Check if the final video already exists
        if os.path.exists(final_video_output_path):
            log_with_time(f"The final video {final_video_output_path} already exists. Skipping export.")
        else:
            final_video.write_videofile(final_video_output_path, codec="libx264", audio_codec="aac")
            log_with_time(f"Final video with audio exported to: {final_video_output_path}")

        # Move the final video to the raw production folder
        os.makedirs(raw_production_folder, exist_ok=True)
        shutil.move(final_video_output_path, new_video_path)
        log_with_time(f"Video moved to: {new_video_path}")

        os.startfile(raw_production_folder)
