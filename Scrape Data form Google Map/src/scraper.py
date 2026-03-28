"""Core scraping logic — Apify (primary) + Outscraper (fallback)."""

from src import config


def scrape_leads(
    queries: list[str],
    limit: int = 50,
    scrape_contacts: bool = True,
    scraper: str | None = None,
) -> list[dict]:
    """
    Scrape Google Maps for business leads.

    Args:
        queries: Search strings like ["dental clinics Dubai UAE"]
        limit: Max results per query
        scrape_contacts: Whether to enrich with emails
        scraper: Force "apify" or "outscraper". Auto-detects if None.

    Returns:
        List of lead dicts with standardized keys.
    """
    active = scraper or config.get_active_scraper()

    if active == "apify":
        raw = _scrape_apify(queries, limit, scrape_contacts)
    else:
        raw = _scrape_outscraper(queries, limit)

    leads = _normalize(raw, source=active)
    print(f"[scraper] {len(leads)} raw leads collected via {active}")
    return leads


# ── Apify ──────────────────���───────────────────────────────────────────

def _scrape_apify(queries: list[str], limit: int, scrape_contacts: bool) -> list[dict]:
    from apify_client import ApifyClient

    client = ApifyClient(config.APIFY_API_TOKEN)
    all_results = []

    for query in queries:
        print(f"[apify] Scraping: {query} (limit={limit})")
        run_input = {
            "searchStringsArray": [query],
            "maxCrawledPlacesPerSearch": limit,
            "language": config.DEFAULT_LANGUAGE,
            "scrapeContacts": scrape_contacts,
        }

        run = client.actor("compass/crawler-google-places").call(run_input=run_input)
        dataset = client.dataset(run["defaultDatasetId"])

        for item in dataset.iterate_items():
            all_results.append(item)

        print(f"[apify] Got {len(all_results)} results so far")

    return all_results


# ─��� Outscraper ──────────��──────────────────────────────────────────────

def _scrape_outscraper(queries: list[str], limit: int) -> list[dict]:
    from outscraper import ApiClient

    client = ApiClient(api_key=config.OUTSCRAPER_API_KEY)
    all_results = []

    for query in queries:
        print(f"[outscraper] Scraping: {query} (limit={limit})")
        results = client.google_maps_search(
            [query],
            limit=limit,
            language=config.DEFAULT_LANGUAGE,
        )
        # Outscraper returns list of lists (one per query)
        for query_results in results:
            if isinstance(query_results, list):
                all_results.extend(query_results)
            elif isinstance(query_results, dict):
                all_results.append(query_results)

        print(f"[outscraper] Got {len(all_results)} results so far")

    return all_results


# ── Normalize ───────��──────────────────────────────────────────────────

def _normalize(raw_results: list[dict], source: str) -> list[dict]:
    """Convert raw API responses to a common lead format."""
    leads = []

    for item in raw_results:
        if source == "apify":
            lead = _normalize_apify(item)
        else:
            lead = _normalize_outscraper(item)

        if lead.get("name"):  # skip empty entries
            leads.append(lead)

    return leads


def _normalize_apify(item: dict) -> dict:
    # Apify contact details are nested
    emails = []
    if item.get("emails"):
        emails = item["emails"] if isinstance(item["emails"], list) else [item["emails"]]
    elif item.get("email"):
        emails = [item["email"]]

    return {
        "name": item.get("title", ""),
        "phone": item.get("phone", ""),
        "email": emails[0] if emails else "",
        "all_emails": emails,
        "website": item.get("website", ""),
        "address": item.get("address", ""),
        "city": item.get("city", ""),
        "country": item.get("countryCode", ""),
        "rating": item.get("totalScore", ""),
        "reviews_count": item.get("reviewsCount", 0),
        "category": item.get("categoryName", ""),
        "opening_hours": _format_hours(item.get("openingHours", [])),
        "google_maps_url": item.get("url", ""),
        "place_id": item.get("placeId", ""),
        "latitude": item.get("location", {}).get("lat", ""),
        "longitude": item.get("location", {}).get("lng", ""),
        "source": "apify",
    }


def _normalize_outscraper(item: dict) -> dict:
    return {
        "name": item.get("name", ""),
        "phone": item.get("phone", ""),
        "email": item.get("email", "") or "",
        "all_emails": [item["email"]] if item.get("email") else [],
        "website": item.get("site", "") or item.get("website", ""),
        "address": item.get("full_address", "") or item.get("address", ""),
        "city": item.get("city", ""),
        "country": item.get("country", ""),
        "rating": item.get("rating", ""),
        "reviews_count": item.get("reviews", 0),
        "category": item.get("category", "") or item.get("type", ""),
        "opening_hours": item.get("working_hours", ""),
        "google_maps_url": item.get("google_maps_url", ""),
        "place_id": item.get("place_id", ""),
        "latitude": item.get("latitude", ""),
        "longitude": item.get("longitude", ""),
        "source": "outscraper",
    }


def _format_hours(hours_list: list) -> str:
    """Convert Apify's structured hours to a readable string."""
    if not hours_list:
        return ""
    parts = []
    for entry in hours_list:
        if isinstance(entry, dict):
            day = entry.get("day", "")
            hours = entry.get("hours", "")
            parts.append(f"{day}: {hours}")
        elif isinstance(entry, str):
            parts.append(entry)
    return " | ".join(parts)


# ── Email Enrichment via Hunter.io ──��──────────────────────────────────

def enrich_emails_hunter(leads: list[dict]) -> list[dict]:
    """
    For leads that have a website but no email, try Hunter.io domain search.
    Requires HUNTER_API_KEY in .env.
    """
    if not config.HUNTER_API_KEY:
        print("[hunter] No HUNTER_API_KEY set, skipping email enrichment")
        return leads

    from pyhunter import PyHunter
    hunter = PyHunter(config.HUNTER_API_KEY)

    enriched_count = 0
    for lead in leads:
        if lead["email"] or not lead["website"]:
            continue

        domain = _extract_domain(lead["website"])
        if not domain:
            continue

        try:
            result = hunter.domain_search(domain)
            if result and result.get("emails"):
                top_email = result["emails"][0].get("value", "")
                if top_email:
                    lead["email"] = top_email
                    lead["all_emails"] = [e.get("value") for e in result["emails"]]
                    enriched_count += 1
        except Exception as e:
            print(f"[hunter] Error for {domain}: {e}")
            continue

    print(f"[hunter] Enriched {enriched_count} leads with emails")
    return leads


def _extract_domain(url: str) -> str:
    """Extract domain from a URL."""
    url = url.strip().lower()
    url = url.replace("https://", "").replace("http://", "").replace("www.", "")
    return url.split("/")[0] if url else ""
