@echo off
REM ---------------------------------------------------------------------------
REM Shared environment for the x-suite ops scripts.
REM Sourced by the other scripts in this folder - not meant to be run directly.
REM
REM Defines:
REM   XS_REPO    absolute path to the monorepo root
REM   XS_API     services/api
REM   XS_WEB     apps/web
REM   XS_PYTHON  interpreter to use (override by setting XS_PYTHON first)
REM ---------------------------------------------------------------------------

REM %~dp0 is this script's folder. "%%~fI" normalises the trailing ".." into a
REM real absolute path. (Do NOT use pushd + %CD% here: %CD% is expanded when
REM the line is parsed, i.e. before pushd has run.)
for %%I in ("%~dp0..") do set "XS_REPO=%%~fI"

set "XS_API=%XS_REPO%\services\api"
set "XS_WEB=%XS_REPO%\apps\web"

REM Put the pure agent library on the import path. services/api imports it as
REM "social_agent", which lives at packages/agent/social_agent. Doing it here
REM keeps the library un-installed and the scripts self-contained.
set "PYTHONPATH=%XS_REPO%\packages\agent;%PYTHONPATH%"

REM Prefer an explicit override, then the interpreter that has the full
REM dependency set (Flask, psycopg2, praw, Scweet, playwright), then PATH.
if not defined XS_PYTHON if exist "C:\Python313\python.exe" set "XS_PYTHON=C:\Python313\python.exe"
if not defined XS_PYTHON set "XS_PYTHON=python"

exit /b 0
