import sqlite3
import pandas as pd
import json
from pathlib import Path

DB_NAME = "boardgame.db"

# 1. Connection
def connect_db():
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# 2. Create Tables
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_catalog (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT UNIQUE NOT NULL,
            strategy REAL, luck REAL, negotiation REAL,
            deduction REAL, deck_building REAL, cooperation REAL,
            complexity REAL, duration_norm REAL,
            category TEXT, players TEXT, icon TEXT, description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_records (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            game_id INTEGER,
            score INTEGER,
            is_winner INTEGER,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(member_id) REFERENCES members(member_id),
            FOREIGN KEY(game_id) REFERENCES game_catalog(game_id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Tables created!")

# 3. Load games from JSON
def load_games():
    if not Path("data/games.json").exists():
        print("❌ data/games.json not found!")
        return
    conn = connect_db()
    cursor = conn.cursor()
    with open("data/games.json", "r", encoding="utf-8") as f:
        games = json.load(f)
    for game_name, features in games.items():
        cursor.execute("""
            INSERT OR IGNORE INTO game_catalog (
                game_name, strategy, luck, negotiation, deduction,
                deck_building, cooperation, complexity, duration_norm,
                category, players, icon, description
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            game_name,
            features.get("strategy"), features.get("luck"),
            features.get("negotiation"), features.get("deduction"),
            features.get("deck_building"), features.get("cooperation"),
            features.get("complexity"), features.get("duration_norm"),
            features.get("category"), features.get("players"),
            features.get("icon"), features.get("description")
        ))
    conn.commit()
    conn.close()
    print("✅ Games loaded!")

# 4. Initialize everything
def initialize_database():
    create_tables()
    load_games()

# 5. Game attributes
def get_game_attributes():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM game_catalog")
    rows = cursor.fetchall()
    conn.close()
    game_dict = {}
    for r in rows:
        game_dict[r["game_name"]] = dict(r)
    return game_dict

# 6. Play history
def get_play_history(player_name=None):
    conn = connect_db()
    cursor = conn.cursor()
    if player_name:
        cursor.execute("""
            SELECT mr.*, m.player_name, g.game_name
            FROM match_records mr
            JOIN members m ON mr.member_id = m.member_id
            JOIN game_catalog g ON mr.game_id = g.game_id
            WHERE m.player_name = ?
            ORDER BY mr.played_at DESC
        """, (player_name,))
    else:
        cursor.execute("""
            SELECT mr.*, m.player_name, g.game_name
            FROM match_records mr
            JOIN members m ON mr.member_id = m.member_id
            JOIN game_catalog g ON mr.game_id = g.game_id
            ORDER BY mr.played_at DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)

# 7. Add match
def add_match_result(player_name, game_name, score, is_winner):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO members(player_name) VALUES (?)", (player_name,))
    cursor.execute("SELECT member_id FROM members WHERE player_name=?", (player_name,))
    member_id = cursor.fetchone()[0]
    cursor.execute("SELECT game_id FROM game_catalog WHERE game_name=?", (game_name,))
    game_id = cursor.fetchone()[0]
    cursor.execute("""
        INSERT INTO match_records (member_id, game_id, score, is_winner)
        VALUES (?, ?, ?, ?)
    """, (member_id, game_id, score, int(is_winner)))
    conn.commit()
    conn.close()
    return True

# 8. Update match
def update_match_result(history_id, score, is_winner):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE match_records SET score=?, is_winner=? WHERE history_id=?
    """, (score, int(is_winner), history_id))
    conn.commit()
    conn.close()
    return True

# 9. Delete match
def delete_match_result(history_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM match_records WHERE history_id=?", (history_id,))
    conn.commit()
    conn.close()
    return True

# 10. Remove player
def remove_player(player_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT member_id FROM members WHERE player_name=?", (player_name,))
    row = cursor.fetchone()
    if not row:
        return False
    member_id = row[0]
    cursor.execute("DELETE FROM match_records WHERE member_id=?", (member_id,))
    cursor.execute("DELETE FROM members WHERE member_id=?", (member_id,))
    conn.commit()
    conn.close()
    return True

# 11. Top games
def get_top_games(limit=5):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.game_id, g.game_name, COUNT(*) as matches_played
        FROM match_records mr
        JOIN game_catalog g ON mr.game_id = g.game_id
        GROUP BY g.game_id
        ORDER BY matches_played DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# 12. Champions
def get_game_champions(game_id, limit=3):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.player_name,
               COUNT(*) as victory_count,
               MAX(mr.score) as peak_score
        FROM match_records mr
        JOIN members m ON mr.member_id = m.member_id
        WHERE mr.game_id=? AND mr.is_winner=1
        GROUP BY m.player_name
        ORDER BY victory_count DESC
        LIMIT ?
    """, (game_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# 13. Recent activity
def get_recent_activity(limit=5):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.player_name, g.game_name, mr.score, mr.is_winner, mr.played_at
        FROM match_records mr
        JOIN members m ON mr.member_id = m.member_id
        JOIN game_catalog g ON mr.game_id = g.game_id
        ORDER BY mr.played_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Run this file directly to set up the database
if __name__ == "__main__":
    initialize_database()