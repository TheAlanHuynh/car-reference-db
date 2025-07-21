from backend.scrapers import register

@register("example.com")
class DummyScraper:
    def scrape(self, url: str) -> dict:
        # Pretend every example.com URL is a 2018 Honda Civic LX
        return {
            "make":        "Honda",
            "model":       "Civic",
            "year":        2018,
            "trim":        "LX",
            "price":       1750000,      # cents
            "mileage_km":  88000,
            "city":        "Calgary",
            "province":    "AB",
            # listing_date intentionally omitted so the UI can test “missing”
        }