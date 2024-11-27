@echo off
setlocal

REM Define the root path for the apps folder
set "rootDir=%~dp0..\apps"

REM Search for all folders named 'migrations' and delete them
for /d /r "%rootDir%" %%d in (migrations) do (
    if exist "%%d" (
        echo Deleting folder: %%d
        rd /s /q "%%d"
    )
)

echo All 'migrations' folders have been processed.

