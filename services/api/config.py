import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Monorepo root — two levels up from services/api.
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))

# Load order matters: python-dotenv does not override already-set variables,
# so the first file to define a key wins.
#
# The monorepo-root .env is the single source of truth and therefore loads
# first. The service-local files are legacy leftovers from before the merge;
# they are only consulted to fill in keys the root file does not define, so
# an un-migrated checkout still runs. Delete them once you are happy.
load_dotenv(os.path.join(ROOT_DIR, '.env'))
load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv(os.path.join(BASE_DIR, '.env.local'))

# Postgres connection string. Prefer the direct (non-pooled) endpoint for
# long-lived scripts; fall back to the pooled one for serverless callers.
# This is the single definition — db.py imports it rather than re-reading
# os.environ, so env loading only ever happens here.
POSTGRES_URL = (
    os.environ.get("POSTGRES_URL_NON_POOLING")
    or os.environ.get("POSTGRES_URL")
    or os.environ.get("DATABASE_URL_UNPOOLED")
    or os.environ.get("DATABASE_URL", "")
)

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

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
MENTION_WATCH_LIMIT = int(os.environ.get("MENTION_WATCH_LIMIT", "50"))
POST_JITTER_MIN = int(os.environ.get("POST_JITTER_MIN", "2"))
POST_JITTER_MAX = int(os.environ.get("POST_JITTER_MAX", "8"))
POST_MAX_RETRIES = int(os.environ.get("POST_MAX_RETRIES", "3"))

# Agent safety switch. Defaults to True so an unconfigured deployment
# can never post by accident. Set DRY_RUN=false to go live.
DRY_RUN = os.environ.get("DRY_RUN", "true")


def is_dry_run():
    """Return True when DRY_RUN is truthy (default True)."""
    return str(DRY_RUN).lower() in ("true", "1", "yes")

REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "")
REDDIT_MENTION_LIMIT = int(os.environ.get("REDDIT_MENTION_LIMIT", "50"))
REDDIT_POST_SUBREDDIT = os.environ.get("REDDIT_POST_SUBREDDIT", "")
REDDIT_POST_MAX_PER_DAY = int(os.environ.get("REDDIT_POST_MAX_PER_DAY", "3"))
REDDIT_FEED_SUBREDDITS = os.environ.get("REDDIT_FEED_SUBREDDITS", "")
REDDIT_FEED_LIMIT = int(os.environ.get("REDDIT_FEED_LIMIT", "20"))
REDDIT_FEED_KEYWORDS = os.environ.get("REDDIT_FEED_KEYWORDS", "")
REDDIT_FEED_DIGEST = os.environ.get("REDDIT_FEED_DIGEST", "")

# Authenticated Reddit session (browser cookies) for reliable feed reads
REDDIT_SESSION_COOKIE = os.environ.get("REDDIT_SESSION_COOKIE", "")
REDDIT_CSRF_TOKEN = os.environ.get("REDDIT_CSRF_TOKEN", "")
REDDIT_TOKEN_V2 = os.environ.get("REDDIT_TOKEN_V2", "")

GROQ_API_KEYS = [k for k in os.environ.get("GROQ_API_KEYS", "").split(",") if k]
GROQ_MODEL = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

# Curate toward these domains (topic targeting; no user-history learning yet)
TARGET_TOPICS = [
    "AI", "machine learning", "LLM", "AI agents", "coding agents",
    "developer tools", "software engineering", "tech", "SaaS",
    "online business", "startups", "indie hackers", "automation",
]

REDDIT_OBSERVE_FEEDS = [
    "https://www.reddit.com/user/trickshame/m/ai_tools/.rss",
    "https://www.reddit.com/user/trickshame/m/saudi/.rss",
]

# On-target AI/tech/SaaS subreddits (curate domain; seed list, agent grows it)
REDDIT_OBSERVE_SUBREDDITS = [
    "AI_Agents", "LocalLLaMA", "SaaS", "indiehackers", "startups",
    "ArtificialIntelligence", "MachineLearning", "devtools", "CodingAgents",
]

# Seed X accounts to learn from (AI / SaaS / online-business); agent grows this
X_OBSERVE_ACCOUNTS = [
    "OpenAI", "AnthropicAI", "swyx", "dvassallo", "levelsio", "shl",
    "ylecun", "simonw", "mattshumer_", "jacobhilton", "lvwerra",
    "JayJayCee", "goodside", "omarsar0", "abacaj",
]
