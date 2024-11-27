
python manage.py populate_country_data
REM --------------------------------- USER -------------------------------------
python manage.py loaddata user_seed.json
python manage.py loaddata role_seed.json
python manage.py loaddata user_role_seed.json
python manage.py loaddata permission_seed.json
python manage.py loaddata resource_seed.json
python manage.py loaddata role_permission_seed.json
REM -------------------------------- LOOKUPS -----------------------------------
python manage.py loaddata media_type_seed.json
python manage.py loaddata measuring_unit_seed.json
python manage.py loaddata tag_seed.json
python manage.py loaddata package_seed.json
REM --------------------------------- ORGANIZATION -------------------------------------
python manage.py loaddata organization_seed.json
python manage.py loaddata organization_package_seed.json
python manage.py loaddata organization_user_seed.json
REM ----------------------------- QUESTION BANK --------------------------------
python manage.py loaddata question_type_seed.json
python manage.py loaddata education_level_seed.json
python manage.py loaddata difficulty_level_seed.json
python manage.py loaddata subject_seed.json
python manage.py loaddata subject_education_level_seed.json
python manage.py loaddata question_seed.json
python manage.py loaddata question_subject_seed.json
python manage.py loaddata question_subject_country_seed.json
python manage.py loaddata question_choice_seed.json
python manage.py loaddata question_retry_hint_seed.json
python manage.py loaddata question_tag_seed.json
REM ----------------------------- EXAM ADMIN --------------------------------
python manage.py loaddata schedule_seed.json
python manage.py loaddata exam_seed.json
python manage.py loaddata section_seed.json
python manage.py loaddata subsection_seed.json
python manage.py loaddata exam_subject_seed.json
python manage.py loaddata exam_subject_question_seed.json
REM ------------------------------ EXAM PUBLIC ---------------------------------
python manage.py loaddata candidate_seed.json
