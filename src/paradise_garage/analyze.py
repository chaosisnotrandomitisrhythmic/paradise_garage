import librosa
import numpy as np

CAMELOT_WHEEL = {
    ("C", "major"): "8B",  ("A", "minor"): "8A",
    ("G", "major"): "9B",  ("E", "minor"): "9A",
    ("D", "major"): "10B", ("B", "minor"): "10A",
    ("A", "major"): "11B", ("F#", "minor"): "11A",
    ("E", "major"): "12B", ("C#", "minor"): "12A",
    ("B", "major"): "1B",  ("G#", "minor"): "1A",
    ("F#", "major"): "2B", ("D#", "minor"): "2A",
    ("Db", "major"): "3B", ("Bb", "minor"): "3A",
    ("Ab", "major"): "4B", ("F", "minor"): "4A",
    ("Eb", "major"): "5B", ("C", "minor"): "5A",
    ("Bb", "major"): "6B", ("G", "minor"): "6A",
    ("F", "major"): "7B",  ("D", "minor"): "7A",
    ("Gb", "major"): "2B", ("Eb", "minor"): "2A",
    ("C#", "major"): "3B",
}

PITCH_CLASSES_MAJOR = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
PITCH_CLASSES_MINOR = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]


def detect_bpm(y, sr):
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(np.atleast_1d(tempo)[0])
    return round(bpm, 1)


def detect_key(y, sr):
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)

    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    best_corr = -1
    best_key = "C"
    best_mode = "major"

    for shift in range(12):
        rolled = np.roll(chroma_mean, -shift)
        maj_corr = np.corrcoef(rolled, major_profile)[0, 1]
        min_corr = np.corrcoef(rolled, minor_profile)[0, 1]

        if maj_corr > best_corr:
            best_corr = maj_corr
            best_key = PITCH_CLASSES_MAJOR[shift]
            best_mode = "major"
        if min_corr > best_corr:
            best_corr = min_corr
            best_key = PITCH_CLASSES_MINOR[shift]
            best_mode = "minor"

    camelot = CAMELOT_WHEEL.get((best_key, best_mode), "?")
    return best_key, best_mode, camelot


def detect_energy(y, sr):
    rms = librosa.feature.rms(y=y)[0]
    avg_rms = float(np.mean(rms))
    if avg_rms > 0.15:
        return "high"
    elif avg_rms > 0.07:
        return "mid"
    return "low"


def analyze_track(path: str) -> dict:
    y, sr = librosa.load(path, sr=None, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    bpm = detect_bpm(y, sr)
    key, mode, camelot = detect_key(y, sr)
    energy = detect_energy(y, sr)

    return {
        "bpm": bpm,
        "key": key,
        "mode": mode,
        "camelot": camelot,
        "energy": energy,
        "duration_sec": round(duration, 1),
        "sample_rate": sr,
    }
