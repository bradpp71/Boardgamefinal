"""
app.py
------
The main entry point for the Streamlit web application.
This script provides the UI for viewing/editing match history (CRUD)
and displays real-time ML board game recommendations.

Run with: streamlit run app.py
"""

import os
import html
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import plotly.graph_objects as go
from boardgame_code.database_init import get_play_history, get_game_attributes, add_match_result, delete_match_result, update_match_result, remove_player, get_top_games, get_game_champions, get_recent_activity
from recommender import Recommender


# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
st.set_page_config(page_title="BoardGame Recommender", layout="wide", initial_sidebar_state="collapsed")
# Banner header
st.markdown("""
<div class="hero-banner">
    <div class="hero-dots top-dots"></div>
    <div class="hero-content">
        <h1 class="hero-title">BOARDGAME</h1>
        <h2 class="hero-subtitle">DASHBOARD</h2>
    </div>
    <div class="dice-container-topright" style="position: absolute; top: 20px; right: 40px;">
        <div class="dice">
            <div class="face front">1</div>
            <div class="face back">6</div>
            <div class="face right">3</div>
            <div class="face left">4</div>
            <div class="face top">5</div>
            <div class="face bottom">2</div>
        </div>
    </div>
    <div class="hero-dots bottom-dots"></div>
</div>
""", unsafe_allow_html=True)

GAME_ATTRIBUTES = get_game_attributes()
available_games = list(GAME_ATTRIBUTES.keys())

# Player count lookup (not stored in DB, defined here for display)
PLAYER_COUNT = {
    "Catan": "3-4", "7 Wonders": "2-7", "Terraforming Mars": "1-5",
    "Dominion": "2-4", "Splendor": "2-4", "Agricola": "1-5",
    "Viticulture": "2-6", "Pandemic": "2-4", "Mansions of Madness": "1-5",
    "The Resistance: Avalon": "5-10", "Ultimate Werewolf": "5-68",
    "Dixit": "3-6", "Codenames": "4-8", "Betrayal at House on the Hill": "3-6",
    "Arkham Horror": "1-6", "Wingspan": "1-5", "Pandemic Legacy: Season 1": "2-4",
    "Twilight Imperium: Fourth Edition": "3-6", "7 Wonders Duel": "2",
    "Root": "2-4", "Blood Rage": "2-4", "Scythe": "1-5", "Brass: Birmingham": "2-4",
    "Ticket to Ride": "2-5", "Gloomhaven": "1-4",
}

# -----------------------------------------------------------------------------
# Admin Login (Secure via Env Var)
# -----------------------------------------------------------------------------
st.sidebar.markdown("""
<style>
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .stMarkdown {
        color: #86473F !important;
    }
</style>
""", unsafe_allow_html=True)
st.sidebar.markdown("### 🔒 Admin Login")
# Fetch password from environment (Cloud Secrets or .env)
env_password = os.getenv("ADMIN_PASSWORD")

if not env_password:
    st.sidebar.warning("⚠️ ADMIN_PASSWORD not set in environment.")
    admin_input = st.sidebar.text_input("Enter password", type="password", disabled=True)
    st.session_state["is_admin"] = False
else:
    admin_input = st.sidebar.text_input("Enter password to edit data", type="password")
    if admin_input == env_password:
        st.session_state["is_admin"] = True
        st.sidebar.success("Admin mode unlocked.")
    elif admin_input:
        st.session_state["is_admin"] = False
        st.sidebar.error("Incorrect password.")
    else:
        st.session_state["is_admin"] = False

st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# Community Dashboard
# -----------------------------------------------------------------------------
st.markdown("## Community Dashboard")
dash_col1, dash_col2 = st.columns([1, 1])

with dash_col1:
    st.markdown("### Most Popular Game")
    # Get just the #1 most played game
    top_games = get_top_games(1)
    if not top_games:
        st.info("No games played yet.")
    else:
        top_game = top_games[0]
        st.markdown(f"#### **{top_game['game_name']}** (*{top_game['matches_played']} total plays*)")
        
        st.markdown(" **Top Champions:**")
        top_players = get_game_champions(top_game['game_id'], 3)
        if not top_players:
            st.write("  No winners recorded yet.")
        else:
            # Pad the list to 3 for the podium
            while len(top_players) < 3:
                top_players.append({"player_name": "-", "victory_count": 0, "peak_score": None})
            
            p1 = top_players[0]
            p2 = top_players[1]
            p3 = top_players[2]
            
            s1 = f"<br>Best Score: {p1['peak_score']}" if p1['peak_score'] is not None else ""
            s2 = f"<br>Best Score: {p2['peak_score']}" if p2['peak_score'] is not None else ""
            s3 = f"<br>Best Score: {p3['peak_score']}" if p3['peak_score'] is not None else ""
            
            # Secure against XSS injections from user-generated player names
            name1 = html.escape(str(p1['player_name']))
            name2 = html.escape(str(p2['player_name']))
            name3 = html.escape(str(p3['player_name']))
            
            podium_html = f"""
            <div class="podium-container">
                <div class="podium-column">
                    <div class="podium-name-top">{name2}</div>
                    <div class="podium-box podium-2">
                        <div class="podium-rank">🥈</div>
                    </div>
                    <div class="podium-stats">Win {p2['victory_count']} Times{s2}</div>
                </div>
                <div class="podium-column">
                    <div class="podium-name-top">{name1}</div>
                    <div class="podium-box podium-1">
                        <div class="podium-rank">🥇</div>
                    </div>
                    <div class="podium-stats">Win {p1['victory_count']} Times{s1}</div>
                </div>
                <div class="podium-column">
                    <div class="podium-name-top">{name3}</div>
                    <div class="podium-box podium-3">
                        <div class="podium-rank">🥉</div>
                    </div>
                    <div class="podium-stats">Win {p3['victory_count']} Times{s3}</div>
                </div>
            </div>
            """
            st.markdown(podium_html, unsafe_allow_html=True)

