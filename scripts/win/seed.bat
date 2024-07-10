
REM -------------------------------- LOOKUPS -----------------------------------
python manage.py loaddata media_type_seed.json
python manage.py loaddata measuring_unit_seed.json
python manage.py loaddata tag_seed.json
REM ----------------------------- QUESTION BANK --------------------------------
python manage.py loaddata question_type_seed.json
python manage.py loaddata education_level_seed.json
python manage.py loaddata difficulty_level_seed.json
python manage.py loaddata subject_seed.json
python manage.py loaddata subject_education_level_seed.json