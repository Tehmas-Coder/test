@echo off
REM Batch script to delete all migrations folders in the my-pyschometric-examination project, excluding venv directory

REM Get the directory of the batch script
SET SCRIPT_DIR=%~dp0

REM Navigate to the project root directory
SET ROOT_DIR=%SCRIPT_DIR%..\..

REM Normalize the path
FOR %%i IN ("%ROOT_DIR%") DO SET ROOT_DIR=%%~fi

REM Recursively find and delete all migrations directories, excluding venv
FOR /d /r %ROOT_DIR% %%x IN (migrations) DO (
    IF NOT "%%x"=="%ROOT_DIR%\venv\migrations" (
        IF EXIST "%%x" (
            ECHO Deleting %%x
            RMDIR /s /q "%%x"
        )
    )
)

ECHO All migrations folders have been deleted, excluding those in the venv directory.
PAUSE
