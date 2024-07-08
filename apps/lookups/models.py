from django.db import models
from core.models import BaseModel
from typing import TYPE_CHECKING

# Create your models here.


class Timezone(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"


class Region(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    countries = models.ManyToManyField(
        "lookups.Country",
        related_name="regions",
    )

    class Meta:
        app_label = "lookups"

    def add_country(self, country):
        self.countries.add(country)

    def remove_country(self, country):
        self.countries.remove(country)

    def get_countries(self):
        return self.countries.all()

    def number_of_countries(self):
        return self.countries.count()

    def has_country(self, country):
        return self.countries.filter(id=country.id).exists()


class Country(BaseModel):
    name = models.CharField(max_length=255)
    iso2_code = models.CharField(max_length=2)
    iso3_code = models.CharField(max_length=3)
    abbreviation = models.CharField(max_length=255)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    dial_code = models.CharField(max_length=255, blank=True)
    capital = models.CharField(max_length=255, blank=True)

    timezones = models.ManyToManyField(
        "lookups.Timezone",
        related_name="countries",
    )

    currencies = models.ManyToManyField(
        "lookups.Currency",
        related_name="countries",
    )

    languages = models.ManyToManyField(
        "lookups.Language",
        related_name="countries",
    )

    flag = models.ImageField(upload_to="flags/", null=True, blank=True)

    is_un_member = models.BooleanField(default=False)

    class Meta:
        app_label = "lookups"

    def get_regions(self):
        return self.regions.all()  # type: ignore

    def add_region(self, region):
        self.regions.add(region)  # type: ignore

    def get_languages(self):
        return self.languages.all()

    def add_language(self, language):
        self.languages.add(language)

    def get_currencies(self):
        return self.currencies.all()

    def add_currency(self, currency):
        self.currencies.add(currency)

    def get_timezones(self):
        return self.timezones.all()

    def add_timezone(self, timezone):
        self.timezones.add(timezone)


class State(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    country = models.ForeignKey(
        "lookups.Country",
        related_name="states",
        on_delete=models.CASCADE,
    )

    class Meta:
        app_label = "lookups"

    def __str__(self):
        return self.name


class City(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    state = models.ForeignKey(
        "lookups.State",
        related_name="cities",
        on_delete=models.CASCADE,
    )

    is_capital = models.BooleanField(default=False)

    class Meta:
        app_label = "lookups"

    def __str__(self):
        return self.name


class Language(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(max_length=10)

    class Meta:
        app_label = "lookups"

    def __str__(self):
        return self.name


class Currency(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    symbol = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = "lookups"

    def get_country(self):
        return self.countries.all()  # type: ignore


class MeasuringUnit(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"


class MediaType(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"


class Tag(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"
