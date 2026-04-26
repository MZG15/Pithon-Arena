# 🐍 Pithon Arena

A real-time two-player snake battle game built with Python and Pygame, using a client-server architecture over TCP. Players connect to a central server, challenge each other, and compete on a shared board — collecting pies to gain health while avoiding collisions.

---

## Features

- **Online multiplayer** — challenge any connected player from the lobby
- **Bot opponent** — play solo against a server-side AI
- **Spectator mode** — watch ongoing matches live
- **Text chat** — communicate with other players during games
- **Multiple pie types** — normal (+10 HP), gold (+25 HP), and bad (−15 HP)
- **Health-based snake length** — your snake grows and shrinks with your HP
- **Collision stun** — collisions deal damage and temporarily freeze your snake
- **Configurable match settings** — time limit, sudden death, speed boost, bad pies, music track
- **Player profiles** — choose from 8 snake color palettes and rebind your movement keys
- **Procedural audio** — synthesized sound effects and three looping music tracks (no audio files needed)
- **Particle effects and smooth animation**

---

## Project Structure

```
pithon-arena/
├── server.py       # Server — manages connections, lobby, and game sessions
├── client.py       # Client — Pygame GUI, input handling, rendering
├── game.py         # Game logic — state, snakes, collisions, bot AI
├── protocol.py     # Shared message framing (length-prefix + pickle over TCP)
└── sounds.py       # Procedural audio engine (NumPy-synthesized)
```

---

## Requirements

- Python 3.9 or higher
- Dependencies:
  - `pygame` — rendering and input
  - `numpy` — game grid and audio synthesis
  - `pynput` *(optional)* — global keyboard capture so movement keys work even when the window is not focused

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/pithon-arena.git
cd pithon-arena
```

### 2. Create and activate a virtual environment

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install pygame numpy pynput
```

> `pynput` is optional. If it is not installed the game falls back to standard Pygame keyboard input, which requires the game window to be in focus for movement keys to register.

---

## Running the Game

### Start the server

The server must be started before any client connects. Run it in its own terminal:

```bash
python server.py
```

By default it listens on **all interfaces** at **port 5555**. You should see:

```
[*] Server listening on port 5555
```

### Start a client

Open a **separate terminal** for each player (activate the virtual environment in each one first), then run:

```bash
python client.py
```

Each client will open a Pygame window and prompt you to enter a username.

> **Playing on the same machine:** open two terminals, run `python client.py` in each, and enter different usernames.

> **Playing over a network:** on each remote machine, open `client.py` and change `SERVER_IP` near the top of the file from `'127.0.0.1'` to the server machine's IP address before running.

---

## How to Play

### Lobby

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate the player list |
| `Enter` | Challenge the selected player |
| `B` | Start a game against the bot |
| `W` | Watch the ongoing match as a spectator |
| `P` | Open your profile (change color and keybinds) |
| `R` | Refresh the player list |
| `A` / `D` | Accept or decline an incoming challenge |
| `ESC` | Quit |

### In-Game (default controls)

Player uses the **arrow keys**.

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move your snake |
| `Enter` | Open chat input |
| `ESC` | Cancel chat |

### Scoring

| Event | HP change |
|-------|-----------|
| Collect a normal pie | +10 HP |
| Collect a gold pie | +25 HP |
| Collect a bad pie | −15 HP |
| Collide with a wall, obstacle, or snake | −25 HP + 1 s stun |

The match ends when a player's HP reaches 0 or when the time limit expires or a player's HP reaches 1000. The player with more HP at the end wins.

---

## Troubleshooting

**`Connection refused` on the client** — make sure the server is running before starting the client, and that `SERVER_IP` in `client.py` points to the correct machine.

**No sound / audio error on startup** — the audio engine requires `numpy`. If `numpy` is missing, the client will start without sound. Install it with `pip install numpy`.

**Movement keys not responding** — click the game window to give it focus, or install `pynput` to enable global key capture.

**`Username already taken`** — each session requires a unique username. Choose a different one or wait for the previous session to disconnect.
