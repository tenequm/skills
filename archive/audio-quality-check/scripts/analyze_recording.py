#!/usr/bin/env python3
"""
Audio recording quality analyzer.

Runs a comprehensive analysis pipeline on a recording directory containing
dual-track M4A files (system audio + mic). Detects echo, measures loudness,
speech quality, intelligibility, spectral characteristics, and SNR.

Usage:
    python analyze_recording.py /path/to/recording/directory
    python analyze_recording.py /path/to/recording/directory --tracks  # track info only
    python analyze_recording.py /path/to/recording/directory --echo    # echo analysis only
    python analyze_recording.py /path/to/recording/directory --quality # quality metrics only

Dependencies: numpy, soundfile, scipy, pyloudnorm, pesq, pystoi, librosa
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def find_audio_files(recording_dir):
    """Find audio files in the recording directory."""
    d = Path(recording_dir)
    files = {}
    for name in ["audio.m4a", "audio-processed.m4a"]:
        p = d / name
        if p.exists():
            files[name] = p
    # Also check for any other audio files
    for ext in ["*.m4a", "*.wav", "*.mp3", "*.aac", "*.flac"]:
        for p in d.glob(ext):
            if p.name not in files:
                files[p.name] = p
    return files


def probe_tracks(audio_path):
    """Get track info via ffprobe. Returns list of stream dicts."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", str(audio_path)
        ],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    data = json.loads(result.stdout)
    return data.get("streams", [])


