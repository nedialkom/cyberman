# dashboard/fetcher.py

import time
from asyncio import timeout

import requests
import os
import datetime
import threading
import random
from django.core.cache import cache
from django.conf import settings
from .models import Listing, Reaction
from .login import  login_to_plaza
from .reserverd_items import reserved_items

import logging
logging.getLogger("urllib3").setLevel(logging.WARNING)

import os
limit=os.getenv("LIMIT")

def fetch_actual_listings():
    """
    Fetches one page of current rental offers and returns
    the parsed JSON dict containing keys 'items', 'total', etc.
    """
    BASE_URL = "https://mosaic-plaza-aanbodapi.zig365.nl/api/v1/actueel-aanbod"

    limit = os.getenv("LIMIT")
    page = 0
    locale = "nl_NL"
    sort_param = "+reactionData.aangepasteTotaleHuurprijs"

    params = {
        "limit":  limit,
        "page":   page,
        "locale": locale,
        "sort":   sort_param
    }

    headers = {
        "Accept":     "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (compatible; PlazaBot/1.0)"
    }

    payload = {"hidden-filters":{"$and":[{"dwellingType.categorie":{"$eq":"woning"}},{"rentBuy":{"$eq":"Huur"}},{"isExtraAanbod":{"$eq":""}},{"isWoningruil":{"$eq":""}},{"$and":[{"$or":[{"street":{"$like":""}},{"houseNumber":{"$like":""}},{"houseNumberAddition":{"$like":""}}]},{"$or":[{"street":{"$like":""}},{"houseNumber":{"$like":""}},{"houseNumberAddition":{"$like":""}}]}]}]}}

    timeout = int(os.getenv("TIMEOUT"))

    resp = requests.get(
        BASE_URL,
        params=params,
        headers=headers,
        timeout=timeout,
        data=payload)
    resp.raise_for_status()
    return resp.json()


def _fetch_loop():
    """
    This function contains the infinite loop. It will be run in its own thread.
    """
    usermane = str(os.getenv("DJANGO_USERNAME"))
    password = str(os.getenv("DJANGO_PASSWORD"))
    timeout = int(os.getenv("TIMEOUT", 1000))
    interval = int(os.getenv("API_FETCH_INTERVAL", 1))

    print("Starting controlled API fetch loop… (use toggle to enable/disable)")

    # login
    session = login_to_plaza(username=usermane, password=password)
    # retrieve list of all reactions/reservations
    reserved_items(session=session)
    #take the id
    obj_ids = list(Reaction.objects.values_list('obj_id', flat=True))
    Listing.objects.all().delete()
    while True:
        if cache.get("fetch_enabled", False):
            try:
                # Retrieve all listings/offers
                listings_data = fetch_actual_listings()
                data = listings_data["data"]
                _metadata = listings_data["_metadata"]
                total_search_count = int(_metadata["total_search_count"])
                record = Listing.objects.create(
                    data=data,
                    total_search_count=total_search_count
                )
                print(f"[{time.strftime('%H:%M:%S')}] Retrieved records:", len(listings_data["data"]))
                city = os.getenv("CITY")

                # Filter-out only the one in CITY
                target_listings=[]
                for item in data:
                    try:
                        item_city = item["city"]
                        item_city_name = item_city["name"]
                        item_dwellingType = item["dwellingType"]
                        item_dwellingType_categorie = item_dwellingType["categorie"]
                        if item_city_name == city and item_dwellingType_categorie == "woning": #and item["id"] in ids:
                            #print("Not reacted: https://plaza.newnewnew.space/aanbod/huurwoningen/details/https://plaza.newnewnew.space/aanbod/huurwoningen/details/", item["urlKey"])
                            target_listings.append(item)
                    except Exception as e:
                        print("Failed to extract city:", e)
                        pass
                cache.set("target_listings", target_listings, timeout=None)
                print(f"[{time.strftime('%H:%M:%S')}] Properties in", city, ": ", len(target_listings))

                # Not reacted properties
                for item in target_listings:
                    for obj_id in obj_ids:
                        obj_id_set = set(obj_ids)
                        target_listings = [item for item in target_listings if item["id"] not in obj_id_set]
                print(f"[{time.strftime('%H:%M:%S')}] Not booked properties in", city, ": ", len(target_listings))

                #Time to book it
                if len(target_listings) > 0:
                    print("Time to book it")
                cache.set("target_listings", target_listings, timeout=None)
            except Exception as e:
                print("Error during fetch iteration:", e)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Fetch disabled; skipping.")

        time.sleep(interval)


def start_fetch_loop():
    """
    Spawn the background thread. This is what AppConfig.ready() will call.
    """
    thread = threading.Thread(target=_fetch_loop, daemon=True)
    thread.start()