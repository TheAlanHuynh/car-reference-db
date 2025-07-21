from urllib.parse import urlparse

SCRAPERS: dict[str, object] = {}

def register(domain: str):
    def _wrap(cls):
        SCRAPERS[domain] = cls()
        return cls
    return _wrap

def get_scraper(url: str):
    host = urlparse(url).netloc.lower()
    for key, scraper in SCRAPERS.items():
        if key in host:
            return scraper
    return None