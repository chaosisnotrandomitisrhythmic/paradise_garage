"""Librosa structural analysis → candidate DJ cue points.

Detects, in seconds from the start of the track:
  - IN     : first sustained low-band (<160 Hz) energy = the groove/bass entry
  - BREAK  : the deepest sustained RMS dip in the body = a breakdown
  - OUT    : where energy starts its final sustained decline = the outro

These are rough, heuristic anchors meant to be grid-snapped and then fine-tuned
by ear in Traktor — not surgical. Returns [(label, time_sec), ...].
"""

import librosa
import numpy as np

N_FFT = 2048
HOP = 512


def analyze_structure(path: str) -> dict:
    y, sr = librosa.load(path, sr=None, mono=True)
    dur = float(librosa.get_duration(y=y, sr=sr))

    S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=HOP)

    rms = librosa.feature.rms(S=S, hop_length=HOP)[0]
    low_rms = np.sqrt(np.mean(S[freqs < 160] ** 2, axis=0))

    win = max(1, int(sr / HOP * 2))  # ~2 s smoothing
    kernel = np.ones(win) / win
    rms_s = np.convolve(rms, kernel, mode="same")
    low_s = np.convolve(low_rms, kernel, mode="same")

    # first downbeat-ish anchor (first detected beat) for the grid fallback
    _, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=HOP)
    first_beat = float(librosa.frames_to_time(beats[0], sr=sr, hop_length=HOP)) if len(beats) else 0.0

    # IN: first frame past ~2 s where low-band energy crosses 40% of its strong level
    low_thr = 0.4 * np.percentile(low_s, 90)
    in_t = next((times[i] for i in range(len(low_s)) if low_s[i] > low_thr and times[i] > 2), first_beat)

    # BREAK: deepest RMS dip in the body (25–85%)
    body = (times > dur * 0.25) & (times < dur * 0.85)
    masked = np.where(body, rms_s, np.inf)
    break_t = float(times[int(np.argmin(masked))]) if body.any() else dur * 0.5

    # OUT: in the last 30%, first sustained drop below 50% of the median level
    med = float(np.median(rms_s))
    out_t = next((times[i] for i in range(len(rms_s)) if times[i] > dur * 0.7 and rms_s[i] < 0.5 * med),
                 dur * 0.9)

    cues = [("IN", float(in_t)), ("BREAK", float(break_t)), ("OUT", float(out_t))]
    return {"duration_sec": dur, "first_beat_sec": first_beat, "cues": cues}
