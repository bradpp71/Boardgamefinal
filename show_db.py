import sqlite3

conn = sqlite3.connect("boardgame.db")
cursor = conn.cursor()

# Show all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("\n📌 Tables in database:")
for t in tables:
    print("-", t[0])

print("\n📊 Sample data from each table:\n")

for t in tables:
    table_name = t[0]

    print(f"=== {table_name} ===")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    print()

conn.close()