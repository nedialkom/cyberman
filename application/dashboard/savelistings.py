import logging
from .models import Offer
logger = logging.getLogger(__name__)
from django.utils.dateparse import parse_datetime, parse_date

def safe_parse_datetime(value):
    if not value or value in ('0000-00-00 00:00:00', '0000-00-00', '', None):
        return None
    try:
        return parse_datetime(value)
    except Exception:
        return None

def savelistings(data, silent=False):
    for item in data:
        city = item.get("city", {}).get("name", "")
        dwelling_type = item.get("dwellingType", {}).get("localizedName", "")
        publication_date = safe_parse_datetime(item.get("publicationDate")) if item.get(
            "publicationDate") else None
        closing_date = safe_parse_datetime(item.get("closingDate")) if item.get("closingDate") else None
        available_from_date = parse_date(item.get("availableFromDate")) if item.get(
            "availableFromDate") else None

        offer, created = Offer.objects.update_or_create(
            id=item["id"],
            defaults={
                "url_key": "https://plaza.newnewnew.space/en/availables-places/living-place/details/" + item.get(
                    "urlKey"),
                "city": city,
                "street": item.get("street"),
                "house_number": item.get("houseNumber"),
                "dwelling_type": dwelling_type,
                "total_rent": item.get("totalRent"),
                "net_rent": item.get("netRent"),
                "publication_date": publication_date,
                "closing_date": closing_date,
                "description": item.get("description"),
                "area_dwelling": item.get("areaDwelling"),
                "available_from_date": available_from_date,
                "data": item,
            }
        )

        if not silent:
            if created:
                msg = f"New offering found in {offer.city} and saved in DB.URL {offer.url_key}"
                # print(msg)
                logger.error(msg)