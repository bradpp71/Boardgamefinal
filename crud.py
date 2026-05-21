#Step-1 Connect to DB
import sqlite3

DB_NAME = "boardgame.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

#Step-2 READ OPERATIONS

#1.Get all games

def get_all_games():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM game_catalog")
    data = cursor.fetchall()

    conn.close()
    return data
#2. Get one game by name

def get_game_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM game_catalog WHERE game_name = ?",
        (name,)
    )

    data = cursor.fetchone()
    conn.close()
    return data


#atep-3 CREATE OPERATIONS

#Add member

def add_member(name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO members (player_name) VALUES (?)",
        (name,)
    )

    conn.commit()
    conn.close()

    #Add match record
def add_match(member_id, game_id, score, is_winner):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO match_records (member_id, game_id, score, is_winner)
            VALUES (?, ?, ?, ?)
        """, (member_id, game_id, score, is_winner))

        conn.commit()
        conn.close()   

# STEP 4 — UPDATE    

def update_game_complexity(game_name, value):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE game_catalog
        SET complexity = ?
        WHERE game_name = ?
    """, (value, game_name))

    conn.commit()
    conn.close()

#STEP 5 — DELETE   
def delete_game(game_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM game_catalog WHERE game_name = ?",
        (game_name,)
    )

    conn.commit()
    conn.close()

import json

# ── Functions needed by app.py ──────────────────────────────

def get_game_attributes():
    """Returns dict of {game_name: {strategy, luck, ...}} for the recommender."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM game_catalog")
    rows = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    conn.close()
    result = {}
    for row in rows:
        d = dict(zip(col_names, row))
        name = d.pop("game_name")
        result[name] = d
    return result

def get_play_history(player_name=None):
    """Returns match history as a list of dicts. Optionally filtered by player."""
    conn = get_connection()
    cursor = conn.cursor()
    if player_name:
        cursor.execute("""
            SELECT mr.history_id, m.player_name, gc.game_name, mr.score,
                   mr.is_winner, mr.played_at, mr.game_id, mr.member_id
            FROM match_records mr
            JOIN members m ON mr.member_id = m.member_id
            JOIN game_catalog gc ON mr.game_id = gc.game_id
            WHERE m.player_name = ?
            ORDER BY mr.played_at DESC
        """, (player_name,))
    else:
        cursor.execute("""
            SELECT mr.history_id, m.player_name, gc.game_name, mr.score,
                   mr.is_winner, mr.played_at, mr.game_id, mr.member_id
            FROM match_records mr
            JOIN members m ON mr.member_id = m.member_id
            JOIN game_catalog gc ON mr.game_id = gc.game_id
            ORDER BY mr.played_at DESC
        """)
    cols = [desc[0] for desc in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    conn.close()
    import pandas as pd
    return pd.DataFrame(rows)

def add_match_result(player_name, game_name, score, is_winner):
    """Adds a match result. Auto-creates player if not exists."""
    conn = get_connection()
    cursor = conn.cursor()
    # Get or create member
    cursor.execute("INSERT OR IGNORE INTO members (player_name) VALUES (?)", (player_name,))
    cursor.execute("SELECT member_id FROM members WHERE player_name = ?", (player_name,))
    member_id = cursor.fetchone()[0]
    # Get game id
    cursor.execute("SELECT game_id FROM game_catalog WHERE game_name = ?", (game_name,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    game_id = row[0]
    cursor.execute("""
        INSERT INTO match_records (member_id, game_id, score, is_winner)
        VALUES (?, ?, ?, ?)
    """, (member_id, game_id, score, 1 if is_winner else 0))
    conn.commit()
    conn.close()
    return True

def update_match_result(history_id, score, is_winner):
    """Updates score and winner status for an existing match."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE match_records SET score = ?, is_winner = ? WHERE history_id = ?
    """, (score, 1 if is_winner else 0, history_id))
    conn.commit()
    conn.close()

def delete_match_result(history_id):
    """Deletes a single match record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM match_records WHERE history_id = ?", (history_id,))
    conn.commit()
    conn.close()

def remove_player(player_name):
    """Removes a player and all their match records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT member_id FROM members WHERE player_name = ?", (player_name,))
    row = cursor.fetchone()
    if row:
        cursor.execute("DELETE FROM match_records WHERE member_id = ?", (row[0],))
        cursor.execute("DELETE FROM members WHERE member_id = ?", (row[0],))
    conn.commit()
    conn.close()

def get_top_games(limit=5):
    """Returns most played games."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT gc.game_id, gc.game_name, COUNT(mr.history_id) as matches_played
        FROM match_records mr
        JOIN game_catalog gc ON mr.game_id = gc.game_id
        GROUP BY gc.game_id
        ORDER BY matches_played DESC
        LIMIT ?
    """, (limit,))
    cols = [desc[0] for desc in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_game_champions(game_id, limit=3):
    """Returns top winners for a specific game."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.player_name,
               COUNT(CASE WHEN mr.is_winner=1 THEN 1 END) as victory_count,
               MAX(mr.score) as peak_score
        FROM match_records mr
        JOIN members m ON mr.member_id = m.member_id
        WHERE mr.game_id = ?
        GROUP BY m.member_id
        ORDER BY victory_count DESC, peak_score DESC
        LIMIT ?
    """, (game_id, limit))
    cols = [desc[0] for desc in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_recent_activity(limit=5):
    """Returns the most recent match records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.player_name, gc.game_name, mr.score, mr.is_winner, mr.played_at
        FROM match_records mr
        JOIN members m ON mr.member_id = m.member_id
        JOIN game_catalog gc ON mr.game_id = gc.game_id
        ORDER BY mr.played_at DESC
        LIMIT ?
    """, (limit,))
    cols = [desc[0] for desc in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    conn.close()
    return rows