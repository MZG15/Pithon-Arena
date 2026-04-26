import math

import queue

import random

import socket

import sys

import threading

import time

import pygame

from protocol import recv_msg, send_msg

from sounds import SoundManager

SERVER_IP = '127.0.0.1'

SERVER_PORT = 5555

CELL_SIZE = 20

GRID_W = 30

GRID_H = 30

PANEL_WIDTH = 200

HUD_HEIGHT = 56

BOARD_W = GRID_W * CELL_SIZE

BOARD_H = GRID_H * CELL_SIZE

WIN_W = BOARD_W + PANEL_WIDTH

WIN_H = HUD_HEIGHT + BOARD_H

FPS = 60

TICK_RATE = 0.1

HEALTH_BAR_MAX = 1000

BLACK = (14, 10, 24)

WHITE = (245, 240, 255)

GRAY = (140, 130, 160)

DARK_GRAY = (28, 20, 44)

GREEN = (255, 140, 0)

GREEN_DARK = (180, 85, 0)

RED = (120, 80, 255)

RED_DARK = (70, 45, 170)

YELLOW = (255, 230, 90)

ORANGE = (255, 90, 140)

BLUE = (90, 180, 255)

PURPLE = (210, 110, 255)

CYAN = (255, 120, 200)

PANEL_BG = (22, 12, 36)

SOFT_RED = (220, 50, 50)

Amber_txt = (255, 160, 40)

COLOR_OPTIONS = [('Amber', (255, 160, 40), (255, 215, 130), (160, 90, 10), (70, 35, 5)), ('Violet', (160, 100, 255), (200, 170, 255), (80, 50, 180), (36, 20, 70)), ('Cyan', (60, 210, 255), (180, 240, 255), (20, 130, 180), (5, 60, 90)), ('Rose', (255, 80, 130), (255, 185, 210), (170, 40, 80), (80, 10, 40)), ('Lime', (120, 255, 60), (200, 255, 150), (60, 170, 20), (20, 80, 5)), ('Gold', (255, 215, 0), (255, 245, 160), (170, 140, 0), (80, 60, 0)), ('Magenta', (255, 60, 220), (255, 185, 245), (160, 20, 140), (70, 5, 60)), ('Teal', (0, 200, 180), (150, 240, 230), (0, 120, 100), (0, 50, 40))]

my_color_idx = 0

my_keybinds = {'UP': pygame.K_UP, 'DOWN': pygame.K_DOWN, 'LEFT': pygame.K_LEFT, 'RIGHT': pygame.K_RIGHT}

state = {}

game_start = {}

inbox = []

inbox_lock = threading.Lock()

sock = None

my_username = None

running = True

is_bot_game = False

audio = None

_key_queue = queue.Queue()

_pynput_listener = None


def sanitize_color_idx(value):

    try:

        return int(value) % len(COLOR_OPTIONS)

    except Exception:

        return 0


def get_color_entry(color_idx):

    return COLOR_OPTIONS[sanitize_color_idx(color_idx)]


def get_head_color(color_idx):

    return get_color_entry(color_idx)[1]


def get_snake_colors(color_idx):

    return tuple(get_color_entry(color_idx)[1:])



def key_name_display(pykey, short=False):

    if short:

        special = {pygame.K_UP: 'UP', pygame.K_DOWN: 'DOWN', pygame.K_LEFT: 'LEFT', pygame.K_RIGHT: 'RIGHT', pygame.K_SPACE: 'SPC', pygame.K_RETURN: 'ENT', pygame.K_TAB: 'TAB', pygame.K_LSHIFT: 'LSHFT', pygame.K_RSHIFT: 'RSHFT', pygame.K_LCTRL: 'LCTRL', pygame.K_RCTRL: 'RCTRL', pygame.K_LALT: 'LALT', pygame.K_RALT: 'RALT', pygame.K_BACKSPACE: 'BACK'}

        if pykey in special:

            return special[pykey]

        name = pygame.key.name(pykey)

        return name.upper()[:4] if name else '?'

    else:

        special = {pygame.K_UP: 'Up Arrow', pygame.K_DOWN: 'Down Arrow', pygame.K_LEFT: 'Left Arrow', pygame.K_RIGHT: 'Right Arrow', pygame.K_SPACE: 'Space', pygame.K_RETURN: 'Enter', pygame.K_TAB: 'Tab', pygame.K_BACKSPACE: 'Backspace', pygame.K_DELETE: 'Delete', pygame.K_HOME: 'Home', pygame.K_END: 'End', pygame.K_PAGEUP: 'PgUp', pygame.K_PAGEDOWN: 'PgDn', pygame.K_LSHIFT: 'L-Shift', pygame.K_RSHIFT: 'R-Shift', pygame.K_LCTRL: 'L-Ctrl', pygame.K_RCTRL: 'R-Ctrl', pygame.K_LALT: 'L-Alt', pygame.K_RALT: 'R-Alt'}

        if pykey in special:

            return special[pykey]

        name = pygame.key.name(pykey)

        return name.upper() if name else f'Key({pykey})'



def _start_global_keyboard(keybinds):

    global _pynput_listener

    try:

        from pynput import keyboard as _kb

        pg_to_pynput = {pygame.K_UP: _kb.Key.up, pygame.K_DOWN: _kb.Key.down, pygame.K_LEFT: _kb.Key.left, pygame.K_RIGHT: _kb.Key.right, pygame.K_SPACE: _kb.Key.space, pygame.K_RETURN: _kb.Key.enter, pygame.K_TAB: _kb.Key.tab, pygame.K_BACKSPACE: _kb.Key.backspace, pygame.K_DELETE: _kb.Key.delete, pygame.K_HOME: _kb.Key.home, pygame.K_END: _kb.Key.end, pygame.K_PAGEUP: _kb.Key.page_up, pygame.K_PAGEDOWN: _kb.Key.page_down, pygame.K_F1: _kb.Key.f1, pygame.K_F2: _kb.Key.f2, pygame.K_F3: _kb.Key.f3, pygame.K_F4: _kb.Key.f4, pygame.K_F5: _kb.Key.f5, pygame.K_F6: _kb.Key.f6, pygame.K_F7: _kb.Key.f7, pygame.K_F8: _kb.Key.f8, pygame.K_F9: _kb.Key.f9, pygame.K_F10: _kb.Key.f10, pygame.K_F11: _kb.Key.f11, pygame.K_F12: _kb.Key.f12}

        named_map = {}

        char_map = {}

        for direction, pykey in keybinds.items():

            if pykey in pg_to_pynput:

                named_map[pg_to_pynput[pykey]] = direction

            else:

                key_name = pygame.key.name(pykey)

                if key_name and len(key_name) == 1:

                    char_map[key_name.lower()] = direction



        def on_press(key):

            mapped = named_map.get(key)

            if mapped:

                _key_queue.put(mapped)

                return

            try:

                ch = key.char

                if ch and ch.lower() in char_map:

                    _key_queue.put(char_map[ch.lower()])

            except AttributeError:

                pass

        _pynput_listener = _kb.Listener(on_press=on_press)

        _pynput_listener.daemon = True

        _pynput_listener.start()

    except Exception as e:

        print(f'[input] pynput unavailable, falling back to pygame-only input: {e}')



