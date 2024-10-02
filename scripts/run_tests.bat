REM --------------------------- LOOKUPS APP TESTS ------------------------------
python manage.py test apps.lookups.tests --failfast
REM ------------------------------ USER APP TESTS ----------------------------------
python manage.py test apps.user.tests --failfast
REM ------------------------------ ORGANIZATION APP TESTS ----------------------------------
python manage.py test apps.organization.tests --failfast
REM ------------------------ QUESTION BANK APP TESTS ---------------------------
@REM python manage.py test apps.questionbank.tests --failfast
REM ------------------------ EXAM ADMIN APP TESTS ---------------------------
python manage.py test apps.exam_admin.tests --failfast
REM ------------------------ EXAM PUBLIC APP TESTS ---------------------------
python manage.py test apps.exam_public.tests --failfast
