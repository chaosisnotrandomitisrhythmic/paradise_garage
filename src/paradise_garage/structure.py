"""Librosa structural analysis → mixable DJ cue points (seconds from start).

Cues are chosen to be useful for *mixing*, not just labelling structure:
  - IN      : groove/bass entry — load + beatmatch cue
  - MIX IN  : first sustained full-energy downbeat — where you bring the fader up
  - BREAK   : deepest sustained dip in the body — a breakdown
  - MIX OUT : ~32 bars before the track's effective end — a full phrase of runway
              to blend out while the beat is still solid (NOT the final fade)

A BPM is needed to size the MIX OUT runway in bars; pass the authoritative grid
BPM if you have it, else it's estimated. Cues are rough anchors to fine-tune by ear.
"""

import librosa
import numpy as np

N_FFT = 2048
HOP = 512
MIXOUT_BARS = 32          # phrase of runway before the end
MIXIN_HOLD_BARS = 2       # energy must stay "full" this long to count as the groove


def analyze_structure(path: str, bpm: float | None = None) -> dict:
    y, sr = librosa.load(path, sr=None, mono=True)
    dur = float(librosa.get_duration(y=y, sr=sr))

    S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=HOP)

    rms = librosa.feature.rms(S=S, hop_length=HOP)[0]
    low_rms = np.sqrt(np.mean(S[freqs < 160] ** 2, axis=0))
    win = max(1, int(sr / HOP * 1.5))
    kernel = np.ones(win) / win
    rms_s = np.convolve(rms, kernel, mode="same")
    low_s = np.convolve(low_rms, kernel, mode="same")

    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=HOP)
    if bpm is None:
        bpm = float(np.atleast_1d(tempo)[0]) or 120.0
    first_beat = float(librosa.frames_to_time(beats[0], sr=sr, hop_length=HOP)) if len(beats) else 0.0
    bar_sec = 4 * 60.0 / bpm

    # active (non-silent) span, relative to the track's loud level
    peak = float(np.percentile(rms_s, 85)) or 1e-9
    floor = 0.12 * peak
    active = np.where(rms_s > floor)[0]
    eff_start = float(times[active[0]]) if len(active) else 0.0
    eff_end = float(times[active[-1]]) if len(active) else dur

    fps = sr / HOP  # frames per second

    # IN — first low-band (bass) entry past the very start
    low_thr = 0.4 * float(np.percentile(low_s, 90))
    in_t = next((times[i] for i in range(len(low_s)) if low_s[i] > low_thr and times[i] >= eff_start),
                max(eff_start, first_beat))

    # MIX IN — first time energy reaches sustained "full" (held ~2 bars) after IN
    full = 0.6 * peak
    hold = max(1, int(MIXIN_HOLD_BARS * bar_sec * fps))
    mixin_t = in_t
    for i in range(len(rms_s)):
        if times[i] <= in_t + bar_sec:
            continue
        seg = rms_s[i:i + hold]
        if len(seg) and float(np.mean(seg)) >= full:
            mixin_t = float(times[i])
            break

    # BREAK — deepest dip in the body (20–85%)
    body = (times > dur * 0.20) & (times < dur * 0.85)
    break_t = float(times[int(np.argmin(np.where(body, rms_s, np.inf)))]) if body.any() else dur * 0.5

    # MIX OUT — a phrase of runway before the effective end (always mixable)
    mixout_t = max(eff_start + bar_sec, eff_end - MIXOUT_BARS * bar_sec)

    cues = [("IN", float(in_t)), ("MIX IN", float(mixin_t)),
            ("BREAK", float(break_t)), ("MIX OUT", float(mixout_t))]
    return {"duration_sec": dur, "first_beat_sec": first_beat, "bpm_est": bpm,
            "eff_end_sec": eff_end, "cues": cues}
