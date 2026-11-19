"""Read Arena, LiveBench, Scale SEAL and OpenRouter on 2026-11-19 without mixing protocols.

Research-only dependencies: pyarrow and beautifulsoup4 in the configured environment.
The application build uses the resulting frozen JSON and does not fetch the network.
"""

from datetime import datetime
import hashlib
import json
import re

from bs4 import BeautifulSoup

from refresh_aa import HERE, ROOT, CHECKED, load, read, write, fetch

PREVIOUS = ROOT / "research/2026-11-18-pm"

META_NAMES = {"Muse Wonder", "Muse Wonder 1.0", "Muse Wonder Full", "Muse Spark 1.3", "Muse Ember", "Muse Ember 1.0"}


def parse_scale_rows(soup):
    """Extract (model_name, score_text) rows from a Scale SEAL leaderboard page."""
    out = []
    for node in soup.select("[data-model-name]"):
        name = node.get_text(" ", strip=True)
        parent, text = node.parent, ""
        while parent and len(parent.select("[data-model-name]")) == 1:
            candidate = parent.get_text(" ", strip=True)
            if re.search(r"\d+\.\d+", candidate.replace(name, "", 1)):
                text = candidate
                break
            parent = parent.parent
        out.append((name, text))
    return out


def main():
    arena = load("arena", "research/2026-10-29/fetch_arena.py")
    arena.OUT = HERE / "arena.json"
    arena.REVISION = json.loads(fetch("https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset"))["sha"]
    arena.TRACKED += tuple(META_NAMES) + (
        "Gemini 4 Carbon", "Gemini 4 Hydrogen", "Gemini 4 Neon",
        "Claude Fable 5.2", "GPT-6.1 Terra", "GPT-6.2 Astra", "GPT-6.2 Sol",
    )
    arena.main()
    doc = read(arena.OUT)
    for board in doc["boards"].values():
        board["rows"] = [r for r in board["rows"] if r["vendor"] != "Meta" or r["model"] in META_NAMES]
    write(arena.OUT, doc)

    live = load("livebench", "research/2026-10-29/fetch_livebench.py")
    live.OUT = HERE / "livebench.json"
    html = fetch("https://livebench.ai/").decode()
    bundle_url = "https://livebench.ai/" + re.search(r'src="\./([^\"]+\.js)"', html)[1]
    bundle = fetch(bundle_url)
    latest = max(re.findall(r"2026\d{4}", bundle.decode()))
    if latest != "20261106":
        raise ValueError(f"Inspect the new LiveBench release ({latest}) and calculation rules before importing")
    live.RELEASE = "2026-11-06"
    live.BASE = "https://livebench.ai/data/20261106/"
    live.NAMES.update({
        "claude-fable-5.2": ("Claude Fable 5.2", "Anthropic", False),
        "gemini-4-carbon": ("Gemini 4 Carbon", "Google", False),
        "gemini-4-hydrogen": ("Gemini 4 Hydrogen", "Google", False),
        "gemini-4-neon": ("Gemini 4 Neon", "Google", False),
        "gpt-6.2-astra": ("GPT-6.2 Astra", "OpenAI", False),
        "gpt-6.2-sol": ("GPT-6.2 Sol", "OpenAI", False),
    })
    live.PAGE_CHECK = {}
    live.get = lambda name: (live.BASE + name, fetch(live.BASE + name))
    live.main()
    doc = read(live.OUT)
    doc["release_discovery"] = {
        "url": bundle_url,
        "sha256": hashlib.sha256(bundle).hexdigest(),
        "checked_at": CHECKED,
        "note": "Read page bundle: weighted Overall and cost per successful task formulas unchanged on the 11-06 task set.",
    }
    write(live.OUT, doc)

    manual = read(PREVIOUS / "manual-boards.json")
    scale_url = "https://labs.scale.com/leaderboard/hle-diamond"
    body = fetch(scale_url)
    soup = BeautifulSoup(body, "html.parser")
    names = {slug: (name, vendor) for slug, name, vendor, *_ in manual["scale"]["rows"]}
    names.update({
        "claude-fable-5-2": ("Claude Fable 5.2", "Anthropic"),
        "inkling": ("Inkling", "Thinking Machines"),
        "muse-ember-1.0": ("Muse Ember", "Meta"),
        "minimax-m3p1-flash": ("MiniMax-M3.1-Flash", "MiniMax"),
        "gemini-4-neon": ("Gemini 4 Neon", "Google"),
        "gpt-6-2-astra": ("GPT-6.2 Astra", "OpenAI"),
        "gpt-6-2-sol": ("GPT-6.2 Sol", "OpenAI"),
    })
    rows, ranks = [], {}
    nodes = soup.select("[data-model-name]")
    for rank, node in enumerate(nodes, 1):
        slug = node.get_text(strip=True)
        if slug == "muse-spark-open":
            continue
        if slug not in names:
            raise ValueError(f"Unreviewed Scale model: {slug}")
        parent, match = node.parent, None
        while parent and len(parent.select("[data-model-name]")) == 1:
            match = re.search(r"(\d+\.\d+)\s*±\s*(\d+\.\d+)(?:\s*Calib Err:\s*(\d+\.\d+))?", parent.get_text(" ", strip=True))
            if match:
                break
            parent = parent.parent
        if not match:
            raise ValueError(f"Missing Scale score: {slug}")
        name, vendor = names[slug]
        rows.append([slug, name, vendor, float(match[1]), float(match[2]), float(match[3]) if match[3] else None])
        ranks[slug] = rank
    manual["scale"].update(
        rows=rows, source_ranks=ranks, page_total=len(nodes),
        checked_at=CHECKED, read_at=CHECKED, source_url=scale_url,
        sha256=hashlib.sha256(body).hexdigest(), source_updated_at=None,
    )

    # Also read SEAL HSS, MultiChallenge and Remote Labor Index top-4 highlights with hashes.
    seal_extra = {}
    for key, url in (
        ("hss", "https://labs.scale.com/leaderboard/hss"),
        ("multichallenge", "https://labs.scale.com/leaderboard/multichallenge?tab=large"),
        ("rli", "https://labs.scale.com/leaderboard/rli"),
    ):
        b = fetch(url)
        s = BeautifulSoup(b, "html.parser")
        parsed = []
        for model_name, raw_text in parse_scale_rows(s)[:10]:
            m_ci = re.search(r"(\d+\.\d+)\s*±\s*(\d+\.\d+)", raw_text)
            m_val = re.search(r"(\d+\.\d+)", raw_text.replace(model_name, "", 1))
            score_str = f"{m_ci[1]} ±{m_ci[2]}" if m_ci else (f"{m_val[1]}%" if m_val else "")
            parsed.append({"model": model_name, "score": score_str})
        seal_extra[key] = {
            "source_url": url,
            "checked_at": CHECKED,
            "sha256": hashlib.sha256(b).hexdigest(),
            "top10": parsed,
        }
    manual["scale_extra"] = seal_extra

    usage_url = "https://openrouter.ai/rankings"
    body = fetch(usage_url)
    soup = BeautifulSoup(body, "html.parser")
    date = re.search(r"Usage data through (\w+ \d+, \d{4})", soup.get_text(" ", strip=True))
    if not date:
        raise ValueError("OpenRouter did not disclose a usage date")
    usage_date = datetime.strptime(date[1], "%b %d, %Y").date().isoformat()
    table = next(t for t in soup.select("table") if "Model rankings by tokens processed" in t.get_text())
    vendors = {
        "deepseek": "DeepSeek", "tencent": "Tencent", "z-ai": "Z.AI", "openai": "OpenAI",
        "anthropic": "Anthropic", "stepfun": "StepFun", "moonshotai": "Moonshot AI",
        "xiaomi": "Xiaomi", "minimax": "MiniMax", "google": "Google", "x-ai": "xAI", "meta-llama": "Meta",
    }
    names = {
        "Step 5 Preview": "Step 5",
        "Hy4": "Tencent Hy4",
        "Hy4 flash": "Tencent Hy4 Flash",
        "MiniMax M3.1 Flash": "MiniMax-M3.1-Flash",
    }
    rows = []
    for tr in table.select("tbody tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.select("th,td")]
        rank, name, vendor, tokens, change = cells
        match = re.fullmatch(r"([\d.]+)T tokens", tokens)
        if int(rank) != len(rows) + 1 or not match:
            raise ValueError(f"Unreviewed OpenRouter rank or unit: {cells}")
        rows.append([names.get(name, name), vendors[vendor], float(match[1]), change])
    if len(rows) != 10:
        raise ValueError("OpenRouter weekly top ten is incomplete")
    manual["openrouter"].update(
        rows=rows, usage_through=usage_date, checked_at=CHECKED, read_at=CHECKED,
        source_url=usage_url, sha256=hashlib.sha256(body).hexdigest(),
    )
    manual["note"] = "各来源独立读取；Scale未披露评测日期，OpenRouter为滚动7天token用量。Meta开放权重系列不纳入。"
    write(HERE / "manual-boards.json", manual)
    print(json.dumps({
        "scale": len(manual["scale"]["rows"]),
        "openrouter_through": usage_date,
        "seal_extra": {k: [r["model"] + " " + r["score"] for r in v["top10"][:4]] for k, v in seal_extra.items()},
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
