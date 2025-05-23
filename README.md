# 🛥 Simple Battleship Game (Classical Version)

## Overview

This simple Battleship game demo features a 10x10 board, classic ship types, drag-and-drop ship placement, and a basic RL agent opponent. The backend is written in Python using Flask, and the frontend is a single-page HTML/JS app.

---

## Game Rules

- **Board:** 10x10 grid for each player (human and agent).
- **Ships:**  
  - Carrier (5 cells)  
  - Battleship (4 cells)  
  - Cruiser (3 cells)  
  - Submarine (3 cells)  
  - Destroyer (2 cells)
- **Placement:**  
  - Ships cannot overlap or touch (not even diagonally).
  - Ships must be placed fully within the board.
  - Once the game starts, ships cannot be moved.
- **Gameplay:**  
  - Players take turns firing at the opponent’s board.
  - A hit is marked with a fire emoji (🔥), a miss with a water emoji (💧).
  - The first player is always the human; the second is the RL agent.
  - The game ends immediately when all ships of one player are sunk.

---

## Backend (Flask)

### Main Concepts

- **Game State:**  
  Stored in-memory in the `GAMES` dictionary, keyed by a unique game ID.
- **Boards:**  
  Each game has two boards: one for the human, one for the agent.
- **Ships:**  
  Each player’s ships are tracked as a list of dictionaries with coordinates and hit status.

### RL Agent

- **Strategy:**  
  - Random firing until a hit.
  - If a hit is made, the agent targets neighboring cells.
  - The agent avoids firing at cells adjacent to sunk ships.

---

### API Endpoints

#### `POST /api/new_game`

- **Purpose:** Start a new game.
- **Returns:**  
  - `game_id`: Unique ID for the game.
  - `current_player`: Always 0 (human).

#### `POST /api/place_ships`

- **Purpose:** Submit ship placements for a player.
- **Body:**  
  - `game_id`: Game ID.
  - `player`: 0 (human) or 1 (agent).
  - `ships`: List of ships, each with `name` and `coords` (list of [x, y] pairs).
- **Returns:**  
  - `success`: True if placement is valid.
  - `both_placed`: True if both players have placed ships.

- **Validation:**  
  - Ships cannot overlap or touch (including diagonally).
  - Invalid placements are rejected.

#### `POST /api/fire`

- **Purpose:** Fire at a cell.
- **Body:**  
  - `game_id`: Game ID.
  - `player`: 0 (human) or 1 (agent).
  - `x`, `y`: Target cell coordinates.
- **Returns:**  
  - `hit`: True if a ship was hit.
  - `sunk`: Coordinates of the sunk ship, if any.
  - `game_over`: True if the game is over.
  - `winner`: 0 (human) or 1 (agent), if game is over.
  - `current_player`: Whose turn is next.

#### `GET /api/state`

- **Purpose:** Get the current game state for rendering.
- **Query:**  
  - `game_id`: Game ID.
  - `player`: 0 (human) or 1 (agent).
- **Returns:**  
  - `boards`: Both boards, with opponent’s ships hidden.
  - `current_player`, `game_over`, `winner`.

#### `/`

- **Purpose:** Serves the frontend HTML.

---

## Frontend (HTML/JS)

- **Ship Placement:**  
  - Drag-and-drop interface with rotation.
  - Ships cannot be placed illegally (overlap/touching/diagonal).
  - Placement is validated both client-side and server-side.
- **Gameplay:**  
  - Click on the agent’s board to fire.
  - Hits and misses are visually marked.
  - The agent’s moves are automatic and follow the RL strategy.
- **Design:**  
  - Modern, clean, and responsive.
  - Ships are visible only on the player’s own board.

---

## Extending the Application

- **Add user authentication** for multiplayer.
- **Persist game state** in a database for long-term play.
- **Improve the RL agent** with more advanced strategies.
- **Add animations or sound effects** for hits/misses.
- **Enhance the UI** with ship icons, better drag-and-drop, or mobile support.

---

## Developer Notes

- **Backend is stateless** except for in-memory game storage; restart will lose all games.
- **Frontend and backend are decoupled**; you can swap out the frontend or backend independently.
- **All validation is enforced on the backend** for security and fairness.

---

If you need a README.md or inline code comments, or want to generate OpenAPI/Swagger docs for the API, just ask!




#### Backend (Python/Flask) — Ship Placement Validation

- The `is_valid_placement` function checks for overlap and for adjacency:  
  - For every cell a ship would occupy, it checks all 8 surrounding cells (including diagonals).
  - If any of those cells already contains a ship ("S"), the placement is rejected.
  - This enforces the classic Battleship rule: ships cannot touch each other, not even at the corners and prevents both the player and the AI from placing ships that overlap or are directly adjacent.
- When a player tries to place a ship (via `/api/place_ships`), the backend uses `is_valid_placement` to validate the placement.
- When the AI places ships randomly, it also uses this function, retrying until a valid spot is found.

