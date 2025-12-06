# Signal Filtering Web Demo

A small FastAPI + static frontend demo that accepts an audio file (or uses a default/synthetic signal), adds noise, applies a low-pass Butterworth filter, and returns waveform images (original / noisy / filtered) as embedded PNG data-URLs.

This repository contains a lightweight backend (FastAPI) and a minimal static frontend. It's intended for demonstration and experimentation with simple DSP operations and visualization.

## Features

- Upload an audio file (wav/ogg/mp3, etc.) and receive 3 waveform images: original, noisy, and filtered.
- A default endpoint that processes a bundled audio file or a generated synthetic tone if the file isn't present.
- Static frontend served by the same FastAPI app (so UI and API share origin).

## How it works (brief)

1. The backend receives an audio file via `POST /process-audio/` (or uses a default file for `GET /process-default`).
2. Audio is read with `soundfile` and converted to mono if needed; samples are normalized.
3. Random Gaussian noise is added to create a 'noisy' signal.
4. A Butterworth low-pass filter (SciPy) is applied to the noisy signal to create the filtered version.
5. The server generates PNG plots for each signal, encodes them as base64 data-URLs, and returns them in JSON. The frontend displays them directly in `<img>` elements.

## Requirements

- Python 3.10+ recommended
- See `requirements.txt` for the minimal Python packages used (FastAPI, uvicorn, numpy, scipy, matplotlib, soundfile, python-multipart, ...).

## Quick setup (local)

1. Create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Run the app with uvicorn from the repository root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open the frontend in your browser:

```
http://localhost:8000/
```

The frontend includes an upload form and an example button which calls the server endpoints.

## API Endpoints

- `GET /process-default` — process a default audio file included in the repo (if present) or a synthetic signal; returns JSON with base64 PNG data-URLs.

- `POST /process-audio/` — accepts a multipart file upload (field name `file`) and returns JSON with the three images.

Example curl to use default processing (GET):

```bash
curl http://localhost:8000/process-default
```

Example curl to upload a file:

```bash
curl -F "file=@/path/to/your/audio.wav" http://localhost:8000/process-audio/ -o response.json

# The returned JSON contains `original_plot`, `noisy_plot`, `filtered_plot` as data URLs.
```

## Where outputs go

- The app creates temporary files during processing and cleans them up. There is a top-level `backend/outputs/` directory (created automatically) used for temporary storage while processing.
- If you want to keep generated PNGs on disk, modify `backend/main.py` to save into a persistent location instead of encoding then deleting.

## Customization

- Adjust noise amplitude by editing `add_noise()` in `backend/main.py`.
- Change filter cutoff frequency or order in the `lowpass_filter()` call inside `process_audio_file()`.
- Change the number of plotted samples (`zoom_samples`) when calling `save_signal_plot()` or `draw_signals()`.

## Troubleshooting

- If `soundfile` fails to read a format, ensure the required system codecs / libs are installed (libsndfile). On Linux: `sudo apt install libsndfile1` (or equivalent for your distro).
- If plotting fails in headless environments, you may need to set a non-interactive matplotlib backend (the code currently uses the default backend which works for many setups). Example: set `MATPLOTLIBRC` or add `matplotlib.use('Agg')` early in `backend/main.py`.

## File structure (relevant)

```
backend/
  main.py        # FastAPI app + DSP processing
  outputs/       # temporary outputs (created automatically)
frontend/
  index.html     # static frontend
  include/assets/
    css/style.css
    js/main.js
requirements.txt
README.md        # <-- this file
```

## Credits

Made by SeifElden Hamdy — seifeldenhamdy@gmail.com — 01032484794

---

If you'd like, I can also:

- Add an example `docker-compose` for easy local development.
- Improve the frontend UI or translate it back to Arabic.
- Save generated PNGs to disk for debugging.

Tell me which of those you'd like next.
