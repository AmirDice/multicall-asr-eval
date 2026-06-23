# Results

Synthetic recording: 242.11s, 4 calls.

## Aggregate (averaged across calls)

| Engine | WER ↓ | Entity exact | Entity fuzzy | Phrase recall | Wall clock |
|--------|------:|-------------:|-------------:|--------------:|-----------:|
| deepgram | 0.065 | 89.8% | 97.8% | 95.0% | 5.1s |
| faster-whisper-small | 0.138 | 82.5% | 90.3% | 90.2% | 282.6s |

## Per-call WER

| Call | deepgram | faster-whisper-small |
|------|------:|------:|
| CALL-001 | 0.085 | 0.14 |
| CALL-002 | 0.056 | 0.157 |
| CALL-003 | 0.066 | 0.151 |
| CALL-004 | 0.051 | 0.102 |