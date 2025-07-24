# backend/scrapers/autotrader.py
from __future__ import annotations
import json, re, requests, datetime as dt
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from backend.scrapers import register

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
    "Referer": "https://www.google.com/",
}

LD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.S,
)

@register("autotrader.ca")
class AutotraderScraper:
    def scrape(self, url: str) -> dict:
        url = self._resolve_canonical(url)

        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # --- choose the JSON-LD block that has @type="Vehicle" ---
        matches = LD_RE.findall(resp.text)
        data = None
        for block in matches:
            try:
                j = json.loads(block)
            except json.JSONDecodeError:
                continue
            if j.get("@type") == "Vehicle" or j.get("vehicle"):
                data = j
                break
        if not data:
            raise ValueError("No vehicle JSON-LD found")

        vehicle = data.get("vehicle", data)

        price_cad = vehicle.get("offers", {}).get("price")
        mileage   = vehicle.get("mileageFromOdometer", {}).get("value")

        loc = vehicle.get("offers", {}).get("areaServed", {}).get("address", {}) or {}
        city     = loc.get("addressLocality")
        province = loc.get("addressRegion")

        date_str = data.get("datePosted") or vehicle.get("offers", {}).get("validFrom")
        listing_date = None
        if date_str:
            try:
                listing_date = dt.date.fromisoformat(date_str[:10])
            except ValueError:
                pass

        if listing_date is None:
            listing_date = dt.date.today()          # fallback = fetch date

        brand = vehicle.get("brand")
        if isinstance(brand, dict):
            brand = brand.get("name")
        
        return {
            "make":   (brand or "").lower(),
            "model":  (vehicle.get("model") or "").lower(),
            "year":   int(vehicle.get("productionDate") or vehicle.get("vehicleModelDate") or 0) or None,
            "trim":   vehicle.get("vehicleConfiguration"),
            "price":  int(float(price_cad) * 100) if price_cad else None,
            "mileage_km": int(mileage) if mileage else None,
            "city":   city,
            "province": province,
            "listing_date": listing_date,
        }

    # ---------- helpers ----------
    def _resolve_canonical(self, url: str) -> str:
        """
        Handle ‘hub’ URLs that return 410 by extracting og:url or meta-refresh.
        """
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if r.status_code != 410:
            return r.url  # already canonical or 200 OK

        soup = BeautifulSoup(r.text, "html.parser")

        og = soup.find("meta", property="og:url")
        if og and og.get("content"):
            return og["content"]

        meta = soup.find("meta", attrs={"http-equiv": "refresh"})
        if meta and "url=" in meta.get("content", ""):
            target = meta["content"].split("url=", 1)[1]
            return urljoin(url, target)

        raise ValueError("Could not resolve canonical Autotrader URL from hub page")