def _stop_global_keyboard():

    global _pynput_listener

    if _pynput_listener is not None:

        try:

            _pynput_listener.stop()

        except Exception:

            pass

        _pynput_listener = None



def receiver():

    global running, state

    while running:

        msg = recv_msg(sock)

        if msg is None:

            running = False

            break

        with inbox_lock:

            if msg['type'] == 'STATE':

                state = msg

            else:

                inbox.append(msg)



def pop_messages():

    with inbox_lock:

        msgs = inbox[:]

        inbox.clear()

    return msgs



class Particle:



    def __init__(self, x, y, color):

        angle = random.uniform(0, 2 * math.pi)

        speed = random.uniform(1.5, 4.0)

        self.x = float(x)

        self.y = float(y)

        self.vx = math.cos(angle) * speed

        self.vy = math.sin(angle) * speed

        self.color = color

        self.life = 1.0

        self.decay = random.uniform(0.04, 0.08)

        self.radius = random.randint(2, 4)



    def update(self, dt):

        self.x += self.vx * dt * 60

        self.y += self.vy * dt * 60

        self.vy += 0.15 * dt * 60

        self.life -= self.decay * dt * 60



    def alive(self):

        return self.life > 0



    def draw(self, surface):

        r, g, b = self.color

        pygame.draw.circle(surface, (min(255, r), min(255, g), min(255, b)), (int(self.x), int(self.y)), self.radius)

particles = []



def spawn_particles(cx, cy, color, count=12):

    for _ in range(count):

        particles.append(Particle(cx, cy, color))



class SnakeInterp:



    def __init__(self):

        self.prev = []

        self.curr = []

        self.t = 1.0



    def update(self, new_body):

        if new_body != self.curr:

            self.prev = self.curr if self.curr else list(new_body)

            self.curr = list(new_body)

            self.t = 0.0



    def advance(self, dt):

        self.t = min(1.0, self.t + dt / TICK_RATE)



    def positions(self):

        t = self.t

        t = t * t * (3.0 - 2.0 * t)

        result = []

        for i, (cx, cy) in enumerate(self.curr):

            px, py = self.prev[i] if i < len(self.prev) else (cx, cy)

            result.append((px + (cx - px) * t, py + (cy - py) * t))

        return result

_s1_interp = SnakeInterp()

_s2_interp = SnakeInterp()



def draw_text(surface, text, x, y, font, color=WHITE):

    surface.blit(font.render(text, True, color), (x, y))



def draw_health_bar(surface, x, y, w, h, value, max_val, color, align_right=False):

    pygame.draw.rect(surface, GRAY, (x, y, w, h), border_radius=6)

    fill = int(w * max(0, min(value, max_val)) / max_val)

    if align_right:

        pygame.draw.rect(surface, color, (x + w - fill, y, fill, h), border_radius=6)

    else:

        pygame.draw.rect(surface, color, (x, y, fill, h), border_radius=6)

    pygame.draw.rect(surface, WHITE, (x, y, w, h), 1, border_radius=6)



def _draw_eyes_f(surface, hx, hy, nx, ny):

    dx = hx - nx

    dy = hy - ny

    cx = int(hx * CELL_SIZE) + CELL_SIZE // 2

    cy = HUD_HEIGHT + int(hy * CELL_SIZE) + CELL_SIZE // 2

    offsets = [(0, -4), (0, 4)] if abs(dx) > abs(dy) else [(-4, 0), (4, 0)]

    for ox, oy in offsets:

        pygame.draw.circle(surface, WHITE, (cx + ox, cy + oy), 2)

        pygame.draw.circle(surface, BLACK, (cx + ox, cy + oy), 1)



def _draw_snake_preview(surface, color_option, right_x, y, cell=11, gap=2, count=8):

    _, head_col, _boost, body_col, body_dark = color_option

    for i in range(count):

        px = right_x - i * (cell + gap)

        if i == 0:

            col = head_col

        else:

            fade = min(1.0, (i - 1) / max(1, count - 2))

            col = tuple((int(body_col[j] + (body_dark[j] - body_col[j]) * fade) for j in range(3)))

        pygame.draw.rect(surface, col, (px, y, cell, cell), border_radius=3)



def format_settings_lines(settings):

    if not settings:

        return []

    music_label = {'chiptune': '8-bit', 'electronic': 'Electronic', 'lofi': 'Lo-fi', 'off': 'Off'}.get(settings.get('music', 'chiptune'), str(settings.get('music', 'chiptune')))

    return [f"Time limit: {settings.get('time_limit', 120)}s", f"Sudden death: {('ON' if settings.get('sudden_death', True) else 'OFF')}", f"Speed boost: {('ON' if settings.get('speed_boost', True) else 'OFF')}", f"Bad pies: {('ON' if settings.get('bad_pies', True) else 'OFF')}", f'Music: {music_label}']



def draw_top_bars(surface, gs, font, font_small, p1_name, p2_name, your_id, p1_color, p2_color):

    scores = gs.get('scores', {'p1': 100, 'p2': 100})

    stun1 = gs.get('stun1', 0)

    stun2 = gs.get('stun2', 0)

    time_left = gs.get('time_left', 0)

    pygame.draw.rect(surface, PANEL_BG, (0, 0, BOARD_W, HUD_HEIGHT))

    pygame.draw.line(surface, CYAN, (0, HUD_HEIGHT - 1), (BOARD_W, HUD_HEIGHT - 1), 1)

    bar_y = 24

    bar_w = 220

    bar_h = 14

    draw_text(surface, p1_name, 12, 4, font_small, p1_color)

    draw_health_bar(surface, 12, bar_y, bar_w, bar_h, scores.get('p1', 0), HEALTH_BAR_MAX, p1_color)

    draw_text(surface, f"{scores.get('p1', 0)} / {HEALTH_BAR_MAX}", 12, 40, font_small, p1_color)

    if stun1 > 0:

        draw_text(surface, f'STUN {stun1:.1f}s', 150, 4, font_small, YELLOW)

    right_x = BOARD_W - 12 - bar_w

    draw_text(surface, p2_name, right_x, 4, font_small, p2_color)

    draw_health_bar(surface, right_x, bar_y, bar_w, bar_h, scores.get('p2', 0), HEALTH_BAR_MAX, p2_color, align_right=True)

    score_label = f"{scores.get('p2', 0)} / {HEALTH_BAR_MAX}"

    label_x = BOARD_W - 12 - font_small.size(score_label)[0]

    draw_text(surface, score_label, label_x, 40, font_small, p2_color)

    if stun2 > 0:

        stun_text = f'STUN {stun2:.1f}s'

        stun_x = right_x + bar_w - font_small.size(stun_text)[0] - 10

        draw_text(surface, stun_text, stun_x, 4, font_small, YELLOW)

    title = 'PITHON ARENA'

    title_x = BOARD_W // 2 - font.size(title)[0] // 2

    draw_text(surface, title, title_x, 4, font, CYAN)

    timer_text = f'Time: {int(time_left)}s'

    timer_x = BOARD_W // 2 - font_small.size(timer_text)[0] // 2

    timer_color = RED if time_left < 30 else WHITE

    draw_text(surface, timer_text, timer_x, 30, font_small, timer_color)

    if your_id == 0:

        spec_text = 'SPECTATING'

        spec_x = BOARD_W // 2 - font_small.size(spec_text)[0] // 2

        draw_text(surface, spec_text, spec_x, 42, font_small, YELLOW)


