"""StockStalker v2 — source credibility weights.

A curated, offline tier map for the major financial-news publishers (no external
API). The long tail of unknown sources gets a neutral default — most real traffic
comes from the mapped publishers, so the credibility-weighted composite stays
directionally sound without enumerating thousands of outlets.

Our scraper ``source`` strings look like "Polygon (Reuters)", "Finviz (Bloomberg)",
"Yahoo Finance", or "Google News (CNBC)" — ``credibility_for`` pulls the real
publisher out of the parentheses (the aggregator wrapper) before matching.
"""

_DEFAULT = 0.5

# Match keys are lowercase substrings; keep them specific enough not to match
# inside unrelated words (e.g. use "associated press", never "ap").
SOURCE_CREDIBILITY: dict[str, float] = {
    # Tier 1 — wire services / paper of record
    "reuters": 1.0,
    "bloomberg": 1.0,
    "associated press": 1.0,
    "wall street journal": 0.97,
    "wsj": 0.97,
    "financial times": 0.97,
    "dow jones": 0.95,
    "the economist": 0.95,
    "barron": 0.93,
    # Tier 2 — major business / general press
    "cnbc": 0.9,
    "the new york times": 0.9,
    "new york times": 0.9,
    "bbc": 0.9,
    "marketwatch": 0.88,
    "washington post": 0.88,
    "morningstar": 0.85,
    "forbes": 0.85,
    "fortune": 0.85,
    "axios": 0.85,
    "the guardian": 0.85,
    "investor's business daily": 0.82,
    "investors business daily": 0.82,
    "cnn": 0.82,
    "politico": 0.82,
    # Tier 3 — markets / retail-investor outlets
    "nasdaq": 0.8,
    "business insider": 0.8,
    "kiplinger": 0.78,
    "yahoo": 0.78,
    "thestreet": 0.72,
    "zacks": 0.72,
    "investing.com": 0.72,
    "benzinga": 0.7,
    "seeking alpha": 0.7,
    "the motley fool": 0.68,
    "motley fool": 0.68,
    "finviz": 0.65,
    # Tier 4 — vendor-supplied press-release wires (low signal)
    "business wire": 0.5,
    "businesswire": 0.5,
    "globenewswire": 0.45,
    "pr newswire": 0.45,
    "prnewswire": 0.45,
    "accesswire": 0.4,
    "newsfile": 0.4,
}


def credibility_for(source: str) -> float:
    """Credibility weight in [0, 1] for a scraper ``source`` string.

    Extracts the real publisher from an aggregator wrapper — "Finviz (Bloomberg)"
    → "Bloomberg" — then matches the tier map, defaulting to a neutral 0.5.
    """
    if not source:
        return _DEFAULT
    publisher = source
    if "(" in source and ")" in source:  # unwrap "Aggregator (Publisher)"
        publisher = source[source.rfind("(") + 1 : source.rfind(")")]
    publisher = publisher.strip().lower()
    for key, weight in SOURCE_CREDIBILITY.items():
        if key in publisher:
            return weight
    return _DEFAULT
