import sqlite3
from pathlib import Path


DB_PATH = Path("instance") / "contrail_dev.db"


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"DB not found: {DB_PATH}")

    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print("tables:", tables)

    if "users" not in tables:
        raise SystemExit("users table not found. Did you run `flask db upgrade` after deleting the db file?")

    cur.execute("PRAGMA table_info('users')")
    cols = cur.fetchall()
    # PRAGMA table_info: cid, name, type, notnull(0/1), dflt_value, pk(0/1)
    info = {c[1]: {"type": c[2], "notnull": bool(c[3]), "default": c[4], "pk": bool(c[5])} for c in cols}
    print("users.columns:", info)

    # quick assertions for this project
    if "id_card_no" not in info:
        raise SystemExit("id_card_no column missing in users table")
    if info["id_card_no"]["notnull"] is not True:
        raise SystemExit("id_card_no should be NOT NULL, but it's nullable in the current DB")

    if "student_id" not in info:
        raise SystemExit("student_id column missing in users table")
    if info["student_id"]["notnull"] is not False:
        raise SystemExit("student_id should be nullable, but it's NOT NULL in the current DB")

    cur.execute("PRAGMA index_list('users')")
    idx_list = cur.fetchall()
    print("users.indexes:", idx_list)

    print("OK: schema matches requirements (id_card_no NOT NULL, student_id nullable).")


if __name__ == "__main__":
    main()



