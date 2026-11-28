"""Resolve numerical prose references from the same data used by the charts."""

import math
import re
from decimal import Decimal, ROUND_HALF_UP
from html import escape


def render_claims(text, data):
    if "{{edition:" in text:
        market = data["market_snapshot"]
        boards = {b["id"]: b for b in market["boards"]}
        reviewed = market["reviewed_at"]
        edition = {"date": reviewed, "issue": reviewed[5:].replace("-", " / "), "headline": market["changes"][0]["title"],
                   "aa_count": len(boards["aa5"]["rows"]), "hle_count": len(boards["scale"]["rows"])}
        for key in ("arena", "arena_webdev", "arena_agent", "openrouter"):
            edition[key] = boards[key]["source_updated_at"][5:]
        text = re.sub(r"\{\{edition:(\w+)\}\}", lambda m: escape(str(edition[m[1]])), text)

    def replace(match):
        kind, reference = match.groups()
        parts = reference.split(":")
        if kind in {"aa", "aa5"}:
            release, effort, metric, digits = parts
            series = data["aa_release_series"] if kind == "aa" else data["aa_v5"]["aa_release_series"]
            candidates = [v for r in series["releases"] if r["releaseSlug"] == release
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
        # Match Intl.NumberFormat's default half-expand rounding in the charts.
        rounded = Decimal(str(value)).quantize(Decimal(1).scaleb(-int(digits)), rounding=ROUND_HALF_UP)
        return f"{rounded:.{digits}f}"

    return re.sub(r"\{\{(aa5|aa|row):([^{}]+)\}\}", replace, text)
