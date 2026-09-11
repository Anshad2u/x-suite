import os
import sys

# Vercel Python runtime only adds api/ to sys.path - add project root
# so app.py / config.py / data_models.py / scraper.py are importable.
_API_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_API_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app import app  # noqa: E402

# Vercel looks for `app` on the module
