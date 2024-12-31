from django.db import models
from django.db.models import QuerySet

from apps.lookups.helpers.queryset_functions import get_organization_detailed_queryset
from core.models import BaseUserModel


class Timezone(BaseUserModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"


class Region(BaseUserModel):
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


class Country(BaseUserModel):
    name = models.CharField(max_length=255)
    iso2_code = models.CharField(max_length=2)
    iso3_code = models.CharField(max_length=3)
    abbreviation = models.CharField(max_length=255)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    dial_code = models.CharField(max_length=255, blank=True)
    capital = models.CharField(max_length=255, blank=True)
    flag = models.ImageField(upload_to="flags/", null=True, blank=True)
    flag_svg = models.TextField(null=True, blank=True)

    is_un_member = models.BooleanField(default=False)

    timezones = models.ManyToManyField("lookups.Timezone", related_name="countries")
    currencies = models.ManyToManyField("lookups.Currency", related_name="countries")
    languages = models.ManyToManyField("lookups.Language", related_name="countries")

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

    @classmethod
    def get_detail_queryset(cls):
        return (
            cls.objects.get_queryset()
            .prefetch_related(
                "timezones",
                "currencies",
                "languages",
                "states",
                "states__cities",
            )
            .order_by("name")
        )


class State(BaseUserModel):
    country = models.ForeignKey("lookups.Country", related_name="states", on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"

    def __str__(self):
        return self.name


class City(BaseUserModel):
    state = models.ForeignKey("lookups.State", related_name="cities", on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    is_capital = models.BooleanField(default=False)

    class Meta:
        app_label = "lookups"

    def __str__(self):
        return self.name


class Language(BaseUserModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(max_length=10)

    class Meta:
        app_label = "lookups"

    def __str__(self):
        return self.name


class Currency(BaseUserModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    symbol = models.CharField(max_length=255, blank=True)

    class Meta:
        app_label = "lookups"


class MeasuringUnit(BaseUserModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"


class MediaType(BaseUserModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"


class Package(BaseUserModel):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=255, null=True, blank=True)
    users = models.PositiveIntegerField()
    questions = models.PositiveIntegerField()
    exams = models.PositiveIntegerField()
    prep_exams = models.PositiveIntegerField()
    exam_attempts = models.PositiveIntegerField()

    class Meta:
        app_label = "lookups"


class Organization(BaseUserModel):
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE, null=True, blank=True)

    name = models.CharField(max_length=255)
    url = models.URLField(max_length=255, null=True, blank=True)
    encryption_key = models.CharField(max_length=255, null=True, blank=True)
    token = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = "lookups"

    @classmethod
    def get_detailed_queryset(cls, country=False, organization_users=False, organization_candidates=False, organization_packages=False) -> QuerySet:
        return get_organization_detailed_queryset(cls, country, organization_users, organization_candidates, organization_packages)
