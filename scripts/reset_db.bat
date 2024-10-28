REM --------------------------- DELETE MIGRATIONS ------------------------------
@REM call .\scripts\delete_migrations.bat
REM ---------------------------- RESET DATABASE --------------------------------
python .\scripts\reset_db.py
REM ---------------------------- MAKE MIGRATIONS -------------------------------
call .\scripts\migrations.bat
REM ---------------------------- POPULATE SEEDS --------------------------------
call .\scripts\seed.bat
