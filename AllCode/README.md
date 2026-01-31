# AllCode – Video pipeline

Creates a final video: green-screen narrator + spinning text background + audio.

## Folder layout

| Folder       | Purpose                                      |
|-------------|----------------------------------------------|
| **NaratorMp4**  | Put your green-screen video here (.mp4)      |
| **SoundFile**   | Put your audio here (.m4a, .mp3, or .wav)    |
| **Temp**        | Manim output, intermediate files             |
| **FinishedMp4** | Final video with audio                       |

## Setup

```bash
cd AllCode
pip install -r requirements.txt
```

## Usage

1. Put your green-screen narrator video in `NaratorMp4/`
2. Put your audio in `SoundFile/`
3. Edit `FinalEdits_settings.json` for text content and style
4. Run:

```bash
python run_all.py
```

Output: `FinishedMp4/final_output_with_audio.mp4`

## Step by step

- **Manim only:** `manim -p FinalEdits.py FinalEdits`
- **Composite only** (if background already exists in Temp): `python create_final_video.py`
