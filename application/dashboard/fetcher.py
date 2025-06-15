# dashboard/fetcher.py
import os
import time
import random
import logging
import datetime
import threading
import traceback
from .login import login_to_plaza
from .book_it import book_property
from .models import Reaction, Offer
from django.core.cache import cache
from .savelistings import savelistings
from .reserverd_items import reserved_items
from .getlistings import fetch_actual_listings


logger = logging.getLogger(__name__)

target_city = os.getenv("CITY")
limit=os.getenv("LIMIT")
timeout = int(os.getenv("TIMEOUT"))
session_timeout = int(os.getenv("SESSION_TIMEOUT"))


def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    # show 2 decimals for sub-second accuracy if needed
    sec = td.total_seconds() % 60
    parts.append(f"{sec:.2f}s")
    return " ".join(parts)

def _fetch_loop():
    """
    This function contains the infinite loop. It will be run in its own thread.
    """
    username = str(os.getenv("DJANGO_USERNAME"))
    password = str(os.getenv("DJANGO_PASSWORD"))
    interval = float(os.getenv("API_FETCH_INTERVAL", 1))

    # login
    session = login_to_plaza(username=username, password=password)
    if session is None:
        logger.error(f"[{time.strftime('%H:%M:%S')}] Initial login failed.")
        return None

    session_start = datetime.datetime.now()
    msg = f"[{time.strftime('%H:%M:%S')}] Server started at {session_start}"
    logger.error(msg)

    listings_data = fetch_actual_listings(session=session)
    if listings_data is None:
        logging.error(f"[{time.strftime('%H:%M:%S')}] No listings data received, starting without data.")
    data = listings_data["data"]
    savelistings(data=data, silent=True)
    logger.error(f"[{time.strftime('%H:%M:%S')}] Listings loaded in db")
    offer_count = Offer.objects.all().count()
    msg = f"[{time.strftime('%H:%M:%S')}] Total offers {offer_count}"
    logger.error(msg)

    offer_count_city = Offer.objects.filter(
        city="Delft"
    ).exclude(dwelling_type="Parkeergelegenheid").count()
    msg = f"[{time.strftime('%H:%M:%S')}] Offers in {target_city}: {offer_count_city}"
    logger.error(msg)

    # updated DB with the reserved items and get the DB items
    reactions = reserved_items(session=session)
    cache.set("latest_api_data", list(reactions.values()), timeout=None)
    reactions_count = len(reactions)
    msg = f"[{time.strftime('%H:%M:%S')}] Total reservations: {reactions_count}"
    logger.error(msg)

    # DB Cleanup
    #Listing.objects.all().delete()
    #Offer.objects.all().delete()

    start = datetime.datetime.now()
    cycles = 0

    while True:

        cycle_start = datetime.datetime.now()

        # Auto start - comment next line if not needed
        cache.set("fetch_enabled", True, timeout=None)

        if datetime.datetime.now() - session_start > datetime.timedelta(minutes=session_timeout):
            session_begin = datetime.datetime.now()
            session = login_to_plaza(username=username, password=password)
            if session is None:
                logger.error(f"[{time.strftime('%H:%M:%S')}] Intermediary login failed.")
                continue
            session_start = datetime.datetime.now()
            logger.error(f"[{time.strftime('%H:%M:%S')}] New login session started for {session_start - session_begin}.")

        if cache.get("fetch_enabled", False):

            try:
                # Retrieve all listings/offers
                listings_data = fetch_actual_listings(session=session)
                if listings_data is None:
                    logging.error(f"[{time.strftime('%H:%M:%S')}] No listings data received, skipping this cycle.")
                    continue
                data = listings_data["data"]

                # Check for changes in offer count
                if len(data) != offer_count:
                    msg = f"[{time.strftime('%H:%M:%S')}] Number of offers changed from: {offer_count} to: {len(data)}"
                    logger.error(msg)
                    offer_count = len(data)

                savelistings(data = data, silent=False)

                # Filter-out only the one in CITY
                target_listings=[]
                for item in data:
                    try:
                        item_city = item["city"]
                        item_city_name = item_city["name"]
                        item_dwellingType = item["dwellingType"]
                        item_dwellingType_categorie = item_dwellingType["categorie"]
                        if item_city_name == target_city and item_dwellingType_categorie == "woning":
                            target_listings.append(item)
                    except Exception as e:
                        logger.error(f"[{time.strftime('%H:%M:%S')}] Exception while fetching listings: {e}")

                if len(target_listings) != offer_count_city:
                    msg = f"[{time.strftime('%H:%M:%S')}] Number of offers in {target_city} changed from: {offer_count_city} to: {len(target_listings)}"
                    #print(msg)
                    logger.error(msg)
                    offer_count_city = len(target_listings)


                # Not reacted/booked properties

                # get all reserved/booked/reacted properties obj_id
                obj_id_set = set(list(Reaction.objects.values_list('obj_id', flat=True)))

                #target_listings contains all not booked properties
                target_listings = [item for item in target_listings if item["id"] not in obj_id_set]
                # print(f"[{time.strftime('%H:%M:%S')}] Not booked properties in", target_city, ": ", len(target_listings))

                #Time to book it
                len_target_listings = len(target_listings)
                if len_target_listings > 0:
                    start_booking_time = datetime.datetime.now()
                    msg = f"[{time.strftime('%H:%M:%S')}] Found {len_target_listings} not booked properties. Start booking at {start_booking_time}"
                    #print(msg)
                    logger.error(msg)

                    #randomize
                    if len_target_listings > 1: random.shuffle(target_listings)

                    #fresh login (do we need it as we relog each .env SESSION_TIMEOUT)
                    session = login_to_plaza(username=username, password=password)
                    booked_properties = []
                    for item in target_listings:
                        ID = item.get("ID")
                        urlKey = item.get("urlKey")
                        base_url = "https://plaza.newnewnew.space/aanbod/huurwoningen/details/"
                        target_url = base_url + urlKey

                        # BOOK IT !!!!
                        if book_property(target_url=target_url, ID=ID, session=session) == "Success":
                            msg=f"[{time.strftime('%H:%M:%S')}] Booked property {target_url}"
                            #print(msg)
                            logger.error(msg)
                            booked_properties.append(item)
                        else:
                            msg = f"[{time.strftime('%H:%M:%S')}] Failed to book property {target_url}"
                            #print(msg)
                            logger.error(msg)


                    msg=f"[{time.strftime('%H:%M:%S')}] {len(booked_properties)} properties in {target_city} were booked for {datetime.datetime.now()-start_booking_time}"
                    #print(msg)
                    logger.error(msg)

                    for asset in booked_properties:
                        try:
                            target_listings.remove(asset)
                        except ValueError:
                            pass  # asset might already be removed, so ignore if not present

                ### Update reactions after booking of all found properties
                reactions = Reaction.objects.all().order_by("created_at")



                cache.set("latest_api_data", list(reactions.values()), timeout=None)
                # print(f"Total cycles: {cycles}; Average cycle duration {average_cycle_time}; Last cycle duration {cycle_end-last_cycle_time}")

            except Exception as e:
                logger.error(f"[{time.strftime('%H:%M:%S')}] Error during fetch iteration: {e}")
                traceback.print_exc()
            time.sleep(interval)
        else:
            time.sleep(interval)
            print(f"[{time.strftime('%H:%M:%S')}] Fetch disabled; skipping.")

        cycles += 1
        cycle_end = datetime.datetime.now()
        average_cycle_time = (cycle_end - start) / cycles
        last_cycle_time = cycle_end - cycle_start
        metadata = [{"average_cycle_time": format_timedelta(average_cycle_time),
                    "last_cycle_time": format_timedelta(last_cycle_time),
                    "cycles":cycles,
                    "total_duration":format_timedelta(cycle_end - start),
        },]

        cache.set("metadata", metadata, timeout=None)


def start_fetch_loop():
    """
    Spawn the background thread. This is what AppConfig.ready() will call.
    """
    thread = threading.Thread(target=_fetch_loop, daemon=True)
    thread.start()