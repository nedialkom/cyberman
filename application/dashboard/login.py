import os
import requests

def login_to_plaza(username: str, password: str):
    """
    Logs into https://plaza.newnewnew.space/ by:
      1) GETting the homepage to establish a session.
      2) GETting the login‐configuration JSON to scrape __id__ and __hash__.
      3) POSTing to the `loginbyservice/format/json` endpoint with those tokens + credentials.
      4) Verifying login by calling getaccount/format/json.
    """

    session = requests.Session()

    # 1) GET the homepage to pick up any initial cookies.
    LOGIN_PAGE_URL = "https://plaza.newnewnew.space/"
    timeout = int(os.getenv("TIMEOUT", 1000))
    resp_home = session.get(LOGIN_PAGE_URL, timeout=timeout)
    resp_home.raise_for_status()

    # 2) GET the login‐configuration JSON to retrieve __id__ and __hash__.
    #    This endpoint returns something like:
    #      {
    #        "formName": "Account_Form_LoginFrontend",
    #        "hash": "<a fresh token string>",
    #        …maybe other keys…
    #      }
    CONFIG_URL = "https://plaza.newnewnew.space/portal/account/frontend/getloginconfiguration/format/json"
    config_resp = session.get(
        CONFIG_URL,
        headers={
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": LOGIN_PAGE_URL,
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

    # Extract __id__ and __hash__ from the JSON structure under "loginForm".
    login_form_cfg = config_json.get("loginForm", {})
    __id__ = login_form_cfg.get("id")
    __hash__ = (
        login_form_cfg.get("elements", {})
                      .get("__hash__", {})
                      .get("initialData")
    )

    if not __id__ or not __hash__:
        raise RuntimeError(
            "Could not find loginForm.id or loginForm.elements['__hash__'].initialData in login configuration JSON. "
            f"Got: {config_json}"
        )

    # 3) Build the form‐encoded payload for the login POST.
    form_data = {
        "__id__":   __id__,
        "__hash__": __hash__,
        "username": username,
        "password": password
    }

    # 4) POST to the `loginbyservice/format/json` endpoint.
    LOGIN_POST_URL = "https://plaza.newnewnew.space/portal/account/frontend/loginbyservice/format/json"
    headers = {
        "Accept":                    "application/json, text/plain, */*",
        "Content-Type":              "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With":          "XMLHttpRequest",
        "Referer":                   LOGIN_PAGE_URL,
        "User-Agent":                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                                     "Chrome/136.0.0.0 Safari/537.36"
    }

    login_resp = session.post(
        LOGIN_POST_URL,
        data=form_data,
        headers=headers,
        timeout=timeout,
        allow_redirects=True
    )
    login_resp.raise_for_status()

    # 5) Check the JSON response from the login endpoint to see if it indicates success.
    try:
        login_json = login_resp.json()
    except ValueError:
        raise RuntimeError(
            "Login response was not valid JSON. "
            f"Status: {login_resp.status_code}, Text: {login_resp.text[:200]}"
        )

    # Typical patterns: { "success": true, … } or { "loggedIn": true, … } or { "redirect": "/…"}
    if login_json.get("success") or login_json.get("loggedIn") or login_json.get("redirect"):
        print("✓ Login appeared to succeed.")
    else:
        errmsg = login_json.get("error") or login_json.get("message") or repr(login_json)
        raise RuntimeError(f"Login failed. Server said: {errmsg}")

    # 6) Verify by calling the protected 'getaccount' endpoint
    GET_ACCOUNT_URL = "https://plaza.newnewnew.space/portal/account/frontend/getaccount/format/json"
    acct_resp = session.get(
        GET_ACCOUNT_URL,
        headers={
            "Accept":           "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer":          LOGIN_PAGE_URL,
            "User-Agent":       headers["User-Agent"]
        },
        timeout=timeout,
    )

    if acct_resp.status_code == 200:
        try:
            acct_json = acct_resp.json()
            print("✓ Account info fetched successfully. User: ", acct_json.get("account", {}).get("username"))
        except ValueError:
            raise RuntimeError(
                "Unable to parse account JSON after login. "
                f"Response text: {acct_resp.text[:200]}"
            )
    else:
        raise RuntimeError(
            f"Failed to fetch account info after login. HTTP {acct_resp.status_code}"
        )

    return session