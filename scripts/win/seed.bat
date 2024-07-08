
REM -------------------------------- LOOKUPS -----------------------------------
python manage.py loaddata media_type_seed.json
python manage.py loaddata measuring_unit_seed.json
python manage.py populate_countries_and_regions_and_currencies