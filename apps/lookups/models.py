from django.db import models
from core.models import BaseModel
from typing import TYPE_CHECKING

# Create your models here.


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
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    currency = models.ForeignKey(
        "lookups.Currency",
        related_name="countries",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        app_label = "lookups"

    def get_regions(self):
        return self.regions.all()  # type: ignore

    def add_region(self, region):
        region.countries.add(self)

    def remove_region(self, region):
        region.countries.remove(self)

    def has_region(self, region):
        return self.regions.filter(id=region.id).exists()  # type: ignore

    def get_currency(self):
        return self.currency


class Currency(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

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
