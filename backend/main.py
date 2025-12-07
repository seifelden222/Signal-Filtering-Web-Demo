import os
import uuid
import base64
import tempfile
import shutil
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
import soundfile as sf 
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse




def load_audio_file(file_path):
    """
    Read an audio file from the specified path and return:
    - t: time axis
    - signal: mono audio signal
    - sample_rate: sampling rate
    """
    data, sample_rate = sf.read(file_path)

    # If the file is stereo (two channels), convert to mono by averaging
    if data.ndim > 1:
        data = data.mean(axis=1)

    # Normalize (optional)
    max_val = np.max(np.abs(data))
    if max_val > 0:
        data = data / max_val

    # Time axis
    duration = len(data) / sample_rate
    t = np.linspace(0, duration, num=len(data), endpoint=False)

    return t, data, sample_rate


def simple_signal_processing(sample_rate=44100, duration=1.0):
    """
    Generate a simple sine wave (if you want to test without an audio file)
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    freq = 440  # Hz
    signal = np.sin(2 * np.pi * freq * t)
    return t, signal, sample_rate


def add_noise(original_signal, noise_amplitude=0.3):
    """
    Add random noise to the signal
    
    Parameters:
    - original_signal: input signal array
    - noise_amplitude: standard deviation of Gaussian noise
    
    Returns:
    - noisy_signal: signal with added noise
    """
    if noise_amplitude < 0:
        raise ValueError(f"Noise amplitude must be non-negative, got {noise_amplitude}")
    
    noise = noise_amplitude * np.random.normal(size=original_signal.shape)
    noisy_signal = original_signal + noise
    return noisy_signal


def lowpass_filter(signal, sample_rate=44100, cutoff_freq=1000, filter_order=5):
    """
    Apply a Butterworth low-pass filter to the signal
    
    Parameters:
    - signal: input signal array
    - sample_rate: sampling rate in Hz
    - cutoff_freq: cutoff frequency in Hz (must be less than Nyquist frequency)
    - filter_order: filter order (higher = steeper roll-off)
    
    Returns:
    - filtered_signal: the filtered signal
    """
    nyquist = 0.5 * sample_rate
    
    # Validate cutoff frequency
    if cutoff_freq <= 0:
        raise ValueError(f"Cutoff frequency must be positive, got {cutoff_freq} Hz")
    if cutoff_freq >= nyquist:
        raise ValueError(f"Cutoff frequency {cutoff_freq} Hz must be less than Nyquist frequency {nyquist} Hz")
    
    normal_cutoff = cutoff_freq / nyquist
    
    # Design Butterworth filter
    b, a = butter(filter_order, normal_cutoff, btype='low', analog=False)
    
    # Apply zero-phase filtering (forward and backward)
    filtered_signal = filtfilt(b, a, signal)
    
    return filtered_signal


def draw_signals(t, original_signal, noisy_signal, filtered_signal, zoom_samples=5000):
    """
    Plot the signals: original, noisy, and filtered
    zoom_samples: number of points to display in the plot
    """
    n = min(zoom_samples, len(t))

    plt.figure(figsize=(12, 8))

    plt.subplot(3, 1, 1)
    plt.plot(t[:n], original_signal[:n])
    plt.title('Original Signal')
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')
    plt.grid()

    plt.subplot(3, 1, 2)
    plt.plot(t[:n], noisy_signal[:n])
    plt.title('Noisy Signal')
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')
    plt.grid()

    plt.subplot(3, 1, 3)
    plt.plot(t[:n], filtered_signal[:n])
    plt.title('Filtered Signal')
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')
    plt.grid()

    plt.tight_layout()
    # This function draws the 3-panel figure but does not save it here.
    return plt


def save_signal_plot(t, signal, title, out_path, zoom_samples=5000):
    """Save a single-signal plot to `out_path`."""
    n = min(zoom_samples, len(t))
    fig = plt.figure(figsize=(12, 3.5))
    plt.plot(t[:n], signal[:n])
    plt.title(title)
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')
    plt.grid()
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Saved plot to: {out_path}")


# --------------- FASTAPI SETUP ----------------- #


script_dir = os.path.dirname(__file__)
outputs_dir = os.path.join(script_dir, "outputs")
os.makedirs(outputs_dir, exist_ok=True)

app = FastAPI()

app.mount("/outputs", StaticFiles(directory=outputs_dir), name="outputs")

# Serve the frontend static files (so UI and backend share the same origin)
frontend_dir = os.path.join(script_dir, "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

# Allow requests from common local dev origins (Live Server, etc.)
# During development allow all origins to avoid CORS issues (file:// or Live Server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_audio_file(audio_path: str):
    """Process audio and return image data URLs for original, noisy and filtered signals.

    This creates a temporary directory, writes three PNGs with fixed names
    (`original.png`, `noisy.png`, `filtered.png`), reads them, encodes as
    data URLs, then deletes the temp directory before returning. This ensures
    frontend can directly use returned data URLs and server does not keep files.
    """
    if os.path.exists(audio_path):
        t, original_signal, sample_rate = load_audio_file(audio_path)
        kind = "audio"
    else:
        t, original_signal, sample_rate = simple_signal_processing()
        kind = "synthetic"

    noisy_signal = add_noise(original_signal, noise_amplitude=0.3)
    filtered_signal = lowpass_filter(
        noisy_signal,
        sample_rate=sample_rate,
        cutoff_freq=3000,
        filter_order=5,
    )

    # create temp dir to hold images
    temp_dir = tempfile.mkdtemp(prefix="proc_")
    try:
        out_orig = os.path.join(temp_dir, "original.png")
        out_noisy = os.path.join(temp_dir, "noisy.png")
        out_filt = os.path.join(temp_dir, "filtered.png")

        save_signal_plot(t, original_signal, "Original Signal", out_orig, zoom_samples=5000)
        save_signal_plot(t, noisy_signal, "Noisy Signal", out_noisy, zoom_samples=5000)
        save_signal_plot(t, filtered_signal, "Filtered Signal", out_filt, zoom_samples=5000)

        def _encode(path):
            with open(path, "rb") as fh:
                data = fh.read()
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:image/png;base64,{b64}"

        orig_data = _encode(out_orig)
        noisy_data = _encode(out_noisy)
        filt_data = _encode(out_filt)

    finally:
        # remove temp dir and files
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: failed to remove temp dir {temp_dir}: {e}")

    return {
        "kind": kind,
        "original_plot": orig_data,
        "noisy_plot": noisy_data,
        "filtered_plot": filt_data,
    }

# --------------- ROUTES / ENDPOINTS ------------ #

@app.get("/process-default")
def process_default():
    """Endpoint to process a default audio file or synthetic signal."""
    script_dir = os.path.dirname(__file__)
    audio_path = os.path.join(script_dir, "WhatsApp Ptt 2025-11-24 at 4.51.36 PM.ogg")

    result = process_audio_file(audio_path)
    return JSONResponse(content=result)

@app.post("/process-audio/")
async def upload_and_process(file: UploadFile = File(...)):  
    # create a temporary directory to store the uploaded file
    temp_dir = os.path.join(outputs_dir, f"temp_{uuid.uuid4().hex}")
    os.makedirs(temp_dir, exist_ok=True)

    temp_path = os.path.join(temp_dir, file.filename)
    try:
        # save uploaded file
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # process the saved file
        result = process_audio_file(temp_path)

    except Exception as e:
        # cleanup on error
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.isdir(temp_dir):
                os.rmdir(temp_dir)
        except Exception:
            pass
        return JSONResponse(content={"error": str(e)}, status_code=500)

    # try to remove temp file and directory (best-effort)
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.isdir(temp_dir):
            os.rmdir(temp_dir)
    except Exception as e:
        print(f"Error deleting temp file/dir: {e}")

    return JSONResponse(content=result)
