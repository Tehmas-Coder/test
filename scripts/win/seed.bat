
REM -------------------------------- LOOKUPS -----------------------------------
python manage.py loaddata media_type_seed.json
python manage.py loaddata measuring_unit_seed.json
python manage.py populate_country_data
python manage.py loaddata tag_seed.json