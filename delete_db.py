import os

if os.path.exists("boardgame.db"):
    os.remove("boardgame.db")
    print("Old database deleted")
else:
    print("No database found")