def draw_grid(surface, gs, dt, tick, p1_snake_colors=None, p2_snake_colors=None):

    s1 = gs.get('snake1', [])

    s2 = gs.get('snake2', [])

    pies = gs.get('pies', [])

    b1 = gs.get('boost1', False)

    b2 = gs.get('boost2', False)

    flash = gs.get('_death_flash', 0)

    _s1_interp.update(s1)

    _s2_interp.update(s2)

    _s1_interp.advance(dt)

    _s2_interp.advance(dt)

    s1_pos = _s1_interp.positions()

    s2_pos = _s2_interp.positions()

    pygame.draw.rect(surface, DARK_GRAY, (0, HUD_HEIGHT, BOARD_W, BOARD_H))

    for x in range(GRID_W):

        for y in range(GRID_H):

            tile = (40, 24, 58) if (x + y) % 2 == 0 else (32, 18, 48)

            rect = (x * CELL_SIZE, HUD_HEIGHT + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

            pygame.draw.rect(surface, tile, rect)

            pygame.draw.rect(surface, (74, 56, 98), rect, 1)

    for ox, oy in game_start.get('obstacles', []):

        pygame.draw.rect(surface, (120, 110, 170), (ox * CELL_SIZE, HUD_HEIGHT + oy * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    pulse = math.sin(tick * 0.1) * 2

    for px, py, kind in pies:

        color = {4: YELLOW, 5: ORANGE, 6: PURPLE}.get(kind, YELLOW)

        cx = px * CELL_SIZE + CELL_SIZE // 2

        cy = HUD_HEIGHT + py * CELL_SIZE + CELL_SIZE // 2

        r = max(2, int(CELL_SIZE // 2 - 2 + pulse))

        pygame.draw.circle(surface, color, (cx, cy), r)

        pygame.draw.circle(surface, WHITE, (cx - 2, cy - 2), max(1, r // 3))


    def lerp_color(c1, c2, amount):

        return tuple((int(c1[i] + (c2[i] - c1[i]) * amount) for i in range(3)))


    def draw_snake(positions, boost, head_col, head_boost_col, body_col, body_dark):

        for i, (fx, fy) in enumerate(positions):

            rx = int(fx * CELL_SIZE) + 1

            ry = HUD_HEIGHT + int(fy * CELL_SIZE) + 1

            if i == 0:

                col = head_boost_col if boost else head_col

            else:

                fade = min(1.0, max(0.0, (i - 2) / max(1, len(positions) - 2)))

                col = lerp_color(body_col, body_dark, fade)

            pygame.draw.rect(surface, col, (rx, ry, CELL_SIZE - 2, CELL_SIZE - 2))

        if len(positions) > 1:

            _draw_eyes_f(surface, positions[0][0], positions[0][1], positions[1][0], positions[1][1])

    p1_cols = p1_snake_colors or (GREEN, (255, 200, 90), GREEN_DARK, (70, 35, 10))

    p2_cols = p2_snake_colors or (RED, (180, 140, 255), RED_DARK, (36, 20, 70))

    draw_snake(s2_pos, b2, *p2_cols)

    draw_snake(s1_pos, b1, *p1_cols)

    for p in particles:

        p.draw(surface)

    if flash > 0:

        overlay = pygame.Surface((BOARD_W, BOARD_H))

        overlay.set_alpha(int(flash * 120))

        overlay.fill((255, 30, 30))

        surface.blit(overlay, (0, HUD_HEIGHT))


def draw_panel(surface, gs, font, font_small, p1_name, p2_name, chat_lines, your_id, p1_color=None, p2_color=None, control_keybinds=None, control_color=None):

    px = BOARD_W

    scores = gs.get('scores', {'p1': 100, 'p2': 100})

    pygame.draw.rect(surface, PANEL_BG, (px, 0, PANEL_WIDTH, WIN_H))

    draw_text(surface, 'LEGEND', px + 10, 10, font, CYAN)

    pygame.draw.line(surface, CYAN, (px + 5, 34), (px + PANEL_WIDTH - 5, 34), 1)

    pygame.draw.circle(surface, YELLOW, (px + 18, 58), 6)

    draw_text(surface, '+10 hp', px + 30, 52, font_small, YELLOW)

    pygame.draw.circle(surface, ORANGE, (px + 18, 78), 6)

    draw_text(surface, '+25 hp', px + 30, 72, font_small, ORANGE)

    pygame.draw.circle(surface, PURPLE, (px + 18, 98), 6)

    draw_text(surface, '-15 hp', px + 30, 92, font_small, PURPLE)

    draw_text(surface, 'Collisions: -25 hp', px + 10, 114, font_small, WHITE)

    draw_text(surface, 'Stun on collision: 1s', px + 10, 130, font_small, WHITE)

    pygame.draw.line(surface, GRAY, (px + 5, 148), (px + PANEL_WIDTH - 5, 148), 1)

    draw_text(surface, 'Controls:', px + 10, 154, font_small, WHITE)

    if your_id == 0:

        draw_text(surface, 'Spectator mode', px + 10, 170, font_small, YELLOW)

        ctrl_end_y = 186

    else:

        ctrl_col = control_color or (p1_color if your_id == 1 else p2_color) or GREEN

        active_keybinds = control_keybinds or my_keybinds

        up_s = key_name_display(active_keybinds['UP'], short=True)

        dn_s = key_name_display(active_keybinds['DOWN'], short=True)

        lt_s = key_name_display(active_keybinds['LEFT'], short=True)

        rt_s = key_name_display(active_keybinds['RIGHT'], short=True)

        draw_text(surface, f'Up:{up_s}  Down:{dn_s}', px + 10, 170, font_small, ctrl_col)

        draw_text(surface, f'Left:{lt_s}  Right:{rt_s}', px + 10, 186, font_small, ctrl_col)

        ctrl_end_y = 202

    draw_text(surface, 'ENTER', px + 10, ctrl_end_y, font_small, BLUE)

    draw_text(surface, ' to open Chat', px + 10 + font_small.size('ENTER')[0], ctrl_end_y, font_small, CYAN)

    draw_text(surface, 'type > ENTER', px + 10, ctrl_end_y + 16, font_small, BLUE)

    draw_text(surface, ' to send', px + 10 + font_small.size('type > ENTER')[0], ctrl_end_y + 16, font_small, CYAN)

    draw_text(surface, 'ESC', px + 10, ctrl_end_y + 32, font_small, BLUE)

    draw_text(surface, ' cancels chat', px + 10 + font_small.size('ESC')[0], ctrl_end_y + 32, font_small, CYAN)

    sep_y = ctrl_end_y + 52

    pygame.draw.line(surface, GRAY, (px + 5, sep_y), (px + PANEL_WIDTH - 5, sep_y), 1)

    p1_col = p1_color or GREEN

    p2_col = p2_color or RED

    draw_text(surface, 'Match:', px + 10, sep_y + 8, font_small, WHITE)

    draw_text(surface, f"{p1_name}: {scores.get('p1', 0)}", px + 10, sep_y + 26, font_small, p1_col)

    draw_text(surface, f"{p2_name}: {scores.get('p2', 0)}", px + 10, sep_y + 42, font_small, p2_col)

    chat_sep_y = sep_y + 62

    pygame.draw.line(surface, GRAY, (px + 5, chat_sep_y), (px + PANEL_WIDTH - 5, chat_sep_y), 1)

    draw_text(surface, 'Chat feed:', px + 10, chat_sep_y + 6, font_small, WHITE)

    for i, line in enumerate(chat_lines[-10:]):

        draw_text(surface, line[:25], px + 10, chat_sep_y + 24 + i * 16, font_small, CYAN)


def screen_connect(surface, clock, font, font_small, error_msg=None):

    username = ''

    while True:

        clock.tick(FPS)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()

                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_RETURN and username.strip():

                    return username.strip()

                if event.key == pygame.K_BACKSPACE:

                    username = username[:-1]

                elif len(username) < 16 and event.unicode.isprintable():

                    username += event.unicode

        surface.fill(BLACK)

        draw_text(surface, 'PITHON ARENA', WIN_W // 2 - 100, 180, font, CYAN)

        draw_text(surface, 'Enter username:', WIN_W // 2 - 90, 250, font_small, WHITE)

        box_rect = pygame.Rect(WIN_W // 2 - 100, 280, 200, 36)

        pygame.draw.rect(surface, GRAY, box_rect)

        pygame.draw.rect(surface, CYAN, box_rect, 2)

        draw_text(surface, username, WIN_W // 2 - 90, 288, font_small, WHITE)

        draw_text(surface, 'Press ENTER to join', WIN_W // 2 - 90, 330, font_small, GRAY)

        if error_msg:

            draw_text(surface, error_msg, WIN_W // 2 - 90, 360, font_small, RED)

        pygame.display.flip()



def screen_profile(surface, clock, font, font_small):

    global my_color_idx, my_keybinds

    color_idx = my_color_idx

    keybinds = dict(my_keybinds)

    DIRECTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT']

    DIR_LABELS = ['Move Up', 'Move Down', 'Move Left', 'Move Right']

    FORBIDDEN = {pygame.K_ESCAPE, pygame.K_RETURN}

    selected = 0

    binding = None

    conflict_msg = ''

    ROW_H = 54

    ROW_X = 40

    ROW_W = WIN_W - 80

    COLOR_Y = 118

    DIR_Y0 = 204

    pygame.event.clear()

    while True:

        clock.tick(FPS)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()

                sys.exit()

            if event.type == pygame.KEYDOWN:

                if binding is not None:

                    if event.key == pygame.K_ESCAPE:

                        binding = None

                        conflict_msg = ''

                    elif event.key not in FORBIDDEN:

                        conflict_dir = next((d for d, k in keybinds.items() if k == event.key and d != binding), None)

                        if conflict_dir:

                            conflict_msg = f'Key already used for {conflict_dir}! Pick another.'

                        else:

                            keybinds[binding] = event.key

                            binding = None

                            conflict_msg = ''

                elif event.key == pygame.K_ESCAPE:

                    return

                elif event.key == pygame.K_RETURN:

                    my_color_idx = color_idx

                    my_keybinds = keybinds

                    if sock:

                        send_msg(sock, {'type': 'PROFILE_UPDATE', 'color_idx': my_color_idx})

                    return

                elif event.key == pygame.K_UP:

                    selected = (selected - 1) % 5

                    conflict_msg = ''

                elif event.key == pygame.K_DOWN:

                    selected = (selected + 1) % 5

                    conflict_msg = ''

                elif event.key == pygame.K_LEFT and selected == 0:

                    color_idx = (color_idx - 1) % len(COLOR_OPTIONS)

                elif event.key == pygame.K_RIGHT and selected == 0:

                    color_idx = (color_idx + 1) % len(COLOR_OPTIONS)

                elif event.key == pygame.K_SPACE and 1 <= selected <= 4:

                    binding = DIRECTIONS[selected - 1]

                    conflict_msg = ''

        surface.fill(BLACK)

        draw_text(surface, 'PLAYER PROFILE', WIN_W // 2 - 112, 28, font, CYAN)

        x_pr = ROW_X + 90

        y_pr = 66

        draw_text(surface, 'UP/DOWN: navigate   ', x_pr, y_pr, font_small, CYAN)

        x_pr += font_small.size('UP/DOWN: navigate   ')[0]

        draw_text(surface, 'LEFT/RIGHT: change color   ', x_pr, y_pr, font_small, YELLOW)

        x_pr += font_small.size('LEFT/RIGHT: change color   ')[0]

        draw_text(surface, 'SPACE: rebind key', x_pr, y_pr, font_small, Amber_txt)

        pygame.draw.line(surface, CYAN, (ROW_X, 90), (WIN_W - ROW_X, 90), 1)

        active = selected == 0

        row_top = COLOR_Y - 10

        pygame.draw.rect(surface, (58, 28, 88) if active else BLACK, (ROW_X, row_top, ROW_W, ROW_H))

        if active:

            pygame.draw.rect(surface, CYAN, (ROW_X, row_top, ROW_W, ROW_H), 1)

        cname, hcol, _, bcol, bdark = COLOR_OPTIONS[color_idx]

        draw_text(surface, 'Snake Color', ROW_X + 20, COLOR_Y, font_small, CYAN if active else WHITE)

        draw_text(surface, f'< {cname} >', WIN_W - 260, COLOR_Y, font_small, YELLOW)

        _draw_snake_preview(surface, COLOR_OPTIONS[color_idx], right_x=WIN_W - ROW_X - 10, y=COLOR_Y + 20)

        for i, (direction, label) in enumerate(zip(DIRECTIONS, DIR_LABELS)):

            row_idx = i + 1

            y_centre = DIR_Y0 + i * (ROW_H + 4)

            row_top2 = y_centre - 10

            active2 = selected == row_idx

            pygame.draw.rect(surface, (58, 28, 88) if active2 else BLACK, (ROW_X, row_top2, ROW_W, ROW_H))

            if active2:

                pygame.draw.rect(surface, CYAN, (ROW_X, row_top2, ROW_W, ROW_H), 1)

            draw_text(surface, label, ROW_X + 20, y_centre, font_small, CYAN if active2 else WHITE)

            if binding == direction:

                draw_text(surface, '>>> press any key <<<', WIN_W - 300, y_centre, font_small, YELLOW)

            else:

                kdisp = key_name_display(keybinds[direction])

                kcol = GREEN if active2 else GRAY

                draw_text(surface, kdisp, WIN_W - 260, y_centre, font_small, kcol)

                if active2:

                    draw_text(surface, 'SPACE to rebind', WIN_W - 260, y_centre + 18, font_small, (90, 90, 110))

        if conflict_msg:

            draw_text(surface, conflict_msg, ROW_X, WIN_H - 80, font_small, RED)

        draw_text(surface, 'ENTER = Save & Return   ESC = Cancel', WIN_W // 2 - 155, WIN_H - 48, font_small, YELLOW)

        pygame.display.flip()



def screen_settings(surface, clock, font, font_small, title='GAME SETTINGS', confirm_label='confirm'):

    from game import TIME_OPTIONS

    settings = {'sudden_death': True, 'speed_boost': True, 'bad_pies': True, 'time_limit': 120, 'music': 'chiptune'}

    options = [('sudden_death', 'Sudden Death  (walls close in last 30s)'), ('speed_boost', 'Speed Boost   (golden pie = 5s speed)'), ('bad_pies', 'Bad Pies      (purple pie = -15 hp)')]

    selected = 0

    time_idx = TIME_OPTIONS.index(120)

    music_opts = ['chiptune', 'electronic', 'lofi', 'off']

    music_idx = 0

    pygame.event.clear()

    while True:

        clock.tick(FPS)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()

                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    return None

                if event.key == pygame.K_UP:

                    selected = (selected - 1) % (len(options) + 2)

                elif event.key == pygame.K_DOWN:

                    selected = (selected + 1) % (len(options) + 2)

                elif event.key == pygame.K_SPACE:

                    if selected < len(options):

                        key = options[selected][0]

                        settings[key] = not settings[key]

                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):

                    if selected < len(options):

                        key = options[selected][0]

                        settings[key] = not settings[key]

                    elif selected == len(options):

                        if event.key == pygame.K_LEFT:

                            time_idx = max(0, time_idx - 1)

                        else:

                            time_idx = min(len(TIME_OPTIONS) - 1, time_idx + 1)

                        settings['time_limit'] = TIME_OPTIONS[time_idx]

                    elif selected == len(options) + 1:

                        if event.key == pygame.K_LEFT:

                            music_idx = (music_idx - 1) % len(music_opts)

                        else:

                            music_idx = (music_idx + 1) % len(music_opts)

                        settings['music'] = music_opts[music_idx]

                        if audio and settings['music'] != 'off':

                            audio.play_music(settings['music'])

                        elif audio:

                            audio.stop_music()

                elif event.key == pygame.K_RETURN:

                    return settings

        surface.fill(BLACK)

        draw_text(surface, title, WIN_W // 2 - 120, 60, font, CYAN)

        x_se = font_small.size('UP/DOWN select  SPACE toggle  LEFT/RIGHT adjust')[0] / 2

        y_se = 100

        draw_text(surface, 'UP/DOWN select  ', x_se, y_se, font_small, CYAN)

        x_se += font_small.size('UP/DOWN select  ')[0]

        draw_text(surface, 'SPACE toggle  ', x_se, y_se, font_small, Amber_txt)

        x_se += font_small.size('SPACE toggle  ')[0]

        draw_text(surface, 'LEFT/RIGHT adjust', x_se, y_se, font_small, YELLOW)

        pygame.draw.line(surface, CYAN, (40, 140), (WIN_W - 40, 140), 1)

        for i, (key, label) in enumerate(options):

            y = 165 + i * 50

            active = selected == i

            bg = (58, 28, 88) if active else BLACK

            pygame.draw.rect(surface, bg, (40, y - 6, WIN_W - 80, 38))

            if active:

                pygame.draw.rect(surface, CYAN, (40, y - 6, WIN_W - 80, 38), 1)

            draw_text(surface, label, 60, y, font_small, CYAN if active else WHITE)

            val = settings[key]

            pill_x = WIN_W - 120

            pill_color = GREEN if val else RED

            pygame.draw.rect(surface, pill_color, (pill_x, y, 60, 22), border_radius=11)

            draw_text(surface, 'ON' if val else 'OFF', pill_x + 14, y + 3, font_small, BLACK)

        ti = len(options)

        y = 165 + ti * 50

        active = selected == ti

        bg = (58, 28, 88) if active else BLACK

        pygame.draw.rect(surface, bg, (40, y - 6, WIN_W - 80, 38))

        if active:

            pygame.draw.rect(surface, CYAN, (40, y - 6, WIN_W - 80, 38), 1)

        draw_text(surface, 'Time Limit     (LEFT/RIGHT)', 60, y, font_small, CYAN if active else WHITE)

        draw_text(surface, f"< {settings['time_limit']}s >", WIN_W - 130, y, font_small, YELLOW)

        mi = len(options) + 1

        y2 = 165 + mi * 50

        active = selected == mi

        bg = (58, 28, 88) if active else BLACK

        pygame.draw.rect(surface, bg, (40, y2 - 6, WIN_W - 80, 38))

        if active:

            pygame.draw.rect(surface, CYAN, (40, y2 - 6, WIN_W - 80, 38), 1)

        draw_text(surface, 'Music Track    (LEFT/RIGHT)', 60, y2, font_small, CYAN if active else WHITE)

        track_display = {'chiptune': '8-bit Chiptune', 'electronic': 'Electronic', 'lofi': 'Lo-fi Chill', 'off': 'Off'}

        draw_text(surface, f"< {track_display[settings['music']]} >", WIN_W - 175, y2, font_small, YELLOW)

        draw_text(surface, f'ENTER = {confirm_label}   ESC = cancel', WIN_W // 2 - font_small.size(f'ENTER = {confirm_label}   ESC = cancel')[0] / 2, y2 + 60, font_small, YELLOW)

        pygame.display.flip()



def screen_lobby(surface, clock, font, font_small):

    global game_start, is_bot_game

    player_list = []

    selected = 0

    status_msg = 'Select a player and press ENTER to configure a challenge'

    chat_lines = []

    first_frame = True

    refresh_timer = 0

    outgoing_target = None

    incoming_from = None

    incoming_settings = None

    while True:

        elapsed = clock.tick(FPS)

        refresh_timer += elapsed

        if first_frame or refresh_timer >= 5000:

            send_msg(sock, {'type': 'REQUEST_PLAYER_LIST'})

            first_frame = False

            refresh_timer = 0

        for msg in pop_messages():

            mtype = msg.get('type')

            if mtype == 'PLAYER_LIST':

                player_list = [p for p in msg['players'] if p != my_username]

                selected = min(selected, max(0, len(player_list) - 1))

            elif mtype == 'CHALLENGE_SENT':

                outgoing_target = msg.get('to')

                status_msg = f'Challenge sent to {outgoing_target}. Waiting for reply.'

            elif mtype == 'CHALLENGED':

                incoming_from = msg.get('by')

                incoming_settings = msg.get('settings') or {}

                status_msg = f'{incoming_from} challenged you. Press A to accept or D to decline.'

            elif mtype == 'DECLINED':

                by = msg.get('by')

                if outgoing_target == by:

                    outgoing_target = None

                if incoming_from == by:

                    incoming_from = None

                    incoming_settings = None

                status_msg = f'{by} declined the challenge'

            elif mtype == 'ERROR':

                status_msg = f"Error: {msg['reason']}"

            elif mtype == 'GAME_START':

                outgoing_target = None

                incoming_from = None

                incoming_settings = None

                game_start = dict(msg)

                is_bot_game = msg.get('opponent') == 'BOT'

                if msg.get('your_id', 1) != 0:

                    return game_start

            elif mtype == 'CHAT':

                chat_lines.append(f"{msg['from']}: {msg['text']}")

            elif mtype == 'WATCH_OK':

                p1 = msg.get('p1', 'P1')

                p2 = msg.get('p2', 'P2')

                game_start['p1_name'] = p1

                game_start['p2_name'] = p2

                game_start['your_id'] = 0

                return game_start

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()

                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    pygame.quit()

                    sys.exit()

                elif event.key == pygame.K_UP and selected > 0:

                    selected -= 1

                elif event.key == pygame.K_DOWN and selected < len(player_list) - 1:

                    selected += 1

                elif event.key == pygame.K_RETURN:

                    if incoming_from:

                        status_msg = 'Respond to the incoming challenge first (A or D).'

                    elif outgoing_target:

                        status_msg = f'Waiting for {outgoing_target} to reply before sending another challenge.'

                    elif player_list:

                        settings = screen_settings(surface, clock, font, font_small, title='CHALLENGE SETTINGS', confirm_label='send challenge')

                        if settings is not None:

                            send_msg(sock, {'type': 'CHALLENGE', 'target': player_list[selected], 'settings': settings})

                            status_msg = f'Sending challenge to {player_list[selected]}...'

                        else:

                            status_msg = 'Challenge cancelled.'

                elif event.key == pygame.K_a:

                    if incoming_from:

                        send_msg(sock, {'type': 'ACCEPT'})

                        status_msg = f"Accepting {incoming_from}'s challenge..."

                    else:

                        status_msg = 'No incoming challenge to accept.'

                elif event.key == pygame.K_d:

                    if incoming_from:

                        send_msg(sock, {'type': 'DECLINE'})

                        status_msg = f"Declining {incoming_from}'s challenge..."

                        incoming_from = None

                        incoming_settings = None

                    else:

                        status_msg = 'No incoming challenge to decline.'

                elif event.key == pygame.K_b:

                    if incoming_from:

                        status_msg = 'Respond to the incoming challenge first (A or D).'

                    elif outgoing_target:

                        status_msg = f'Waiting for {outgoing_target} to reply before starting something else.'

                    else:

                        settings = screen_settings(surface, clock, font, font_small, title='BOT MATCH SETTINGS', confirm_label='start bot game')

                        if settings is not None:

                            send_msg(sock, {'type': 'PLAY_BOT', 'settings': settings})

                            status_msg = 'Starting game vs Bot...'

                        else:

                            status_msg = 'Bot match cancelled.'

                elif event.key == pygame.K_w:

                    send_msg(sock, {'type': 'WATCH'})

                    status_msg = 'Requesting to watch...'

                elif event.key == pygame.K_r:

                    send_msg(sock, {'type': 'REQUEST_PLAYER_LIST'})

                    status_msg = 'Refreshing player list...'

                elif event.key == pygame.K_p:

                    screen_profile(surface, clock, font, font_small)

                    status_msg = 'Profile saved.'

        surface.fill(BLACK)

        draw_text(surface, 'PITHON ARENA - Lobby', 20, 20, font, CYAN)

        draw_text(surface, 'Online players:', 20, 70, font_small, WHITE)

        if not player_list:

            draw_text(surface, 'Waiting for other players...', 20, 100, font_small, GRAY)

        else:

            for i, name in enumerate(player_list):

                color = CYAN if i == selected else WHITE

                prefix = '> ' if i == selected else '  '

                draw_text(surface, prefix + name, 20, 100 + i * 28, font_small, color)

        cname = COLOR_OPTIONS[my_color_idx][0]

        hcol = COLOR_OPTIONS[my_color_idx][1]

        pygame.draw.rect(surface, hcol, (WIN_W - 160, 22, 14, 14), border_radius=3)

        draw_text(surface, f'Color: {cname}', WIN_W - 142, 22, font_small, GRAY)

        draw_text(surface, status_msg, 20, WIN_H - 170, font_small, YELLOW)

        if incoming_from and incoming_settings:

            draw_text(surface, 'Incoming challenge settings:', 20, WIN_H - 144, font_small, WHITE)

            for i, line in enumerate(format_settings_lines(incoming_settings)):

                draw_text(surface, line, 20, WIN_H - 126 + i * 16, font_small, CYAN)

        else:

            x_sc = 20

            y_sc = WIN_H - 136

            draw_text(surface, 'UP/DN=select  ', x_sc, y_sc, font_small, CYAN)

            x_sc += font_small.size('UP/DN=select  ')[0]

            draw_text(surface, 'ENTER=challenge  ', x_sc, y_sc, font_small, YELLOW)

            x_sc += font_small.size('ENTER=challenge  ')[0]

            draw_text(surface, 'B=bot  ', x_sc, y_sc, font_small, RED)

            x_sc += font_small.size('B=bot  ')[0]

            draw_text(surface, 'W=watch  ', x_sc, y_sc, font_small, SOFT_RED)

            x_sc += font_small.size('W=watch  ')[0]

            draw_text(surface, 'P=profile(color & movement)  ', x_sc, y_sc, font_small, hcol)

            x_sc += font_small.size('P=profile(color & movement)  ')[0]

            draw_text(surface, 'R=refresh', x_sc, y_sc, font_small, GRAY)

            if outgoing_target:

                draw_text(surface, f'Pending outgoing challenge: {outgoing_target}', 20, WIN_H - 116, font_small, CYAN)

            else:

                draw_text(surface, ' ' * 48, 20, WIN_H - 116, font_small, GRAY)

        if incoming_from:

            draw_text(surface, 'A=accept   D=decline', 20, WIN_H - 36, font_small, CYAN)

        else:

            draw_text(surface, 'ESC=quit', 20, WIN_H - 36, font_small, GRAY)

        pygame.draw.line(surface, GRAY, (20, WIN_H - 42), (WIN_W - 20, WIN_H - 42), 1)

        for i, line in enumerate(chat_lines[-3:]):

            draw_text(surface, line, 20, WIN_H - 52 + i * 16, font_small, CYAN)

        pygame.display.flip()



def screen_game(surface, clock, font, font_small, p1_name, p2_name, your_id=1, match_settings=None, countdown_seconds=0, p1_color_idx=0, p2_color_idx=1):

    global is_bot_game

    chat_lines = []

    chat_input = ''

    chat_mode = False

    countdown_seconds = max(0, int(countdown_seconds or 0))

    countdown_end = time.perf_counter() + countdown_seconds if countdown_seconds > 0 else None

    last_count_value = None

    music_started = False

    match_settings = match_settings or {}

    music_track = match_settings.get('music', 'chiptune')

    tick = 0

    prev_pies = []

    prev_p1_health = 100

    prev_p2_health = 100

    death_flash = 0.0

    sudden_death_played = False

    prev_boost1 = False

    prev_boost2 = False

    last_time = time.perf_counter()

    global_dir_keys = {'UP', 'DOWN', 'LEFT', 'RIGHT'}

    p1_snake_colors = get_snake_colors(p1_color_idx)

    p2_snake_colors = get_snake_colors(p2_color_idx)

    p1_head_color = get_head_color(p1_color_idx)

    p2_head_color = get_head_color(p2_color_idx)

    control_color = p1_head_color if your_id == 1 else p2_head_color if your_id == 2 else None

    effective_keybinds = dict(my_keybinds)

    pygame_key_map = {v: k for k, v in effective_keybinds.items()}

    _start_global_keyboard(effective_keybinds)

    if audio:

        audio.stop_music()

    while not _key_queue.empty():

        try:

            _key_queue.get_nowait()

        except queue.Empty:

            break

    while True:

        now = time.perf_counter()

        dt = now - last_time

        last_time = now

        clock.tick(FPS)

        tick += 1

        countdown_active = False

        countdown_value = 0

        if countdown_end is not None:

            remaining = countdown_end - now

            if remaining > 0:

                countdown_active = True

                countdown_value = max(1, int(math.ceil(remaining)))

                if countdown_value != last_count_value:

                    if audio:

                        audio.play(f'count_{countdown_value}')

                    last_count_value = countdown_value

            elif last_count_value is not None:

                if audio:

                    audio.play('count_go')

                last_count_value = None

        if not countdown_active and (not music_started):

            if audio and music_track != 'off':

                audio.play_music(music_track)

            music_started = True

        msgs = pop_messages()

        game_over_result = None

        for i, msg in enumerate(msgs):

            mtype = msg.get('type')

            if mtype == 'GAME_OVER':

                game_over_result = msg

                leftovers = msgs[i + 1:]

                if leftovers:

                    with inbox_lock:

                        inbox[:] = leftovers + inbox

                break

            elif mtype == 'CHAT':

                chat_lines.append(f"{msg['from']}: {msg['text']}")

        if game_over_result is not None:

            _stop_global_keyboard()

            if audio:

                audio.stop_music()

                audio.play('game_over')

            return game_over_result

        gs = state

        scores = gs.get('scores', {'p1': 100, 'p2': 100})

        if scores.get('p1', 100) <= 0 < prev_p1_health or scores.get('p2', 100) <= 0 < prev_p2_health:

            death_flash = 1.0

            if audio:

                audio.play('death')

        prev_p1_health = scores.get('p1', 100)

        prev_p2_health = scores.get('p2', 100)

        time_left = gs.get('time_left', 999)

        if not sudden_death_played and 0 < time_left < 30:

            sudden_death_played = True

            if audio:

                audio.play('sudden_death')

        current_pie_positions = {(px, py) for px, py, _ in gs.get('pies', [])}

        for px, py, kind in prev_pies:

            if (px, py) not in current_pie_positions:

                color = {4: YELLOW, 5: ORANGE, 6: PURPLE}.get(kind, YELLOW)

                cx = px * CELL_SIZE + CELL_SIZE // 2

                cy = HUD_HEIGHT + py * CELL_SIZE + CELL_SIZE // 2

                spawn_particles(cx, cy, color, count=14)

                if audio:

                    if kind == 5:

                        audio.play('pie_gold')

                    elif kind == 6:

                        audio.play('pie_bad')

                    else:

                        audio.play('pie')

        b1 = gs.get('boost1', False)

        b2 = gs.get('boost2', False)

        if b1 and (not prev_boost1) or (b2 and (not prev_boost2)):

            if audio:

                audio.play('boost')

        prev_boost1 = b1

        prev_boost2 = b2

        death_flash = max(0.0, death_flash - 0.08 * dt * 60)

        particles[:] = [p for p in particles if p.alive()]

        for p in particles:

            p.update(dt)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                _stop_global_keyboard()

                pygame.quit()

                sys.exit()

            if event.type == pygame.KEYDOWN:

                if countdown_active:

                    continue

                if chat_mode:

                    if event.key == pygame.K_RETURN:

                        if chat_input.strip():

                            send_msg(sock, {'type': 'CHAT', 'text': chat_input.strip()})

                        chat_input = ''

                        chat_mode = False

                    elif event.key == pygame.K_ESCAPE:

                        chat_mode = False

                        chat_input = ''

                    elif event.key == pygame.K_BACKSPACE:

                        chat_input = chat_input[:-1]

                    elif event.unicode.isprintable():

                        chat_input += event.unicode

                elif event.key == pygame.K_RETURN:

                    chat_mode = True

                elif your_id != 0:

                    direction = pygame_key_map.get(event.key)

                    if direction:

                        send_msg(sock, {'type': 'INPUT', 'direction': direction})

        if countdown_active:

            while True:

                try:

                    _key_queue.get_nowait()

                except queue.Empty:

                    break

        elif your_id != 0 and (not chat_mode):

            while True:

                try:

                    key_name = _key_queue.get_nowait()

                except queue.Empty:

                    break

                if key_name in global_dir_keys:

                    send_msg(sock, {'type': 'INPUT', 'direction': key_name})

        gs_draw = dict(gs)

        gs_draw['_death_flash'] = death_flash

        surface.fill(BLACK)

        draw_top_bars(surface, gs_draw, font, font_small, p1_name, p2_name, your_id, p1_head_color, p2_head_color)

        draw_grid(surface, gs_draw, dt, tick, p1_snake_colors=p1_snake_colors, p2_snake_colors=p2_snake_colors)

        draw_panel(surface, gs_draw, font, font_small, p1_name, p2_name, chat_lines, your_id, p1_color=p1_head_color, p2_color=p2_head_color, control_keybinds=effective_keybinds, control_color=control_color)

        prev_pies = list(gs.get('pies', []))

        if countdown_active:

            overlay = pygame.Surface((BOARD_W, 120))

            overlay.set_alpha(215)

            overlay.fill(BLACK)

            surface.blit(overlay, (0, WIN_H // 2 - 60))

            label = 'Match starts in'

            label_x = BOARD_W // 2 - font.size(label)[0] // 2

            draw_text(surface, label, label_x, WIN_H // 2 - 54, font, CYAN)

            big_font = pygame.font.SysFont('consolas', 56, bold=True)

            count_text = str(countdown_value)

            count_x = BOARD_W // 2 - big_font.size(count_text)[0] // 2

            draw_text(surface, count_text, count_x, WIN_H // 2 - 4, big_font, YELLOW)

            hint = '(controls unlock automatically)'

            hint_x = BOARD_W // 2 - font_small.size(hint)[0] // 2

            draw_text(surface, hint, hint_x, WIN_H // 2 + 58, font_small, GRAY)

        if chat_mode:

            box = pygame.Rect(10, WIN_H - 30, BOARD_W - 20, 24)

            pygame.draw.rect(surface, GRAY, box)

            pygame.draw.rect(surface, CYAN, box, 1)

            draw_text(surface, f'Chat: {chat_input}', 16, WIN_H - 27, font_small, WHITE)

        pygame.display.flip()



def screen_game_over(surface, clock, font, font_small, result, p1_name, p2_name, p1_color_idx=0, p2_color_idx=1):

    winner = result.get('winner')

    scores = result.get('scores', {})

    tick = 0

    p1_color = get_head_color(p1_color_idx)

    p2_color = get_head_color(p2_color_idx)

    while True:

        clock.tick(FPS)

        tick += 1

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()

                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_RETURN:

                    return True

                if event.key == pygame.K_ESCAPE:

                    pygame.quit()

                    sys.exit()

        surface.fill(BLACK)

        overlay = pygame.Surface((WIN_W, WIN_H))

        overlay.set_alpha(30)

        overlay.fill((20, 0, 40))

        surface.blit(overlay, (0, 0))

        pulse = abs(math.sin(tick * 0.04))

        draw_text(surface, 'GAME OVER', WIN_W // 2 - font.size('GAME OVER')[0] / 2, 140, font, CYAN)

        pygame.draw.line(surface, CYAN, (WIN_W // 2 - 150, 170), (WIN_W // 2 + 150, 170), 1)

        if winner is None:

            draw_text(surface, "It's a draw!", WIN_W // 2 - font.size("It's a draw!")[0] / 2, 195, font, WHITE)

        else:

            winner_color = tuple((int(c * (0.72 + 0.28 * pulse)) for c in YELLOW))

            draw_text(surface, f'{winner} wins!', WIN_W // 2 - font.size(f'{winner} wins!')[0] / 2, 195, font, winner_color)

        pygame.draw.line(surface, GRAY, (WIN_W // 2 - 150, 235), (WIN_W // 2 + 150, 235), 1)

        draw_text(surface, p1_name, WIN_W // 2 - 140, 255, font_small, p1_color)

        draw_health_bar(surface, WIN_W // 2 - 140, 275, 280, 14, scores.get('p1', 0), HEALTH_BAR_MAX, p1_color)

        draw_text(surface, f"{scores.get('p1', 0)} hp", WIN_W // 2 - 140, 293, font_small, p1_color)

        draw_text(surface, p2_name, WIN_W // 2 - 140, 320, font_small, p2_color)

        draw_health_bar(surface, WIN_W // 2 - 140, 340, 280, 14, scores.get('p2', 0), HEALTH_BAR_MAX, p2_color)

        draw_text(surface, f"{scores.get('p2', 0)} hp", WIN_W // 2 - 140, 358, font_small, p2_color)

        pygame.draw.line(surface, GRAY, (WIN_W // 2 - 150, 385), (WIN_W // 2 + 150, 385), 1)

        lobby_color = tuple((int(c * (0.6 + 0.4 * pulse)) for c in CYAN))

        draw_text(surface, 'ENTER  -  Return to lobby', WIN_W // 2 - 120, 400, font_small, lobby_color)

        draw_text(surface, 'ESC    -  Quit game', WIN_W // 2 - 120, 422, font_small, GRAY)

        pygame.display.flip()


def main():

    global sock, my_username, running, audio, state, game_start, is_bot_game

    pygame.init()

    surface = pygame.display.set_mode((WIN_W, WIN_H))

    pygame.display.set_caption('Pithon Arena')

    clock = pygame.time.Clock()

    font = pygame.font.SysFont('consolas', 20, bold=True)

    font_small = pygame.font.SysFont('consolas', 14)

    try:

        audio = SoundManager()

    except Exception as e:

        print(f'[audio] Could not initialize sound: {e}')

        audio = None

    sock = socket.socket()

    try:

        sock.connect((SERVER_IP, SERVER_PORT))

    except Exception as e:

        print(f'Could not connect to server: {e}')

        sys.exit()

    join_error = None

    while True:

        username = screen_connect(surface, clock, font, font_small, join_error)

        try:

            send_msg(sock, {'type': 'JOIN', 'username': username, 'color_idx': my_color_idx})

            resp = recv_msg(sock)

        except Exception:

            resp = None

        if resp and resp['type'] == 'JOIN_OK':

            my_username = username

            break

        if resp and resp['type'] == 'JOIN_FAIL':

            join_error = resp.get('reason', 'Username rejected - try another')

        else:

            try:

                sock.close()

            except Exception:

                pass

            join_error = 'Connection lost - reconnecting...'

            try:

                sock = socket.socket()

                sock.connect((SERVER_IP, SERVER_PORT))

                join_error = 'Reconnected. Try a different username.'

            except Exception as e:

                print(f'Could not reconnect: {e}')

                sys.exit()

    t = threading.Thread(target=receiver, daemon=True)

    t.start()

    while True:

        with inbox_lock:

            inbox[:] = [m for m in inbox if m.get('type') not in ('STATE', 'GAME_OVER')]

        state = {}

        game_start = {}

        is_bot_game = False

        particles.clear()

        send_msg(sock, {'type': 'REQUEST_PLAYER_LIST'})

        start_msg = screen_lobby(surface, clock, font, font_small)

        your_id = start_msg.get('your_id', 1)

        if your_id == 0:

            p1_name = start_msg.get('p1_name', 'P1')

            p2_name = start_msg.get('p2_name', 'P2')

        elif your_id == 1:

            p1_name = my_username

            p2_name = start_msg.get('opponent', 'P2')

        else:

            p1_name = start_msg.get('opponent', 'P1')

            p2_name = my_username

        match_settings = start_msg.get('settings') or {}

        countdown_seconds = start_msg.get('countdown_seconds', 0)

        p1_color_idx = sanitize_color_idx(start_msg.get('p1_color_idx', 0))

        p2_color_idx = sanitize_color_idx(start_msg.get('p2_color_idx', 1))

        result = screen_game(surface, clock, font, font_small, p1_name, p2_name, your_id, match_settings=match_settings, countdown_seconds=countdown_seconds, p1_color_idx=p1_color_idx, p2_color_idx=p2_color_idx)

        screen_game_over(surface, clock, font, font_small, result, p1_name, p2_name, p1_color_idx=p1_color_idx, p2_color_idx=p2_color_idx)

if __name__ == '__main__':

    main()
