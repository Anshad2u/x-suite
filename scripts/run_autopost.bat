@echo off
REM ---------------------------------------------------------------------------
REM Drain the post queue, then run the autonomous autopost fallback.
REM
REM Registered as Windows Task Scheduler task: FollowerDashboard-AutoPost
REM Recommended schedule: every 2 hours.
REM
REM Extra args are forwarded, e.g.:
REM   run_autopost.bat --dry-run
REM ---------------------------------------------------------------------------
call "%~dp0_env.bat" || exit /b 1
cd /d "%XS_API%" || exit /b 1

"%XS_PYTHON%" autopost_runner.py %*
exit /b %ERRORLEVEL%
