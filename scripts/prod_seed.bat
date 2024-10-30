python manage.py populate_country_data
REM --------------------------------- USER -------------------------------------
python manage.py loaddata prod_user_seed.json
python manage.py loaddata prod_role_seed.json
python manage.py loaddata prod_user_role_seed.json
python manage.py loaddata prod_resource_seed.json
python manage.py loaddata prod_permission_seed.json
python manage.py loaddata prod_role_permission_seed.json
REM -------------------------------- LOOKUPS -----------------------------------
python manage.py loaddata prod_media_type_seed.json
python manage.py loaddata prod_measuring_unit_seed.json
python manage.py loaddata prod_tag_seed.json
python manage.py loaddata prod_package_seed.json
REM --------------------------------- ORGANIZATION -------------------------------------
python manage.py loaddata prod_organization_seed.json
python manage.py loaddata prod_organization_package_seed.json
python manage.py loaddata prod_organization_user_seed.json
REM ----------------------------- QUESTION BANK --------------------------------
python manage.py loaddata prod_question_type_seed.json
python manage.py loaddata prod_education_level_seed.json
python manage.py loaddata prod_difficulty_level_seed.json
python manage.py loaddata prod_subject_seed.json
python manage.py loaddata prod_subject_education_level_seed.json
