@echo off
echo Starting Follower Dashboard...
echo.
echo You need to set your X auth token first:
echo   set X_AUTH_TOKEN=your_auth_token_here
echo.
echo OR get it from: x.com > DevTools (F12) > Application > Cookies > x.com > auth_token
echo.
echo Starting Flask server on http://localhost:5000...
python app.py