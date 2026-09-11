@echo off
REM ---------------------------------------------------------------------------
REM x-suite - single dev entry point.
REM
REM Opens two windows: the Flask API on :5000 and the Next.js app on :3000.
REM Close those windows to stop the services.
REM
REM Config lives in ONE place: the .env at this repo root.
REM ---------------------------------------------------------------------------
setlocal
call "%~dp0scripts\_env.bat" || exit /b 1

if not exist "%XS_REPO%\.env" (
  echo.
  echo   [!] No .env found at:
  echo       %XS_REPO%\.env
  echo.
  echo   Copy .env.example to .env and fill in your credentials first.
  echo.
  pause
  exit /b 1
)

echo.
echo   x-suite
echo   ---------------------------------------------
echo   repo    %XS_REPO%
echo   python  %XS_PYTHON%
echo   env     %XS_REPO%\.env
echo.

echo   starting API  -^>  http://localhost:5000
start "x-suite API" /D "%XS_API%" cmd /k ""%XS_PYTHON%" app.py"

echo   starting Web  -^>  http://localhost:3000
start "x-suite Web" /D "%XS_WEB%" cmd /k "npm run dev"

echo.
echo   Two windows opened. Close them to stop the services.
echo.

endlocal
