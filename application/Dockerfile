# 1. Use an official Python runtime as a parent image
FROM python:3.13-slim

# 2. Set environment variables. Prevents Python from writing .pyc files and buffering stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Create a working directory inside the container
WORKDIR /app

# 4. Install system dependencies (PostgreSQL client for migrations, build-essential for psycopg2)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy only requirements.txt first to leverage Docker caching
COPY requirements.txt .

# 6. Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 7. Copy the rest of the Django project code
COPY . .

# 8. Ensure entrypoint script has execution permissions
RUN chmod +x ./entrypoint.sh

# 9. Expose the port Django will run on
EXPOSE 9000

# 10. Set the default entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# 11. Specify the default command to run when the container starts
#CMD ["gunicorn", "settings.wsgi:application", "--bind", "0.0.0.0:9000"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:9000"]
