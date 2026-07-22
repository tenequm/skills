# Skill Card

## Description

audio-quality-check analyzes audio recording quality - echo detection, loudness (EBU R128), speech intelligibility (PESQ/STOI), SNR, and spectral metrics - for call recordings and processed audio files. It bundles an analysis script for dual-track M4A, single-track, and AEC-processed recordings, plus interpretation guidance for every metric.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers and audio engineers diagnosing why a recording sounds bad: detecting echo or signal duplication, measuring speech clarity, comparing original vs AEC-processed tracks, or auditing recordings from call-recording apps such as Blackbox.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Dependencies:
- Required binaries (declared in metadata.openclaw requires.bins, brew formula ffmpeg): ffmpeg, ffprobe
- Python: numpy, soundfile, scipy, pyloudnorm, pesq, pystoi, librosa
- Optional: sox (quick loudness checks)

## Known Risks and Mitigations

Risk: The skill instructs the agent to run pip installs and shell commands (ffmpeg extraction, bundled Python script) on the local machine, which modifies the Python environment and writes temporary WAV files.

Mitigation: Review the install and extraction commands before execution; run in a virtual environment; temporary files are written to /tmp-style paths and can be deleted after analysis.

Risk: Metric thresholds (PESQ, STOI, SNR, autocorrelation echo peaks) are heuristics; an automated verdict may mislabel a recording as good or bad.

Mitigation: Treat script output as diagnostic evidence, not a verdict; the SKILL.md documents how to read each metric so a human can confirm by listening to the flagged segments.

Risk: Recordings analyzed may contain private conversations; paths and analysis output could leak sensitive content into logs.

Mitigation: Process recordings locally only; avoid pasting transcript-like content or personal file paths into shared logs or reports.

## References

- ITU-T P.862 (PESQ) and STOI speech-quality standards referenced by the bundled script
- Source: https://github.com/tenequm/skills/tree/main/skills/audio-quality-check

## Skill Output

Output type(s): Analysis - quality metrics, echo-detection results, and diagnostic interpretation of audio files

Output format: Terminal text from the bundled Python script plus Markdown summary written by the agent

Output parameters: Metrics include LUFS loudness, autocorrelation echo peaks (lag ms, correlation r), cross-track correlation, PESQ MOS, STOI, SNR dB, spectral centroid/rolloff/ZCR, per-minute energy

Other properties: Analysis is read-only with respect to the input audio; temporary extracted WAV files are side effects

## Skill Version

0.1.2

## Ethical Considerations

Recordings may contain private conversations; users must have the right to analyze the audio they process. Automated quality verdicts should be confirmed by human listening before driving decisions about processing pipelines.
