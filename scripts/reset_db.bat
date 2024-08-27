REM --------------------------- RESETTING DATABASE ------------------------------
python .\scripts\reset_db.py
REM --------------------------- INITIALIZING MIGRATION ------------------------------
call .\scripts\migrate.bat
REM --------------------------- INITIALIZING SEED ------------------------------
call .\scripts\seed.bat