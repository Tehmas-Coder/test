# management/commands/populate_models.py

import pandas as pd
import requests
from django.core.management.base import BaseCommand
from apps.lookups.models import (
    Country,
    Region,
    Currency,
    Language,
    Timezone,
    State,
)


class Command(BaseCommand):
    help = "Populate Country, Currency, Region, Language, Timezone, and State models from an external API and CSV files"

    def handle(self, *args, **kwargs):
        countries_api_url = "https://restcountries.com/v3.1/all"

        response = requests.get(countries_api_url)
        if response.status_code == 200:
            countries_data = response.json()
            currencies_cache = {}
            regions_cache = {}
            languages_cache = {}
            timezones_cache = {}

            # Populate countries from API data
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
                                    "symbol": details.get("symbol", ""),
                                },
                            )
                            currencies_cache[currency_code] = currency
                        else:
                            currency = currencies_cache[currency_code]

                # Populate country
                country, created = Country.objects.get_or_create(
                    name=country_data["name"]["common"],
                    defaults={
                        "iso3_code": country_data["cca3"],
                        "iso2_code": country_data["cca2"],
                        "abbreviation": country_data["cca2"],
                        "lat": country_data.get("latlng", [None])[0],
                        "lon": country_data.get("latlng", [None])[1],
                        "dial_code": country_data.get("idd", {}).get("root", "")
                        + (country_data.get("idd", {}).get("suffixes", [""])[0]),
                        "capital": country_data.get("capital", [""])[0],
                        "is_un_member": country_data.get("unMember", False),
                        "flag": country_data.get("flags", {}).get("svg", ""),
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

                # Associate currency with country
                if currency:
                    country.currencies.add(currency)

                # Populate region
                region_name = country_data.get("region")
                if region_name:
                    if region_name not in regions_cache:
                        region, created = Region.objects.get_or_create(
                            name=region_name,
                            defaults={
                                "code": region_name[:3].upper(),
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

                # Populate languages
                language_data = country_data.get("languages")
                if language_data:
                    for language_code, language_name in language_data.items():
                        if language_code not in languages_cache:
                            language, created = Language.objects.get_or_create(
                                code=language_code,
                                defaults={
                                    "name": language_name,
                                    "abbreviation": language_code[:3].upper(),
                                },
                            )
                            languages_cache[language_code] = language
                        else:
                            language = languages_cache[language_code]

                        country.languages.add(language)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Language "{language.name}" created/exists'
                            )
                        )

                # Populate timezones
                timezones_data = country_data.get("timezones")
                if timezones_data:
                    for timezone_name in timezones_data:
                        if timezone_name not in timezones_cache:
                            timezone, created = Timezone.objects.get_or_create(
                                name=timezone_name,
                                defaults={
                                    "code": timezone_name,
                                    "abbreviation": timezone_name[:3].upper(),
                                },
                            )
                            timezones_cache[timezone_name] = timezone
                        else:
                            timezone = timezones_cache[timezone_name]

                        country.timezones.add(timezone)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Timezone "{timezone.name}" created/exists'
                            )
                        )

            # Populate states from CSV files
            states_csv_path = "data/states.csv"
            countries_csv_path = "data/countries.csv"

            try:
                states_df = pd.read_csv(states_csv_path)
                countries_df = pd.read_csv(countries_csv_path)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading CSV files: {e}"))
                return

            for _, state_row in states_df.iterrows():
                country_code = state_row["country_code"]
                country = Country.objects.filter(iso2_code=country_code).first()
                if country:
                    state, created = State.objects.get_or_create(
                        name=state_row["name"],
                        defaults={
                            "code": state_row["state_code"],
                            "abbreviation": state_row["state_code"],
                            "country": country,
                        },
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'State "{state.name}" created')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'State "{state.name}" already exists')
                        )

            # Update capital information for countries from countries.csv
            for _, country_row in countries_df.iterrows():
                country = Country.objects.filter(iso2_code=country_row["iso2"]).first()
                if country:
                    capital_name = country_row["capital"]
                    if capital_name:
                        country.capital = capital_name
                        country.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Updated capital for country "{country.name}"'
                            )
                        )

        self.stdout.write(self.style.SUCCESS("Finished populating models"))
