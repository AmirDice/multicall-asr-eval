#!/usr/bin/env python3
"""Synthesise a multi-call recording from the fictional call scripts.

For each turn, text is rendered with edge-tts using a distinct voice per role
(so the recording has two real speakers for diarization). Turns are
concatenated with short gaps; calls are separated by a longer silence, so the
result is one long MP3 containing several unrelated support calls, like a
call-centre queue recording.

Outputs:
  data/synthetic_calls.mp3        the recording
  data/ground_truth.json          per-call windows + verbatim turns with
                                  exact timestamps and speaker labels

Because we generate the audio, the ground truth is VERBATIM (every word) and
the speakers are known exactly, so both WER and Diarization Error Rate are
valid here, unlike on a real condensed human reference (see README).

    python scripts/generate_synthetic.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import edge_tts  # noqa: E402
from pydub import AudioSegment  # noqa: E402

from src.synthetic_calls import CALLS  # noqa: E402

VOICES = {
    "agent": "es-ES-AlvaroNeural",   # male
    "client": "es-ES-ElviraNeural",  # female
}

GAP_WITHIN_CALL_MS = 350
GAP_BETWEEN_CALLS_MS = 3000
LEAD_SILENCE_MS = 500

DATA = _ROOT / "data"
TMP = DATA / "_tmp_tts"


async def _render_turn(text: str, voice: str, out: Path) -> None:
    await edge_tts.Communicate(text, voice).save(str(out))


async def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)

    recording = AudioSegment.silent(duration=LEAD_SILENCE_MS)
    cursor_ms = LEAD_SILENCE_MS
    gt_calls = []

    for ci, call in enumerate(CALLS):
        call_start_ms = cursor_ms
        gt_turns = []
        for ti, (speaker, text) in enumerate(call["turns"]):
            voice = VOICES[speaker]
            clip_path = TMP / f"{call['id']}_{ti:02d}.mp3"
            await _render_turn(text, voice, clip_path)
            seg = AudioSegment.from_mp3(clip_path)
            turn_start_ms = cursor_ms
            recording += seg
            cursor_ms += len(seg)
            gt_turns.append({
                "start": round(turn_start_ms / 1000, 2),
                "end": round(cursor_ms / 1000, 2),
                "speaker": speaker,
                "text": text,
            })
            # gap within the call
            recording += AudioSegment.silent(duration=GAP_WITHIN_CALL_MS)
            cursor_ms += GAP_WITHIN_CALL_MS

        gt_calls.append({
            "id": call["id"],
            "topic": call["topic"],
            "start": round(call_start_ms / 1000, 2),
            "end": round(cursor_ms / 1000, 2),
            "turns": gt_turns,
        })

        if ci != len(CALLS) - 1:
            recording += AudioSegment.silent(duration=GAP_BETWEEN_CALLS_MS)
            cursor_ms += GAP_BETWEEN_CALLS_MS

    out_mp3 = DATA / "synthetic_calls.mp3"
    recording.export(out_mp3, format="mp3", bitrate="128k")

    gt = {
        "description": "Synthetic multi-call recording, fully fictional, generated with edge-tts.",
        "voices": VOICES,
        "duration_sec": round(cursor_ms / 1000, 2),
        "calls": gt_calls,
    }
    (DATA / "ground_truth.json").write_text(
        json.dumps(gt, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # cleanup temp clips
    for p in TMP.glob("*.mp3"):
        p.unlink()
    TMP.rmdir()

    total_turns = sum(len(c["turns"]) for c in gt_calls)
    print(f"Wrote {out_mp3} ({gt['duration_sec']}s)")
    print(f"Wrote {DATA / 'ground_truth.json'}: {len(gt_calls)} calls, {total_turns} turns")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
