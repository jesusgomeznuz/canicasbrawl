# CanicasBrawl

## Introduction
**CanicasBrawl** is a Unity-based project that combines simulation mechanics, music, and visual storytelling. The primary goal is to provide a unique and exciting experience through interactions with marbles, songs, and iconic characters. Additionally, the project integrates **Python automation scripts** to optimize content generation, from videos to detailed statistics.

---

## Project Structure

The project is organized into the following key folders and files:

- **canciones/**: Contains the songs used in the project, including separated vocal and instrumental tracks.
- **scripts/**: Python scripts for automation.
- **raw production/**: Stores intermediate materials generated during content creation, such as unedited videos.
- **runs/**: Folder containing data and videos for each run.
- **CanicasBrawl/**: Unity project folder with essential images, scripts, and assets.
- **historico_runs.xlsx**: File that logs the historical data of all previous runs.
- **prompt1.txt**: File with prompts used for automation assistance.

---

## How the Project Works

### Overview
The core of the project is the main script, `generate-videos.py`, which connects and manages the different elements needed to produce **CanicasBrawl** videos. 

### 1. `generate-videos.py`
- **Purpose**: Combines run video (from `run_folder`) and voice files (from `canciones`) to produce final CanicasBrawl videos.
- **Automates the process of**:
  - Verifying if a video has already been produced.
  - Checking for missing character voice files.
  - Generating missing voices using integrated voice services ([Jammable](https://www.jammable.com/), [Applio](https://applio.org/), or [AICoverGen](https://huggingface.co/spaces/r3gm/AICoverGen)).
  - Cutting and joining audio tracks based on lead times from `winner_log.csv`.
  - Synchronizing the audio with the race video.
- **Output**: A fully synchronized video file ready for final distribution.
- [View Process Diagram](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/generate-videos-diagram.png)

This process is supported by two fundamental subprocesses:

### 1. `guardar_run.py`
- **Purpose**: Prepares the `run_folder` by organizing the run video (`Movie_*.mp4`) and the `winner_log.csv` file for video generation. Additionally, it saves `results.csv` and `winner.csv` to maintain a historical record of lead times and winners in `historico_runs.xlsx`.
- **Automates the process of**:
  - Creating the `run_folder` and organizing its contents.
  - Moving the most recent recording (`Movie_*.mp4`) to the folder for video generation.
  - Moving `winner_log.csv` to the `run_folder` as the key file required for generating the final video.
  - Generating `results.csv` and `winner.csv` in the `run_folder` to maintain a historical record of lead times and winners in `historico_runs.xlsx`.
- **Output**: A structured `run_folder` containing:
  - The run video (`Movie_*.mp4`).
  - `winner_log.csv` (required for video generation).
  - `results.csv` (for lead times).
  - `winner.csv` (for historical records).
- **Purpose**: This script organizes essential files needed for video generation and maintains a history of runs for analysis.
- [View Process Diagram](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/guardar_run.png)

### 2. `voice_removal.py`
- **Purpose**: Downloads audio from YouTube, extracts specific segments, and organizes them in the `canciones` folder for further processing.
- **Automates the process of**:
  - Reading song metadata from `log_canciones.csv` to determine the YouTube video to download.
  - Downloading audio files from YouTube using `yt_dlp` and extracting 60-second segments based on start times defined in the log.
  - Extracting music and vocals from the YouTube segment and organizing the processed files in the `canciones` folder (requires manual intervention for separation).
- **Output**: A well-organized folder structure for each song, feeding the `canciones` folder with:
  - `instrumental.mp3` (the instrumental track).
  - `voz.mp3` (the vocal track).
  - `[song_name].mp3` (the original 60-second segment).
- **Purpose**: This script ensures the `canciones` folder is filled with the required audio files of songs. It prepares audio files for synchronization with run videos while maintaining a clean backup system.
- [View Process Diagram](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/voice_removal.png)

These three scripts (along with `generate-videos.py`) form **the backbone of the project**, transforming data and songs into engaging visual content.

---

## Main Process Diagrams

### 1. General Process: `generate-videos.py`
This diagram illustrates the primary workflow of the script and how it interacts with subprocesses:
- **Explainer Video**: [Watch video](#) *(Add link to the explainer video of the process)*
- **Main Diagram**: [View diagram](#) *(Add link to the main flow diagram)*

### 2. Subprocesses
- **`guardar-run.py`**:
  - **Description**: Generates the `run_folder`, essential for video generation.
  - **Explainer Video**: [Watch video](#)
  - **Process Diagram**: [View diagram](#)

- **`voice-removal.py`**:
  - **Description**: Downloads song segments and separates vocal and instrumental tracks.
  - **Explainer Video**: [Watch video](#)
  - **Process Diagram**: [View diagram](#)

---

## Supporting Processes

In addition to the main processes, the project includes specific workflows that are key to content generation:

- **Voice Generation**:
  - **Description**: Processes using specific platforms (e.g., Jammable, CoverAIGen, and Applio).
  - **Diagrams**:
    - [Jammable](#)
    - [CoverAIGen](#)
    - [Applio](#)

- **Final Audio Creation**:
  - **Description**: Combines generated vocal tracks with the instrumental to create the final audio.
  - **Process Diagram**: [View diagram](#)

- **Winner Logging**:
  - **Description**: Uses a C program in Unity to log the winners of each run.
  - **Process Diagram**: [View diagram](#)

---

## Additional Resources

- **Screenshots**: [Gallery](#)
- **Project Demo Video**: [Watch video](#)
- **Extended Documentation**: [View documentation](#)

---

## Contact
- **Name:** Jesús
- **Email:** your_email@example.com
- **LinkedIn:** [Your Profile](https://linkedin.com/in/your_profile)

---

## Next Steps
1. Document additional processes as needed.
2. Add links to explainer videos and diagrams when they are ready.
3. Continue optimizing the core scripts for better efficiency.

---
