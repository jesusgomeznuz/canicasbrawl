import yt_dlp
from pydub import AudioSegment
import pandas as pd
import os
import shutil

log_canciones_path = r"C:\Users\LENOVO\Documents\canicasbrawl\scripts\log_canciones.csv"
downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")

def convert_to_seconds(time_str):
    """
    Converts a time string in MM:SS format to total seconds.
    """
    minutes, seconds = map(int, time_str.split(':'))
    return minutes * 60 + seconds

# Read the song log CSV file
log_canciones = pd.read_csv(log_canciones_path)

# Identify and display songs that do not require conversion
no_convertir = log_canciones[(log_canciones['URL'] == 'na') | (log_canciones['inicio'] == 'na')]
if not no_convertir.empty:
    print("The following songs do not require conversion:")
    for index, row in no_convertir.iterrows():
        print(f"- {row['nombre']}")

# Filter songs that have valid URLs and start times
log_canciones = log_canciones[(log_canciones['URL'] != 'na') & (log_canciones['inicio'] != 'na')]

# Process each song
for index, row in log_canciones.iterrows():
    youtube_url = row['URL']
    start_time = convert_to_seconds(row['inicio'])
    folder_name = row['nombre']

    # Create the song folder if it doesn't exist
    output_dir = os.path.join("D:\\canicasbrawl\\canciones", folder_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Download audio from YouTube
    print(f"Downloading audio for {folder_name}...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, 'temp_audio.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    # Convert to MP3 and extract the desired segment
    print("Processing audio...")
    audio = AudioSegment.from_file(os.path.join(output_dir, 'temp_audio.mp3'))
    segment = audio[start_time*1000:(start_time + 60)*1000]  # Fixed duration of 60 seconds
    output_file = os.path.join(downloads_dir, f"{folder_name}.mp3")
    segment.export(output_file, format="mp3")

    # Remove temporary audio file
    os.remove(os.path.join(output_dir, 'temp_audio.mp3'))

    print(f"Segment saved as {output_file}")

print("All segments have been downloaded and saved in the downloads folder.")

def verify_files():
    """
    Verifies that all necessary files are present in the downloads directory.
    Returns a list of missing files.
    """
    missing_files = []
    for index, row in log_canciones.iterrows():
        folder_name = row['nombre']
        required_files = [
            f"{folder_name}.mp3",
            f"{folder_name} [music].mp3",
            f"{folder_name} [vocals].mp3"
        ]

        for file in required_files:
            if not os.path.exists(os.path.join(downloads_dir, file)):
                missing_files.append(file)

    return missing_files

# Verification loop to ensure all files are generated
while True:
    missing_files = verify_files()
    if missing_files:
        print("The following files are missing:")
        for file in missing_files:
            print(file)
        input("Please manually separate the audio tracks on the website. Press Enter when you have finished.")
    else:
        print("All files have been successfully generated.")
        break

# Move and copy files to their respective folders
for index, row in log_canciones.iterrows():
    folder_name = row['nombre']
    output_dir = os.path.join("D:\\canicasbrawl\\canciones", folder_name)
    backup_dir = os.path.join(output_dir, "backup")

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    required_files = {
        f"{folder_name}.mp3": f"{folder_name}.mp3",
        f"{folder_name} [music].mp3": "instrumental.mp3",
        f"{folder_name} [vocals].mp3": "voz.mp3"
    }

    for original_file, new_name in required_files.items():
        original_path = os.path.join(downloads_dir, original_file)
        backup_path = os.path.join(backup_dir, new_name)
        main_path = os.path.join(output_dir, new_name)

        # Move and rename files to the backup folder
        shutil.move(original_path, backup_path)

        # Copy files to the main song folder
        shutil.copy(backup_path, main_path)

print("Files moved and copied successfully.")
