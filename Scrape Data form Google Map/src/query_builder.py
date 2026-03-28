"""Generate optimized Google Maps search queries for an industry + location."""

# Common industry synonyms to improve coverage
INDUSTRY_SYNONYMS = {
    "dentist": ["dental clinics", "dentist", "dental care center"],
    "dental": ["dental clinics", "dentist", "dental care center"],
    "construction": ["construction companies", "construction contractors", "building contractors"],
    "interior design": ["interior design firms", "interior designers", "interior decoration"],
    "security": ["security companies", "security services", "security guard services"],
    "real estate": ["real estate agencies", "real estate agents", "property dealers"],
    "hvac": ["HVAC companies", "air conditioning services", "heating and cooling"],
    "plumbing": ["plumbing services", "plumbers", "plumbing contractors"],
    "electrical": ["electrical contractors", "electricians", "electrical services"],
    "cleaning": ["cleaning services", "cleaning companies", "janitorial services"],
    "legal": ["law firms", "lawyers", "attorneys"],
    "law firm": ["law firms", "lawyers", "attorneys"],
    "accounting": ["accounting firms", "accountants", "CPA firms"],
    "restaurant": ["restaurants", "dining", "eateries"],
    "salon": ["beauty salons", "hair salons", "spas"],
    "auto repair": ["auto repair shops", "car mechanics", "auto service centers"],
    "veterinary": ["veterinary clinics", "animal hospitals", "pet clinics"],
    "gym": ["gyms", "fitness centers", "health clubs"],
    "marketing": ["marketing agencies", "digital marketing", "advertising agencies"],
    "it services": ["IT companies", "IT services", "software companies"],
    "landscaping": ["landscaping companies", "lawn care services", "garden services"],
    "photography": ["photography studios", "photographers", "photo studios"],
}

# Middle East countries need explicit country names for better results
MIDDLE_EAST_CITIES = {
    "dubai": "UAE",
    "abu dhabi": "UAE",
    "sharjah": "UAE",
    "ajman": "UAE",
    "riyadh": "Saudi Arabia",
    "jeddah": "Saudi Arabia",
    "dammam": "Saudi Arabia",
    "doha": "Qatar",
    "manama": "Bahrain",
    "kuwait city": "Kuwait",
    "muscat": "Oman",
    "amman": "Jordan",
    "cairo": "Egypt",
}


def build_queries(industry: str, location: str, num_queries: int = 3) -> list[str]:
    """
    Generate search queries for Google Maps.

    Args:
        industry: e.g. "dentist", "construction"
        location: e.g. "Dubai", "Houston, Texas"
        num_queries: how many query variations to generate (max 3)

    Returns:
        List of search strings like ["dental clinics Dubai UAE", "dentist Dubai UAE"]
    """
    industry_lower = industry.lower().strip()
    location_clean = location.strip()

    # Check if we need to append country for Middle East
    location_with_country = _append_country_if_needed(location_clean)

    # Get synonyms or fall back to raw industry term
    synonyms = INDUSTRY_SYNONYMS.get(industry_lower)
    if synonyms:
        terms = synonyms[:num_queries]
    else:
        # No synonyms found — use the raw term + common suffixes
        terms = [
            f"{industry_lower}",
            f"{industry_lower} companies",
            f"{industry_lower} services",
        ][:num_queries]

    queries = [f"{term} {location_with_country}" for term in terms]
    return queries


def _append_country_if_needed(location: str) -> str:
    """Add country name for Middle East cities if not already present."""
    location_lower = location.lower()
    for city, country in MIDDLE_EAST_CITIES.items():
        if city in location_lower and country.lower() not in location_lower:
            return f"{location}, {country}"
    return location
