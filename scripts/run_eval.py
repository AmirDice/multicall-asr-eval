#!/usr/bin/env python3
"""Run the ASR engine comparison on the synthetic recording and write results.

    python scripts/run_eval.py                  # both engines
    python scripts/run_eval.py --engines deepgram
    python scripts/run_eval.py --whisper-model base

Reads data/synthetic_calls.mp3 + data/ground_truth.json, transcribes with each
engine, scores per-call WER / entity accuracy / phrase recall, and writes
results/results.json + results/results.md.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src import metrics  # noqa: E402
from src.transcribe import transcribe_deepgram, transcribe_faster_whisper  # noqa: E402

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"


def segments_in_window(segments: list[dict], start: float, end: float, pad: float = 1.0) -> str:
    return " ".join(
        s["text"] for s in segments
        if s.get("text") and (start - pad) <= float(s.get("start", 0)) <= (end + pad)
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engines", nargs="+", default=["deepgram", "whisper"],
                    choices=["deepgram", "whisper"])
    ap.add_argument("--whisper-model", default="small")
    args = ap.parse_args()

    gt = json.loads((DATA / "ground_truth.json").read_text(encoding="utf-8"))
    audio = DATA / "synthetic_calls.mp3"
    RESULTS.mkdir(parents=True, exist_ok=True)

    transcripts = {}
    timings = {}
    for eng in args.engines:
        t0 = time.perf_counter()
        if eng == "deepgram":
            tr = transcribe_deepgram(audio)
            key = "deepgram"
        else:
            tr = transcribe_faster_whisper(audio, model=args.whisper_model)
            key = f"faster-whisper-{args.whisper_model}"
        timings[key] = round(time.perf_counter() - t0, 1)
        transcripts[key] = tr
        (RESULTS / f"transcript_{key}.json").write_text(
            json.dumps(tr, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"transcribed with {key}: {len(tr['segments'])} segments in {timings[key]}s")

    # Per-call, per-engine metrics
    rows = []
    for call in gt["calls"]:
        ref_lines = [t["text"] for t in call["turns"]]
        ref_text = " ".join(ref_lines)
        terms = set(metrics.norm(t) for t in metrics.DOMAIN_TERMS if metrics.norm(t) in metrics.norm(ref_text))
        for line in ref_lines:
            terms |= metrics.proper_nouns(line)
        terms = {t for t in terms if len(t) > 3}

        for key, tr in transcripts.items():
            hyp = segments_in_window(tr["segments"], call["start"], call["end"])
            rows.append({
                "call": call["id"], "engine": key,
                "wer": round(metrics.wer(ref_text, hyp), 3),
                "entity": metrics.entity_accuracy(terms, hyp),
                "phrase": metrics.phrase_recall(ref_lines, hyp),
            })

    # Aggregates
    agg = {}
    for key in transcripts:
        erows = [r for r in rows if r["engine"] == key]
        n = len(erows) or 1
        agg[key] = {
            "wer": round(sum(r["wer"] for r in erows) / n, 3),
            "entity_exact_pct": round(sum(r["entity"]["exact_pct"] for r in erows) / n, 1),
            "entity_fuzzy_pct": round(sum(r["entity"]["fuzzy_pct"] for r in erows) / n, 1),
            "phrase_recall_pct": round(sum(r["phrase"]["recall_pct"] for r in erows) / n, 1),
            "wall_clock_sec": timings.get(key),
        }

    out = {"per_call": rows, "aggregate": agg, "audio_duration_sec": gt["duration_sec"]}
    (RESULTS / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown
    md = ["# Results\n", f"Synthetic recording: {gt['duration_sec']}s, {len(gt['calls'])} calls.\n"]
    md.append("## Aggregate (averaged across calls)\n")
    md.append("| Engine | WER ↓ | Entity exact | Entity fuzzy | Phrase recall | Wall clock |")
    md.append("|--------|------:|-------------:|-------------:|--------------:|-----------:|")
    for key, a in agg.items():
        md.append(f"| {key} | {a['wer']} | {a['entity_exact_pct']}% | {a['entity_fuzzy_pct']}% "
                  f"| {a['phrase_recall_pct']}% | {a['wall_clock_sec']}s |")
    md.append("\n## Per-call WER\n")
    md.append("| Call | " + " | ".join(transcripts.keys()) + " |")
    md.append("|------|" + "|".join("------:" for _ in transcripts) + "|")
    for call in gt["calls"]:
        cells = []
        for key in transcripts:
            r = next((x for x in rows if x["call"] == call["id"] and x["engine"] == key), None)
            cells.append(str(r["wer"]) if r else "n/a")
        md.append(f"| {call['id']} | " + " | ".join(cells) + " |")
    (RESULTS / "results.md").write_text("\n".join(md), encoding="utf-8")

    # Print ASCII-safe (Windows terminals default to cp1252).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("\n" + "\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