with dash_col2:
    st.markdown("### Recent Activity Feed")
    recent = get_recent_activity(5)
    if not recent:
        st.info("No activity yet.")
    else:
        for row in recent:
            # Map SQL tinyint to boolean for the check
            is_win = bool(row['is_winner'])
            result = " Won" if is_win else "Played"
            # Format score if exists
            score_text = f" (Score: {int(row['score'])})" if row['score'] is not None else ""
            st.markdown(f"*{row['played_at']}* | **{row['player_name']}** {result} **{row['game_name']}**{score_text}")

st.divider()

# GAME INFORMATION CAROUSEL

col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("## Explore Games")
    st.markdown("Scroll through to learn about each board game →")
with col2:
    st.write("") # Spacing alignment
    see_all = st.toggle("See All Games", value=False)

import json

# Build carousel cards dynamically from GAME_ATTRIBUTES
def _badge_class(cat: str) -> str:
    c = cat.lower()
    if "cooperative" in c or "thematic" in c: return "cooperative"
    if "party" in c: return "party"
    return ""

all_games = list(GAME_ATTRIBUTES.items())
display_games = all_games if see_all else all_games[:5]

carousel_cards_html = ""
for gname, gdata in display_games:
    cat      = gdata.get("category", "Unknown")
    badge_cls = _badge_class(cat)
    players  = PLAYER_COUNT.get(gname, "—")
    dur_min  = int(round(gdata.get("duration_norm", 0) * 180))
    dur_str  = f"{dur_min} min" if dur_min > 0 else "—"
    stars    = int(round(gdata.get("complexity", 0) * 5))
    stars_str = "&#9733;" * stars + "&#9734;" * (5 - stars)
    
    desc = gdata.get("description")
    if not desc:
        desc = "Discover and play this amazing board game!"
        
    tags_json = gdata.get("tags")
    tags = []
    if tags_json and isinstance(tags_json, str):
        try:
            tags = json.loads(tags_json)
        except json.JSONDecodeError:
            pass
    elif isinstance(tags_json, list):
        tags = tags_json
        
    tags_html = "".join([f'<span class="feature-tag">{tag}</span>' for tag in tags])
    icon = gdata.get("icon", "🎲")

    carousel_cards_html += f"""
    <div class="game-card">
      <div class="game-card-header">
        <h3>{icon} {gname}</h3>
        <span class="game-badge {badge_cls}">{cat}</span>
      </div>
      <div class="game-stats">
        <div class="stat-item"><span class="stat-label">Players</span><span class="stat-value">{players}</span></div>
        <div class="stat-item"><span class="stat-label">Time</span><span class="stat-value">{dur_str}</span></div>
        <div class="stat-item"><span class="stat-label">Complexity</span><span class="stat-value">{stars_str}</span></div>
      </div>
      <div class="game-description">
        <p>{desc}</p>
        <div class="game-features">{tags_html}</div>
      </div>
    </div>"""

n_games = len(display_games)
dots_html = "".join(
    f'<div class="dot {"active" if i == 0 else ""}" onclick="goTo({i})"></div>'
    for i in range(n_games)
)

