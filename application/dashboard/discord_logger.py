import logging
import requests
import os

class DiscordHandler(logging.Handler):
    def emit(self, record):
        webhook_url = os.environ.get('DISCORD_WEBHOOK')
        if not webhook_url:
            return
        log_entry = self.format(record)
        payload = {'content': f'🚨 Error from Cyberman:\n{log_entry}'}
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            # Avoid infinite logging loop
            print(f"Failed to send Discord log: {e}")