"""Read Arena, LiveBench, Scale and OpenRouter without mixing their protocols.

Research-only dependencies: pyarrow and beautifulsoup4 in the configured environment.
The application build uses the resulting frozen JSON and does not fetch the network.
"""

from datetime import datetime, timezone
import hashlib
import json
import re

from bs4 import BeautifulSoup

from refresh_aa import HERE, ROOT, CHECKED, load, read, write, fetch

# 11-18 morning reused the 11-15 board files; this evening re-reads every board from them.
PREVIOUS = ROOT / "research/2026-11-15"

META_NAMES = {"Muse Wonder", "Muse Wonder 1.0", "Muse Wonder Full", "Muse Spark 1.3", "Muse Ember", "Muse Ember 1.0"}


def main():
    arena = load("arena", "research/2026-10-29/fetch_arena.py")
    arena.OUT = HERE / "arena.json"
    arena.REVISION = json.loads(fetch("https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset"))["sha"]
    arena.TRACKED += tuple(META_NAMES) + ("Gemini 4 Carbon", "Gemini 4 Hydrogen", "Claude Fable 5.2", "GPT-6.1 Terra",
                                          "GPT-6.2 Astra", "GPT-6.2 Sol")
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
        raise ValueError("Inspect the new LiveBench release and calculation rules before importing")
    live.RELEASE = "2026-11-06"
    live.BASE = "https://livebench.ai/data/20261106/"
    live.NAMES.update({"claude-fable-5.2":("Claude Fable 5.2","Anthropic",False),
                       "gemini-4-carbon":("Gemini 4 Carbon","Google",False),
                       "gemini-4-hydrogen":("Gemini 4 Hydrogen","Google",False),
                       "gpt-6.2-astra":("GPT-6.2 Astra","OpenAI",False),
                       "gpt-6.2-sol":("GPT-6.2 Sol","OpenAI",False)})
    live.PAGE_CHECK = {}
    live.get = lambda name: (live.BASE + name, fetch(live.BASE + name))
    live.main()
    doc = read(live.OUT)
    doc["release_discovery"] = {"url":bundle_url, "sha256":hashlib.sha256(bundle).hexdigest(), "checked_at":CHECKED,
        "note":"Read page bundle: weighted Overall and cost per successful task formulas unchanged; the 11-06 task set gained GPT-6.2 Astra / Sol after 11-15."}
    write(live.OUT, doc)

    manual = read(PREVIOUS / "manual-boards.json")
    scale_url = "https://labs.scale.com/leaderboard/hle-diamond"
    body = fetch(scale_url)
    soup = BeautifulSoup(body, "html.parser")
    names = {slug:(name,vendor) for slug,name,vendor,*_ in manual["scale"]["rows"]}
    names.update({"claude-fable-5-2":("Claude Fable 5.2","Anthropic"), "inkling":("Inkling","Thinking Machines"),
                  "muse-ember-1.0":("Muse Ember","Meta")})
    rows, ranks = [], {}
    nodes = soup.select("[data-model-name]")
    for rank, node in enumerate(nodes,1):
        slug = node.get_text(strip=True)
        if slug == "muse-spark-open":
            continue
        if slug not in names:
            raise ValueError(f"Unreviewed Scale model: {slug}")
        parent, match = node.parent, None
        while parent and len(parent.select("[data-model-name]")) == 1:
            match = re.search(r"(\d+\.\d+)\s*±\s*(\d+\.\d+)(?:\s*Calib Err:\s*(\d+\.\d+))?", parent.get_text(" ",strip=True))
            if match:
                break
            parent = parent.parent
        if not match:
            raise ValueError(f"Missing Scale score: {slug}")
        name,vendor = names[slug]
        rows.append([slug,name,vendor,float(match[1]),float(match[2]),float(match[3]) if match[3] else None])
        ranks[slug] = rank
    manual["scale"].update(rows=rows, source_ranks=ranks, page_total=len(nodes), checked_at=CHECKED, read_at=CHECKED,
        source_url=scale_url, sha256=hashlib.sha256(body).hexdigest(), source_updated_at=None)

    usage_url = "https://openrouter.ai/rankings"
    body = fetch(usage_url)
    soup = BeautifulSoup(body,"html.parser")
    date = re.search(r"Usage data through (\w+ \d+, \d{4})",soup.get_text(" ",strip=True))
    if not date:
        raise ValueError("OpenRouter did not disclose a usage date")
    usage_date = datetime.strptime(date[1],"%b %d, %Y").date().isoformat()
    table = next(t for t in soup.select("table") if "Model rankings by tokens processed" in t.get_text())
    vendors = {"deepseek":"DeepSeek","tencent":"Tencent","z-ai":"Z.AI","openai":"OpenAI",
               "anthropic":"Anthropic","stepfun":"StepFun","moonshotai":"Moonshot AI","xiaomi":"Xiaomi"}
    names = {"Step 5 Preview":"Step 5", "Hy4":"Tencent Hy4", "Hy4 flash":"Tencent Hy4 Flash"}
    rows = []
    for tr in table.select("tbody tr"):
        cells = [c.get_text(" ",strip=True) for c in tr.select("th,td")]
        rank,name,vendor,tokens,change = cells
        match = re.fullmatch(r"([\d.]+)T tokens",tokens)
        if int(rank) != len(rows)+1 or not match:
            raise ValueError(f"Unreviewed OpenRouter rank or unit: {cells}")
        rows.append([names.get(name,name),vendors[vendor],float(match[1]),change])
    if len(rows) != 10:
        raise ValueError("OpenRouter weekly top ten is incomplete")
    manual["openrouter"].update(rows=rows, usage_through=usage_date, checked_at=CHECKED, read_at=CHECKED,
        source_url=usage_url, sha256=hashlib.sha256(body).hexdigest())
    manual["note"] = "各来源独立读取；Scale未披露评测日期，OpenRouter为滚动7天token用量。Meta开放权重系列不纳入。"
    write(HERE / "manual-boards.json", manual)
    print(json.dumps({"scale":len(manual["scale"]["rows"]),"openrouter_through":usage_date}))


if __name__ == "__main__":
    main()
