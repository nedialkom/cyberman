import os
from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse


def index(request):
    """
    Main page
    :param request:
    :return: template "dashboard.html with context data
    """
    city = os.environ.get("CITY")
    username = os.environ.get("DJANGO_USERNAME")
    password = os.environ.get("DJANGO_PASSWORD")

    return render(request, "dashboard.html", {
        "city": city,
        "username": username,
        "password": password,
    })

def toggle_fetch(request, action):
    """
    AJAX endpoint that starts or stops the background fetch loop.
    Expected `action` values: "start" or "stop".
    Returns JSON: {"status": "started"} or {"status": "stopped"}.
    """
    if action == "start":
        cache.set("fetch_enabled", True, timeout=None)
        return JsonResponse({"status": "started"})
    elif action == "stop":
        cache.set("fetch_enabled", False, timeout=None)
        return JsonResponse({"status": "stopped"})
    else:
        return JsonResponse({"error": "invalid action"}, status=400)

def latest_data(request):
    """
    AJAX endpoint: returns whatever is currently in cache under 'latest_api_data'.
    If nobody’s fetched it yet, returns an empty JSON or a suitable default.
    """
    data = cache.get("latest_api_data", None)
    if data is None or data == []:
        # Return a default structure so the frontend can handle it.
        return JsonResponse({"status": "no_data_yet"})

    return JsonResponse(data, safe=False)

def target_listings(request):
    """
    AJAX endpoint: returns whatever is currently in cache under 'target_listings'.
    If nobody’s fetched it yet, returns an empty JSON or a suitable default.
    """
    data = cache.get("target_listings", None)
    if data is None or data == []:
        return JsonResponse({"status": "no_data_yet"})
    return JsonResponse(data, safe=False)