def extract_track(audio_path, track_index, output_path, target_sr=16000):
    """Extract a single track to mono WAV at target sample rate."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "quiet",
            "-i", str(audio_path),
            "-map", f"0:{track_index}",
            "-ac", "1", "-ar", str(target_sr),
            str(output_path)
        ],
        capture_output=True
    )
    return Path(output_path).exists()


def analyze_loudness(data, sr):
    """EBU R128 integrated loudness via pyloudnorm."""
    import pyloudnorm as pyln
    meter = pyln.Meter(sr)
    try:
        loudness = meter.integrated_loudness(data)
    except Exception:
        loudness = float("nan")
    return loudness


def analyze_echo_autocorrelation(data, sr, segment_duration=5, num_segments=6):
    """
    Detect echo/duplication via autocorrelation.
    Looks for peaks in the 20-100ms range (above pitch period, within echo range).
    Returns list of (time_label, lag_ms, correlation_strength) tuples.
    """
    from scipy import signal as sig

    results = []
    total_secs = len(data) / sr
    # Spread segments evenly across the recording
    step = max(1, int(total_secs / (num_segments + 1)))
    offsets = [step * (i + 1) for i in range(num_segments)]

    for start_sec in offsets:
        start = int(start_sec * sr)
        end = min(start + segment_duration * sr, len(data))
        if start >= len(data) or end - start < sr:
            continue

        seg = data[start:end]
        rms = np.sqrt(np.mean(seg ** 2))
        if rms < 0.005:
            continue  # skip silence

        seg_norm = seg / (np.max(np.abs(seg)) + 1e-10)
        autocorr = np.correlate(seg_norm, seg_norm, mode="full")
        mid = len(seg_norm) - 1
        autocorr = autocorr / (autocorr[mid] + 1e-10)

        min_lag = int(0.020 * sr)  # 20ms
        max_lag = int(0.100 * sr)  # 100ms
        region = autocorr[mid + min_lag:mid + max_lag]

        if len(region) == 0:
            continue

        peaks, props = sig.find_peaks(region, height=0.1, distance=int(0.005 * sr))
        label = f"{start_sec // 60}:{start_sec % 60:02d}"

        for i, p in enumerate(peaks[:3]):
            lag_ms = (p + min_lag) / sr * 1000
            strength = props["peak_heights"][i]
            results.append({
                "time": label,
                "lag_ms": round(lag_ms, 1),
                "correlation": round(float(strength), 4),
                "rms_db": round(20 * np.log10(rms + 1e-10), 1),
            })

    return results


def cross_correlate_tracks(data1, data2, sr, segment_duration=30, num_segments=4):
    """
    Cross-correlation between two tracks to detect echo bleed.
    Returns list of dicts with correlation strength and lag.
    """
    from scipy import signal as sig

    min_len = min(len(data1), len(data2))
    results = []
    step = max(1, int((min_len / sr) / (num_segments + 1)))

    for i in range(num_segments):
        start_sec = step * (i + 1)
        start = int(start_sec * sr)
        end = min(start + segment_duration * sr, min_len)
        if start >= min_len or end - start < sr:
            continue

        s1 = data1[start:end]
        s2 = data2[start:end]

        s1_norm = s1 / (np.max(np.abs(s1)) + 1e-10)
        s2_norm = s2 / (np.max(np.abs(s2)) + 1e-10)

        max_lag = int(0.5 * sr)
        corr = sig.correlate(s2_norm, s1_norm, mode="full")
        mid = len(s1_norm) - 1
        window = corr[mid - max_lag:mid + max_lag]

        norm_factor = np.sqrt(np.sum(s1_norm ** 2) * np.sum(s2_norm ** 2))
        if norm_factor > 0:
            window = window / norm_factor

        peak_corr = float(np.max(np.abs(window)))
        peak_lag = (int(np.argmax(np.abs(window))) - max_lag) / sr * 1000

        label = f"{start_sec // 60}:{start_sec % 60:02d}"
        results.append({
            "time": label,
            "correlation": round(peak_corr, 4),
            "lag_ms": round(peak_lag, 1),
        })

    return results


def analyze_pesq_segments(ref_data, deg_data, sr, segment_duration=30, num_segments=3):
    """PESQ speech quality score on segments. Returns list of (label, nb_score, wb_score)."""
    from pesq import pesq
    import librosa

    min_len = min(len(ref_data), len(deg_data))
    results = []
    step = max(1, int((min_len / sr) / (num_segments + 1)))

    for i in range(num_segments):
        start_sec = step * (i + 1)
        start = int(start_sec * sr)
        end = min(start + segment_duration * sr, min_len)
        if start >= min_len:
            continue

        ref = ref_data[start:end]
        deg = deg_data[start:end]

        if np.sqrt(np.mean(ref ** 2)) < 0.001:
            continue

        label = f"{start_sec // 60}:{start_sec % 60:02d}-{(start_sec + segment_duration) // 60}:{(start_sec + segment_duration) % 60:02d}"
        try:
            ref_8k = librosa.resample(ref, orig_sr=sr, target_sr=8000)
            deg_8k = librosa.resample(deg, orig_sr=sr, target_sr=8000)
            ml = min(len(ref_8k), len(deg_8k))
            nb = pesq(8000, ref_8k[:ml], deg_8k[:ml], "nb")

            ml16 = min(len(ref), len(deg))
            wb = pesq(16000, ref[:ml16], deg[:ml16], "wb")

            results.append({"time": label, "narrowband": round(nb, 2), "wideband": round(wb, 2)})
        except Exception as e:
            results.append({"time": label, "error": str(e)})

    return results


def analyze_stoi_segments(ref_data, deg_data, sr, segment_duration=30, num_segments=3):
    """STOI intelligibility score on segments."""
    from pystoi import stoi

    min_len = min(len(ref_data), len(deg_data))
    results = []
    step = max(1, int((min_len / sr) / (num_segments + 1)))

    for i in range(num_segments):
        start_sec = step * (i + 1)
        start = int(start_sec * sr)
        end = min(start + segment_duration * sr, min_len)
        if start >= min_len:
            continue

        ref = ref_data[start:end]
        deg = deg_data[start:end]

        if np.sqrt(np.mean(ref ** 2)) < 0.001:
            continue

        label = f"{start_sec // 60}:{start_sec % 60:02d}"
        try:
            score = stoi(ref, deg, sr, extended=False)
            results.append({"time": label, "stoi": round(score, 3)})
        except Exception as e:
            results.append({"time": label, "error": str(e)})

    return results


def analyze_spectral(data, sr):
    """Spectral analysis via librosa on a 30s segment from the middle."""
    import librosa

    mid = len(data) // 2
    seg = data[mid:mid + 30 * sr]
    if len(seg) < sr:
        seg = data

    centroid = librosa.feature.spectral_centroid(y=seg, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=seg, sr=sr, roll_percent=0.85)[0]
    zcr = librosa.feature.zero_crossing_rate(seg)[0]

    return {
        "centroid_hz": round(float(np.mean(centroid))),
        "rolloff_85pct_hz": round(float(np.mean(rolloff))),
        "zero_crossing_rate": round(float(np.mean(zcr)), 4),
    }


def estimate_snr(data, sr):
    """Energy-based SNR estimate using VAD (bottom 30% frames = noise)."""
    frame_len = int(0.025 * sr)
    hop = int(0.010 * sr)
    n_frames = (len(data) - frame_len) // hop

    if n_frames < 10:
        return float("nan")

    energies = np.array([
        np.sum(data[i * hop:i * hop + frame_len] ** 2) / frame_len
        for i in range(n_frames)
    ])

    energy_db = 10 * np.log10(energies + 1e-10)
    threshold = np.percentile(energy_db, 30)

    speech_energy = np.mean(energies[energy_db > threshold])
    noise_energy = np.mean(energies[energy_db <= threshold])
    snr = 10 * np.log10(speech_energy / (noise_energy + 1e-10))

    return round(float(snr), 1)


def per_minute_energy(data, sr):
    """Per-minute RMS and voice-band energy."""
    from scipy import signal as sig

    results = []
    total_mins = int(len(data) / sr / 60) + 1
    b, a = sig.butter(4, [300 / (sr / 2), min(3400, sr / 2 - 1) / (sr / 2)], btype="band")

    for m in range(total_mins):
        start = m * 60 * sr
        end = min(start + 60 * sr, len(data))
        if start >= len(data):
            break
        seg = data[start:end]
        rms = np.sqrt(np.mean(seg ** 2))
        rms_db = 20 * np.log10(rms + 1e-10)

        try:
            voice = sig.filtfilt(b, a, seg)
            voice_rms = np.sqrt(np.mean(voice ** 2))
            voice_db = 20 * np.log10(voice_rms + 1e-10)
        except Exception:
            voice_db = float("nan")

        results.append({
            "minute": m,
            "rms_db": round(float(rms_db), 1),
            "voice_db": round(float(voice_db), 1),
        })

    return results


def coherence_analysis(data1, data2, sr):
    """Frequency-domain coherence between two tracks (voice band and full band)."""
    from scipy import signal as sig

    min_l = min(len(data1), len(data2))
    f, Cxy = sig.coherence(data1[:min_l], data2[:min_l], fs=sr, nperseg=4096)

    voice_mask = (f >= 300) & (f <= 3400)
    voice_coh = float(np.mean(Cxy[voice_mask])) if np.any(voice_mask) else 0.0
    full_coh = float(np.mean(Cxy))

    return {
        "voice_band_coherence": round(voice_coh, 4),
        "full_band_coherence": round(full_coh, 4),
    }


# =============================================================
# Main pipeline
# =============================================================

def run_full_analysis(recording_dir, mode="all"):
    d = Path(recording_dir)
    if not d.is_dir():
        print(f"Error: {recording_dir} is not a directory")
        sys.exit(1)

    files = find_audio_files(recording_dir)
    if not files:
        print(f"Error: no audio files found in {recording_dir}")
        sys.exit(1)

    print("=" * 64)
    print("AUDIO QUALITY ANALYSIS REPORT")
    print(f"Directory: {recording_dir}")
    print("=" * 64)

    # Metadata
    meta_path = d / "metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        print(f"\nRecording: {meta.get('title', 'unknown')}")
        print(f"App: {meta.get('appName', 'unknown')}")
        print(f"Created: {meta.get('createdAt', 'unknown')}")
        speakers = meta.get("speakers", {})
        if speakers:
            print(f"Speakers: {', '.join(speakers.values())}")

    # ---- TRACK INFO ----
    print("\n" + "-" * 64)
    print("TRACK INFO")
    print("-" * 64)

    for name, path in files.items():
        streams = probe_tracks(path)
        print(f"\n  {name}:")
        for i, s in enumerate(streams):
            sr = s.get("sample_rate", "?")
            ch = s.get("channels", "?")
            dur = float(s.get("duration", 0))
            br = int(s.get("bit_rate", 0)) // 1000
            codec = s.get("codec_name", "?")
            layout = s.get("channel_layout", "?")
            print(f"    Track {i}: {codec} {sr}Hz {ch}ch ({layout}) {br}kbps {dur:.1f}s")

    if mode == "tracks":
        return

    # Extract tracks to temp directory for analysis
    target_sr = 16000
    tmpdir = tempfile.mkdtemp(prefix="audio_analysis_")

    # Determine primary file (audio.m4a) and processed file
    primary = files.get("audio.m4a")
    processed = files.get("audio-processed.m4a")

    if not primary:
        # Use first available file
        primary = next(iter(files.values()))

    primary_streams = probe_tracks(primary)
    is_dual_track = len(primary_streams) >= 2

    # Extract primary tracks
    tracks = {}
    print(f"\nExtracting tracks at {target_sr}Hz for analysis...")

    if is_dual_track:
        sys_path = os.path.join(tmpdir, "system.wav")
        mic_path = os.path.join(tmpdir, "mic.wav")
        extract_track(primary, 0, sys_path, target_sr)
        extract_track(primary, 1, mic_path, target_sr)
        tracks["system"] = sf.read(sys_path)
        tracks["mic"] = sf.read(mic_path)
    else:
        mono_path = os.path.join(tmpdir, "mono.wav")
        extract_track(primary, 0, mono_path, target_sr)
        tracks["mono"] = sf.read(mono_path)

    # Extract processed tracks if available
    if processed:
        proc_streams = probe_tracks(processed)
        if len(proc_streams) >= 2:
            aec_sys_path = os.path.join(tmpdir, "aec_system.wav")
            aec_mic_path = os.path.join(tmpdir, "aec_mic.wav")
            extract_track(processed, 0, aec_sys_path, target_sr)
            extract_track(processed, 1, aec_mic_path, target_sr)
            tracks["aec_system"] = sf.read(aec_sys_path)
            tracks["aec_mic"] = sf.read(aec_mic_path)

    # ---- LOUDNESS ----
    print("\n" + "-" * 64)
    print("EBU R128 LOUDNESS (target for speech: -16 to -24 LUFS)")
    print("-" * 64)

    for name, (data, sr) in tracks.items():
        loudness = analyze_loudness(data, sr)
        status = ""
        if -24 <= loudness <= -16:
            status = "[OK]"
        elif loudness < -24:
            status = "[quiet]"
        elif loudness > -10:
            status = "[TOO LOUD]"
        else:
            status = "[loud]"
        print(f"  {name:15s}: {loudness:6.1f} LUFS  {status}")

    if mode == "quality":
        # Skip echo, go to quality metrics
        pass
    else:
        # ---- ECHO DETECTION ----
        print("\n" + "-" * 64)
        print("ECHO DETECTION - AUTOCORRELATION (self-echo in each track)")
        print("Peaks > 0.3 at consistent lag = signal duplication")
        print("-" * 64)

        for name, (data, sr) in tracks.items():
            echoes = analyze_echo_autocorrelation(data, sr)
            strong = [e for e in echoes if e["correlation"] > 0.3]
            print(f"\n  {name}:")
            if not echoes:
                print("    No echo peaks detected (or track too quiet)")
            else:
                for e in echoes:
                    marker = " <<<" if e["correlation"] > 0.3 else ""
                    print(f"    [{e['time']}] {e['lag_ms']:5.1f}ms  r={e['correlation']:.4f}  (RMS={e['rms_db']}dB){marker}")

            if strong:
                # Find most common lag
                lags = [e["lag_ms"] for e in strong]
                median_lag = np.median(lags)
                print(f"    ** ECHO DETECTED: consistent peak at ~{median_lag:.0f}ms (r>{0.3})")

        # ---- CROSS-TRACK CORRELATION ----
        if is_dual_track:
            print("\n" + "-" * 64)
            print("CROSS-TRACK CORRELATION (echo bleed between system and mic)")
            print("Values near 0 = no bleed, near 1 = identical signals")
            print("-" * 64)

            sys_data, sr = tracks["system"]
            mic_data, _ = tracks["mic"]
            xcorr = cross_correlate_tracks(sys_data, mic_data, sr)
            for x in xcorr:
                print(f"  [{x['time']}] correlation={x['correlation']:.4f}  lag={x['lag_ms']:.1f}ms")

            coh = coherence_analysis(sys_data, mic_data, sr)
            print(f"\n  Voice-band coherence: {coh['voice_band_coherence']:.4f}")
            print(f"  Full-band coherence:  {coh['full_band_coherence']:.4f}")

            if "aec_mic" in tracks:
                print("\n  After AEC processing:")
                aec_mic_data, _ = tracks["aec_mic"]
                aec_sys_data, _ = tracks["aec_system"]
                xcorr2 = cross_correlate_tracks(aec_sys_data, aec_mic_data, sr)
                for x in xcorr2:
                    print(f"  [{x['time']}] correlation={x['correlation']:.4f}  lag={x['lag_ms']:.1f}ms")
                coh2 = coherence_analysis(aec_sys_data, aec_mic_data, sr)
                print(f"\n  Voice-band coherence: {coh2['voice_band_coherence']:.4f}")
                print(f"  Full-band coherence:  {coh2['full_band_coherence']:.4f}")

    if mode == "echo":
        return

    # ---- PESQ (if we have original + processed mic) ----
    if "mic" in tracks and "aec_mic" in tracks:
        print("\n" + "-" * 64)
        print("PESQ - Speech Quality (MOS 1.0-4.5, comparing AEC vs original mic)")
        print("4.0+ excellent, 3.0+ good, <2.5 poor")
        print("-" * 64)

        mic_data, sr = tracks["mic"]
        aec_data, _ = tracks["aec_mic"]
        pesq_results = analyze_pesq_segments(mic_data, aec_data, sr)
        for r in pesq_results:
            if "error" in r:
                print(f"  [{r['time']}] error: {r['error']}")
            else:
                print(f"  [{r['time']}] NB={r['narrowband']:.2f}  WB={r['wideband']:.2f}")

        # ---- STOI ----
        print("\n" + "-" * 64)
        print("STOI - Speech Intelligibility (0.0-1.0, comparing AEC vs original mic)")
        print(">0.8 good, >0.6 fair, <0.6 poor")
        print("-" * 64)

        stoi_results = analyze_stoi_segments(mic_data, aec_data, sr)
        for r in stoi_results:
            if "error" in r:
                print(f"  [{r['time']}] error: {r['error']}")
            else:
                quality = "[good]" if r["stoi"] > 0.8 else "[fair]" if r["stoi"] > 0.6 else "[poor]"
                print(f"  [{r['time']}] STOI={r['stoi']:.3f}  {quality}")

    # ---- SPECTRAL ----
    print("\n" + "-" * 64)
    print("SPECTRAL ANALYSIS")
    print("-" * 64)

    for name, (data, sr) in tracks.items():
        spec = analyze_spectral(data, sr)
        print(f"  {name:15s}: centroid={spec['centroid_hz']}Hz  rolloff={spec['rolloff_85pct_hz']}Hz  ZCR={spec['zero_crossing_rate']}")

    # ---- SNR ----
    print("\n" + "-" * 64)
    print("SNR ESTIMATE (speech-to-noise ratio)")
    print("-" * 64)

    for name, (data, sr) in tracks.items():
        snr = estimate_snr(data, sr)
        quality = ""
        if snr > 20:
            quality = "[excellent]"
        elif snr > 15:
            quality = "[good]"
        elif snr > 10:
            quality = "[fair]"
        else:
            quality = "[poor]"
        print(f"  {name:15s}: {snr:5.1f} dB  {quality}")

    # ---- PER-MINUTE ENERGY ----
    print("\n" + "-" * 64)
    print("PER-MINUTE ENERGY (voice band 300-3400Hz)")
    print("-" * 64)

    # Only show for primary tracks to keep output manageable
    primary_track_name = "system" if "system" in tracks else "mono"
    if primary_track_name in tracks:
        data, sr = tracks[primary_track_name]
        energy = per_minute_energy(data, sr)
        print(f"\n  {primary_track_name}:")
        for e in energy:
            bar = "#" * max(0, int((e["rms_db"] + 50) / 2))
            print(f"    [{e['minute']:2d}:00] RMS={e['rms_db']:6.1f}dB  voice={e['voice_db']:6.1f}dB  {bar}")

    if "mic" in tracks:
        data, sr = tracks["mic"]
        energy = per_minute_energy(data, sr)
        print(f"\n  mic:")
        for e in energy:
            bar = "#" * max(0, int((e["rms_db"] + 50) / 2))
            print(f"    [{e['minute']:2d}:00] RMS={e['rms_db']:6.1f}dB  voice={e['voice_db']:6.1f}dB  {bar}")

    # Cleanup
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 64)
    print("ANALYSIS COMPLETE")
    print("=" * 64)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze audio recording quality")
    parser.add_argument("directory", help="Path to recording directory")
    parser.add_argument("--tracks", action="store_true", help="Track info only")
    parser.add_argument("--echo", action="store_true", help="Echo analysis only")
    parser.add_argument("--quality", action="store_true", help="Quality metrics only (skip echo)")
    args = parser.parse_args()

    mode = "all"
    if args.tracks:
        mode = "tracks"
    elif args.echo:
        mode = "echo"
    elif args.quality:
        mode = "quality"

    run_full_analysis(args.directory, mode=mode)
