import os
import logging
from .reserverd_items import reserved_items

logger = logging.getLogger(__name__)

def book_property(target_url, ID, session):
    try:
        url = "https://plaza.newnewnew.space/portal/object/frontend/react/format/json"
        username = os.getenv("DJANGO_USERNAME")
        password = os.getenv("DJANGO_PASSWORD")
        timeout = int(os.getenv("TIMEOUT", 1000))

        # 1) Get the id and __hash__ from special api
        config_resp = session.get(
            "https://plaza.newnewnew.space/portal/core/frontend/getformsubmitonlyconfiguration/format/json",
            headers={
                "Accept": "application/json, text/plain, */*",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": target_url,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/136.0.0.0 Safari/537.36"
            },
            timeout=timeout,
        )
        config_resp.raise_for_status()
        try:
            config_json = config_resp.json()
        except ValueError:
            raise RuntimeError(
                "Unable to parse login configuration JSON. "
                f"Response text: {config_resp.text[:200]}"
            )

        # 2) Extract __id__ and __hash__ from the JSON structure under "form".
        form_cfg = config_json.get("form", {})
        __id__ = form_cfg.get("id")
        __hash__ = (
            form_cfg.get("elements", {})
            .get("__hash__", {})
            .get("initialData")
        )

        if not __id__ or not __hash__:
            raise RuntimeError(
                "Could not find loginForm.id or loginForm.elements['__hash__'].initialData in login configuration JSON. "
                f"Got: {config_json}"
            )

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,bg;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
            # Note: you don’t need to set referrer/sec-ch-ua in Python
        }

        # 3) Get the assigmentID/toewijzingID based on id - post call to special endpoint
        assetURL = "https://plaza.newnewnew.space/portal/object/frontend/getobject/format/json"
        try:
            assigmentResp = session.post(
                assetURL,
                data={"id": ID},
                headers=headers,
                timeout=timeout,
            )
            assigmentResp.raise_for_status()
            assigment_json = assigmentResp.json()
            toewijzingID = assigment_json.get("result", {}).get("assignmentID")
        except Exception as e:
            toewijzingID = None
            logger.error(f"Getting the assigmentID/toewijzingID based on id no successful: {e}")

        # 4) Build the form‐encoded payload for the reservation POST.
        payload = {
            "__id__": __id__,
            "__hash__": __hash__,
            "add": toewijzingID,
            "dwellingID": ID,
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,bg;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
            # Note: you don’t need to set referrer/sec-ch-ua in Python
        }

        # 5) call the reservation post api
        try:
            resp = session.post(
                url,
                data=payload,
                headers=headers,
                timeout=timeout,
                allow_redirects=True
            )
            resp.raise_for_status()

            # Check the JSON response from the login endpoint to see if it indicates success.
            try:
                post_json = resp.json()
            except ValueError:
                raise RuntimeError(
                    "Login response was not valid JSON. "
                    f"Status: {resp.status_code}, Text: {resp.text[:200]}"
                )

            if post_json.get("success"):
                print("✓ Successful booking of ", target_url)
            else:
                errmsg = post_json.get("error") or post_json.get("message") or repr(post_json)
                raise RuntimeError(f"Failed to book property. Server said: {errmsg}")
            reserved_items(session)
            return "Success"
        except Exception as e:
            print(f"Unexpected error during booking or fetching: {e}")
            return None
    except Exception as e:
        print(f"Unsuccessful booking with error: {e}")
        return "Failed"