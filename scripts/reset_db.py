from decouple import config
from django.conf import settings
from django.db import connections

# import os
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "..\core.settings")

settings.configure(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": config("DB_NAME"),
            "USER": config("DB_USERNAME"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": config("DB_HOST"),
            "PORT": config("DB_PORT"),
        }
    }
)

database_name = settings.DATABASES["default"]["NAME"]
connection = connections["default"]

# Check if the schema exists
with connection.cursor() as cursor:
    cursor.execute("SHOW SCHEMAS")
    existing_schemas = [row[0] for row in cursor.fetchall()]

if database_name in existing_schemas:
    print(f"Database '{database_name}' already exists, dropping it...")
    # Drop the database if it exists
    with connection.cursor() as cursor:
        cursor.execute(f"DROP DATABASE {database_name}")
    print(f"Database '{database_name}' dropped")

# Create the database if it doesn't exist
with connection.cursor() as cursor:
    cursor.execute(f"CREATE DATABASE {database_name}")
    print(f"Database '{database_name}' created")
