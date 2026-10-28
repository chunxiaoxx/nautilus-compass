"""Probe nautilus DB schema state."""
import psycopg

dsn = "postgresql://postgres@localhost:5433/nautilus"
c = psycopg.connect(dsn)
cur = c.cursor()

cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
print("Total public tables:", cur.fetchone()[0])

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1 LIMIT 30")
print("First 30 tables:", [r[0] for r in cur.fetchall()])

try:
    cur.execute("SELECT version_num FROM alembic_version")
    print("Alembic version:", cur.fetchone())
except Exception as e:
    print("alembic_version: NOT FOUND ·", type(e).__name__)

c.close()
