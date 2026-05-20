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