import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

limit = os.getenv("LIMIT")
timeout = int(os.getenv("TIMEOUT"))

def fetch_actual_listings(session):
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

    try:
        resp = session.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=timeout,
            data=payload)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in fetcher.py fetch_actual_listings in running API: {e}")
        return None