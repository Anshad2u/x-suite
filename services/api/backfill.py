"""One-time pipeline: scrape ALL accounts you follow, save to Postgres,
auto-categorize into groups by bio keywords. Safe to re-run (upserts).
Usage: python backfill.py [username] [--limit N]
"""
import sys

import config
import db
import data_models as dm


CATEGORY_RULES = [
    ("Saudi Govt", ["وزارة", "هيئة", "أمانة", "سفارة", "مجلس", "government", "ministry",
                    "authority", "embassy", "municipality", "council", "gov"]),
    ("News & Media", ["news", "media", "أخبار", "صحف", "صحفية", "إعلام", "عاجل", "journal",
                      "breaking", "press", "newspaper", "قناة", "times", "post", "herald",
                      "alarabiya", "aljazeera", "العربية", "الجزيرة", "reporter", "مراسل"]),
    ("Islamic & Dawah", ["islam", "quran", "قرآن", "شيخ", "داعية", "إسلامي", "مسجد", "mosque",
                         "fatwa", "فتوى", "hadith", "حديث", "ummah", "دعوة", "تلاوة", "imam", "إمام"]),
    ("Tech & AI", ["ai", "tech", "developer", "engineer", "software", "saas", "startup",
                   "machine learning", "data", "cloud", "devops", "programmer", "تقني",
                   "برمجة", "code", "coding", "python", "javascript", "cyber", "blockchain"]),
    ("Business & Finance", ["finance", "invest", "business", "ceo", "founder", "entrepreneur",
                            "trading", "stocks", "crypto", "اقتصاد", "تجارة", "استثمار",
                            "ريادة", "marketer", "marketing", "تسويق"]),
    ("Sports", ["football", "soccer", "sport", "كرة", "رياضة", "coach", "athlete",
                "لاعب", "مدرب", "نادي", "fc ", "united", "fifa"]),
    ("Entertainment", ["music", "artist", "actor", "film", "movie", "فنان", "ممثل",
                       "طرب", "singer", "موسيقى", "comedy", "كوميدي", "designer", "مصمم"]),
]


def categorize(display_name, bio):
    text = f"{display_name or ''} {bio or ''}".lower()
    hits = []
    for cat_name, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in text:
                hits.append(cat_name)
                break
    return hits


GROUP_COLORS = {
    "Saudi Govt": "#0ea5e9",
    "News & Media": "#ef4444",
    "Islamic & Dawah": "#22c55e",
    "Tech & AI": "#8b5cf6",
    "Business & Finance": "#f59e0b",
    "Sports": "#14b8a6",
    "Entertainment": "#ec4899",
}


def main():
    username = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else (
        config.TWITTER_USERNAME or "me")
    limit = 3000
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    dm.init_dbs()
    for cat in GROUP_COLORS:
        dm.create_group(cat, f"Auto-created: {cat}", GROUP_COLORS[cat])
    print(f"groups ready")

    categorize_only = "--categorize-only" in sys.argv

    if categorize_only:
        rows = db.query_all('SELECT username, display_name, bio FROM followers')
        follower_rows = [(r['username'], r['display_name'], r['bio']) for r in rows]
        print(f"loaded {len(follower_rows)} existing profiles from DB (no scraping)")
    else:
        from scraper import _get_scweet
        s = _get_scweet()
        if not s:
            print("ERROR: no X auth token")
            return

        following = s.get_following([username], limit=limit)
        print(f"fetched {len(following)} profiles")

        import psycopg2.extras
        conn = db.get_conn()
        cur = conn.cursor()

        follower_rows = []
        for user in following:
            uname = user.get('username', '')
            if not uname:
                continue
            follower_rows.append((
                uname,
                user.get('name', ''),
                user.get('description', ''),
                user.get('followers_count', 0),
                user.get('following_count', 0),
                user.get('statuses_count', 0),
                bool(user.get('verified', False)),
                user.get('created_at', '')))

        psycopg2.extras.execute_values(cur, '''INSERT INTO followers
            (username, display_name, bio, followers_count, following_count, tweets_count, verified, created_at)
            VALUES %s
            ON CONFLICT (username) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                bio = EXCLUDED.bio,
                followers_count = EXCLUDED.followers_count,
                following_count = EXCLUDED.following_count,
                tweets_count = EXCLUDED.tweets_count,
                verified = EXCLUDED.verified,
                created_at = EXCLUDED.created_at,
                fetched_at = NOW()''',
            follower_rows, page_size=250)
        conn.commit()
        print(f"upserted {len(follower_rows)} followers")
        follower_rows = [(r[0], r[1], r[2]) for r in follower_rows]

    cat_map = {}
    uncategorized = []
    for uname, dname, bio in follower_rows:
        cats = categorize(dname, bio)
        if cats:
            cat_map[uname] = cats[:3]
        else:
            uncategorized.append(uname)

    import psycopg2.extras
    conn = db.get_conn()
    cur = conn.cursor()
    all_usernames = [r[0] for r in follower_rows]
    cur.execute('SELECT id, username FROM followers WHERE username = ANY(%s)', (all_usernames,))
    id_by_username = {u: i for i, u in cur.fetchall()}

    assign_rows = [
        (id_by_username[uname], cat)
        for uname, cats in cat_map.items()
        for cat in cats
        if uname in id_by_username
    ]
    psycopg2.extras.execute_values(cur, '''INSERT INTO follower_groups (follower_id, group_name)
        VALUES %s ON CONFLICT DO NOTHING''', assign_rows, page_size=500)
    conn.commit()
    print(f"assigned {len(assign_rows)} group memberships")

    counts = {}
    for _, cat in assign_rows:
        counts[cat] = counts.get(cat, 0) + 1

    total_in_db = len(dm.get_all_followers())
    print("\n=== DONE ===")
    print(f"total in DB: {total_in_db}")
    for cat, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {cat}: {n}")
    print(f"  uncategorized: {len(uncategorized)}")


if __name__ == '__main__':
    main()
