# CanicasBrawl

## Introduction
**CanicasBrawl** is a Unity-based project that combines simulation mechanics, music, and visual storytelling. The primary goal is to provide a unique and exciting experience through interactions with marbles, songs, and iconic characters. 

A key feature of the project is its integration of **Python automation scripts**, which streamline content generation, from videos to detailed statistics. These scripts work together to process race data (`winner_log.csv`), manage song queues (`log_canciones.csv`), and synchronize audio with visual content, ensuring a seamless and dynamic experience.

---

## Project Structure

The project is organized into the following key folders and files:

- **runs/**: Folder containing data and videos for each run.
- **canciones/**: Contains the songs used in the project, including separated vocal and instrumental tracks.
- **raw production/**: Stores intermediate materials generated during content creation, such as unedited videos.
- **scripts/**: Python scripts for automation.
- **historico_runs.xlsx**: File that logs the historical data of all previous runs.
- **prompt1.txt**: File with prompts used for automation assistance.

---

## How the Project Works

### Overview
The core of the project is the integration of multiple scripts and processes, all working together to produce **CanicasBrawl** videos. The main script, `generate-videos.py`, connects these elements to ensure seamless video production.

Key components include:
- **`guardar_run.py`**: Prepares the `run_folder` by organizing the race video (`Movie_*.mp4`) and necessary log files (`winner_log.csv`). It also maintains historical data in `historico_runs.xlsx` for lead times and winners.
- **`voice_removal.py`**: Downloads, processes, and organizes audio files into the `canciones` folder. It extracts 60-second segments from YouTube based on metadata in `log_canciones.csv`, separates vocals and music, and ensures all audio files are ready for synchronization.
- **`log_canciones.csv`**: Acts as the main queue of songs, determining which tracks from the `canciones` folder are used during the video production process.

Together, these components feed into the `generate-videos.py` script, which combines the organized run video, synchronized audio tracks, and additional data to produce the final **CanicasBrawl** videos.

### 1. `generate-videos.py`
- **Purpose**: Combines the run video (from `run_folder`), the song queue (`log_canciones.csv`), and voice files (from `canciones`) to produce final CanicasBrawl videos. It ensures a seamless synchronization of songs with race leader transitions.
- **Automates the process of**:
  - Reviewing `log_canciones.csv` as the primary song queue to determine the songs available for the next runs. It prints the number of songs in the queue and the number of runs available for processing.
  - Verifying if a video has already been produced.
  - Checking for missing character voice files.
  - Generating missing voices using integrated voice services ([Jammable](https://www.jammable.com/), [Applio](https://applio.org/), or [AICoverGen](https://huggingface.co/spaces/r3gm/AICoverGen)).
  - Cutting and joining audio tracks from the queue based on the leader transitions recorded in `winner_log.csv`, dynamically matching the audio to the race leader.
- **Output**: A fully synchronized video file ready for final distribution.

**Process Diagram**:
<p align="center">
  <img src="https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/generate-videos-diagram.png" alt="Process Diagram" width="600">
</p>

This process is supported by two fundamental subprocesses:

### 1. `guardar_run.py`
- **Purpose**: Prepares the `run_folder` by organizing the run video (`Movie_*.mp4`) and the `winner_log.csv` file for video generation. Additionally, it saves `results.csv` and `winner.csv` to maintain a historical record of lead times and winners in `historico_runs.xlsx`.
- **Automates the process of**:
  - Creating the `run_folder` and organizing its contents.
  - Moving the most recent recording (`Movie_*.mp4`) to the folder for video generation.
  - Moving `winner_log.csv` to the `run_folder` to map leader transitions, which are later matched to songs using `log_canciones.csv`.
  - Generating `results.csv` and `winner.csv` in the `run_folder` to maintain a historical record of lead times and winners in `historico_runs.xlsx`.
- **Output**: A structured `run_folder` containing:
  - The run video (`Movie_*.mp4`).
  - `winner_log.csv` (required for video generation).
  - `results.csv` (for lead times).
  - `winner.csv` (for historical records).
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

These two scripts (along with `generate-videos.py`) form **the backbone of the project**, transforming data and songs into engaging visual content.

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
  - [View Process Diagram](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/jammable.png)
  - [Watch Workflow in Action](https://drive.google.com/file/d/1wA-9G51DJUBaLN_zec-aCZTNGpND5ot7/view?usp=sharing)

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
  - [View Process Diagram](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/AICoverGen.png)
  - [Watch Workflow in Action](https://drive.google.com/file/d/1TJD9XPC5EW-qPIH8XRtvKvJ1gdJJQpFo/view?usp=sharing)

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
  - [View Process Diagram](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/Applio.png)
  - [Watch Workflow in Action](https://drive.google.com/file/d/1fLL0_rjS0zbbhg93d-NWkbagxR4KQSNt/view?usp=sharing)


---

### Summary Table

| Workflow         | Best Use Case                           | Advantages                                     | Disadvantages                                   |
|-------------------|-----------------------------------------|-----------------------------------------------|-----------------------------------------------|
| **Jammable**      | Full song for all characters quickly    | Fast, precise, and reliable for prototyping   | Requires third-party service; subscription-based; quality not as polished as AICoverGen |
| **AICoverGen**    | Refining or updating specific voices    | Produces the best audio quality               | Slower than Jammable; requires high resources or paid Google Colab subscription         |
| **Applio**        | Generating all voices locally           | Free and fully local; straightforward automation | Slower and lower quality; depends on hardware; may need post-processing                |

---

## Interactive Example: AI-Generated 1vs1 Races

In this section, you'll see how ChatGPT o1-preview improves 1vs1 races in CanicasBrawl, with Marceline competing against Dipper. We'll start with the original setup of 8 marbles, analyze the data, and show how the race evolves with AI-generated assignments.

### Initial Setup

#### Race Setup Photo
![Initial Setup](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/initial_setup.jpg)

#### Winner Log Data
The race shown in the initial setup produces the following times and positions, taken from winner_log.csv and summarized in winner_list.csv, as shown below.

```csv
Table 1 (original without duplicates):
            Time   Winner   Nickname
0   00:00:00:000  Player5   Mordecai
2   00:00:03:033  Player7     Naruto
4   00:00:03:333  Player8      Ben10
6   00:00:04:000  Player4  marceline
8   00:00:04:133  Player8      Ben10
10  00:00:06:033  Player7     Naruto
12  00:00:06:067  Player1       Finn
14  00:00:06:200  Player3     Steven
16  00:00:07:000  Player1       Finn
18  00:00:09:000  Player2        BMO
20  00:00:09:067  Player4  marceline
22  00:00:09:133  Player2        BMO
24  00:00:09:200  Player8      Ben10
26  00:00:13:133  Player4  marceline
28  00:00:15:700  Player8      Ben10
30  00:00:17:267  Player4  marceline
32  00:00:21:167  Player8      Ben10
34  00:00:23:967  Player5   Mordecai
36  00:00:24:033  Player8      Ben10
38  00:00:24:667  Player5   Mordecai
40  00:00:24:867  Player1       Finn
42  00:00:26:933  Player8      Ben10
44  00:00:26:967  Player1       Finn
46  00:00:27:600  Player8      Ben10
48  00:00:28:000  Player4  marceline
50  00:00:30:033  Player7     Naruto
52  00:00:30:800  Player5   Mordecai
54  00:00:31:200  Player7     Naruto
56  00:00:33:033  Player1       Finn
58  00:00:33:400  Player2        BMO
60  00:00:36:967  Player1       Finn
62  00:00:48:667  Player6      Quico
64  00:00:53:967  Player3     Steven
66  00:00:54:300  Player7     Naruto

Table 2 (total times per player):
    Nickname    Time
0   Mordecai   3.699
1     Naruto   1.834
2      Ben10  11.935
3  marceline   8.699
4       Finn  16.899
5     Steven   1.133
6        BMO   3.701
7      Quico   5.300
```

### AI-Optimized Arrangement
To enhance the dynamics of a 1vs1 race between Marceline and Dipper, ChatGPT analyzed the `winner_log.csv` and `winner_list.csv` data. The goal was to balance singing times, alternate leadership frequently, and create an engaging competition while maintaining fairness.

#### ChatGPT Interaction
You can view the full conversation with **ChatGPT** [here](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/chatgpt_interaction.md).

#### Key Result: Suggested Marble Assignments
The AI proposed the following optimized teams based on the total times:

##### Marceline:
- **Player1**: Finn - 16.899 s  
- **Player2**: BMO - 3.701 s  
- **Player3**: Steven - 1.133 s  
- **Player5**: Mordecai - 3.699 s  

**Total Time for Marceline:**
```text
16.899 + 3.701 + 1.133 + 3.699 = 25.432 seconds
```

##### Dipper:
- **Player4**: Marceline - 8.699 s  
- **Player6**: Quico - 5.300 s  
- **Player7**: Naruto - 1.834 s  
- **Player8**: Ben10 - 11.935 s  

**Total Time for Dipper:**
```text
8.699 + 5.300 + 1.834 + 11.935 = 27.768 seconds
```
---

#### New Setup Photo
![AI-Optimized Setup](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/ai-optimized-setup.jpg)

---

### Visual Comparison and Script Execution

The following video showcases the **Original Setup** versus the **AI-Optimized Setup**. Observe how the changes in the marble arrangement impact the race dynamics.

### Side-by-Side Comparison Video
[Watch the Comparison Video on Google Drive](https://drive.google.com/file/d/1fcl16KqnHXeUDdfe-ZsutFwzEGX08mVZ/view?usp=sharing)

In addition, this video includes a demonstration of the script `generate-videos-jammable.py` in action. 

#### Script Execution Video
[Watch the Script in Action](https://drive.google.com/file/d/1G8Z9XosDuK4ynH42xNVoTrqoVpYtK2DT/view?usp=sharing)

---

### Key Takeaways

1. The AI-optimized setup resulted in:
   - More balanced team times.
   - A visually engaging and competitive race.
2. The integration of **ChatGPT** allowed for:
   - Simplified decision-making in marble assignments.
   - Increased flexibility in workflow.

The optimization process demonstrates the scalability and adaptability of **CanicasBrawl** for dynamic content creation.

---

### Additional Support Diagrams

To conclude, here are two additional diagrams highlighting valuable scripts that enhance the understanding of **CanicasBrawl's** functionality: 

#### 1. Winner Log Generation (`WinnerTracker.cs`)  
This diagram provides a visual overview of the `WinnerTracker.cs` script in Unity. It showcases how the script tracks the current race leader in real time and logs transitions in leadership to the `winner_log.csv` file.  
The diagram highlights interactions with `WinnerDetector`, ensuring accurate data capture for post-race analytics.  
[Winner Log Generation Diagram](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/WinnerTracker.png)

#### 2. Final Audio Creation (`create_final_audio`)  
This diagram illustrates how the `create_final_audio` function processes audio tracks to align them with race data.  
It overlays normalized player segments with an instrumental track to create the final race audio.  
This process ensures that each race has a unique and dynamic soundtrack.  
[Final Audio Creation Diagram](https://github.com/jesusgomeznuz/canicasbrawl/blob/master/assets/create_final_audio.png)

---

## Contact
- **Name:** Jesús Gómez
- **Email:** info@canicasbrawl
- **Discord:** jesus.gomeznz

---

## Next Steps
1. **Optimize Game Design for Flexibility**  
   Simplify the player data system to make it easier to add new players and modify backgrounds. Focus on creating a dynamic level generation system by incorporating common obstacle patterns and varying their order of appearance. This will keep levels fresh and engaging while making future updates and changes more manageable.

2. **Automate Voice Generation**  
   Develop scripts to automate the extraction and generation of new character voices. This involves diarizing YouTube videos to isolate voice segments based on a character's appearance, sending these segments to an audio bank, and processing them into usable voice files. This approach will ensure a steady stream of new voices, identify fan favorites, and maintain audience interest.

3. **Enable User-Generated Videos**  
   Work on simplifying the video creation process for users. This feature will allow users to input converted audio files, set up marble races, and have tracks dynamically update based on which player is in the lead. Making this process more accessible will broaden engagement and enhance user experience.


---
