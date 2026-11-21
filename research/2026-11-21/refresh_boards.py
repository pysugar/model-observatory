"""Freeze dated Arena, LiveBench, Scale SEAL and OpenRouter observations."""

from datetime import datetime
from hashlib import sha256
import json
import re

from bs4 import BeautifulSoup

from refresh_aa import CHECKED, HERE, ROOT, load, reader, write

CACHE = ROOT / "test-results" / f"refresh-{CHECKED}" / "boards"
META = {"Muse Wonder", "Muse Wonder 1.0", "Muse Wonder Full", "Muse Spark 1.3", "Muse Ember", "Muse Ember 1.0"}
FOCUS = ("Gemini 4 Carbon", "Gemini 4 Hydrogen", "Gemini 4 Neon", "Claude Fable 5.2",
         "GPT-6.1 Terra", "GPT-6.2 Astra", "GPT-6.2 Sol", "Qwen4-Max")
VENDORS = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "meta": "Meta",
           "moonshot": "Moonshot AI", "xai": "xAI", "deepseek": "DeepSeek", "minimax": "MiniMax",
           "zai": "Z.AI", "thinkingmachines": "Thinking Machines", "nvidia": "NVIDIA",
           "z-ai": "Z.AI", "stepfun": "StepFun", "xiaomi": "Xiaomi", "moonshotai": "Moonshot AI"}


def arena_board():
    arena = load(HERE.with_name("2026-10-29") / "fetch_arena.py")
    arena.REVISION = "abbae57d7888809e8b686f8548a6f77c81fa03f4"
    arena.TRACKED += tuple(META) + FOCUS
    arena.OUT = HERE / "arena.json"
    arena.main()
    result = json.loads(arena.OUT.read_text())
    for board in result["boards"].values():
        board["rows"] = [r for r in board["rows"] if r["vendor"] != "Meta" or r["model"] in META]
    write(arena.OUT, result)


def livebench():
    live = load(HERE.with_name("2026-10-29") / "fetch_livebench.py")
    live.OUT = HERE / "livebench.json"
    homepage = reader.fetch("https://livebench.ai/").decode()
    bundle_url = "https://livebench.ai/" + re.search(r'src="\./([^"]+\.js)"', homepage)[1]
    bundle = reader.fetch(bundle_url)
    if max(re.findall(r"2026\d{4}", bundle.decode())) != "20261106":
        raise ValueError("Review the task set and weights before changing the release")
    live.RELEASE, live.BASE = "2026-11-06", "https://livebench.ai/data/20261106/"
    live.NAMES.update({
        "claude-fable-5.2": ("Claude Fable 5.2", "Anthropic", False),
        "gemini-4-carbon": ("Gemini 4 Carbon", "Google", False),
        "gemini-4-hydrogen": ("Gemini 4 Hydrogen", "Google", False),
        "gemini-4-neon": ("Gemini 4 Neon", "Google", False),
        "gpt-6.2-astra": ("GPT-6.2 Astra", "OpenAI", False), "gpt-6.2-sol": ("GPT-6.2 Sol", "OpenAI", False),
        "qwen4-max": ("Qwen4-Max", "Alibaba", False), "kimi-k3.1-pro": ("Kimi K3.1 Pro", "Moonshot AI", True),
    })
    live.get = lambda name: (live.BASE + name, reader.fetch(live.BASE + name))
    live.PAGE_CHECK = {"gemini-4-neon": (87.4, 2.654), "gpt-6.2-astra": (84.9, 1.941)}
    live.main()
    result = json.loads(live.OUT.read_text())
    result["release_discovery"] = {"url": bundle_url, "sha256": sha256(bundle).hexdigest(), "checked_at": CHECKED}
    write(live.OUT, result)


def scale_board(path):
    url = "https://labs.scale.com/leaderboard/" + path
    body = reader.fetch(url)
    soup = BeautifulSoup(body, "html.parser")
    visible = [node.get_text(strip=True) for node in soup.select("[data-model-name]")]
    flight = load(HERE.with_name("2026-10-28") / "fetch_aa_v5.py").flight_data(body.decode())
    for match in re.finditer(r'"entries":(?=\[\{"model":)', flight):
        entries, _ = json.JSONDecoder().raw_decode(flight[match.end():])
        if visible and [r["model"] for r in entries] == visible:
            break
    else:
        raise ValueError(f"Could not match the displayed Scale tab at {url}")
    fields = ("model", "version", "rank", "score", "confidenceInterval_upper", "calibrationError", "company")
    rows = [{k: r.get(k) for k in fields} for r in entries]
    return {"source_url": url, "checked_at": CHECKED, "source_updated_at": None,
            "sha256": sha256(body).hexdigest(), "page_total": len(rows), "rows": rows}


def openrouter():
    url = "https://openrouter.ai/rankings"
    body = reader.fetch(url)
    soup = BeautifulSoup(body, "html.parser")
    stamp = re.search(r"Usage data through (\w+ \d+, \d{4})", soup.get_text(" ", strip=True))[1]
    table = next(t for t in soup.select("table") if t.caption and t.caption.get_text(strip=True) == "Model rankings by tokens processed")
    names = {"Step 5 Preview": "Step 5", "MiniMax M3.1 Flash": "MiniMax-M3.1-Flash"}
    rows = []
    for tr in table.select("tbody tr"):
        rank, model, vendor, tokens, change = [cell.get_text(" ", strip=True) for cell in tr.select("th,td")]
        amount = re.fullmatch(r"([\d.]+)T tokens", tokens)
        if not amount or int(rank) != len(rows) + 1:
            raise ValueError(f"Unrecognized OpenRouter unit or rank: {tokens}, {rank}")
        rows.append(dict(source_rank=int(rank), model=names.get(model, model), vendor=VENDORS[vendor],
                         score=float(amount[1]), change=change))
    if len(rows) != 10:
        raise ValueError("Incomplete weekly OpenRouter leaderboard")
    return {"source_url": url, "usage_through": datetime.strptime(stamp, "%b %d, %Y").date().isoformat(),
            "checked_at": CHECKED, "sha256": sha256(body).hexdigest(), "rows": rows}


if __name__ == "__main__":
    reader.CACHE = CACHE
    arena_board()
    livebench()
    manual = {name: scale_board(path) for name, path in
              (("scale", "hle-diamond"), ("hss", "hss"), ("multichallenge", "multichallenge?tab=large"), ("rli", "rli"),
               ("swe_full", "swe_bench_pro_public_v2?tab=full"), ("swe_hard", "swe_bench_pro_public_v2?tab=hard"))}
    manual["openrouter"] = openrouter()
    write(HERE / "manual-boards.json", manual)
