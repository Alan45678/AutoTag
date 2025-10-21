

# AutoTag User Guide

## Introduction

AutoTag is a tool that automatically analyzes MP3 audio files to predict their musical genres (e.g., Classical, Rock) and moods (e.g., Happy, Sad) using machine learning models. It processes audio files, adds predictions as metadata tags to the MP3 files, and saves detailed results to text files. This guide explains how to set up and use AutoTag to tag your music collection, even if you're not a developer.

### What AutoTag Does
- **Loads Audio**: Reads MP3 files from a folder (e.g., `data/`).
- **Predicts Genres/Moods**: Uses pre-trained models to identify genres and moods.
- **Tags Files**: Adds predictions to MP3 files as metadata (e.g., "GENRE_AUTO" or "HUMEUR_1").
- **Saves Results**: Writes detailed reports to `result/genre_result.txt` and `result/mood_result.txt`.
- **Logs Progress**: Records execution details in `result/log.txt`.

### Who This Guide Is For
- Music enthusiasts wanting to organize their MP3 collection.
- Developers or researchers needing automated genre/mood tagging.
- Anyone curious about audio analysis with minimal setup.

## Prerequisites

Before using AutoTag, ensure you have:
- **Python 3.10** installed (download from [python.org](https://www.python.org/downloads/)).
- **FFmpeg** installed (required for audio processing):
  - Ubuntu: Run `sudo apt-get install ffmpeg`.
  - macOS: Run `brew install ffmpeg`.
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
- MP3 files in the `data/` folder (e.g., `Beethoven - Quatuor à Cordes No. 14 En Do Diese Mineur, Op. 131.mp3`).
- Model files in the `models/` folder (e.g., `discogs-effnet-bs64-1.pb`, `genre_discogs400-discogs-effnet-1.json`).

## Setup

### Step 1: Get the Project
If you have the project folder (`AUTO_TAG/`), skip to Step 2. Otherwise:
1. Clone or download the project from its repository (if available):
   ```bash
   git clone https://github.com/your-username/auto_tag.git
   cd AUTO_TAG
   ```
2. Ensure the folder contains:
   - `main.py`, `config.json`, `src/`, `data/`, `models/`, `result/`.

### Step 2: Install Dependencies
1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install required Python libraries:
   ```bash
   pip install essentia mutagen numpy tqdm
   ```
   If you have a `requirements.txt`, use:
   ```bash
   pip install -r requirements.txt
   ```

### Step 3: Prepare Your Music Files
- Place MP3 files in the `data/` folder. Examples included:
  - `Aphex Twin - Xtal.mp3`
  - `Vitalic - Poison Lips.mp3`
  - `Supreme Ntm - Pose Ton Gun.mp3`
- Ensure the `models/` folder contains the necessary model files (e.g., `.pb` and `.json` files like `genre_discogs400-discogs-effnet-1.pb`).

### Step 4: Configure AutoTag
AutoTag uses a configuration file (`config.json`) to define how it processes audio. You can use the default settings or customize them.

#### Using the Default Configuration
The project includes a `config.json` file. If it’s set up, you can skip to running the pipeline. A typical configuration looks like:
```json
{
  "pipelines": [
    {
      "name": "genre",
      "data_folder": "data",
      "embedding_model_path": "models/discogs-effnet-bs64-1.pb",
      "prediction_model_path": "models/genre_discogs400-discogs-effnet-1.pb",
      "metadata_path": "models/genre_discogs400-discogs-effnet-1.json",
      "result_file_path": "result/genre_result.txt",
      "tags_to_write": ["GENRE_AUTO", "COMMENT"],
      "threshold": 0.1,
      "input_node": "serving_default_model_Placeholder",
      "output_node": "PartitionedCall"
    },
    {
      "name": "mood",
      "data_folder": "data",
      "embedding_model_path": "models/discogs-effnet-bs64-1.pb",
      "prediction_model_path": "models/mtg_jamendo_moodtheme-discogs-effnet-1.pb",
      "metadata_path": "models/mtg_jamendo_moodtheme-discogs-effnet-1.json",
      "result_file_path": "result/mood_result.txt",
      "tags_to_write": ["TXXX:HUMEUR_1"],
      "threshold": 0.15,
      "min_freq": 5,
      "min_score": 0.07,
      "max_labels": 5,
      "input_node": "model/Placeholder",
      "output_node": "model/Sigmoid"
    }
  ]
}
```

#### Customizing Configuration
To change settings (e.g., output file names or thresholds):
1. Open `config.json` in a text editor.
2. Adjust parameters:
   - `"data_folder"`: Folder with your MP3s (default: `"data"`).
   - `"result_file_path"`: Where results are saved (e.g., `"result/my_genres.txt"`).
   - `"tags_to_write"`: Metadata tags to add to MP3s (e.g., `["GENRE_AUTO"]` for genres).
   - `"threshold"`: Minimum confidence for predictions (higher = stricter).
3. Save the file.

If `config.json` is missing, copy the example above to `AUTO_TAG/config.json`.

## Running AutoTag

1. Activate your virtual environment (if used):
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Run the pipeline:
   ```bash
   python main.py
   ```
3. Monitor progress:
   - A progress bar shows the number of files processed (e.g., `Processing MP3 files (genre): 100%|██████████| 10/10`).
   - Logs are written to `result/log.txt`.

## Understanding Outputs

AutoTag produces three types of outputs:

### 1. MP3 Metadata Tags
- Predictions are added to MP3 files in `data/` as ID3 tags.
- Example:
  - File: `Beethoven - Quatuor à Cordes No. 14 En Do Diese Mineur, Op. 131.mp3`
  - Tags added:
    - `GENRE_AUTO`: "Classical ; Chamber Music"
    - `TXXX:HUMEUR_1`: "Calm ; Reflective"
- View tags using a media player like VLC or a tag editor like Mp3tag.

### 2. Result Files
- **Genre Results**: Saved in `result/genre_result.txt`.
  - Example:
    ```
    Analyzed file: Beethoven - Quatuor à Cordes No. 14 En Do Diese Mineur, Op. 131.mp3
    Normalized results:
    =====================================
    Label                                         | Count | Freq (%) | Mean Score
    --------------------------------------------------------------------------------
    Classical                                    |    60 |    75.00 |    0.9000
    Chamber Music                                |    20 |    25.00 |    0.6500
    =====================================
    Genres assigned: Classical ; Chamber Music
    ================================================================================
    ```
- **Mood Results**: Saved in `result/mood_result.txt`.
  - Example:
    ```
    Analyzed file: Aphex Twin - Xtal.mp3
    Relevant labels (frequency >= 5 and mean score >= 0.07):
    =====================================
    Dreamy          | Frequency: 10   | Mean score: 0.8200
    Ambient         | Frequency: 8    | Mean score: 0.7500
    =====================================
    Moods assigned: Dreamy ; Ambient
    ================================================================================
    ```

### 3. Log File
- Execution details are saved in `result/log.txt`.
- Example:
  ```
  2025-04-12 10:00:00,123 - INFO - Running pipeline: genre
  2025-04-12 10:00:05,789 - INFO - Processing MP3 files (genre): 100%|██████████| 10/10 [00:10<00:00,  1.00file/s]
  2025-04-12 10:00:06,456 - INFO - Running pipeline: mood
  ```

## Troubleshooting

- **Error: "FFmpeg not found"**:
  - Ensure FFmpeg is installed and accessible in your PATH.
  - Test with: `ffmpeg -version`.
- **Error: "Model file not found"**:
  - Verify that `.pb` and `.json` files are in `models/` (e.g., `discogs-effnet-bs64-1.pb`).
- **No tags added to MP3s**:
  - Check `config.json` for correct `tags_to_write` (e.g., `["GENRE_AUTO"]`).
  - Ensure MP3 files are not read-only.
- **Empty result files**:
  - Confirm that `data/` contains valid MP3 files.
  - Check `result/log.txt` for errors.
- **Slow processing**:
  - Large MP3 files or low CPU power may increase runtime.
  - Reduce `sample_rate` in `config.json` (e.g., from 16000 to 8000) for faster processing, but this may affect accuracy.

## Tips
- **Organize Your Music**: Move MP3s to `data/` before running to process specific albums or artists.
- **Experiment with Thresholds**: Increase `threshold` in `config.json` (e.g., to 0.2) for stricter predictions, or lower it for more labels.
- **Backup Files**: AutoTag modifies MP3s by adding tags. Copy `data/` before running if you want to preserve originals.
- **Check Results**: Open `result/genre_result.txt` to verify predictions before tagging all files.

## Further Customization
- **Add New Models**: Place additional `.pb` and `.json` files in `models/` and update `config.json`.
- **Change Tags**: Modify `tags_to_write` to use different ID3 tags (e.g., `["TXXX:MY_MOOD"]`).
- **Adjust Filters**: For mood predictions, tweak `min_freq`, `min_score`, or `max_labels` in `config.json` to control output.

## Contact
For issues or questions, check the [README.md](README.md) or contact the project maintainer (if shared publicly, open a GitHub issue at `https://github.com/your-username/auto_tag/issues`).

---

Happy tagging with AutoTag!

