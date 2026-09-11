@echo off
REM ---------------------------------------------------------------------------
REM Check X mentions and push anything needing a reply to the approval queue.
REM
REM Not registered as a scheduled task by default - run it by hand, or add a
REM task pointing at this file if you want it on a timer.
REM ---------------------------------------------------------------------------
call "%~dp0_env.bat" || exit /b 1
cd /d "%XS_API%" || exit /b 1

"%XS_PYTHON%" mention_watcher.py %*
exit /b %ERRORLEVEL%