if see_all:
    # Grid Layout for all games
    components.html(f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
      * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Space Grotesk', sans-serif; }}
      body {{ background: transparent; padding-bottom: 2rem; }}
      .game-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.5rem; padding: 0.5rem; }}
      .game-card {{ background: #FFFFFF; border: 3px solid #B8C5B0; border-radius: 20px; padding: 1.5rem; box-shadow: 0 6px 25px rgba(107,142,111,0.15); transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease; }}
      .game-card:hover {{ transform: translateY(-8px) scale(1.02); box-shadow: 0 12px 40px rgba(107,142,111,0.25); border-color: #6B8E6F; }}
      .game-card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.8rem; border-bottom: 2px solid #E8DED0; }}
      .game-card-header h3 {{ margin: 0; font-size: 1.3rem; color: #3E5641; font-weight: 700; }}
      .game-badge {{ padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; background: linear-gradient(135deg, #6B8E6F, #556B58); color: white; white-space: nowrap; }}
      .game-badge.cooperative {{ background: linear-gradient(135deg, #5B8DB8, #3A6B99); }}
      .game-badge.party {{ background: linear-gradient(135deg, #C87941, #A05A2C); }}
      .game-stats {{ display: flex; gap: 0.8rem; margin-top: 0.8rem; }}
      .stat-item {{ flex: 1; text-align: center; background: #F5F1E8; border-radius: 10px; padding: 0.5rem; }}
      .stat-label {{ display: block; font-size: 0.7rem; color: #8B6F47; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 0.2rem; }}
      .stat-value {{ display: block; font-size: 0.9rem; color: #3E5641; font-weight: 700; }}
      .game-description {{ margin-top: 1rem; }}
      .game-description p {{ margin: 0.4rem 0; font-size: 0.9rem; line-height: 1.5; color: #5D5D5D; }}
      .game-description strong {{ color: #6B8E6F; font-size: 1rem; }}
      .game-features {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.8rem; }}
      .feature-tag {{ padding: 0.4rem 0.8rem; background: #FFFFFF; border: 1.5px solid #B8C5B0; border-radius: 15px; font-size: 0.8rem; color: #6B8E6F; font-weight: 500; transition: all 0.3s ease; }}
      .feature-tag:hover {{ background: #6B8E6F; color: #FFFFFF; border-color: #6B8E6F; }}
    </style>
    <div class="game-grid">
      {carousel_cards_html}
    </div>
    """, height=1200, scrolling=True)

else:
    # Carousel Layout for 5 games
    components.html(f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
      * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Space Grotesk', sans-serif; }}
      body {{ background: transparent; overflow: hidden; }}
      .game-carousel-container {{ width: 100%; overflow-x: auto; overflow-y: hidden; padding: 1rem 0 1rem 0; scroll-behavior: smooth; -webkit-overflow-scrolling: touch; cursor: grab; user-select: none; }}
      .game-carousel-container.dragging {{ cursor: grabbing; scroll-behavior: auto; }}
      .game-carousel {{ display: flex; gap: 1.5rem; padding: 0.5rem 1rem 1rem 1rem; min-width: min-content; }}
      .game-card {{ min-width: 320px; max-width: 320px; background: #FFFFFF; border: 3px solid #B8C5B0; border-radius: 20px; padding: 1.5rem; box-shadow: 0 6px 25px rgba(107,142,111,0.15); transition: transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease; flex-shrink: 0; }}
      .game-card:hover {{ transform: translateY(-8px) scale(1.02); box-shadow: 0 12px 40px rgba(107,142,111,0.25); border-color: #6B8E6F; }}
      .game-card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.8rem; border-bottom: 2px solid #E8DED0; }}
      .game-card-header h3 {{ margin: 0; font-size: 1.3rem; color: #3E5641; font-weight: 700; }}
      .game-badge {{ padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; background: linear-gradient(135deg, #6B8E6F, #556B58); color: white; white-space: nowrap; }}
      .game-badge.cooperative {{ background: linear-gradient(135deg, #5B8DB8, #3A6B99); }}
      .game-badge.party {{ background: linear-gradient(135deg, #C87941, #A05A2C); }}
      .game-stats {{ display: flex; gap: 0.8rem; margin-top: 0.8rem; }}
      .stat-item {{ flex: 1; text-align: center; background: #F5F1E8; border-radius: 10px; padding: 0.5rem; }}
      .stat-label {{ display: block; font-size: 0.7rem; color: #8B6F47; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 0.2rem; }}
      .stat-value {{ display: block; font-size: 0.9rem; color: #3E5641; font-weight: 700; }}
      .game-description {{ margin-top: 1rem; }}
      .game-description p {{ margin: 0.4rem 0; font-size: 0.9rem; line-height: 1.5; color: #5D5D5D; }}
      .game-description strong {{ color: #6B8E6F; font-size: 1rem; }}
      .game-features {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.8rem; }}
      .feature-tag {{ padding: 0.4rem 0.8rem; background: #FFFFFF; border: 1.5px solid #B8C5B0; border-radius: 15px; font-size: 0.8rem; color: #6B8E6F; font-weight: 500; transition: all 0.3s ease; }}
      .feature-tag:hover {{ background: #6B8E6F; color: #FFFFFF; border-color: #6B8E6F; }}
      .game-carousel-container::-webkit-scrollbar {{ height: 6px; }}
      .game-carousel-container::-webkit-scrollbar-track {{ background: #E8DED0; border-radius: 10px; }}
      .game-carousel-container::-webkit-scrollbar-thumb {{ background: linear-gradient(90deg, #B8C5B0, #6B8E6F); border-radius: 10px; }}
      .dots {{ display: flex; justify-content: center; gap: 6px; margin-top: 8px; flex-wrap: wrap; }}
      .dot {{ width: 9px; height: 9px; border-radius: 50%; background: #D4CEC3; transition: background 0.3s ease, transform 0.3s ease; cursor: pointer; }}
      .dot.active {{ background: #6B8E6F; transform: scale(1.3); }}
    </style>
    <div class="game-carousel-container" id="carousel">
      <div class="game-carousel">
        {carousel_cards_html}
      </div>
    </div>
    <div class="dots" id="dots">{dots_html}</div>
    <script>
      const carousel = document.getElementById('carousel');
      const dots = document.querySelectorAll('.dot');
      const CARD_WIDTH = 320 + 24;
      const TOTAL = {n_games};
      let current = 0, isHovered = false, isDragging = false, startX = 0, scrollLeft = 0;
    
      function goTo(index) {{
        current = index;
        carousel.scrollTo({{ left: index * CARD_WIDTH, behavior: 'smooth' }});
        dots.forEach((d, i) => d.classList.toggle('active', i === index));
      }}
      setInterval(() => {{ if (!isHovered && !isDragging) goTo((current + 1) % TOTAL); }}, 3000);
      carousel.addEventListener('mouseenter', () => isHovered = true);
      carousel.addEventListener('mouseleave', () => {{ isHovered = false; isDragging = false; carousel.classList.remove('dragging'); }});
      carousel.addEventListener('mousedown', (e) => {{ isDragging = true; startX = e.pageX - carousel.offsetLeft; scrollLeft = carousel.scrollLeft; carousel.classList.add('dragging'); }});
      carousel.addEventListener('mouseup', (e) => {{
        if (isDragging) {{
          const moved = (e.pageX - carousel.offsetLeft) - startX;
          if (Math.abs(moved) > 50) goTo(moved < 0 ? Math.min(current+1,TOTAL-1) : Math.max(current-1,0));
        }}
        isDragging = false; carousel.classList.remove('dragging');
      }});
      carousel.addEventListener('mousemove', (e) => {{ if (!isDragging) return; e.preventDefault(); carousel.scrollLeft = scrollLeft - (e.pageX - carousel.offsetLeft - startX); }});
      let touchStartX = 0;
      carousel.addEventListener('touchstart', (e) => {{ touchStartX = e.touches[0].clientX; scrollLeft = carousel.scrollLeft; }});
      carousel.addEventListener('touchend', (e) => {{
        const moved = e.changedTouches[0].clientX - touchStartX;
        if (Math.abs(moved) > 50) goTo(moved < 0 ? Math.min(current+1,TOTAL-1) : Math.max(current-1,0));
      }});
      carousel.addEventListener('scroll', () => {{
        const idx = Math.round(carousel.scrollLeft / CARD_WIDTH);
        if (idx !== current) {{ current = idx; dots.forEach((d,i) => d.classList.toggle('active', i===current)); }}
      }});
    </script>
    """, height=490, scrolling=False)

st.divider()

col_data, col_ml = st.columns([1, 1])

# Custom CSS 
st.markdown("""
<style>
    /* Hero Banner CSS */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Oswald:wght@500;600;700&display=swap');

    .hero-banner {
        position: relative;
        width: 100%;
        min-height: 220px;
        background-color: #2b4c3e;
        background-image: 
            radial-gradient(ellipse at top left, rgba(255,255,255,0.03) 0%, transparent 40%),
            radial-gradient(ellipse at bottom right, rgba(0,0,0,0.2) 0%, transparent 60%);
        border-radius: 12px;
        overflow: hidden;
        margin-top: 1rem;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        padding: 40px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }

    /* Create the background leaf/shadow shapes using pseudo-elements */
    .hero-banner::before, .hero-banner::after {
        content: '';
        position: absolute;
        background-color: #243a2e;
        border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%;
        transform: rotate(45deg);
        z-index: 1;
        opacity: 0.8;
    }
    
    .hero-banner::before {
        width: 300px;
        height: 300px;
        top: -150px;
        right: 15%;
    }
    
    .hero-banner::after {
        width: 450px;
        height: 450px;
        bottom: -250px;
        left: 25%;
    }

    .hero-content {
        position: relative;
        z-index: 10;
        display: flex;
        flex-direction: column;
        text-transform: uppercase;
        margin-left: 20px;
    }
    
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 800;
        font-size: 4.5rem !important;
        color: #FFFFFF !important;

        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.1 !important;
        letter-spacing: -1px;
        
    }
    
    .hero-subtitle {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 2.5rem !important;
        color: #ead177 !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        letter-spacing: 1px;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }

    .hero-dots {
        position: absolute;
        width: 80px;
        height: 40px;
        background-image: radial-gradient(#fff 2px, transparent 2px);
        background-size: 15px 15px;
        opacity: 0.6;
        z-index: 2;
    }

    .top-dots {
        top: 20px;
        right: 30%;
    }

    .bottom-dots {
        bottom: 20px;
        right: 20px;
    }

    /* Import Space Grotesk font */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    /* Main app styling nude */
    .main {
        background-color: #2b4c3e;
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* streamlit's default white background override */
    .stApp {
        background-color: #2b4c3e;
    }
    
    /* headers */
    h1 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 3.2rem !important;
        background: linear-gradient(135deg, #6B8E6F 0%, #556B58 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem !important;
        letter-spacing: -1px !important;
    }
    
    h2 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 2.2rem !important;
        color: #E8DED0 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        letter-spacing: -0.5px !important;
    }
    
    h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.6rem !important;
        color: #D4CEC3 !important;
        margin-top: 1rem !important;
        letter-spacing: -0.3px !important;
    }
    
    h4 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        font-size: 1.3rem !important;
        color: #A5B59D !important;
    }
    
    /* regular text */
    p, .stMarkdown, label, div {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.1rem !important;
        color: #F5F1E8 !important;
        line-height: 1.7 !important;
    }
    
    /* input box */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.05rem !important;
        background-color: #FFFFFF !important;
 color: #2b4c3e !important;
        border: 2.5px solid #6B8E6F !important;
        border-radius: 12px !important;
        padding: 0.8rem !important;
        transition: all 0.3s ease !important;
        color: #F5F1E8 !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #A5B59D !important;
        box-shadow: 0 0 0 4px rgba(107, 142, 111, 0.15) !important;
        background-color: #FFFFFF !important;
 color: #2b4c3e !important;
    }
    
    /* buttons = sage green */
    .stButton > button {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #B8C5B0 0%, #A5B59D 100%) !important;
        color: #FFFFFF !important;

        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(107, 142, 111, 0.25) !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #6B8E6F 0%, #556B58 100%) !important;
        box-shadow: 0 6px 18px rgba(107, 142, 111, 0.35) !important;
        transform: translateY(-3px) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6B8E6F 0%, #556B58 100%) !important;
        color: #FFFFFF !important;

        font-weight: 700 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #556B58 0%, #3E5641 100%) !important;
        box-shadow: 0 6px 20px rgba(107, 142, 111, 0.4) !important;
    }
    
    /* Dataframe = white with sage border */
    .stDataFrame {
        background-color: #FFFFFF !important;
 color: #2b4c3e !important;
        border: 2.5px solid #6B8E6F !important;
        border-radius: 15px !important;
        overflow: hidden !important;
        box-shadow: 0 5px 20px rgba(107, 142, 111, 0.15) !important;
    }
    
    /* info warning boxes */
    .stAlert {
        font-family: 'Space Grotesk', sans-serif !important;
        border-radius: 12px !important;
        font-size: 1.05rem !important;
        border-left: 5px solid !important;
        background-color: #FFFFFF !important;
 color: #2b4c3e !important;
    }
    
    div[data-testid="stNotificationContentInfo"] {
        background-color: #FFFFFF !important;
 color: #2b4c3e !important;
        border-left-color: #A5B59D !important;
        color: #E8DED0 !important;
    }
    
    div[data-testid="stNotificationContentSuccess"] {
        background-color: #FFFFFF !important;
 color: #2b4c3e !important;
        border-left-color: #5A8A5A !important;
        color: #B8C5B0 !important;
    }
    
    div[data-testid="stNotificationContentWarning"] {
        background-color: #FFFFFF !important;
 color: #2b4c3e !important;
        border-left-color: #BC8B6A !important;
        color: #E8DED0 !important;
    }
    
    div[data-testid="stNotificationContentError"] {
        background-color: #FFFFFF !important;
 color: #2b4c3e !important;
        border-left-color: #A67C5D !important;
        color: #E8DED0 !important;
    }
    
    /* divider=sage green */
    hr {
        margin: 2.5rem 0 !important;
        border: none !important;
        height: 3px !important;
        background: linear-gradient(90deg, transparent, #B8C5B0, transparent) !important;
    }
    
    

      /* Checkbox Toggle Make More Obvious */
      div[data-testid="stToggle"] > label > div > div > div {
          background-color: #A5B59D !important;
      }
      /* checkbox */
    .stCheckbox {
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    /* form colors */
    .stForm {
        background: #FFFFFF !important;
        border: 2.5px solid #6B8E6F !important;
        border-radius: 18px !important;
        padding: 2rem !important;
        box-shadow: 0 5px 25px rgba(107, 142, 111, 0.15) !important;
    }
    
    /* reco boxes */
    .rec-card {
        background: #FFFFFF;
        border: 2.5px solid #B8C5B0;
        border-radius: 18px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(107, 142, 111, 0.12);
    }
    
    .rec-card:hover {
        border-color: #6B8E6F;
        box-shadow: 0 8px 25px rgba(107, 142, 111, 0.25);
        transform: translateY(-4px);
    }
    
    .rec-card h3 {
        margin: 0 0 0.8rem 0 !important;
        color: #A5B59D !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    
    .rec-card p {
        margin: 0 !important;
        color: #5D5D5D !important;
        font-size: 1.05rem !important;
    }
    
    /* column style =cream  */
    [data-testid="column"] {
        background: #FFFFFF;
        border: 2.5px solid #D4CEC3;
        border-radius: 18px;
        padding: 2.5rem;
        box-shadow: 0 5px 20px rgba(107, 142, 111, 0.1);
    }
    
    /* spinner = sage */
    .stSpinner > div {
        border-top-color: #A5B59D !important;
    }
    
    /* metrics = sage accent */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #A5B59D !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    /* Podium Styles */
    .podium-container {
        display: flex;
        justify-content: center;
        align-items: flex-end;
        gap: 20px;
        margin-top: 25px;
    }
    
    .podium-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
    }
    
    .podium-box {
        text-align: center;
        border-radius: 12px 12px 0 0;
        padding: 10px;
        color: white;
        font-weight: 600;
        box-shadow: 0 -4px 15px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        position: relative;
    }
    
    .podium-1 {
        height: 130px;
        width: 110px;
        background: linear-gradient(135deg, #FFD700 0%, #FDB931 100%);
        z-index: 3;
    }
    
    .podium-2 {
        height: 85px;
        width: 100px;
        background: linear-gradient(135deg, #E0E0E0 0%, #BDBDBD 100%);
        z-index: 2;
    }
    
    .podium-3 {
        height: 50px;
        width: 100px;
        background: linear-gradient(135deg, #CD7F32 0%, #A0522D 100%);
        z-index: 1;
    }
    
    .podium-rank {
        font-size: 1.8rem;
        margin-bottom: 5px;
    }
    
    .podium-name-top {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 5px;
        text-align: center;
        word-wrap: break-word;
        max-width: 110px;
    }
    
    .podium-stats {
        margin-top: 8px;
        font-size: 0.95rem;
        color: #555;
        font-weight: 500;
        text-align: center;
        line-height: 1.4;
        height: 45px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    
    /*dropdown box */
    .stSelectbox [data-baseweb="select"] {
        background-color: #FFFFFF !important;
    }
    /* Dropdown selected text and option list - dark brown matching Explore Games Players label */
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div,
    .stSelectbox [data-baseweb="select"] input,
    [data-baseweb="popover"] li span,
    [data-baseweb="popover"] li div,
    [data-baseweb="popover"] [role="option"] span,
    [data-baseweb="popover"] [role="option"] div {
        color: #8B6F47 !important;
    }
    /* Rec card specific overrides */
    .rec-game-name {
        color: #2b4c3e !important;
    }
    .rec-desc, .rec-desc p, .rec-desc div {
        color: #2b4c3e !important;
    }
    
    /*make sure all backgrounds are cream */
    [data-testid="stAppViewContainer"] {
        background-color: #2b4c3e !important;
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /*caption text */
    .stCaption {
        font-family: 'Space Grotesk', sans-serif !important;
    }
    /* ============================================
    GOLD DICE ROTATING
   ============================================ */
            
.dice-container-topright {
    position: relative;
    perspective: 600px;
    width: 50px;
    height: 50px;
    z-index: 99;
}

.dice {
    width: 50px;
    height: 50px;
    position: relative;
    transform-style: preserve-3d;
    animation: rotate-dice 8s infinite linear;
}

@keyframes rotate-dice {
    0% {
        transform: rotateX(0deg) rotateY(0deg);
    }
    25% {
        transform: rotateX(90deg) rotateY(90deg);
    }
    50% {
        transform: rotateX(180deg) rotateY(180deg);
    }
    75% {
        transform: rotateX(270deg) rotateY(270deg);
    }
    100% {
        transform: rotateX(360deg) rotateY(360deg);
    }
}

.dice .face {
    position: absolute;
    width: 50px;
    height: 50px;
    background: linear-gradient(145deg, #FFD700 0%, #FFA500 50%, #FFD700 100%);
    border: 2px solid #B8860B;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.2rem;
    color: #3E2723;
    font-weight: 900;
    box-shadow: 
        inset 2px 2px 8px rgba(255, 255, 255, 0.5),
        inset -2px -2px 8px rgba(184, 134, 11, 0.4),
        0 4px 12px rgba(218, 165, 32, 0.5);
    text-shadow: 
        1px 1px 2px rgba(255, 255, 255, 0.8),
        -1px -1px 2px rgba(0, 0, 0, 0.3);
}

.dice .front {
    transform: translateZ(25px);
}

.dice .back {
    transform: rotateY(180deg) translateZ(25px);
}

.dice .right {
    transform: rotateY(90deg) translateZ(25px);
}

.dice .left {
    transform: rotateY(-90deg) translateZ(25px);
}

.dice .top {
    transform: rotateX(90deg) translateZ(25px);
}

.dice .bottom {
    transform: rotateX(-90deg) translateZ(25px);
}

/* Hover effect */
.dice-container-topright:hover .dice {
    animation: rotate-dice-fast 2s infinite linear;
}

@keyframes rotate-dice-fast {
    0% {
        transform: rotateX(0deg) rotateY(0deg);
    }
    100% {
        transform: rotateX(360deg) rotateY(360deg);
    }
}


/* ============================================
   Explore Games Carousel
   ============================================ */

.game-carousel-container {
    width: 100%;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 2rem 0;
    margin: 2rem 0;
    scroll-behavior: smooth;
    -webkit-overflow-scrolling: touch;
}

.game-carousel {
    display: flex;
    gap: 2rem;
    padding: 0 1rem 1rem 1rem;
    min-width: min-content;
}

.game-card {
    min-width: 350px;
    max-width: 350px;
    background: #FFFFFF;
    border: 3px solid #B8C5B0;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 6px 25px rgba(107, 142, 111, 0.15);
    transition: all 0.4s ease;
    flex-shrink: 0;
}

.game-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 12px 40px rgba(107, 142, 111, 0.25);
    border-color: #6B8E6F;
}

.game-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #E8DED0;
}

.game-card-header h3 {
    margin: 0 !important;
    font-size: 1.8rem !important;
    color: #E8DED0 !important;
    font-weight: 700 !important;
}

.game-badge {
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    background: linear-gradient(135deg, #6B8E6F 0%, #556B58 100%);
    color: #FFFFFF;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.game-badge.cooperative {
    background: linear-gradient(135deg, #27AE60 0%, #1E8449 100%);
}

.game-badge.party {
    background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%);
}

.game-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: linear-gradient(135deg, #F5F1E8 0%, #E8DED0 100%);
    border-radius: 12px;
}

.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.stat-label {
    font-size: 0.75rem;
    color: #8B6F47;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
    margin-bottom: 0.3rem;
}

.stat-value {
    font-size: 1.1rem;
    color: #3E5641;
    font-weight: 700;
}

.game-description {
    margin-top: 1.5rem;
}

.game-description p {
    margin: 0.5rem 0 !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    color: #5D5D5D !important;
}

.game-description strong {
    color: #6B8E6F;
    font-size: 1.1rem;
}

.game-features {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
}

.feature-tag {
    padding: 0.4rem 0.8rem;
    background: #FFFFFF;
    border: 1.5px solid #B8C5B0;
    border-radius: 15px;
    font-size: 0.8rem;
    color: #6B8E6F;
    font-weight: 500;
    transition: all 0.3s ease;
}

.feature-tag:hover {
    background: #6B8E6F;
    color: #FFFFFF;
    border-color: #6B8E6F;
}

/* Custom scrollbar for carousel */
.game-carousel-container::-webkit-scrollbar {
    height: 8px;
}

.game-carousel-container::-webkit-scrollbar-track {
    background: #E8DED0;
    border-radius: 10px;
}

.game-carousel-container::-webkit-scrollbar-thumb {
    background: linear-gradient(90deg, #B8C5B0 0%, #6B8E6F 100%);
    border-radius: 10px;
}

.game-carousel-container::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(90deg, #6B8E6F 0%, #556B58 100%);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loading & ML Engine Initialization (Optimized)
# -----------------------------------------------------------------------------
history_df = get_play_history() # Cached
rec_engine = None
existing_players = []
if not history_df.empty:
    existing_players = history_df["player_name"].unique().tolist()

# -----------------------------------------------------------------------------
# Main Columns
# -----------------------------------------------------------------------------
col_data, col_ml = st.columns([1, 1], gap="large")

with col_data:
    st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>Who is playing?</h2>", unsafe_allow_html=True)
    current_player = st.selectbox("Select Player", existing_players)
    
    # Initialize Recommender once for use in both columns
    if current_player and not history_df.empty:
        try:
            rec_engine = Recommender(history_df, game_attrs=GAME_ATTRIBUTES)
        except:
             pass
    
    if st.session_state.get("is_admin", False):
        new_p = st.text_input("Or enter a new player name to create/select:")
        if new_p.strip():
            current_player = new_p.strip()
        
    if not current_player:
        st.warning("Please select or enter a player name to continue.")
        st.stop()

    # Display the user's top 3 best games (highest win count, or best score)
    st.markdown(f"### Profile for **{current_player}**")

    player_history_df = get_play_history(current_player)
    
    if player_history_df.empty:
        st.info("No play history found.")
    else:
        # Calculate their top 3 games
        wins_df = player_history_df[player_history_df['is_winner'] == 1]
        
        st.markdown("🏅 **Personal Best Games**")
        if wins_df.empty:
            # No victory_count, just show highest scores
            best_scores = player_history_df.dropna(subset=['score']).sort_values('score', ascending=False)
            if best_scores.empty:
                st.write("Keep playing to earn your first win!")
            else:
                top_3 = best_scores.head(3)
                for _, row in top_3.iterrows():
                    st.markdown(f"- **{row['game_name']}** (Score: *{row['score']}*)")
        else:
            # Show top 3 by win count
            win_counts = wins_df.groupby('game_name').size().reset_index(name='victory_count').sort_values('victory_count', ascending=False).head(3)
            for _, row in win_counts.iterrows():
                st.markdown(f"- **{row['game_name']} — *Win: {row['victory_count']}* 👑**")

        # --- Personality Analysis (Moved to Profile) ---
        if rec_engine:
            try:
                traits = rec_engine.get_player_traits(current_player)
                
                # Use .get() to avoid KeyError 'person' or others
                t_title = traits.get('title', 'You are a Versatile Gamer')
                t_desc = traits.get('desc', 'You have a balanced and adaptable playstyle.')
                t_person = traits.get('person', 'Unknown')
                t_status = traits.get('status', 'A mysterious figure in history.')
                t_quote = traits.get('quote', '"Success is not final, failure is not fatal."')

                # Strip all emojis from title
                import re
                t_title = re.sub(r'[^\w\s\-\'".,!?]', '', t_title).strip()
                
                # Restore original text style for analysis header
                st.markdown('<p style="color:#2b4c3e !important; font-weight:700; font-size:1.05rem; margin-bottom:8px;">Based on your tracking data, here is your analysis:</p>', unsafe_allow_html=True)

                # --- Radar Chart (Hexagon - 6 Attributes) ---
                all_metrics = rec_engine.get_player_profile_metrics(current_player)
                target_features = ["strategy", "luck", "negotiation", "deduction", "cooperation", "complexity"]

                categories = []
                values = []
                for feat in target_features:
                    if feat in all_metrics:
                        label = feat.replace('_', ' ').title()
                        if label == "Complexity":
                            label = "Organization"
                        categories.append(label)
                        values.append(all_metrics[feat])

                if categories:
                    categories += [categories[0]]
                    values += [values[0]]
                else:
                    st.info("No data available for the radar chart.")
                    st.stop()

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='Player Profile',
                    line_color='#FFD700',
                    fillcolor='rgba(255, 215, 0, 0.3)'
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1],
                            showticklabels=False,
                            gridcolor='rgba(255,255,255,0.3)',
                            linecolor='rgba(255,255,255,0.3)'
                        ),
                        angularaxis=dict(
                            tickfont=dict(color='#FFFFFF', size=12),
                            gridcolor='rgba(255,255,255,0.3)',
                            linecolor='rgba(255,255,255,0.3)'
                        ),
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    showlegend=False,
                    margin=dict(l=40, r=40, t=20, b=20),
                    height=300,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

                st.markdown("""
                <style>
                #personality-analysis h3,
                #personality-analysis p,
                #personality-analysis i {
                    color: #86473F !important;
                }
                </style>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div id="personality-analysis" style="padding:1.5rem; border-radius:18px; border: 2.5px solid #B8C5B0; background-color: #FFFFFF; margin-bottom:10px; box-shadow: 0 4px 15px rgba(107,142,111,0.12);">
                    <h3 style="margin:0 0 10px 0; color: #86473F !important; font-size:1.5rem; font-weight:700;">{t_title}</h3>
                    <p style="margin:0 0 10px 0; color: #86473F !important; font-size: 0.95rem; line-height:1.6;">{t_desc}</p>
                    <div style="padding-top: 10px; border-top: 2px solid #E8DED0;">
                        <p style="margin:0 0 5px 0; color: #86473F !important; font-weight: 600; font-size:0.95rem;">Historical Match: {t_person}</p>
                        <p style="margin:0 0 5px 0; color: #86473F !important; font-size: 0.9rem;"><i>{t_status}</i></p>
                        <p style="margin:0; color: #86473F !important; font-style: italic; font-size:0.9rem;">{t_quote}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Analysis error: {e}")

    st.divider()

    st.divider()

    # -----------------------------------------------------------------------------
    # Admin Section: Grouped for visibility control
    # -----------------------------------------------------------------------------
    if st.session_state.get("is_admin", False):
        st.markdown("## 🛠 Admin Controls")
        
        # 1. Add New Match Result
        st.markdown("### ➕ Add New Match Result")
        with st.form("add_match_form", clear_on_submit=True):
            game_options = ["-- Select a Game --"] + available_games
            new_game = st.selectbox("Select Board Game", game_options)
            new_score_raw = st.text_input("Your Score (Leave empty for win/loss only games)", value="")
            new_is_winner = st.checkbox("Did you win?")
    
            submitted = st.form_submit_button("Save Match Result", type="primary")
            if submitted:
                if new_game == "-- Select a Game --":
                    st.warning("Please select a game first.")
                    st.stop()
                parsed_score = None
                if new_score_raw.strip():
                    try:
                        parsed_score = int(new_score_raw)
                    except ValueError:
                        st.error("Score must be a number or left empty.")
                        st.stop()
                if add_match_result(current_player, new_game, parsed_score, new_is_winner):
                    st.success(f"Successfully added {new_game} to history!")
                    st.rerun()
                else:
                    st.error("Failed to save to database")

        st.divider()

        # 2. Manage Play History
        if not player_history_df.empty:
            st.markdown("### ⚙️ Manage Play History")
            display_df = player_history_df[['game_name', 'score', 'is_winner', 'played_at']].copy()
            display_df['score'] = display_df['score'].fillna("-")
            display_df['is_winner'] = display_df['is_winner'].map({1: "👑", 0: "", True: "👑", False: ""})
            display_df = display_df.rename(columns={"game_name": "Game", "score": "Score", "is_winner": "Winner", "played_at": "Date"})
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            player_history_df_sorted = player_history_df.sort_values("played_at", ascending=False)
            record_options = {
                f"{row['game_name']} - {row['played_at']} (Score: {row['score'] if row['score'] is not None else '-'}) {'' if row['is_winner'] else ''}": row
                for _, row in player_history_df_sorted.iterrows()
            }
            record_to_modify = st.selectbox("Select record to modify or delete:", list(record_options.keys()))
            selected_row = record_options[record_to_modify]
            current_score_str = str(int(selected_row['score'])) if selected_row['score'] is not None else ""
            edit_score_raw = st.text_input("Update Score", value=current_score_str, key=f"score_{selected_row['history_id']}")
            edit_is_winner = st.checkbox("Did you win?", value=bool(selected_row['is_winner']), key=f"winner_{selected_row['history_id']}")
            
            edit_col1, edit_col2 = st.columns(2)
            with edit_col1:
                if st.button("Save Changes", key=f"save_{selected_row['history_id']}"):
                    parsed_edit_score = None
                    if edit_score_raw.strip():
                        try:
                            parsed_edit_score = int(edit_score_raw)
                        except ValueError:
                            st.error("Score must be a number.")
                            st.stop()
                    if update_match_result(selected_row['history_id'], parsed_edit_score, edit_is_winner):
                        st.success("Successfully updated record!")
                        st.rerun()
            with edit_col2:
                if st.button("🗑 Delete Record", key=f"delete_{selected_row['history_id']}"):
                    if delete_match_result(selected_row['history_id']):
                        st.success("Successfully deleted record!")
                        st.rerun()

            st.divider()
            st.markdown("### ⚠️ Danger Zone")
            if current_player != "-- Create New Player --":
                if st.button("🗑 Delete Entire Player Profile", key="del_player_btn", type="primary"):
                    if remove_player(current_player):
                        st.success(f"Player {current_player} deleted.")
                        st.rerun()
                    else:
                        st.error("Failed to delete.")

# -----------------------------------------------------------------------------
# Right Column: ML Engine
# -----------------------------------------------------------------------------
with col_ml:
    st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>You may like...</h2>", unsafe_allow_html=True)
    
    if history_df.empty or not current_player:
        st.info("Not enough data to make recommendations. Please add at least 1 game to your history.")
    else:
        try:
            if rec_engine:
                with st.spinner('Calculating...'):
                    recommendations = rec_engine.recommend(current_player, top_n=5)
                
                if not recommendations:
                    st.warning("All available games played.")
                else:
                    for i, rec_dict in enumerate(recommendations):
                        game_name = rec_dict["game"]
                        match_score = rec_dict["score"]
                        
                        stats = GAME_ATTRIBUTES.get(game_name, {})
                        category = stats.get('category', 'Unknown')
                        complexity = stats.get('complexity', 0)
                        
                        duration_norm = stats.get('duration_norm', 0)
                        duration_min = int(round(duration_norm * 180))
                        duration_str = f"{duration_min} min" if duration_min > 0 else "—"
                        players_str = PLAYER_COUNT.get(game_name, "—")

                        # Badge color matching Explore Games carousel
                        cat_lower = category.lower()
                        if "cooperative" in cat_lower or "thematic" in cat_lower:
                            badge_color = "linear-gradient(135deg,#5B8DB8,#3A6B99)"
                        elif "party" in cat_lower:
                            badge_color = "linear-gradient(135deg,#C87941,#A05A2C)"
                        else:
                            badge_color = "linear-gradient(135deg,#6B8E6F,#556B58)"

                        import urllib.parse
                        bgg_url = f"https://boardgamegeek.com/geeksearch.php?action=search&q={urllib.parse.quote(game_name)}"
                        desc = stats.get('description', 'Discover and play this amazing board game!')

                        st.markdown(f"""
                        <div style="
                            background: #FFFFFF;
                            border: 3px solid #B8C5B0;
                            border-radius: 20px;
                            padding: 1.5rem;
                            margin-bottom: 1rem;
                            box-shadow: 0 6px 25px rgba(107,142,111,0.15);
                            transition: all 0.3s ease;
                        ">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem; padding-bottom:0.8rem; border-bottom:2px solid #E8DED0;">
                                <h3 class="rec-game-name" style="margin:0; font-size:1.3rem; font-weight:700;">#{i+1}. {game_name}</h3>
                                <span style="padding:0.3rem 0.8rem; border-radius:20px; font-size:0.8rem; font-weight:600; background:{badge_color}; color:white; white-space:nowrap;">{category}</span>
                            </div>
                            <div style="display:flex; gap:0.8rem; margin-bottom: 1rem;">
                                <div style="flex:1; text-align:center; background:#FDF0F5; border-radius:10px; padding:0.5rem; border: 1.5px solid #F2C4D8;">
                                    <span style="display:block; font-size:0.7rem; color:#C0617A; text-transform:uppercase; letter-spacing:0.5px; font-weight:600; margin-bottom:0.2rem;">Match</span>
                                    <span style="display:block; font-size:0.95rem; color:#A04060; font-weight:700;">{int(match_score * 100)}%</span>
                                </div>
                                <div style="flex:1; text-align:center; background:#F5F1E8; border-radius:10px; padding:0.5rem;">
                                    <span style="display:block; font-size:0.7rem; color:#8B6F47; text-transform:uppercase; letter-spacing:0.5px; font-weight:600; margin-bottom:0.2rem;">Players</span>
                                    <span style="display:block; font-size:0.95rem; color:#3E5641; font-weight:700;">{players_str}</span>
                                </div>
                                <div style="flex:1; text-align:center; background:#F5F1E8; border-radius:10px; padding:0.5rem;">
                                    <span style="display:block; font-size:0.7rem; color:#8B6F47; text-transform:uppercase; letter-spacing:0.5px; font-weight:600; margin-bottom:0.2rem;">Complexity</span>
                                    <span style="display:block; font-size:0.95rem; color:#3E5641; font-weight:700;">{"★" * round(complexity * 5) + "☆" * (5 - round(complexity * 5))}</span>
                                </div>
                            </div>
                            <div class="rec-desc" style="font-size: 0.9rem; line-height: 1.5;">
                                <p>{desc}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                                
        except Exception as e:
            st.error(f"Error: {e}")
