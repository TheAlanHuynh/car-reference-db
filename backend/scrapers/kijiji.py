"""
Kijiji.ca vehicle-listing scraper
================================
Example URL:
https://www.kijiji.ca/v-cars-trucks/edmonton/2020-honda-civic-sport/1705824639

Approach:
* Prefer the JSON-LD Vehicle block.
* Fallback: scrape price & mileage from visible spans.
"""

from __future__ import annotations
import json, re, requests, datetime as dt
from bs4 import BeautifulSoup
from backend.scrapers import register

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
    "Referer": "https://www.google.com/",
}

LD_RE = re.compile(
    r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.S,
)
KM_RE = re.compile(r"([\d,]+)\s*km", re.I)
PRICE_RE = re.compile(r"\$?\s*([\d,]+)")

@register("kijiji.ca")
class KijijiScraper:
    def scrape(self, url: str) -> dict:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # --- 1 · try JSON-LD ---
        matches = LD_RE.findall(html)
        data = None
        for block in matches:
            try:
                j = json.loads(block)
            except json.JSONDecodeError:
                continue
            if j.get("@type") in ("Vehicle", "Car"):
                data = j
                break

        if data:
            vehicle = data
            brand  = (vehicle.get("brand") or {}).get("name", "")
            model  = vehicle.get("model", "")
            year   = vehicle.get("vehicleModelDate")
            price  = vehicle.get("offers", {}).get("price")
            mileage= vehicle.get("mileageFromOdometer", {}).get("value")
            loc    = vehicle.get("offers", {}).get("areaServed", {}).get("address", {}) or {}
            city   = loc.get("addressLocality")
            province = loc.get("addressRegion")
            date_str = vehicle.get("datePosted")
        else:
            # --- 2 · fallback DOM parse ---
            brand = model = year = price = mileage = city = province = date_str = None

            h1 = soup.find("h1")
            if h1:
                # e.g. “2020 Honda Civic Sport”
                parts = h1.text.strip().split()
                if len(parts) >= 3 and parts[0].isdigit():
                    year, brand, model = parts[0], parts[1].lower(), parts[2].lower()

            p_tag = soup.find("span", string=KM_RE)
            if p_tag:
                mileage = KM_RE.search(p_tag.text).group(1).replace(",", "")

            price_tag = soup.find("span", {"itemprop": "price"})
            if price_tag:
                price = PRICE_RE.search(price_tag.text).group(1).replace(",", "")

            loc_tag = soup.find("span", {"data-qa-id": "ad-description-location"})
            if loc_tag and "," in loc_tag.text:
                city, province = [x.strip() for x in loc_tag.text.split(",", 1)]

        listing_date = None
        if date_str:
            try:
                listing_date = dt.date.fromisoformat(date_str[:10])
            except ValueError:
                pass


        # If price or mileage still missing, look inside __NEXT_DATA__
        if (not price) or (not mileage):
            next_data = soup.find("script", id="__NEXT_DATA__")
            if next_data and next_data.string:
                try:
                    nxt = json.loads(next_data.string)
                    ad  = nxt["props"]["pageProps"]["ad"]

                    if not price:
                        price = ad.get("price")
                    if not mileage:
                        odo = ad.get("kilometers")
                        mileage = odo if isinstance(odo, int) else None

                    # city / province often here too
                    if not city or not province:
                        loc = ad.get("adLocation", {})
                        city = city or loc.get("city")
                        province = province or loc.get("province")
                except Exception:
                    pass    # swallow if structure changed
        return {
            "make":  (brand or "").lower(),
            "model": (model or "").lower(),
            "year":  int(year) if year and str(year).isdigit() else None,
            "trim":  None,  # Kijiji rarely provides trim in structured data
            "price": int(float(price) * 100) if price else None,
            "mileage_km": int(mileage) if mileage else None,
            "city": city,
            "province": province,
            "listing_date": listing_date,
        }