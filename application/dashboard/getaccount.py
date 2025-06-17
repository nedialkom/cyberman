import os
import time
import logging
import requests

timeout = int(os.getenv("TIMEOUT", 1000))

logger = logging.getLogger(__name__)

def getaccount(session):
    """
    Trys to account data (username)
    :param session:
    :return: True if username correct, else False
    """

    GET_ACCOUNT_URL = "https://plaza.newnewnew.space/portal/account/frontend/getaccount/format/json"

    for attempt in range(3):
        try:
            acct_resp = session.get(
                GET_ACCOUNT_URL,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": GET_ACCOUNT_URL,
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/136.0.0.0 Safari/537.36"
                },
                timeout=timeout,
            )
            acct_resp.raise_for_status()
            if acct_resp.status_code == 200:
                try:
                    acct_json = acct_resp.json()
                    # print("✓ Account info fetched successfully. User: ", acct_json.get("account", {}).get("username"))
                    break  # Success! Got User account!

                except ValueError:
                    logger.error(
                        f"Unable to parse account JSON after login. Response text: {acct_resp.text[:200]}"
                    )
                    if attempt == 2: return False # last attempt failed
            elif acct_resp.status_code == 524:
                logging.error(f"524 timeout from server. Retrying in {timeout} seconds.")
                if attempt == 2: return False # last attempt failed
                time.sleep(timeout)  # Wait and try again
            else:
                logger.error(f"Failed to fetch account info after login. HTTP {acct_resp.status_code}")
                if attempt == 2: return False # last attempt failed

        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection error to {GET_ACCOUNT_URL}: {e}")
            if attempt == 2: return False # last attempt failed

    if acct_json.get("account", {}).get("username") == os.getenv("DJANGO_USERNAME"):
        return True
    else:
        return False
