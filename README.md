# multicall-asr-eval

**Evaluating ASR (and speaker attribution) on multi-call recordings — and why WER lies on real support-call data.**

A small, reproducible toolkit for comparing speech-to-text engines on the kind
of audio you actually get in a call centre: one long mono recording containing
several unrelated support calls. It ships a synthetic-data generator so the
whole thing runs end-to-end on any machine, no private audio required.

> Built from a real production investigation (Spanish pharmacy support calls).
> The client audio can't be shared, so this repo reproduces the **methodology**
> on fully synthetic, fictional calls.

---

## The interesting problem: you usually can't use WER

Word Error Rate is the default ASR metric. It needs a **verbatim** reference —
every spoken word, transcribed exactly. On real support calls you almost never
have that. What you have is a **human-written summary**: cleaned, condensed,
maybe 3 lines per minute. Run WER against a summary and *both* engines score
as catastrophically wrong — not because they're bad, but because the reference
isn't verbatim. WER is measuring the wrong thing.

So this toolkit measures accuracy three ways, and only the first needs a
verbatim reference:

| Metric | Needs verbatim ref? | What it tells you |
|--------|:-------------------:|-------------------|
| **WER** | yes | Classic word accuracy (valid on the synthetic data here). |
| **Entity accuracy** | no | Does the engine get the domain terms / proper nouns right? Reported as **exact** and **fuzzy** (fuzzy credits near-miss spellings). This is the metric that survives a condensed reference — and the one that matters for downstream RAG/search. |
| **Phrase recall** | no | Fraction of each reference line's content words present in the transcript. |

The synthetic recording has a **verbatim** ground truth (we generate the audio,
so we know every word), which lets us show WER *and* the reference-light metrics
side by side — and demonstrate that the reference-light ones track WER closely.
On real condensed references you'd drop WER and keep the other two.

---

## Results (synthetic, 4 calls / ~4 min)

| Engine | WER ↓ | Entity exact | Entity fuzzy | Phrase recall | Wall clock |
|--------|------:|-------------:|-------------:|--------------:|-----------:|
| Deepgram `nova-2` (cloud) | **0.065** | 89.8% | **97.8%** | **95.0%** | **5.1 s** |
| faster-whisper `small` (local CPU) | 0.138 | 82.5% | 90.3% | 90.2% | 282.6 s |

Read it as a **case study, not a benchmark** (n = 4 calls). Takeaways that do
generalise:

- **Cloud vs local is a latency/accuracy trade**, not just accuracy. Deepgram
  was ~55× faster wall-clock here (cloud vs CPU `small`) and a bit more
  accurate. A local GPU or a smaller-but-faster model changes that calculus.
- **Exact vs fuzzy entity accuracy is the honest way to report term errors.**
  Deepgram's exact 89.8% → fuzzy 97.8%: most "misses" are near-miss spellings
  of brand/jargon terms, not dropped content. Reporting only exact-match
  over-states the problem; only fuzzy hides it. Show both.
- The reference-light metrics (entity, phrase recall) **rank the engines the
  same way WER does** — evidence they're usable when WER isn't available.

Full per-call numbers: [`results/results.md`](results/results.md).

---

## A note on speaker attribution (diarization)

The production motivation was as much about **who spoke** (agent vs client) as
*what* was said. Two findings from that work, included here as design notes:

- **Full-file diarization on mono phone audio tends to collapse to one
  speaker.** Re-running diarization on a **per-call slice** with the speaker
  count pinned to 2 recovers a credible agent/client split.
- **The ASR model size barely affects diarization.** Speaker clustering is done
  by the diarizer (e.g. pyannote), which is independent of the Whisper model —
  a bigger ASR model improves the *text*, not *who-spoke-when*.

This repo focuses on the transcription metrics (which run anywhere); a
diarization-error-rate harness over the synthetic audio (where speakers are
known exactly) is a natural extension — see `src/transcribe.py`, where Deepgram
already returns speaker labels.

---

## Run it

```bash
python -m venv .venv && . .venv/Scripts/activate        # or source .venv/bin/activate
pip install -r requirements.txt                          # needs ffmpeg on PATH

# 1. Generate the synthetic multi-call recording + verbatim ground truth
python scripts/generate_synthetic.py

# 2. Run the comparison (set DEEPGRAM_API_KEY for the cloud engine)
export DEEPGRAM_API_KEY=...        # omit to run faster-whisper only
python scripts/run_eval.py --engines deepgram whisper --whisper-model small
```

Outputs land in `results/`.

---

## How it works

```
src/synthetic_calls.py   fictional Spanish helpdesk call scripts (agent/client turns)
scripts/generate_synthetic.py  edge-tts (2 voices) → one MP3 of several calls + ground truth
src/transcribe.py        Deepgram (cloud) and faster-whisper (local) wrappers
src/metrics.py           WER, entity accuracy (exact + fuzzy), phrase recall
scripts/run_eval.py      transcribe → score per call → results.{json,md}
```

## Limitations (read these)

- **Tiny sample** — 4 synthetic calls. Enough to demonstrate the method, not to
  rank engines definitively.
- **Synthetic ≠ real.** TTS audio is clean; real telephony has codecs, overlap,
  crosstalk, and noise that hurt both engines more (and unevenly).
- **Single language/domain** (Spanish software support).
- The diarization claims come from the production work, not re-measured here.

## Why this exists

Most ASR write-ups are "engine A beat engine B on LibriSpeech." Real call-centre
audio breaks the usual assumptions: no verbatim reference, multiple calls per
file, mono telephony that wrecks diarization. This is a compact, honest example
of evaluating speech systems under those constraints — including being explicit
about what the numbers can and can't tell you.

## License

MIT.
