# dashboard/fetcher.py
import os
import time
import random
import logging
import requests
import datetime
import threading
import traceback
from .book_it import book_property
from .login import  login_to_plaza
from django.core.cache import cache
from .reserverd_items import reserved_items
from .models import Listing, Reaction, Offer
from django.utils.dateparse import parse_datetime, parse_date

logging.getLogger("urllib3").setLevel(logging.WARNING)
limit=os.getenv("LIMIT")
timeout = int(os.getenv("TIMEOUT"))

def fetch_actual_listings():
    """
    Fetches one page of current rental offers and returns
    the parsed JSON dict containing keys 'items', 'total', etc.
    """
    BASE_URL = "https://mosaic-plaza-aanbodapi.zig365.nl/api/v1/actueel-aanbod"

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
    interval = float(os.getenv("API_FETCH_INTERVAL", 1))


    print("Starting controlled API fetch loop… (use toggle to enable/disable)")

    # login
    session = login_to_plaza(username=usermane, password=password)
    # retrieve list of all reactions/reservations
    reserved_items(session=session)
    #take the id
    #Listing.objects.all().delete()
    Offer.objects.all().delete()
    start = datetime.datetime.now()
    while True:
        # get all reserved/booked/reacted properties obj_id

        # Auto start
        cache.set("fetch_enabled", True, timeout=None)
        obj_ids = list(Reaction.objects.values_list('obj_id', flat=True))
        if cache.get("fetch_enabled", False):
            cycle_start = datetime.datetime.now()
            try:
                # Retrieve all listings/offers
                listings_data = fetch_actual_listings()
                data = listings_data["data"]
                _metadata = listings_data["_metadata"]
                total_search_count = int(_metadata["total_search_count"])
                #record = Listing.objects.create(
                #    data=data,
                #    total_search_count=total_search_count
                #)

                # save offers
                for item in data:
                    city = item.get("city", {}).get("name", "")
                    dwelling_type = item.get("dwellingType", {}).get("localizedName", "")
                    publication_date = parse_datetime(item.get("publicationDate")) if item.get(
                        "publicationDate") else None
                    closing_date = parse_datetime(item.get("closingDate")) if item.get("closingDate") else None
                    available_from_date = parse_date(item.get("availableFromDate")) if item.get(
                        "availableFromDate") else None

                    offer, created = Offer.objects.update_or_create(
                        id=item["id"],
                        defaults={
                            "url_key": item.get("urlKey"),
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
                reactions = Reaction.objects.all().order_by("created_at")

                print(f"[{time.strftime('%H:%M:%S')}] Number of offers:", len(listings_data["data"]))
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
                cache.set("latest_api_data", list(reactions.values()), timeout=None)
                print(f"[{time.strftime('%H:%M:%S')}] Properties in", city, ": ", len(target_listings))

                # Not reacted properties
                obj_id_set = set(obj_ids)
                #for item in target_listings:

                target_listings = [item for item in target_listings if item["id"] not in obj_id_set]
                print(f"[{time.strftime('%H:%M:%S')}] Not booked properties in", city, ": ", len(target_listings))

                #Time to book it
                if len(target_listings) > 0:
                    start_booking_time = datetime.datetime.now()
                    print("It is now time time to book it")
                    #randomize
                    random.shuffle(target_listings)
                    #login
                    #session = login_to_plaza(username=usermane, password=password)
                    booked_properties = []
                    for item in target_listings:
                        ID = item.get("ID")
                        urlKey = item.get("urlKey")
                        base_url = "https://plaza.newnewnew.space/aanbod/huurwoningen/details/"
                        target_url = base_url + urlKey

                        # BOOK!!!!
                        if book_property(target_url, ID=ID) == "Success": booked_properties.append(item)
                        else: raise Exception("Failed to book property"+target_url)
                    print(len(booked_properties),"properties in ", city, "were booked for ", datetime.datetime.now()-start_booking_time)
                    for asset in booked_properties:
                        try:
                            target_listings.remove(asset)
                        except ValueError:
                            pass  # asset might already be removed, so ignore if not present
                    reactions = Reaction.objects.all().order_by('created_at')
                cache.set("latest_api_data", list(reactions.values()), timeout=None)
                total_properties = {
                    "cycle": datetime.datetime.now() - start,
                    "offer_count": Offer.objects.count(),
                    "total_reserved": len(obj_id_set),
                    "not_booked": len(target_listings),
                }
                cache.set("total_properties",total_properties,timeout=None)
            except Exception as e:
                print("Error during fetch iteration:", e)
                traceback.print_exc()
            start = datetime.datetime.now()
            time.sleep(interval)
            cycle_end = datetime.datetime.now()
            print("Cycle duration:", cycle_end - cycle_start)
        else:
            time.sleep(interval)
            print(f"[{time.strftime('%H:%M:%S')}] Fetch disabled; skipping.")


def start_fetch_loop():
    """
    Spawn the background thread. This is what AppConfig.ready() will call.
    """
    thread = threading.Thread(target=_fetch_loop, daemon=True)
    thread.start()