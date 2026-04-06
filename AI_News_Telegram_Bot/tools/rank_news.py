"""Rank and summarize news articles — LLM-powered or keyword fallback.

Usage:
    python tools/rank_news.py --input .tmp/raw_news.json --top 5
    python tools/rank_news.py --input .tmp/raw_news.json --top 5 --no-llm

Output:
    Writes JSON array of top N ranked articles to .tmp/ranked_news.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.env_loader import load_env, get_optional
from shared.logger import info, error
from shared.cost_tracker import check_budget, record_cost
from shared.sandbox import validate_write_path


# Keywords that boost relevance score
AI_KEYWORDS = [
    "openai", "anthropic", "google deepmind", "meta ai", "mistral",
    "gpt", "claude", "gemini", "llama", "llm", "large language model",
    "artificial intelligence", "machine learning", "deep learning",
    "ai agent", "agentic", "deployment", "production", "fine-tuning",
    "rag", "retrieval", "transformer", "diffusion", "multimodal",
    "regulation", "safety", "alignment", "open source", "benchmark",
]

# Trusted sources get a boost
AUTHORITY_SOURCES = {
    "TechCrunch AI": 3, "The Verge AI": 3, "MIT Tech Review": 4,
    "Ars Technica": 3, "Reuters": 4, "Bloomberg": 4, "Wired": 3,
    "The Information": 4, "VentureBeat": 3,
}


def keyword_score(article: dict) -> float:
    """Score an article based on keyword matches + source authority."""
    text = f"{article.get('title', '')} {article.get('description', '')}".lower()
    score = sum(2.0 for kw in AI_KEYWORDS if kw in text)
    source = article.get("source", "")
    score += AUTHORITY_SOURCES.get(source, 0)
    if article.get("published"):
        score += 1.0  # Boost articles with timestamps (more recent = more relevant)
    return score


def rank_with_keywords(articles: list, top_n: int) -> list:
    """Rank articles using keyword frequency + source authority. No AI needed."""
    scored = [(keyword_score(a), a) for a in articles]
    scored.sort(key=lambda x: x[0], reverse=True)
    ranked = []
    for score, article in scored[:top_n]:
        article["summary"] = article.get("description", "")[:200]
        article["rank_score"] = score
        article["rank_method"] = "keyword"
        ranked.append(article)
    info(f"Keyword ranking: top {len(ranked)} selected")
    return ranked


def rank_with_llm(articles: list, top_n: int) -> list:
    """Use LLM to rank and summarize. Falls back to keywords on failure."""
    from openai import OpenAI

    euri_key = get_optional("EURI_API_KEY")
    openrouter_key = get_optional("OPENROUTER_API_KEY")

    if euri_key:
        client = OpenAI(base_url="https://api.euron.one/api/v1/euri", api_key=euri_key)
        model = "gpt-4o-mini"
        provider = "euri"
    elif openrouter_key:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key)
        model = "openai/gpt-4o-mini"
        provider = "openrouter"
    else:
        info("No LLM key found — falling back to keyword ranking")
        return rank_with_keywords(articles, top_n)

    check_budget(estimated_cost=0.01)

    articles_text = ""
    for i, a in enumerate(articles[:25], 1):
        articles_text += f"{i}. [{a.get('source', 'Unknown')}] {a.get('title', '')}\n   {a.get('description', '')[:150]}\n\n"

    prompt = f"""You are an AI news editor. From these {len(articles[:25])} articles, pick the top {top_n} most important and interesting AI news stories.

For each pick, provide:
- The article number from the list
- A 1-2 sentence summary written for a tech-savvy audience

Return ONLY valid JSON — an array of objects:
[
  {{"index": 1, "summary": "One-line summary here"}},
  ...
]

Articles:
{articles_text}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        content = response.choices[0].message.content.strip()
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\[[\s\S]*\]', content)
        if not json_match:
            error("LLM returned no valid JSON — falling back to keywords")
            return rank_with_keywords(articles, top_n)

        picks = json.loads(json_match.group())
        record_cost("rank_news", 0.005)

        ranked = []
        for pick in picks[:top_n]:
            idx = pick.get("index", 1) - 1
            if 0 <= idx < len(articles):
                article = articles[idx]
                article["summary"] = pick.get("summary", article.get("description", "")[:200])
                article["rank_method"] = f"llm:{provider}"
                ranked.append(article)

        info(f"LLM ranking ({provider}): top {len(ranked)} selected")
        return ranked

    except Exception as e:
        error(f"LLM ranking failed: {e} — falling back to keywords")
        return rank_with_keywords(articles, top_n)


def main():
    parser = argparse.ArgumentParser(description="Rank and summarize AI news")
    parser.add_argument("--input", default=".tmp/raw_news.json", help="Input JSON file")
    parser.add_argument("--top", type=int, default=5, help="Number of top articles")
    parser.add_argument("--output", default=".tmp/ranked_news.json", help="Output file")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM, use keyword scoring only")
    args = parser.parse_args()

    load_env()

    input_path = Path(__file__).parent.parent / args.input
    if not input_path.exists():
        error(f"Input file not found: {input_path}")
        sys.exit(1)

    articles = json.loads(input_path.read_text())
    info(f"Loaded {len(articles)} articles for ranking")

    if args.no_llm:
        ranked = rank_with_keywords(articles, args.top)
    else:
        ranked = rank_with_llm(articles, args.top)

    output_path = validate_write_path(str(Path(__file__).parent.parent / args.output))
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(ranked, indent=2, ensure_ascii=False))
    print(json.dumps({"status": "success", "output_path": str(output_path), "articles": len(ranked)}))


if __name__ == "__main__":
    main()
