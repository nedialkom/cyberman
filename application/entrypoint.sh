#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for Postgres to be ready
# You can install 'wait-for-it' or use a simple loop. Here’s a minimalistic approach:
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

# Apply database migrations
python manage.py makemigrations dashboard
python manage.py migrate --noinput

# Create a Django superuser non-interactively (if it doesn't already exist)
#    Django will look for the three environment variables:
#      DJANGO_SUPERUSER_USERNAME
#      DJANGO_SUPERUSER_EMAIL
#      DJANGO_SUPERUSER_PASSWORD
#
#    If you run `createsuperuser --noinput` and a user with that username already
#    exists, Django will raise an IntegrityError. To avoid that, we can wrap it in a check.
#
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = "${DJANGO_SUPERUSER_USERNAME}"
email    = "${DJANGO_SUPERUSER_EMAIL}"
password = "${DJANGO_SUPERUSER_PASSWORD}"

# Only create if no existing user with that username
if not User.objects.filter(username=username).exists():
    print("Creating superuser ${DJANGO_SUPERUSER_USERNAME}")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print("Superuser ${DJANGO_SUPERUSER_USERNAME} already exists. Skipping.")
EOF

python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = "${DJANGO_USERNAME}"
email    = "${DJANGO_EMAIL}"
password = "${DJANGO_PASSWORD}"

# Only create if no existing user with that username
if not User.objects.filter(username=username).exists():
    print("Creating user ${DJANGO_USERNAME}")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print("User ${DJANGO_USERNAME} already exists. Skipping.")
EOF

# Collect static files (if using)
python manage.py collectstatic --noinput

# Start the fetch_api_loop in the background
# python manage.py fetch_api_loop >> /var/log/fetch_api_loop.log 2>&1 &

# Then run any passed command (e.g., runserver, gunicorn)
exec "$@"