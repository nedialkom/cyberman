import os
import json
import logging
import requests
from .models import Reaction
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logging.getLogger("urllib3").setLevel(logging.WARNING)

def reserved_items(session: requests.Session):
    """
    Fetches all properties that the logged-in user has “reserved” (active reactions).
    Returns the parsed JSON response from:
      https://plaza.newnewnew.space/portal/registration/frontend/getactievereacties/format/json
    """

    def parse_int(value):
        try:
            if value in (None, '', 'None'):
                return None  # Or return 0 if you want
            return int(value)
        except Exception:
            return None  # Or 0

    def safe_parse_datetime(value):
        if not value or value in ('0000-00-00 00:00:00', '0000-00-00', '', None):
            return None
        try:
            return parse_datetime(value)
        except Exception:
            return None

    # Reaction.objects.all().delete()

    URLS = [
        'https://plaza.newnewnew.space/portal/registration/frontend/getactievereacties/format/json',
        'https://plaza.newnewnew.space/portal/registration/frontend/getreactiesinbehandeling/format/json',
        'https://plaza.newnewnew.space/portal/registration/frontend/gethistorischereacties/format/json',
    ]

    for URL in URLS:
        headers = {
            "Accept":             "application/json, text/plain, */*",
            "X-Requested-With":   "XMLHttpRequest",
            "Referer":            "https://plaza.newnewnew.space/",
            "User-Agent":         "Mozilla/5.0 (compatible; PlazaBot/1.0)"
        }
        timeout = int(os.getenv("TIMEOUT"))
        resp = session.get(URL, headers=headers, timeout=timeout)
        resp.raise_for_status()

        #print("DEBUG data:", resp.json()["result"]["items"])
        for item in resp.json()["result"]["items"]:
            closingDate = safe_parse_datetime(item["object"]["closingDate"])
            if closingDate is not None and timezone.is_naive(closingDate):
                closingDate = timezone.make_aware(closingDate, timezone.get_default_timezone())
            else: closingDate = datetime.min + timedelta(days=730)
            publicationDate = safe_parse_datetime(item["object"]["publicationDate"])
            if publicationDate is not None and timezone.is_naive(publicationDate):
                publicationDate = timezone.make_aware(publicationDate, timezone.get_default_timezone())
            else: publicationDate = datetime.min + timedelta(days=730)
            huidige_aanbieding = item.get("huidigeAanbieding")
            if huidige_aanbieding and huidige_aanbieding.get("uitersteReactiedatum"):
                uitersteReactiedatum = parse_datetime(huidige_aanbieding["uitersteReactiedatum"])
                if uitersteReactiedatum is not None and timezone.is_naive(uitersteReactiedatum):
                    uitersteReactiedatum = timezone.make_aware(uitersteReactiedatum, timezone.get_default_timezone())
            else:
                uitersteReactiedatum = None
            dt = parse_datetime(item["reactiedatum"])
            if dt is not None and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_default_timezone())

            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_default_timezone())

            if timezone.is_naive(publicationDate):
                publicationDate = timezone.make_aware(publicationDate, timezone.get_default_timezone())

            if timezone.is_naive(closingDate):
                closingDate = timezone.make_aware(closingDate, timezone.get_default_timezone())

            defaults = {
                "obj_id": int(item["object"]["id"]),
                "urlKey": "https://plaza.newnewnew.space/en/availables-places/living-place/details/" +
                          item["object"]["urlKey"],
                "closingDate": closingDate,
                "publicationDate": publicationDate,
                "kan_verwijderd_worden": item["kanVerwijderdWorden"],
                "toewijzing_id": int(item["toewijzingId"]),
                "reactiedatum": dt,
                "type": item["type"],
                "positie_is_definitief": item["positieIsDefinitief"],
                "positie": item["positie"],
                "motivatie": item["motivatie"],
                "advertentie": item.get("advertentie"),
                "object_data": item.get("object"),
                "huidige_aanbieding": item.get("huidigeAanbieding"),
                "uitersteReactiedatum": uitersteReactiedatum,
                "persoonlijke_aanbieding": item.get("persoonlijkeAanbieding"),
            }

            existing = Reaction.objects.filter(id=int(item["id"])).first()
            changed = False

            if existing:
                if existing.created_at:
                    defaults["created_at"] = existing.created_at
                # Compare each field you care about
                for key, value in defaults.items():
                    if getattr(existing, key) != value:
                        changed = True
                        break

            rec, created = Reaction.objects.update_or_create(
                id=int(item["id"]),
                defaults=defaults,
            )

            if created:
                print("New property booked")
            elif changed:
                print("Existing property updated (fields changed)")
            else:
                print("Existing property unchanged (no real update)")
    # correct created_at based on json
    try:
        with open('dashboard/delft_offers.json', 'r') as file:
            data = json.load(file)
        for entry in data:
            try:
                rec = Reaction.objects.filter(obj_id=entry["id"]).first()
                if rec:
                    rec.created_at = safe_parse_datetime(entry["created_at"])
                    rec.save(update_fields=["created_at"])
            except Exception as e:
                print(f"Error updating created_at for obj_id={entry['id']}: {e}")
    except Exception as e:
        print(e)

    for item in Reaction.objects.all():
        item.delta = item.reactiedatum - item.created_at
        item.save(update_fields=["delta"])
    return