# Battleship Game - Simplified Demo Version
# Backend: Python (Flask)
# Frontend: HTML/CSS/JavaScript with design based on the provided visual style

import random
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BOARD_SIZE = 10
SHIP_TYPES = [
    {"name": "Carrier", "size": 5},
    {"name": "Battleship", "size": 4},
    {"name": "Cruiser", "size": 3},
    {"name": "Submarine", "size": 3},
    {"name": "Destroyer", "size": 2}
]
EMPTY = "."
HIT = "🔥"
MISS = "💧"

# In-memory game storage
GAMES = {}

# --- Helper functions ---
def create_board():
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def is_valid_placement(board, coords):
    for x, y in coords:
        if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
            return False
        if board[x][y] != EMPTY:
            return False
    return True

def place_ship(board, coords):
    for x, y in coords:
        board[x][y] = "S"

def all_ships_sunk(ships):
    return all(len(ship["hits"]) == len(ship["coords"]) for ship in ships)

# --- RL Agent ---
class RLAgent:
    def __init__(self):
        self.reset()
    def reset(self):
        self.possible = set((x, y) for x in range(BOARD_SIZE) for y in range(BOARD_SIZE))
        self.hunt_targets = []
        self.last_hits = []
    def choose_action(self, board):
        while self.hunt_targets:
            x, y = self.hunt_targets.pop(0)
            if (x, y) in self.possible and board[x][y] not in [HIT, MISS]:
                self.possible.remove((x, y))
                return x, y
        if self.possible:
            x, y = random.choice(list(self.possible))
            self.possible.remove((x, y))
            return x, y
        return 0, 0
    def notify_result(self, x, y, hit, sunk_coords=None):
        if hit:
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and (nx, ny) in self.possible:
                    self.hunt_targets.append((nx, ny))
            self.last_hits.append((x, y))
        if sunk_coords:
            for sx, sy in sunk_coords:
                for dx in [-1,0,1]:
                    for dy in [-1,0,1]:
                        nx, ny = sx+dx, sy+dy
                        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                            self.possible.discard((nx, ny))
            self.last_hits = []

rl_agent = RLAgent()

# --- API Endpoints ---
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/new_game', methods=['POST'])
def new_game():
    game_id = str(uuid.uuid4())
    boards = [create_board(), create_board()]
    GAMES[game_id] = {
        "boards": boards,
        "ships": [[], []],
        "current_player": 0,
        "game_over": False,
        "winner": None,
        "placed": [False, False]
    }
    rl_agent.reset()
    return jsonify({"game_id": game_id, "current_player": 0})

@app.route('/api/place_ships', methods=['POST'])
def place_ships():
    data = request.json
    game_id = data.get("game_id")
    player = data.get("player")
    ships = data.get("ships")
    game = GAMES.get(game_id)
    if not game or game["placed"][player]:
        return jsonify({"error": "Invalid game or already placed."}), 400
    board = create_board()
    for ship in ships:
        coords = [tuple(coord) for coord in ship["coords"]]
        if not is_valid_placement(board, coords):
            return jsonify({"error": "Invalid ship placement."}), 400
        place_ship(board, coords)
    game["boards"][player] = board
    game["ships"][player] = [{"name": s["name"], "coords": [tuple(c) for c in s["coords"]], "hits": []} for s in ships]
    game["placed"][player] = True
    return jsonify({"success": True, "both_placed": all(game["placed"])})

@app.route('/api/fire', methods=['POST'])
def fire():
    data = request.json
    game_id = data.get("game_id")
    player = int(data.get("player", 0))
    x = int(data.get("x"))
    y = int(data.get("y"))
    game = GAMES.get(game_id)
    if not game or game["game_over"]:
        return jsonify({"error": "Invalid game or game over."}), 400
    if player != game["current_player"]:
        return jsonify({"error": "Not your turn."}), 400
    opponent = 1 - player
    board = game["boards"][opponent]
    ships = game["ships"][opponent]
    if board[x][y] in [HIT, MISS]:
        return jsonify({"error": "Already fired here."}), 400
    hit = False
    sunk_coords = None
    for ship in ships:
        if (x, y) in ship["coords"] and (x, y) not in ship["hits"]:
            ship["hits"].append((x, y))
            board[x][y] = HIT
            hit = True
            if len(ship["hits"]) == len(ship["coords"]):
                sunk_coords = ship["coords"]
            break
    if not hit:
        board[x][y] = MISS
    if player == 1:
        rl_agent.notify_result(x, y, hit, sunk_coords)
    # FIX: Stop the game immediately if all opponent ships are sunk
    if all_ships_sunk(ships):
        game["game_over"] = True
        game["winner"] = player
    else:
        game["current_player"] = opponent
        # Only let the agent fire if the game is not over
        if game["current_player"] == 1 and not game["game_over"]:
            ax, ay = rl_agent.choose_action(game["boards"][0])
            fire_agent(game_id, 1, ax, ay)
    return jsonify({
        "hit": hit,
        "sunk": sunk_coords,
        "game_over": game["game_over"],
        "winner": game["winner"],
        "current_player": game["current_player"]
    })

def fire_agent(game_id, player, x, y):
    game = GAMES.get(game_id)
    if not game or game["game_over"]:
        return
    opponent = 1 - player
    board = game["boards"][opponent]
    ships = game["ships"][opponent]
    if board[x][y] in [HIT, MISS]:
        return
    hit = False
    sunk_coords = None
    for ship in ships:
        if (x, y) in ship["coords"] and (x, y) not in ship["hits"]:
            ship["hits"].append((x, y))
            board[x][y] = HIT
            hit = True
            if len(ship["hits"]) == len(ship["coords"]):
                sunk_coords = ship["coords"]
            break
    if not hit:
        board[x][y] = MISS
    rl_agent.notify_result(x, y, hit, sunk_coords)
    # FIX: Stop the game immediately if all opponent ships are sunk
    if all_ships_sunk(ships):
        game["game_over"] = True
        game["winner"] = player
    else:
        game["current_player"] = 0

@app.route('/api/state', methods=['GET'])
def state():
    game_id = request.args.get("game_id")
    player = int(request.args.get("player", 0))
    game = GAMES.get(game_id)
    if not game:
        return jsonify({"error": "Invalid game."}), 400
    boards = []
    for idx, board in enumerate(game["boards"]):
        b = []
        for i in range(BOARD_SIZE):
            row = []
            for j in range(BOARD_SIZE):
                cell = board[i][j]
                if idx != player and cell == "S":
                    row.append(EMPTY)
                else:
                    row.append(cell)
            b.append(row)
        boards.append(b)
    return jsonify({
        "boards": boards,
        "current_player": game["current_player"],
        "game_over": game["game_over"],
        "winner": game["winner"]
    })

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
