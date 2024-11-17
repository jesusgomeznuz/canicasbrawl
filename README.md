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

1. **`generate-videos.py`**:
   - Combines race video (run_folder) and character audio to produce final CanicasBrawl videos.
   - Automates the process of:
     - Verifying if a video has already been produced.
     - Checking for missing character voice files.  
     - Generating missing voices using integrated voice services ([Jammable](#), [Applio](#), or [AICoverGen](#)).
     - Normalizing audio levels across all character tracks.
     - Synchronizing the audio with the race video.
   - Ensures the final video is stored in the raw production folder for further distribution.
   - **[View Process Diagram](link-to-generate-videos-diagram)**

This process is supported by two fundamental subprocesses:

1. **`guardar-run.py`**:
   - Creates the run folder (`run_folder`) containing:
     - `winner_log.csv`: A log of the winner and run statistics.
     - Run video: A video capture of the run itself.
   - This script is essential for generating the final videos.
   - **[View Process Diagram](link-to-guardar-run-diagram)**

2. **`voice-removal.py`**:
   - Takes as input the name, YouTube link, and start time of a song to:
     - Download a 1-minute segment.
     - Separate vocal and instrumental tracks.
   - **Note**: This process requires manual intervention due to platform limitations that detect Selenium as a bot.
   - **[View Process Diagram](link-to-voice-removal-diagram)**

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
