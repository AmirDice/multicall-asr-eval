"""Accuracy metrics for ASR transcripts against a ground truth.

Three complementary metrics, chosen so the toolkit works on BOTH a verbatim
reference (synthetic) and a condensed human reference (real-world):

  - WER          — valid only when the reference is verbatim. Reported here
                   because the synthetic ground truth is exact.
  - Entity acc   — does the engine get the domain terms / proper nouns right?
                   Reported as exact AND fuzzy match (fuzzy credits near-miss
                   spellings like "GestorPro" vs "gestor pro"). This is the
                   metric that survives a condensed reference.
  - Phrase recall— fraction of a reference line's content words present in the
                   engine transcript. Also survives a condensed reference.

See README for why WER alone is the wrong tool on real support-call data.
"""

from __future__ import annotations

import re
import unicodedata

import jiwer
from rapidfuzz import fuzz

# Curated domain glossary for the synthetic scripts — the brand/technical terms
# an ASR for this domain must get right (the real-world analogue is the
# product/vendor jargon a support line uses constantly). Person/place proper
# nouns are added per call from the reference at runtime.
DOMAIN_TERMS = [
    "GestorPro", "FactuCloud", "SEPA", "IBAN", "código de barras",
    "ajuste de inventario", "remesa", "proveedor", "albarán", "código",
]

_STOP = set(
    "de la el los las un una y o que en a por para con se su sus al del lo me te "
    "es son está están ya no sí si le les nos mi tu como cuando donde más muy pero "
    "porque eso esa ese esto esta este hay he ha han has".split()
)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", norm(s))


def content_words(s: str) -> list[str]:
    return [w for w in words(s) if w not in _STOP and len(w) > 2]


def proper_nouns(text: str) -> set[str]:
    """Capitalised tokens (>3 chars) that look like names, normalised."""
    out = set()
    for tok in re.findall(r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{3,}", text or ""):
        n = norm(tok)
        if n not in _STOP:
            out.add(n)
    return out


def wer(reference: str, hypothesis: str) -> float:
    ref, hyp = norm(reference), norm(hypothesis)
    if not ref:
        return 0.0
    if not hyp:
        return 1.0
    return float(jiwer.wer(ref, hyp))


def entity_accuracy(terms: set[str], transcript: str, *, fuzzy_threshold: int = 85) -> dict:
    """Exact and fuzzy presence of each expected term in the transcript."""
    tnorm = norm(transcript)
    exact, fuzzy_hit = [], []
    for t in terms:
        tn = norm(t)
        if re.search(rf"\b{re.escape(tn)}\b", tnorm):
            exact.append(t)
            fuzzy_hit.append(t)
        elif fuzz.partial_ratio(tn, tnorm) >= fuzzy_threshold:
            fuzzy_hit.append(t)
    n = len(terms) or 1
    return {
        "total": len(terms),
        "exact": len(exact),
        "fuzzy": len(fuzzy_hit),
        "exact_pct": round(100 * len(exact) / n, 1),
        "fuzzy_pct": round(100 * len(fuzzy_hit) / n, 1),
        "missing": sorted(terms - set(fuzzy_hit)),
    }


def phrase_recall(ref_lines: list[str], transcript: str, *, threshold: float = 0.7) -> dict:
    """Fraction of each reference line's content words present in the transcript."""
    tword_set = set(words(transcript))
    recalled, scores = 0, []
    for line in ref_lines:
        cw = content_words(line)
        if not cw:
            continue
        hit = sum(1 for w in cw if w in tword_set) / len(cw)
        scores.append(hit)
        if hit >= threshold:
            recalled += 1
    n = len(scores) or 1
    return {
        "lines": len(scores),
        "recalled": recalled,
        "recall_pct": round(100 * recalled / n, 1),
        "avg_token_recall_pct": round(100 * sum(scores) / n, 1) if scores else 0.0,
    }
