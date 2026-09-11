import config, db
import data_models, memory
data_models.init_dbs()
for mod in ("memory", "autopost", "engagement", "telegram_approval"):
    __import__(mod)
con = db.get_conn(); cur = con.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [r[0] for r in cur.fetchall()]
print("TOTAL_TABLES", len(tables))
print("TABLES:", ", ".join(tables))
print("----COUNTS----")
for t in tables:
    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
    print(f"{t}: {cur.fetchone()[0]}")
print("----KEY COLUMNS----")
for t in ("accounts", "followers", "groups", "follower_groups", "observed_posts",
          "post_insights", "posted_log", "topics", "decisions_log", "source_scores",
          "pending_drafts", "engagement_profiles"):
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", (t,))
    cols = cur.fetchall()
    print(f"{t}(" + ", ".join(f"{c[0]}:{c[1]}" for c in cols) + ")")
