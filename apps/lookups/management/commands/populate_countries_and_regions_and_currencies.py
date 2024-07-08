# lookups/management/commands/populate_countries_and_regions.py

import requests
from django.core.management.base import BaseCommand
from apps.lookups.models import Country, Region, Currency


class Command(BaseCommand):
    help = "Populate Country, Currency, and Region models from an external API"

    def handle(self, *args, **kwargs):
        countries_api_url = "https://restcountries.com/v3.1/all"

        # Fetch and populate countries, currencies, and regions
        response = requests.get(countries_api_url)
        if response.status_code == 200:
            countries_data = response.json()
            currencies_cache = {}
            regions_cache = {}

            for country_data in countries_data:
                # Populate currency
                currency_data = country_data.get("currencies")
                currency = None
                if currency_data:
                    for currency_code, details in currency_data.items():
                        if currency_code not in currencies_cache:
                            currency, created = Currency.objects.get_or_create(
                                code=currency_code,
                                defaults={
                                    "name": details.get("name", currency_code),
                                    "abbreviation": currency_code,
                                },
                            )
                            currencies_cache[currency_code] = currency
                        else:
                            currency = currencies_cache[currency_code]

                # Populate country
                country, created = Country.objects.get_or_create(
                    name=country_data["name"]["common"],
                    defaults={
                        "code": country_data["cca3"],
                        "abbreviation": country_data["cca2"],
                        "currency": currency,
                    },
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Country "{country.name}" created')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Country "{country.name}" already exists')
                    )

                # Populate region
                region_name = country_data.get("region")
                if region_name:
                    if region_name not in regions_cache:
                        region, created = Region.objects.get_or_create(
                            name=region_name,
                            defaults={
                                "code": region_name[
                                    :3
                                ].upper(),  # Example code, modify as needed
                                "abbreviation": region_name[:3].upper(),
                            },
                        )
                        regions_cache[region_name] = region
                    else:
                        region = regions_cache[region_name]

                    country.add_region(region)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Country "{country.name}" added to region "{region.name}"'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "Finished populating Country, Currency, and Region models"
            )
        )
