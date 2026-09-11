@echo off
REM ---------------------------------------------------------------------------
REM One observation cycle: read the Reddit (and optionally X) feeds, analyse
REM new posts, and update accounts / topics / engagement profiles.
REM
REM Registered as Windows Task Scheduler task: FollowerDashboard-Observe
REM Recommended schedule: daily at 09:00.
REM ---------------------------------------------------------------------------
call "%~dp0_env.bat" || exit /b 1
cd /d "%XS_API%" || exit /b 1

"%XS_PYTHON%" runner.py %*
exit /b %ERRORLEVEL%
