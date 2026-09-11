import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv(os.path.join(BASE_DIR, '.env.local'))

IS_VERCEL = os.environ.get("VERCEL") == "1"

if IS_VERCEL:
    DATA_DIR = os.path.join("/tmp", "follower-dashboard")
    os.makedirs(DATA_DIR, exist_ok=True)
else:
    DATA_DIR = os.path.join(BASE_DIR, "data")
    os.makedirs(DATA_DIR, exist_ok=True)

X_AUTH_TOKEN = os.environ.get("X_AUTH_TOKEN", "")
X_PROXY = os.environ.get("X_PROXY", "")
CT0 = os.environ.get("CT0", "")
TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
AUTO_POST_SECRET = os.environ.get("AUTO_POST_SECRET", "")
AUTO_POST_GROUP = os.environ.get("AUTO_POST_GROUP", "Tech & AI")
AUTO_POST_MAX_PER_DAY = int(os.environ.get("AUTO_POST_MAX_PER_DAY", "8"))
