from crud import get_all_games, add_member

games = get_all_games()

for g in games:
    print(f"""
Game: {g[1]}
Category: {g[9]}
Players: {g[10]}
Strategy: {g[2]}
Complexity: {g[7]}
Description: {g[12]}
----------------------
""")

add_member("Radhika")
print("Member added!")