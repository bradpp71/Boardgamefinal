import os
import subprocess

DB_FILE = "boardgame.db"

if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print("🗑️ Old database deleted")
else:
    print("ℹ️ No old database found")

print("🔄 Rebuilding database...")

result = subprocess.run(["python", "db_manager.py"], capture_output=True, text=True)

print(result.stdout)

if result.stderr:
    print("❌ Errors:")
    print(result.stderr)

print("✅ Reset complete")