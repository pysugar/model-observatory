"""Resolve numerical prose references from the same data used by the charts."""

import math
import re


def render_claims(text, data):
    def replace(match):
        kind, reference = match.groups()
        parts = reference.split(":")
        if kind == "aa":
            release, effort, metric, digits = parts
            candidates = [v for r in data["aa_release_series"]["releases"] if r["releaseSlug"] == release
                          for v in r["variants"] if v["effort"] == effort]
        else:
            benchmark, model, effort, metric, digits = parts
            candidates = [r for r in data["rows"] if
                          (r["benchmark"], r["model"], r["effort"]) == (benchmark, model, effort)]
        if len(candidates) != 1 or digits not in {"0", "1", "2", "3", "4"}:
            raise ValueError(f"Ambiguous or invalid narrative reference: {reference}")
        record = candidates[0]
        if metric.startswith("eval/"):
            value = record["evalMetrics"][metric[5:]]
        elif metric in {"complex", "coding", "planning", "agentic", "automation", "knowledge"}:
            value = record["taskScores"][metric]
        else:
            value = record[metric]
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"Missing or invalid narrative value: {reference}")
        return f"{value:.{digits}f}"

    return re.sub(r"\{\{(aa|row):([^{}]+)\}\}", replace, text)
