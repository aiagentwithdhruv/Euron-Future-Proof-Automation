"""
Google Maps Lead Scraper — CLI Entry Point

Usage:
    python main.py "dentists" "Dubai" --limit 50
    python main.py "construction" "Houston, Texas" --limit 100 --min-rating 4.0
    python main.py "security" "Riyadh" --limit 30 --sheets
    python main.py "interior design" "New York" --scraper outscraper
"""

import argparse

from src.query_builder import build_queries
from src.scraper import scrape_leads, enrich_emails_hunter
from src.exporter import clean_leads, to_csv, to_google_sheets, print_summary


def main():
    parser = argparse.ArgumentParser(description="Scrape leads from Google Maps")
    parser.add_argument("industry", help="Industry to search (e.g. 'dentist', 'construction')")
    parser.add_argument("location", help="City/region (e.g. 'Dubai', 'Houston, Texas')")
    parser.add_argument("--limit", type=int, default=50, help="Max leads per query (default: 50)")
    parser.add_argument("--min-rating", type=float, default=None, help="Minimum Google rating filter")
    parser.add_argument("--sheets", action="store_true", help="Also export to Google Sheets")
    parser.add_argument("--sheet-name", type=str, default=None, help="Google Sheets tab name")
    parser.add_argument("--scraper", choices=["apify", "outscraper"], default=None, help="Force a specific scraper")
    parser.add_argument("--no-enrich", action="store_true", help="Skip Hunter.io email enrichment")
    args = parser.parse_args()

    # Step 1: Build queries
    queries = build_queries(args.industry, args.location)
    print(f"\n[query] Generated {len(queries)} search queries:")
    for q in queries:
        print(f"  -> {q}")

    # Step 2: Scrape
    leads = scrape_leads(
        queries=queries,
        limit=args.limit,
        scrape_contacts=True,
        scraper=args.scraper,
    )

    if not leads:
        print("\n[!] No leads found. Try a different industry or location.")
        return

    # Step 3: Email enrichment (Hunter.io fallback)
    if not args.no_enrich:
        leads = enrich_emails_hunter(leads)

    # Step 4: Clean
    leads = clean_leads(leads, min_rating=args.min_rating)

    if not leads:
        print("\n[!] No leads remaining after cleaning.")
        return

    # Step 5: Export
    csv_path = to_csv(leads, args.industry, args.location)

    if args.sheets:
        to_google_sheets(leads, sheet_name=args.sheet_name)

    # Step 6: Summary
    print_summary(leads)
    print(f"  CSV saved: {csv_path}")


if __name__ == "__main__":
    main()
