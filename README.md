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
The core of the project is the integration of multiple scripts and processes, all working together to produce **CanicasBrawl** videos. The main script, `generate-videos.py`, connects these elements to ensure seamless video production.

Key components include:
- **`guardar_run.py`**: Prepares the `run_folder` by organizing the race video (`Movie_*.mp4`) and necessary log files (`winner_log.csv`). It also maintains historical data in `historico_runs.xlsx` for lead times and winners.
- **`voice_removal.py`**: Downloads, processes, and organizes audio files into the `canciones` folder. It extracts 60-second segments from YouTube based on metadata in `log_canciones.csv`, separates vocals and music, and ensures all audio files are ready for synchronization.
- **`log_canciones.csv`**: A key metadata file containing the YouTube URLs, start times, and track names required for processing and organizing the audio files.

Together, these components feed into the `generate-videos.py` script, which combines the organized run video, synchronized audio tracks, and additional data to produce the final **CanicasBrawl** videos.

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

## `generate-videos.py`: Comparison and Workflow

### Overview
This section explores the three different implementations of the `generate-videos.py` script: `generate-videos-jammable.py`, `generate-videos-aicovergen.py`, and `generate-videos-applio.py`. Each implementation has unique strengths and trade-offs, making them suitable for specific use cases.

For each implementation, you’ll find:
- A **process diagram** illustrating the script’s workflow.
- A **demo video** showing how the script generates a video.
- An explanation of its **advantages**, **disadvantages**, and **recommended use cases**.

### Implementations

#### 1. **Jammable Workflow (generate-videos-jammable.py)**
- **Overview**: 
  - This implementation is ideal for generating complete songs for all characters. It processes multiple voice files at once, ensuring consistency across the entire song.
- **Use Case**: Use this when you need to generate audio for every character in a race.
- **Diagram**: [View Process Diagram](#)
- **Demo Video**: [Watch Jammable Workflow in Action](#)
- **Advantages**:
  - Handles multiple voices efficiently.
  - Produces consistent results for full songs.
  - Minimal manual intervention once configured.
- **Disadvantages**:
  - Requires significant pre-processing and file organization.
  - May be resource-intensive for large-scale processing.

---

#### 2. **AI Cover Workflow (generate-videos-aicovergen.py)**
- **Overview**:
  - This implementation is best suited for refining or correcting specific voices. It is useful when only a few characters need adjustments or updates.
- **Use Case**: Use this to refine up to three character voices for an existing video setup.
- **Diagram**: [View Process Diagram](#)
- **Demo Video**: [Watch AI Cover Workflow in Action](#)
- **Advantages**:
  - Focuses on specific voices, reducing processing time.
  - Allows for targeted improvements without redoing the entire song.
- **Disadvantages**:
  - Limited to processing a small number of voices per run.
  - May require additional manual steps to align corrections with the video.

---

#### 3. **Applio Workflow (generate-videos-applio.py)**
- **Overview**:
  - This implementation is designed for single-voice scenarios. It simplifies the process by focusing on generating audio for one character at a time.
- **Use Case**: Use this for quick adjustments or single-character songs.
- **Diagram**: [View Process Diagram](#)
- **Demo Video**: [Watch Applio Workflow in Action](#)
- **Advantages**:
  - Simplified workflow for one-character runs.
  - Faster processing times for targeted use cases.
- **Disadvantages**:
  - Limited scalability for larger races or full songs.
  - Less efficient for multiple-character scenarios.

---

### Summary Table

| Workflow         | Best Use Case                  | Advantages                                    | Disadvantages                                  |
|-------------------|--------------------------------|-----------------------------------------------|-----------------------------------------------|
| **Jammable**      | Full song for all characters  | Efficient for multi-voice processing          | Requires pre-processed files, resource-heavy  |
| **AI Cover**      | Refining specific voices      | Targeted corrections, faster for small changes| Limited to a few voices, manual adjustments   |
| **Applio**        | Single-character adjustments  | Quick and simple for one character            | Inefficient for multiple characters           |



---

## Interactive Example: AI-Generated 1vs1 Races

### Overview
In this section, you’ll explore how AI is used to optimize **1vs1 races** for **CanicasBrawl**. This example walks through the workflow step by step, including how the AI interacts with the process and the visual differences in the final videos.

### Process Flow
1. **Interaction with AI (ChatGPT)**:
   - Define parameters for the race setup.
2. **Script Execution**:
   - Generate the race video using the optimized parameters.
3. **Visual Comparison**:
   - Original Random Setup vs. AI-Optimized Setup.

### Demo Videos
- [ChatGPT Interaction Preview](#)
- [Original Random Setup](#)
- [AI-Optimized Setup](#)

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
