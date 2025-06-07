import os
import sys
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        # Only start the fetch loop when running the 'runserver' command
        # and not when Django is collecting static files, running migrations, etc.
        #
        # The autoreloader sets the environment variable 'RUN_MAIN' = 'true' on the
        # reloaded process, so we kick off our thread only if RUN_MAIN is 'true'.
        #
        # Also check sys.argv[1] == "runserver" so we don't start during 'manage.py migrate', 'shell', etc.
        if os.environ.get("RUN_MAIN") == "true" and len(sys.argv) > 1 and sys.argv[1] == "runserver":
            # Import here to avoid side-effects at import time
            from .fetcher import start_fetch_loop
            start_fetch_loop()
