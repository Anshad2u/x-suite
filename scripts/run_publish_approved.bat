@echo off
REM ---------------------------------------------------------------------------
REM Publish drafts you approved in the console (or via Telegram).
REM
REM Closes the approve -> publish loop: the web Activity page only sets
REM status='approved'; this script sends those tweets and marks them posted.
REM It NEVER posts anything you did not approve.
REM
REM Registered as Windows Task Scheduler task: FollowerDashboard-PublishApproved
REM Recommended schedule: hourly (so an approval goes out within the hour).
REM
REM Extra args are forwarded, e.g.:
REM   run_publish_approved.bat --dry-run
REM ---------------------------------------------------------------------------
call "%~dp0_env.bat" || exit /b 1
cd /d "%XS_API%" || exit /b 1

"%XS_PYTHON%" publish_approved.py %*
exit /b %ERRORLEVEL%
