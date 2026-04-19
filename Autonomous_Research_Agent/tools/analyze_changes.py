"""Classify + rank diffs using an LLM (Euri → OpenRouter), with rule-based fallback.

Consumes `.tmp/diff/*.json` (source of truth — never re-reads full scraped pages)
and produces a merged, ranked insights JSON across all competitors.

Usage:
    python tools/analyze_changes.py \\
        --diffs .tmp/diff/n8n.json,.tmp/diff/lindy.json \\
        --business-context "AI automation / agent platforms" \\
        --top 5 --run-id run_2026-04-19
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.env_loader import load_env, get_optional
from shared.logger import info, warn, error
from shared.cost_tracker import check_budget, record_cost, BudgetExceededError
from shared.sandbox import validate_write_path


PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.md").read_text()


# --- Rule-based fallback ---------------------------------------------------

KEYWORD_TAGS = [
    ("pricing", ["price", "pricing", "plan", "tier", "$", "per month", "per seat", "per user", "free forever", "enterprise"]),
    ("launch", ["launch", "introducing", "announcing", "now available", "new feature", "release", "ga ", "beta"]),
    ("hire", ["hiring", "we're hiring", "join the team", "careers", "job opening", "welcome", "appointed"]),
    ("partnership", ["partnership", "partners with", "integration with", "collaboration", "powered by"]),
    ("press", ["funding", "raised", "series", "acquired", "acquisition", "valuation"]),
]


def rule_classify(change: dict) -> tuple[str, str]:
    """Return (tag, why_it_matters_note) from keywords."""
    text_parts = []
    if change["type"] in ("added", "modified"):
        rec = change.get("after") or {}
        text_parts.extend([rec.get("title", ""), rec.get("description", ""), rec.get("meta_description", "")])
        text_parts.extend((rec.get("pricing_hints") or []))
        text_parts.extend(rec.get("headings") or [])
    if change["type"] == "modified":
        for field_name, v in (change.get("fields") or {}).items():
            text_parts.append(str(v.get("before", "")))
            text_parts.append(str(v.get("after", "")))

    blob = " ".join(str(x) for x in text_parts).lower()
    for tag, kws in KEYWORD_TAGS:
        if any(k in blob for k in kws):
            return tag, f"keyword-match:{tag}"
    return "other", "no-keyword-match"


def rule_score(change: dict, tag: str) -> int:
    base = {"pricing": 9, "launch": 8, "partnership": 7, "press": 7, "hire": 5, "site": 3, "other": 2}.get(tag, 2)
    if change["type"] == "modified":
        base += 1
    if change["kind"] == "news":
        base += 1
    return min(base, 10)


def rule_based_insights(all_changes: list[dict]) -> list[dict]:
    insights = []
    for c in all_changes:
        tag, note = rule_classify(c)
        insights.append({
            "change_id": c["change_id"],
            "competitor": c["competitor"],
            "kind": c["kind"],
            "type": c["type"],
            "url": c.get("url", ""),
            "tag": tag,
            "what_changed": _short_what_changed(c),
            "why_it_matters": note,
            "score": rule_score(c, tag),
            "source": c.get("url", ""),
            "method": "rule",
        })
    insights.sort(key=lambda x: x["score"], reverse=True)
    for rank, item in enumerate(insights, 1):
        item["rank"] = rank
    return insights


def _short_what_changed(c: dict) -> str:
    if c["type"] == "added":
        rec = c.get("after") or {}
        return f"New {c['kind']} item: {rec.get('title') or c.get('url', '')}"[:200]
    if c["type"] == "removed":
        rec = c.get("before") or {}
        return f"Removed {c['kind']} item: {rec.get('title') or c.get('url', '')}"[:200]
    if c["type"] == "modified":
        fields = list((c.get("fields") or {}).keys())
        return f"Modified {c['kind']} at {c.get('url', '')} — fields: {', '.join(fields)}"[:200]
    return f"Change at {c.get('url', '')}"


# --- LLM analysis ----------------------------------------------------------

def get_llm_client():
    """Return (client, model, provider) or (None, None, None) if no keys."""
    from openai import OpenAI
    euri = get_optional("EURI_API_KEY")
    orkey = get_optional("OPENROUTER_API_KEY")
    if euri:
        return OpenAI(base_url="https://api.euron.one/api/v1/euri", api_key=euri), "gpt-4o-mini", "euri"
    if orkey:
        return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=orkey), "openai/gpt-4o-mini", "openrouter"
    return None, None, None


def _call_llm_json(client, model: str, prompt: str, max_tokens: int = 1200) -> list:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=max_tokens,
    )
    content = (resp.choices[0].message.content or "").strip()
    match = re.search(r"\[[\s\S]*\]", content)
    if not match:
        raise ValueError("LLM response contained no JSON array")
    return json.loads(match.group())


def llm_classify(client, model: str, provider: str, competitor: str, business_context: str,
                 changes: list[dict], run_id: str) -> list[dict]:
    if not changes:
        return []
    # Budget check: cheap call, but still count.
    est_cost = 0.01
    check_budget(estimated_cost=est_cost, run_id=run_id)

    # Trim changes for prompt.
    trimmed = [
        {
            "change_id": c["change_id"],
            "kind": c["kind"],
            "type": c["type"],
            "url": c.get("url", ""),
            "before": c.get("before") if c["type"] in ("removed", "modified") else None,
            "after": c.get("after") if c["type"] in ("added", "modified") else None,
            "fields": c.get("fields") if c["type"] == "modified" else None,
        }
        for c in changes[:40]  # cap to control tokens
    ]

    prompt_tpl = load_prompt("classify_change_v1")
    prompt = (prompt_tpl
              .replace("{competitor_name}", competitor)
              .replace("{business_context}", business_context)
              .replace("{diff_json}", json.dumps(trimmed, ensure_ascii=False)))

    try:
        result = _call_llm_json(client, model, prompt, max_tokens=1500)
        record_cost(f"analyze_changes:classify:{provider}:{competitor}", est_cost, run_id=run_id)
        # Index by change_id to merge later.
        by_id = {r.get("change_id"): r for r in result if isinstance(r, dict) and r.get("change_id")}
        return [by_id.get(c["change_id"], {"change_id": c["change_id"], "tag": "other",
                                           "what_changed": _short_what_changed(c), "why_it_matters": "unclassified"})
                for c in changes]
    except Exception as e:
        warn(f"LLM classify failed for {competitor}: {e} — falling back to rules")
        return [{"change_id": c["change_id"],
                 "tag": rule_classify(c)[0],
                 "what_changed": _short_what_changed(c),
                 "why_it_matters": "rule-fallback"} for c in changes]


def llm_rank(client, model: str, provider: str, business_context: str,
             findings: list[dict], top_n: int, run_id: str) -> list[dict]:
    if not findings:
        return []

    est_cost = 0.01
    check_budget(estimated_cost=est_cost, run_id=run_id)

    prompt_tpl = load_prompt("rank_findings_v1")
    prompt = (prompt_tpl
              .replace("{business_context}", business_context)
              .replace("{top_n}", str(top_n))
              .replace("{findings_json}", json.dumps(findings[:60], ensure_ascii=False)))

    try:
        result = _call_llm_json(client, model, prompt, max_tokens=1200)
        record_cost(f"analyze_changes:rank:{provider}", est_cost, run_id=run_id)
        by_id = {r.get("change_id"): r for r in result if isinstance(r, dict) and r.get("change_id")}
        ranked = []
        for f in findings:
            r = by_id.get(f["change_id"], {})
            ranked.append({
                **f,
                "score": int(r.get("score", rule_score({"type": f.get("type", "modified"),
                                                         "kind": f.get("kind", "site")}, f.get("tag", "other")))),
                "rationale": r.get("rationale", "rule-fallback"),
            })
        ranked.sort(key=lambda x: x["score"], reverse=True)
        for rank, item in enumerate(ranked, 1):
            item["rank"] = rank
        return ranked
    except Exception as e:
        warn(f"LLM rank failed: {e} — falling back to rules")
        for f in findings:
            f["score"] = rule_score({"type": f.get("type", "modified"), "kind": f.get("kind", "site")},
                                    f.get("tag", "other"))
            f["rationale"] = "rule-fallback"
        findings.sort(key=lambda x: x["score"], reverse=True)
        for rank, item in enumerate(findings, 1):
            item["rank"] = rank
        return findings


# --- Orchestration ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Classify + rank competitor diffs")
    parser.add_argument("--diffs", required=True, help="Comma-separated .tmp/diff/*.json paths")
    parser.add_argument("--business-context", default="AI automation platforms")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--output", default=".tmp/insights.json")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM, use rule-based only")
    parser.add_argument("--run-id", default=None, help="Run ID for cost tracking")
    args = parser.parse_args()

    load_env()
    project_root = Path(__file__).parent.parent

    diff_files = [Path(project_root / f.strip()) for f in args.diffs.split(",") if f.strip()]
    all_changes = []
    competitor_summaries = {}
    for f in diff_files:
        if not f.exists():
            warn(f"diff file missing: {f}")
            continue
        data = json.loads(f.read_text())
        competitor = data.get("competitor", f.stem)
        competitor_summaries[competitor] = {
            "first_run": data.get("first_run", False),
            "counts": data.get("counts", {}),
        }
        for c in data.get("changes", []):
            c["competitor"] = competitor
            all_changes.append(c)

    info(f"analyze: {len(all_changes)} total changes across {len(competitor_summaries)} competitors")

    if not all_changes:
        insights = []
    elif args.no_llm:
        insights = rule_based_insights(all_changes)
    else:
        client, model, provider = get_llm_client()
        if not client:
            warn("no LLM key — rule-based insights only")
            insights = rule_based_insights(all_changes)
        else:
            try:
                per_competitor_changes: dict = {}
                for c in all_changes:
                    per_competitor_changes.setdefault(c["competitor"], []).append(c)
                classified: list = []
                for competitor, changes in per_competitor_changes.items():
                    tags = llm_classify(client, model, provider, competitor, args.business_context, changes, args.run_id or "adhoc")
                    # Merge tags onto source changes.
                    by_id = {t["change_id"]: t for t in tags}
                    for c in changes:
                        t = by_id.get(c["change_id"], {})
                        classified.append({
                            "change_id": c["change_id"],
                            "competitor": competitor,
                            "kind": c["kind"],
                            "type": c["type"],
                            "url": c.get("url", ""),
                            "tag": t.get("tag", "other"),
                            "what_changed": t.get("what_changed") or _short_what_changed(c),
                            "why_it_matters": t.get("why_it_matters", ""),
                            "source": c.get("url", ""),
                            "method": "llm",
                        })
                insights = llm_rank(client, model, provider, args.business_context, classified, args.top, args.run_id or "adhoc")
            except BudgetExceededError as e:
                error(f"budget exceeded during analyze — aborting: {e}")
                print(json.dumps({"status": "budget_exceeded", "error": str(e)}))
                sys.exit(2)

    output_path = validate_write_path(str(project_root / args.output))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "business_context": args.business_context,
        "competitor_summaries": competitor_summaries,
        "insights": insights,
        "counts": {"total_changes": len(all_changes), "ranked": len(insights)},
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(json.dumps({"status": "success", "output_path": str(output_path), "counts": payload["counts"]}))


if __name__ == "__main__":
    main()
