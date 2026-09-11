@echo off
REM ---------------------------------------------------------------------------
REM Build the daily digest and send it to Telegram.
REM
REM Registered as Windows Task Scheduler task: FollowerDashboard-Digest
REM Recommended schedule: daily at 18:00.
REM
REM Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the root .env.
REM With them unset the digest is still printed to stdout.
REM ---------------------------------------------------------------------------
call "%~dp0_env.bat" || exit /b 1
cd /d "%XS_API%" || exit /b 1

"%XS_PYTHON%" daily_digest.py %*
exit /b %ERRORLEVEL%
