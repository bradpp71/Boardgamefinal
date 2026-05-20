#Step-1 Import Required Libraries
import sqlite3
import json
import pandas as pd
from pathlib import Path


#Step-2  Create Database Connection
DB_NAME = "boardgame.db"


def connect_db():
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 10000;")
    return conn
#This creates/connects to your SQLite database.

##Step-3Create Database Tables

def create_tables():

    conn = connect_db()
    cursor = conn.cursor()

    # members table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name TEXT UNIQUE NOT NULL
    )
    """)

    # game catalog table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_catalog (
        game_id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_name TEXT UNIQUE NOT NULL,
        strategy REAL,
        luck REAL,
        negotiation REAL,
        deduction REAL,
        deck_building REAL,
        cooperation REAL,
        complexity REAL,
        duration_norm REAL,
        category TEXT,
        players TEXT,
        icon TEXT,
        description TEXT
    )
    """)

    # match records table
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

    ##created 3 database tables:
    #   Table                              Purpose
    #  members                          Stores players
    #  game_catalog                    Stores board games
    #  match_records                   Stores gameplay history

    #This is the main database structure of the project.

#Step-4  Load games.json Into Database

def load_games():

    conn = connect_db()
    cursor = conn.cursor()

    with open("data/games.json", "r", encoding="utf-8") as file:
        games = json.load(file)

    for game_name, features in games.items():

        cursor.execute("""
        INSERT OR IGNORE INTO game_catalog (
            game_name,
            strategy,
            luck,
            negotiation,
            deduction,
            deck_building,
            cooperation,
            complexity,
            duration_norm,
            category,
            players,
            icon,
            description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_name,
            features["strategy"],
            features["luck"],
            features["negotiation"],
            features["deduction"],
            features["deck_building"],
            features["cooperation"],
            features["complexity"],
            features["duration_norm"],
            features["category"],
            features["players"],
            features["icon"],
            features["description"]
        ))
    conn.commit()
    conn.close()
#This:

# reads games.json
# loops through all games
# inserts them into game_catalog

# The INSERT OR IGNORE prevents duplicate entries.    


#Step-5  Initialize Everything
def initialize_database():

    create_tables()
    load_games()


#Step-6    Run Initialization
if __name__ == "__main__":
    initialize_database()