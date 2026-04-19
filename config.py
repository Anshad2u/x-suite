import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

FOLLOWERS_DB = os.path.join(DATA_DIR, "followers.db")
GROUPS_DB = os.path.join(DATA_DIR, "groups.db")

X_AUTH_TOKEN = os.environ.get("X_AUTH_TOKEN", "")
X_PROXY = os.environ.get("X_PROXY", "")