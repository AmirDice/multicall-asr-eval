"""Transcription wrappers for the two engines under comparison.

Engines are kept isolated and dependency-light:
  - Deepgram (cloud)        — needs DEEPGRAM_API_KEY.
  - faster-whisper (local)  — CPU-friendly CTranslate2 build of Whisper.

Both return a uniform list of segments: {start, end, speaker, text}.
"""

from __future__ import annotations

import os
from pathlib import Path


def transcribe_deepgram(audio: Path, *, model: str = "nova-2", language: str = "es") -> dict:
    """Transcribe with Deepgram (SDK v7). Diarization on for speaker labels."""
    from deepgram import DeepgramClient

    api_key = os.getenv("DEEPGRAM_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPGRAM_API_KEY is not set")

    dg = DeepgramClient(api_key=api_key)
    with open(audio, "rb") as f:
        audio_bytes = f.read()

    resp = dg.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model=model,
        language=language,
        diarize=True,
        punctuate=True,
        utterances=True,
    )
    data = resp.dict() if hasattr(resp, "dict") else (resp if isinstance(resp, dict) else resp.__dict__)

    results = data.get("results") if isinstance(data, dict) else getattr(data, "results", None)
    utterances = []
    if isinstance(results, dict):
        utterances = results.get("utterances") or []
    elif results is not None:
        utterances = getattr(results, "utterances", None) or []

    segments = []
    for u in utterances:
        get = (lambda k, d=None: u.get(k, d)) if isinstance(u, dict) else (lambda k, d=None: getattr(u, k, d))
        segments.append({
            "start": float(get("start", 0.0) or 0.0),
            "end": float(get("end", 0.0) or 0.0),
            "speaker": f"SPEAKER_{get('speaker', 0)}",
            "text": (get("transcript") or "").strip(),
        })
    return {"engine": "deepgram", "model": model, "segments": segments}


def transcribe_faster_whisper(
    audio: Path, *, model: str = "small", language: str = "es", compute_type: str = "int8"
) -> dict:
    """Transcribe locally with faster-whisper (no diarization)."""
    from faster_whisper import WhisperModel

    wm = WhisperModel(model, device="cpu", compute_type=compute_type)
    seg_iter, _info = wm.transcribe(str(audio), language=language, vad_filter=True)
    segments = []
    for s in seg_iter:
        segments.append({
            "start": float(s.start),
            "end": float(s.end),
            "speaker": None,  # faster-whisper alone does not diarize
            "text": (s.text or "").strip(),
        })
    return {"engine": f"faster-whisper-{model}", "model": model, "segments": segments}
