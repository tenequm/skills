---
name: audio-quality-check
description: Analyze audio recording quality - echo detection, loudness, speech intelligibility, SNR, spectral analysis. Use when the user wants to check a recording's quality, detect echo or duplication in audio files, measure speech clarity, compare original vs processed audio, diagnose why a recording sounds bad, or analyze audio tracks from Blackbox or any call recording app. Triggers on audio quality, recording analysis, echo detection, check recording, sound quality, analyze audio, speech quality, PESQ, STOI, loudness, SNR, audio diagnostics, recording sounds bad, echo in recording, audio duplication.
metadata:
  version: "0.1.0"
---

# Audio Recording Quality Analyzer

Comprehensive audio quality analysis for call recordings. Handles dual-track M4A files (system audio + mic), single-track recordings, and AEC-processed files.

## Quick Start

Run the bundled analysis script on a recording directory:

```bash
python <skill-path>/scripts/analyze_recording.py "/path/to/recording/directory"
```

Modes for focused analysis:
```bash
python <skill-path>/scripts/analyze_recording.py /path --tracks   # track info only
python <skill-path>/scripts/analyze_recording.py /path --echo     # echo detection only
python <skill-path>/scripts/analyze_recording.py /path --quality  # quality metrics (skip echo)
```

For Blackbox recordings, the directory is typically:
`~/Library/Application Support/Blackbox/Recordings/<timestamp-id>/`

## Dependencies

System: `ffmpeg`, `ffprobe` (brew install ffmpeg)
Python: `numpy`, `soundfile`, `scipy`, `pyloudnorm`, `pesq`, `pystoi`, `librosa`

Install all Python deps: `pip3 install numpy soundfile scipy pyloudnorm pesq pystoi librosa`

## What Each Metric Tells You

### EBU R128 Loudness (pyloudnorm)
- **What**: Perceptual loudness in LUFS (Loudness Units Full Scale)
- **Target**: -16 to -24 LUFS for speech
- **Watch for**: AEC/post-processed tracks being significantly louder than originals (indicates the processing is amplifying without normalizing)

### Echo Detection - Autocorrelation
- **What**: Detects delayed copies of the signal within a single track by correlating the signal with itself at various time offsets
- **How to read**: Peaks in the 20-100ms range with correlation > 0.3 indicate signal duplication. The lag tells you the delay of the duplicate copy
- **Key insight**: If you see a consistent peak at the same lag across multiple time segments, that's a systematic duplication (e.g., a virtual audio processor like Krisp introducing a delayed copy at ~53ms)
- **Normal values**: Peaks below 0.15 are typically speech pitch harmonics (harmless). Peaks above 0.3 at consistent lags are echo

### Cross-Track Correlation
- **What**: Measures how much one track's content appears in another (e.g., system audio bleeding into the mic track)
- **How to read**: Values near 0 mean no bleed. Values above 0.1 indicate the mic is picking up system audio
- **Coherence**: Frequency-domain version of the same test. Voice-band coherence (300-3400Hz) is most relevant for speech echo

### PESQ - Speech Quality (requires reference + degraded)
- **What**: ITU-T P.862 standard. Gives a MOS (Mean Opinion Score) comparing a degraded signal against a reference
- **Scale**: 1.0 (bad) to 4.5 (excellent). NB = narrowband (phone quality), WB = wideband
- **Use for**: Comparing AEC-processed mic vs original mic to see if processing helps or hurts
- **Thresholds**: 4.0+ excellent, 3.0+ good, 2.5-3.0 fair, <2.5 poor

### STOI - Speech Intelligibility (requires reference + degraded)
- **What**: Short-Time Objective Intelligibility. Measures how understandable speech remains after processing
- **Scale**: 0.0 to 1.0
- **Thresholds**: >0.8 good, >0.6 fair, <0.6 poor
- **Key insight**: If STOI drops significantly between original and processed, the processing is degrading intelligibility

### Spectral Analysis (librosa)
- **Centroid**: Average frequency weighted by amplitude. Higher = brighter/harsher audio
- **Rolloff (85%)**: Frequency below which 85% of spectral energy sits. Lower = more bass-heavy
- **Zero-crossing rate**: How often the signal crosses zero. Higher = noisier signal. Speech is typically 0.05-0.20; values above 0.30 suggest significant noise

### SNR - Signal-to-Noise Ratio
- **What**: Ratio of speech energy to background noise energy (estimated via energy-based VAD)
- **Thresholds**: >20dB excellent, >15dB good, >10dB fair, <10dB poor
- **Note**: This measures background noise, not echo. A recording can have excellent SNR but still have echo problems

### Per-Minute Energy
- **What**: RMS energy and voice-band energy per minute of recording
- **Use for**: Spotting segments that went silent (mic cut out), got unexpectedly loud (clipping risk), or had activity patterns that help identify when speakers were active

## Manual Analysis Recipes

When you need analysis beyond what the script provides, these patterns are useful.

### Extract individual tracks from dual-track M4A
```bash
ffmpeg -y -i audio.m4a -map 0:0 -ac 1 -ar 16000 /tmp/system.wav
ffmpeg -y -i audio.m4a -map 0:1 -ac 1 -ar 16000 /tmp/mic.wav
```

### Quick loudness check with sox
```bash
sox audio.wav -n stat 2>&1
```

### Check specific time range for echo (Python)
```python
import numpy as np
import soundfile as sf
from scipy import signal

data, sr = sf.read('/tmp/system.wav')
# Analyze 5 seconds starting at 2 minutes
start = 120 * sr
seg = data[start:start + 5*sr]
seg_norm = seg / (np.max(np.abs(seg)) + 1e-10)
autocorr = np.correlate(seg_norm, seg_norm, mode='full')
mid = len(seg_norm) - 1
autocorr = autocorr / autocorr[mid]
# Check 20-100ms range for echo peaks
min_lag = int(0.020 * sr)
max_lag = int(0.100 * sr)
region = autocorr[mid + min_lag:mid + max_lag]
peaks, props = signal.find_peaks(region, height=0.1)
for i, p in enumerate(peaks[:5]):
    lag_ms = (p + min_lag) / sr * 1000
    print(f"  Peak at {lag_ms:.1f}ms, r={props['peak_heights'][i]:.3f}")
```

## Common Issues and What Causes Them

| Symptom | Likely cause | What to check |
|---------|-------------|---------------|
| Speakers sound slightly doubled/echoed | Virtual audio processor (Krisp) creating delayed copy in system audio | Autocorrelation: consistent peak at 40-60ms |
| Mic track has remote speakers' voices | Acoustic echo (speakers to mic) | Cross-track correlation > 0.1 |
| AEC-processed file sounds worse | DTLN-aec degrading signal quality | PESQ/STOI comparing original vs processed |
| AEC-processed file is too loud | Missing loudness normalization after processing | Loudness: processed > -10 LUFS |
| Recording has hiss/noise | Low SNR, noisy mic, or AGC artifacts | SNR < 15dB, high zero-crossing rate |
| Quiet segments mid-recording | Mic cut out or device changed | Per-minute energy: sudden RMS drop |
