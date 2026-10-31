"""Re-read Arena's official dataset and the latest published LiveBench release."""

from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import json
import re

from refresh_aa import load

HERE = Path(__file__).resolve().parent


def get(url):
    return urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=45).read()


def main():
    arena = load("arena", "research/2026-10-29/fetch_arena.py")
    arena.OUT = HERE / "arena.json"
    arena.REVISION = json.loads(get("https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset"))["sha"]
    arena.TRACKED += ("Gemini 4 Carbon", "GPT-6.1 Terra", "Muse Wonder", "Muse Wonder 1.0", "Muse Wonder Full", "Muse Spark 1.3")
    arena.main()
    doc = json.loads(arena.OUT.read_text())
    for board in doc["boards"].values():
        board["rows"] = [r for r in board["rows"] if r["vendor"] != "Meta"
                         or r["model"] in {"Muse Wonder", "Muse Wonder 1.0", "Muse Wonder Full", "Muse Spark 1.3"}]
    arena.OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")

    live = load("livebench", "research/2026-10-29/fetch_livebench.py")
    live.OUT = HERE / "livebench.json"
    html = get("https://livebench.ai/").decode()
    bundle_url = "https://livebench.ai/" + re.search(r'src="\./([^"]+\.js)"', html)[1]
    bundle = get(bundle_url)
    releases = re.findall(r"2026\d{4}", bundle.decode())
    latest = max(releases)
    live.RELEASE = f"{latest[:4]}-{latest[4:6]}-{latest[6:]}"
    live.BASE = f"https://livebench.ai/data/{latest}/"
    if live.RELEASE != "2026-10-25":
        raise ValueError("New LiveBench release: inspect names, weights and page checks before importing")
    # Historical costs are not assertions about the current, mutable cost.csv.
    # Keep score checks; current costs are independently checked against the live page.
    live.PAGE_CHECK = {}
    live.main()
    doc = json.loads(live.OUT.read_text())
    doc["release_discovery"] = {"url": bundle_url, "sha256": hashlib.sha256(bundle).hexdigest(),
                                "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    live.OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
