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
The `generate-videos.py` script is implemented in three variations: `generate-videos-jammable.py`, `generate-videos-aicovergen.py`, and `generate-videos-applio.py`. While all three serve the same purpose — generating **CanicasBrawl** videos — each variation offers unique efficiencies and trade-offs depending on the context.

This section explores the unique workflows of these scripts, showing:
- A detailed explanation of the voice generation workflow for each platform.
- Visual demonstrations with process diagrams and practical examples.
- A breakdown of their strengths, limitations, and best use cases.

---

### Implementations

#### 1. **Jammable Workflow**  
**Script**: `generate-videos-jammable.py`  
- **Use Case**: Best for quickly generating full songs for all characters, providing a clear preview of the final race.
- **How It Works**:
  - Processes multiple voices simultaneously to generate audio for each character.
  - Synchronizes the audio and video for the entire race.
- **Why Use It?**:
  - Fast, precise, and reliable for rapid prototyping and decision-making.
  - Helps evaluate if a song or character setup works effectively for the race.
- **Challenges**:
  - Requires careful use to avoid overloading third-party resources.
  - Subscription-based service, which may limit accessibility for some users.
  - While quality is good, it’s not as clear or polished as AICoverGen for final production.
- **Resources**:
  - [View Process Diagram](#)
  - [Watch Workflow in Action](#)

---

#### 2. **r3gm/AICoverGen Workflow**  
**Script**: `generate-videos-aicovergen.py`  
- **Use Case**: Ideal for final production, refining or updating specific character voices with the best audio quality.
- **How It Works**:
  - Processes selected voices with high precision, ensuring clear and polished results.
  - Can handle full songs or individual character adjustments, but it is slower compared to Jammable.
- **Why Use It?**:
  - Produces the highest-quality audio for **CanicasBrawl** videos.
  - Perfect for finalizing projects after decisions on songs and character roles are made.
- **Challenges**:
  - Slower processing compared to Jammable, making it less suitable for rapid prototyping or experimentation.
  - Requires significant resources to run locally (T4 GPU with High RAM) or a paid Google Colab subscription.
  - Costs can add up, though not excessively.
- **Resources**:
  - [View Process Diagram](#)
  - [Watch Workflow in Action](#)

---

#### 3. **Applio Workflow**  
**Script**: `generate-videos-applio.py`  
- **Use Case**: Suitable for generating all voices locally, especially when budget constraints are a priority.
- **How It Works**:
  - Processes voices locally, either for all characters or specific ones, with the same workflow as other scripts.
  - Allows full automation using Selenium for integration into local setups.
- **Why Use It?**:
  - Free and completely local, making it accessible without requiring paid subscriptions or external servers.
  - Useful for prototyping or when hardware resources are limited.
- **Challenges**:
  - Voice quality is lower compared to Jammable and AICoverGen.
  - Processing speed depends on local hardware; slower on less powerful systems.
  - Often requires post-processing (e.g., cleaning voices with AICoverGen) for production-quality results.
- **Resources**:
  - [View Process Diagram](#)
  - [Watch Workflow in Action](#)


---

### Summary Table

| Workflow         | Best Use Case                           | Advantages                                     | Disadvantages                                   |
|-------------------|-----------------------------------------|-----------------------------------------------|-----------------------------------------------|
| **Jammable**      | Full song for all characters quickly    | Fast, precise, and reliable for prototyping   | Requires third-party service; subscription-based; quality not as polished as AICoverGen |
| **AICoverGen**    | Refining or updating specific voices    | Produces the best audio quality               | Slower than Jammable; requires high resources or paid Google Colab subscription         |
| **Applio**        | Generating all voices locally           | Free and fully local; straightforward automation | Slower and lower quality; depends on hardware; may need post-processing                |

---

## Interactive Example: AI-Generated 1vs1 Races

### Overview
This section demonstrates how AI is used to optimize **1vs1 races** in **CanicasBrawl**. The example walks through:
1. The initial setup of the race.
2. Interaction with AI to refine the marble positions.
3. Execution of the `generate-videos-jammable.py` script with the new setup.
4. A final visual comparison between the **Original Random Setup** and the **AI-Optimized Setup**.

---

### Initial Setup
Here’s a snapshot of the initial race setup and the corresponding data from `winner_log.csv`:

#### Race Setup Photo
![Initial Setup](path/to/initial_setup_photo.png)

#### Winner Log (`winner_log.csv`)
```csv
Nickname,Time
Player1,15
Player2,20
Player3,30
...

### Interaction with AI
To optimize the race, **ChatGPT** was used to recommend a new arrangement for the marbles based on the times in `winner_log.csv`.

#### ChatGPT Interaction
You can view the full interaction [here](link/to/chatgpt_interaction.md).

#### Key Result
ChatGPT suggested the following arrangement:
```text
Marble Positions:
1. Player3
2. Player2
3. Player1
...

---

#### New Setup Photo
![AI-Optimized Setup](path/to/ai_optimized_setup_photo.png)

---

### Script Execution
Using the `generate-videos-jammable.py` script, the voices were generated for the new setup.

#### Demo Video: Generating Voices
[Watch Voice Generation in Action](path/to/voice_generation_demo.mp4)

---

### Final Comparison
Below is a side-by-side comparison of the **Original Random Setup** vs. the **AI-Optimized Setup**, showcasing how the changes impacted the final video:

#### Comparison Video
[Watch Side-by-Side Comparison](path/to/comparison_video.mp4)

---

### Key Takeaways
- The AI-optimized setup resulted in a more balanced and visually engaging race.
- This example highlights how AI can be used not only for optimization but also to demonstrate the flexibility and scalability of the **CanicasBrawl** workflow.

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
