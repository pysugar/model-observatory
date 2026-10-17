"""Prepare human/agent research work packets and inspect independent review status.

No LLM calls, credential provisioning, schedule changes or merge operations.
"""

import argparse
import json
from pathlib import Path
import sys

import preview_ci as ci

ROOT = ci.ROOT
POLICY = ROOT / "research/automation/policy.json"
SCOPES = {"all": "模型、价格和基准的近期变化", "models": "模型身份、可用性与 API 规格",
          "pricing": "计价单位、阶梯价、缓存价与过期优惠", "benchmarks": "近期公开基准与比较口径"}


def independent_reviews(reviews, author, head, allowed):
    """Latest non-comment review per allowed independent identity, at current head."""
    latest = {}
    for review in sorted(reviews, key=lambda item: item["id"]):
        login = review["user"]["login"]
        if login in allowed and login != author and review["state"] != "COMMENTED":
            latest[login] = review
    return sorted(login for login, review in latest.items()
                  if review["state"] == "APPROVED" and review["commit_id"] == head)


def packet(scope, destination):
    ci.require(scope in SCOPES, "Unsupported research scope")
    data = json.loads((ROOT / "report-data.json").read_text())
    commit = ci.publish.git("rev-parse", "HEAD")
    destination.mkdir(parents=True, exist_ok=True)
    value = {"schema_version": 1, "repository": ci.REPO, "base_sha": commit,
             "scope": scope, "report_reviewed_at": data["meta"]["reviewed_at"],
             "researcher": (ROOT / "research/automation/researcher.md").read_text(),
             "reviewer": (ROOT / "research/automation/reviewer.md").read_text(),
             "source_count": len(data["sources"]), "sources": data["sources"],
             "execution": {"llm_calls_started": False, "merge_enabled": False, "production_credentials": False}}
    ci.save(destination / "work-packet.json", value)
    (destination / "work-packet.md").write_text(
        f"# Model Observatory 研究任务\n\n范围：{SCOPES[scope]}。基线 `{commit}`，报告日期 {data['meta']['reviewed_at']}。\n\n"
        "此文件只准备任务，不代表调研已经运行。多名研究者可按厂商或主题分工，各自在源码分支提交 PR；"
        "独立复核者检查当前 head 的轻量清单。最终由用户审阅合并。\n\n"
        + value["researcher"] + "\n\n" + value["reviewer"], encoding="utf-8")
    return {"status": "prepared", "scope": scope, "base_sha": commit, "output": str(destination)}


def review_status(number):
    policy = json.loads(POLICY.read_text())
    ci.require(policy["auto_merge_enabled"] is False, "Automatic merge is not implemented/enabled; review identity and scope need owner approval first")
    pr = ci.repo_api(f"/pulls/{ci.positive(number)}")
    reviews = ci.pages(f"/pulls/{ci.positive(number)}/reviews")
    approved = independent_reviews(reviews, pr["user"]["login"], pr["head"]["sha"], policy["reviewer_logins"])
    return {"pr": int(number), "head_sha": pr["head"]["sha"], "state": pr["state"],
            "independent_approvals": approved, "review_identity_configured": bool(policy["reviewer_logins"]),
            "auto_merge": "disabled", "next_action": "Owner reviews current-head evidence and CI before merging",
            "note": "No reviewer login configured means unknown identity, not a passed review. This report never merges."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("packet")
    prepare.add_argument("--scope", choices=SCOPES, default="all")
    prepare.add_argument("--output", type=Path, default=ROOT / "test-results/research")
    review = sub.add_parser("review-status")
    review.add_argument("--pr", required=True)
    args = parser.parse_args()
    try:
        result = packet(args.scope, args.output) if args.command == "packet" else review_status(args.pr)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
