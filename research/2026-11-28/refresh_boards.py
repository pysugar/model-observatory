"""Collect Arena's pinned data, LiveBench's release files, Scale tabs and weekly usage."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import re

from bs4 import BeautifulSoup

from refresh_aa import CHECKED, HERE, PREVIOUS, fetch, load, read, write

REVISION = "4e9c2f140324df03c630a1fe91aaeacfb241f1ca"
prior = load(PREVIOUS / "refresh_boards.py")


def arena_board():
    arena = load(HERE.with_name("2026-10-29") / "fetch_arena.py")
    arena.REVISION = REVISION
    arena.TRACKED += tuple(prior.META) + prior.FOCUS + ("GLM-5.4", "Hy4", "Hy4 flash", "Tencent Hy4", "Hy4-Flash", "Inkling 2 Small", "Inkling 2 Mini")
    arena.OUT = HERE / "arena.json"
    arena.main()
    result = read(arena.OUT)
    for board in result["boards"].values():
        board["rows"] = [r for r in board["rows"] if r["vendor"] != "Meta" or r["model"] in prior.META]
    write(arena.OUT, result)


def livebench():
    live = load(HERE.with_name("2026-10-29") / "fetch_livebench.py")
    homepage = fetch("https://livebench.ai/").decode()
    bundle_url = "https://livebench.ai/" + re.search(r'src="\./([^"]+\.js)"', homepage)[1]
    bundle = fetch(bundle_url)
    if max(re.findall(r"2026\d{4}", bundle.decode())) != "20261106":
        raise ValueError("Review the new LiveBench task set and weights")
    live.RELEASE, live.BASE = "2026-11-06", "https://livebench.ai/data/20261106/"
    live.NAMES = {r["slug"]: (r["model"], r["vendor"], r["open_weights"])
                  for r in read(PREVIOUS / "livebench.json")["rows"] if r["vendor"]}
    live.NAMES["qwen3.8-max"] = ("Qwen3.8 Max", "Alibaba", False)
    live.NAMES["inkling-2-small"] = ("Inkling 2 Small", "Thinking Machines", True)
    live.NAMES["inkling-2-mini"] = ("Inkling 2 Mini", "Thinking Machines", True)
    live.get = lambda name: (live.BASE + name, fetch(live.BASE + name))
    live.PAGE_CHECK = {"gemini-4-neon": (87.4, 2.654), "gpt-6.2-astra": (84.9, 1.941)}
    live.OUT = HERE / "livebench.json"
    live.main()
    result = read(live.OUT)
    result["release_discovery"] = {"url": bundle_url, "sha256": sha256(bundle).hexdigest(), "checked_at": CHECKED}
    write(live.OUT, result)


def manual_boards():
    boards = {"scale": "hle-diamond", "hss": "hss", "multichallenge": "multichallenge?tab=large",
              "rli": "rli", "swe_full": "swe_bench_pro_public_v2?tab=full", "swe_hard": "swe_bench_pro_public_v2?tab=hard"}
    with ThreadPoolExecutor(max_workers=4) as executor:
        result = dict(zip(boards, executor.map(prior.scale_board, boards.values())))
    prior.VENDORS["tencent"] = "Tencent"
    usage = prior.openrouter()
    soup = BeautifulSoup(fetch(usage["source_url"]), "html.parser")
    if "asterisk when a day in the period shown is capped" not in soup.get_text(" ", strip=True):
        raise ValueError("Recheck OpenRouter's asterisk before interpreting BYOK traffic")
    for row in usage["rows"]:
        row["byok_capped"] = row["model"].endswith(" *")
        row["model"] = row["model"].removesuffix(" *")
    result["openrouter"] = usage
    write(HERE / "manual-boards.json", result)


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as executor:
        for task in [executor.submit(f) for f in (arena_board, livebench, manual_boards)]:
            task.result()
