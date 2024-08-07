
python manage.py populate_country_data
REM --------------------------------- USER -------------------------------------
python manage.py loaddata user_seed.json
python manage.py loaddata role_seed.json
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
python manage.py loaddata question_seed.json
python manage.py loaddata question_choice_seed.json
python manage.py loaddata question_retry_hint_seed.json
REM ----------------------------- EXAM --------------------------------
python manage.py loaddata schedule_seed.json
python manage.py loaddata exam_seed.json
python manage.py loaddata section_seed.json
python manage.py loaddata subsection_seed.json