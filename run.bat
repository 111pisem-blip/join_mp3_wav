@echo off
REM ================================
REM Move to the folder where this .bat file is located
REM ================================
cd /d "%~dp0"

echo -----------------------------------------
echo Current folder: %cd%
echo -----------------------------------------

REM ================================
REM Activate Anaconda (base environment)
REM ================================
echo Activating Anaconda...
call "D:\program_files\anaconda3\Scripts\activate.bat" base

echo -----------------------------------------
echo Running Python script (merge MP3)...
echo -----------------------------------------

REM ================================
REM Run the Python script
REM ================================
python merge_mp3.py

echo.
echo -----------------------------------------
echo Script finished with exit code: %errorlevel%
echo -----------------------------------------

pause
