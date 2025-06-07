import requests
from .models import Reaction
import os

from django.utils.dateparse import parse_datetime
from django.utils import timezone

import logging
logging.getLogger("urllib3").setLevel(logging.WARNING)

def reserved_items(session: requests.Session):
    """
    Fetches all properties that the logged-in user has “reserved” (active reactions).
    Returns the parsed JSON response from:
      https://plaza.newnewnew.space/portal/registration/frontend/getactievereacties/format/json
    """
    URL = "https://plaza.newnewnew.space/portal/registration/frontend/getactievereacties/format/json"
    headers = {
        "Accept":             "application/json, text/plain, */*",
        "X-Requested-With":   "XMLHttpRequest",
        "Referer":            "https://plaza.newnewnew.space/",
        "User-Agent":         "Mozilla/5.0 (compatible; PlazaBot/1.0)"
    }
    timeout = int(os.getenv("TIMEOUT"))
    resp = session.get(URL, headers=headers, timeout=timeout)
    resp.raise_for_status()

    Reaction.objects.all().delete()
    #print("DEBUG data:", resp.json()["result"]["items"])
    for item in resp.json()["result"]["items"]:
        dt = parse_datetime(item["reactiedatum"])
        if dt is not None and timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_default_timezone())
        rec = Reaction.objects.create(
            id=int(item["id"]),
            kan_verwijderd_worden=item["kanVerwijderdWorden"],
            toewijzing_id=int(item["toewijzingId"]),
            reactiedatum=dt,  # Consider parsing to datetime
            type=item["type"],
            positie_is_definitief=item["positieIsDefinitief"],
            positie=item["positie"],
            motivatie=item["motivatie"],
            advertentie=item.get("advertentie"),
            object_data=item.get("object"),
            huidige_aanbieding=item.get("huidigeAanbieding"),
            persoonlijke_aanbieding=item.get("persoonlijkeAanbieding"),
        )
    return resp.json()