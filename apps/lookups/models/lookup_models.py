from django.db import models
from django.db.models import QuerySet

from apps.lookups.helpers.queryset_functions import get_organization_detailed_queryset
from core.models import BaseUserModel
from utils.datetime_utils import get_current_utc_datetime_timestamp


def upload_to(instance, filename):
    folder_name = "media"
    timestamp = get_current_utc_datetime_timestamp()
    return f"{folder_name}/{timestamp}/{filename}"


class Timezone(BaseUserModel):
    """
    Represents a timezone.

    - id: Autofield (PK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    """

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"


class Region(BaseUserModel):
    """
    Represents a region.

    - id: Autofield (PK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    - countries: Country (M2M)
    """

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
    """
    Represents a country.

    - id: Autofield (PK)
    - name: CharField
    - iso2_code: CharField
    - iso3_code: CharField
    - abbreviation: CharField
    - lat: FloatField
    - lon: FloatField
    - dial_code: CharField
    - capital: CharField
    - flag: ImageField
    - flag_svg: TextField
    - is_un_member: BooleanField
    - timezones: Timezone (M2M)
    - currencies: Currency (M2M)
    - languages: Language (M2M)
    """

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

    timezones = models.ManyToManyField("lookups.Timezone")
    currencies = models.ManyToManyField("lookups.Currency")
    languages = models.ManyToManyField("lookups.Language")

    class Meta:
        app_label = "lookups"

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

    def add_region(self, region):
        """
        Adds a region to the country.
        """
        if not isinstance(region, Region):
            raise ValueError("Expected a Region instance.")
        self.regions.add(region)

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
    """
    Represents a state.

    - id: Autofield (PK)
    - country: Country (FK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    """

    country = models.ForeignKey("lookups.Country", related_name="states", on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"

    def __str__(self):
        return self.name


class City(BaseUserModel):
    """
    Represents a city.

    - id: Autofield (PK)
    - state: State (FK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    - is_capital: BooleanField
    """

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
    """
    Represents a language.

    - id: Autofield (PK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    """

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(max_length=10)

    class Meta:
        app_label = "lookups"

    def __str__(self):
        return self.name


class Currency(BaseUserModel):
    """
    Represents a currency.

    - id: Autofield (PK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    - symbol: CharField
    """

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    symbol = models.CharField(max_length=255, blank=True)

    class Meta:
        app_label = "lookups"


class MeasuringUnit(BaseUserModel):
    """
    Represents a measuring unit.

    - id: Autofield (PK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    """

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"


class MediaType(BaseUserModel):
    """
    Represents a media type.

    - id: Autofield (PK)
    - name: CharField
    - code: CharField
    - abbreviation: CharField
    """

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    class Meta:
        app_label = "lookups"


class Package(BaseUserModel):
    """
    Represents a package.

    - id: Autofield (PK)
    - name: CharField
    - abbreviation: CharField
    - users: PositiveIntegerField
    - questions: PositiveIntegerField
    - exams: PositiveIntegerField
    - prep_exams: PositiveIntegerField
    - exam_attempts: PositiveIntegerField
    """

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
    """
    Represents an organization.

    - id: Autofield (PK)
    - country: Country (FK)
    - logo: ImageField
    - name: CharField
    - url: URLField
    - encryption_key: CharField
    - token: CharField
    """

    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE, null=True, blank=True)
    logo = models.ImageField(upload_to=upload_to, null=True, blank=True)

    name = models.CharField(max_length=255)
    url = models.URLField(max_length=255, null=True, blank=True)
    encryption_key = models.CharField(max_length=255, null=True, blank=True)
    token = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = "lookups"

    @classmethod
    def get_detailed_queryset(cls, country=False, organization_users=False, organization_candidates=False, organization_packages=False) -> QuerySet:
        return get_organization_detailed_queryset(cls, country, organization_users, organization_candidates, organization_packages)
