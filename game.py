import numpy as np

import random

GRID_W = 30

GRID_H = 30

EMPTY = 0

SNAKE1 = 1

SNAKE2 = 2

OBSTACLE = 3

PIE = 4

PIE_GOLD = 5

PIE_BAD = 6

PIE_HEALTH = {PIE: 10, PIE_GOLD: 25, PIE_BAD: -15}

COLLISION_DAMAGE = 25

STUN_DURATION = 1.0

MAX_HEALTH = 1000

WIN_HEALTH = 1000

HEALTH_BAR_MAX = 1000

LENGTH_MIN_BLOCKS = 2

LENGTH_MAX_BLOCKS = 10

LENGTH_STEP_HP = 50

DIRS = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}

OPPOSITE = {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}

TIME_OPTIONS = [60, 90, 120, 180]

DEFAULT_SETTINGS = {'sudden_death': True, 'speed_boost': True, 'bad_pies': True, 'time_limit': 120, 'music': 'chiptune'}



def _round_half_up(value):

    return int(value + 0.5)



def rounded_health_for_length(health):

    health = max(0, int(health))

    rounded = _round_half_up(health / LENGTH_STEP_HP) * LENGTH_STEP_HP

    return max(100, rounded)



def snake_length_from_health(health):

    rounded = rounded_health_for_length(health)

    blocks = rounded // LENGTH_STEP_HP

    return max(LENGTH_MIN_BLOCKS, min(LENGTH_MAX_BLOCKS, blocks))



class Snake:



    def __init__(self, body, direction):

        self.body = list(body)

        self.direction = direction

        self.health = 100

        self.alive = True

        self.stun_timer = 0.0



    def head(self):

        return self.body[0]



    def set_direction(self, new_dir):

        if new_dir != OPPOSITE.get(self.direction):

            self.direction = new_dir



    def next_head(self):

        dx, dy = DIRS[self.direction]

        hx, hy = self.head()

        return (hx + dx, hy + dy)



    def is_stunned(self):

        return self.stun_timer > 0



    def update_timers(self, dt):

        if self.stun_timer > 0:

            self.stun_timer = max(0.0, self.stun_timer - dt)



    def clamp_health(self):

        self.health = max(0, min(MAX_HEALTH, int(self.health)))

        if self.health <= 0:

            self.alive = False



    def damage_and_stun(self, amount):

        self.health -= amount

        self.clamp_health()

        if self.alive:

            self.stun_timer = max(self.stun_timer, STUN_DURATION)



    def target_length(self):

        return snake_length_from_health(self.health)



    def sync_length(self):

        target = self.target_length()

        if not self.body:

            return

        if len(self.body) > target:

            self.body = self.body[:target]

        elif len(self.body) < target:

            tail = self.body[-1]

            self.body.extend([tail] * (target - len(self.body)))



class GameState:



    def __init__(self, settings=None):

        self.grid = np.zeros((GRID_H, GRID_W), dtype=int)

        self.snake1 = Snake([(4, 15), (3, 15)], 'RIGHT')

        self.snake2 = Snake([(25, 15), (26, 15)], 'LEFT')

        self.pies = []

        self.obstacles = []

        self.game_over = False

        self.winner = None

        self.started = False

        self.settings = settings if settings is not None else DEFAULT_SETTINGS.copy()

        self.time_left = float(self.settings.get('time_limit', 120))

        self._place_obstacles()

        self._render_grid()

        self._spawn_pies(5)



    def apply_settings(self, settings):

        if settings:

            updated = DEFAULT_SETTINGS.copy()

            updated.update(settings)

            self.settings = updated

            self.time_left = float(updated.get('time_limit', self.time_left))

            self._remove_disallowed_pies()

            self._render_grid()

            self._spawn_pies(max(0, 5 - len(self.pies)))



    def _allowed_pie_kinds(self):

        kinds = [PIE, PIE, PIE]

        if self.settings.get('speed_boost', True):

            kinds.append(PIE_GOLD)

        if self.settings.get('bad_pies', True):

            kinds.append(PIE_BAD)

        return kinds



    def _remove_disallowed_pies(self):

        allowed = {PIE}

        if self.settings.get('speed_boost', True):

            allowed.add(PIE_GOLD)

        if self.settings.get('bad_pies', True):

            allowed.add(PIE_BAD)

        self.pies = [(x, y, kind) for x, y, kind in self.pies if kind in allowed]



    def _place_obstacles(self):

        obs_positions = [(10, 5), (10, 6), (10, 7), (20, 5), (20, 6), (20, 7), (10, 23), (10, 24), (10, 25), (20, 23), (20, 24), (20, 25), (15, 10), (15, 11), (15, 19), (15, 20)]

        for pos in obs_positions:

            self.obstacles.append(pos)

            x, y = pos

            self.grid[y][x] = OBSTACLE



    def _render_grid(self):

        self.grid = np.zeros((GRID_H, GRID_W), dtype=int)

        for x, y in self.obstacles:

            self.grid[y][x] = OBSTACLE

        for x, y, kind in self.pies:

            self.grid[y][x] = kind

        for x, y in self.snake1.body:

            self.grid[y][x] = SNAKE1

        for x, y in self.snake2.body:

            self.grid[y][x] = SNAKE2





    def _count_pies(self):

        counts = {PIE: 0, PIE_GOLD: 0, PIE_BAD: 0}

        for _, _, kind in self.pies:

            if kind in counts:

                counts[kind] += 1

        return counts



    def _choose_spawn_kind(self):

        counts = self._count_pies()

        if self.settings.get('bad_pies', True) and counts[PIE_BAD] == 0:

            return PIE_BAD

        if self.settings.get('speed_boost', True) and counts[PIE_GOLD] == 0:

            return PIE_GOLD

        return random.choice(self._allowed_pie_kinds())


    def _spawn_pies(self, count):

        spawned = 0

        attempts = 0

        while spawned < count and attempts < 1000:

            x = random.randint(1, GRID_W - 2)

            y = random.randint(1, GRID_H - 2)

            if self.grid[y][x] == EMPTY:

                kind = self._choose_spawn_kind()

                self.pies.append((x, y, kind))

                self.grid[y][x] = kind

                spawned += 1

            attempts += 1



    def set_direction(self, player_id, direction):

        if direction not in DIRS:

            return

        if player_id == 1:

            self.snake1.set_direction(direction)

        elif player_id == 2:

            self.snake2.set_direction(direction)



    def tick(self, dt):

        if self.game_over:

            return

        self.snake1.update_timers(dt)

        self.snake2.update_timers(dt)

        self.time_left -= dt

        if self.time_left <= 0:

            self._end_game_by_time()

            return

        self._move_snakes()

        self._render_grid()

        self._check_win_condition()



    def _would_tail_move(self, snake, proposed_head):

        if snake.is_stunned() or not snake.alive:

            return False

        projected_health = snake.health

        for px, py, kind in self.pies:

            if (px, py) == proposed_head:

                projected_health = max(0, min(MAX_HEALTH, projected_health + PIE_HEALTH[kind]))

                break

        target_after_move = snake_length_from_health(projected_health)

        return target_after_move <= len(snake.body)



    def _collision_reason(self, snake, proposed_head, other_snake, other_head, own_tail_moves, other_tail_moves):

        nx, ny = proposed_head

        if nx < 0 or nx >= GRID_W or ny < 0 or (ny >= GRID_H):

            return 'wall'

        if (nx, ny) in self.obstacles:

            return 'obstacle'

        own_body = set(snake.body)

        other_body = set(other_snake.body)

        if own_tail_moves and snake.body:

            own_body.discard(snake.body[-1])

        if other_tail_moves and other_snake.body:

            other_body.discard(other_snake.body[-1])

        if (nx, ny) in own_body:

            return 'self'

        if (nx, ny) in other_body:

            return 'player'

        if other_head is not None and (nx, ny) == other_head:

            return 'player'

        return None



    def _consume_pie_if_present(self, snake, head_pos):

        consumed_kind = None

        remaining = []

        for px, py, kind in self.pies:

            if (px, py) == head_pos and consumed_kind is None:

                consumed_kind = kind

            else:

                remaining.append((px, py, kind))

        if consumed_kind is not None:

            snake.health += PIE_HEALTH[consumed_kind]

            snake.clamp_health()

            self.pies = remaining

            self._spawn_pies(1)



    def _move_snakes(self):

        s1 = self.snake1

        s2 = self.snake2

        p1_head = None if not s1.alive or s1.is_stunned() else s1.next_head()

        p2_head = None if not s2.alive or s2.is_stunned() else s2.next_head()

        p1_tail_moves = p1_head is not None and self._would_tail_move(s1, p1_head)

        p2_tail_moves = p2_head is not None and self._would_tail_move(s2, p2_head)

        c1 = None

        c2 = None

        if p1_head is not None:

            c1 = self._collision_reason(s1, p1_head, s2, p2_head, p1_tail_moves, p2_tail_moves)

        if p2_head is not None:

            c2 = self._collision_reason(s2, p2_head, s1, p1_head, p2_tail_moves, p1_tail_moves)

        if p1_head is not None and p2_head is not None:

            if p1_head == p2_head:

                c1 = 'player'

                c2 = 'player'

            elif p1_head == s2.head() and p2_head == s1.head():

                c1 = 'player'

                c2 = 'player'

        if c1 is not None:

            s1.damage_and_stun(COLLISION_DAMAGE)

        if c2 is not None:

            s2.damage_and_stun(COLLISION_DAMAGE)

        if p1_head is not None and c1 is None and s1.alive:

            s1.body.insert(0, p1_head)

            self._consume_pie_if_present(s1, p1_head)

            s1.sync_length()

        else:

            s1.sync_length()

        if p2_head is not None and c2 is None and s2.alive:

            s2.body.insert(0, p2_head)

            self._consume_pie_if_present(s2, p2_head)

            s2.sync_length()

        else:

            s2.sync_length()



    def _check_win_condition(self):

        if self.snake1.health >= WIN_HEALTH and self.snake2.health >= WIN_HEALTH:

            self.game_over = True

            self.winner = None

            return

        if self.snake1.health >= WIN_HEALTH:

            self.game_over = True

            self.winner = 1

            return

        if self.snake2.health >= WIN_HEALTH:

            self.game_over = True

            self.winner = 2

            return

        s1_dead = not self.snake1.alive or self.snake1.health <= 0

        s2_dead = not self.snake2.alive or self.snake2.health <= 0

        if s1_dead and s2_dead:

            self.game_over = True

            self.winner = None

        elif s1_dead:

            self.game_over = True

            self.winner = 2

        elif s2_dead:

            self.game_over = True

            self.winner = 1



    def _end_game_by_time(self):

        self.game_over = True

        self.time_left = 0

        if self.snake1.health > self.snake2.health:

            self.winner = 1

        elif self.snake2.health > self.snake1.health:

            self.winner = 2

        else:

            self.winner = None



    def get_state_msg(self):

        return {'type': 'STATE', 'snake1': self.snake1.body, 'snake2': self.snake2.body, 'pies': self.pies, 'scores': {'p1': self.snake1.health, 'p2': self.snake2.health}, 'stun1': round(self.snake1.stun_timer, 2), 'stun2': round(self.snake2.stun_timer, 2), 'time_left': round(self.time_left, 1)}



    def get_start_msg(self, your_id, opponent, settings=None, countdown_seconds=0, p1_color_idx=0, p2_color_idx=1):

        return {'type': 'GAME_START', 'your_id': your_id, 'opponent': opponent, 'obstacles': self.obstacles, 'grid_w': GRID_W, 'grid_h': GRID_H, 'settings': settings if settings is not None else self.settings, 'countdown_seconds': int(countdown_seconds), 'p1_color_idx': int(p1_color_idx), 'p2_color_idx': int(p2_color_idx)}



class Bot:



    def __init__(self, player_id):

        self.player_id = player_id



    def _flood_fill(self, grid, start_x, start_y, max_count=60):

        visited = set()

        queue = [(start_x, start_y)]

        visited.add((start_x, start_y))

        count = 0

        while queue and count < max_count:

            cx, cy = queue.pop(0)

            count += 1

            for d in DIRS.values():

                nx, ny = (cx + d[0], cy + d[1])

                if (nx, ny) in visited:

                    continue

                if nx < 0 or nx >= GRID_W or ny < 0 or (ny >= GRID_H):

                    continue

                if grid[ny][nx] in (OBSTACLE, SNAKE1, SNAKE2):

                    continue

                visited.add((nx, ny))

                queue.append((nx, ny))

        return count



    def decide(self, game):

        snake = game.snake1 if self.player_id == 1 else game.snake2

        if not snake.alive or snake.health <= 0 or snake.is_stunned():

            return None

        hx, hy = snake.head()

        good_pies = [(x, y, k) for x, y, k in game.pies if k != PIE_BAD]

        target_pies = good_pies if good_pies else game.pies

        if target_pies:

            nearest = min(target_pies, key=lambda p: abs(p[0] - hx) + abs(p[1] - hy))

            tx, ty = (nearest[0], nearest[1])

            dx, dy = (tx - hx, ty - hy)

        else:

            dx, dy = (0, 0)

        candidates = []

        if abs(dx) >= abs(dy):

            candidates.append('RIGHT' if dx > 0 else 'LEFT')

            candidates.append('DOWN' if dy > 0 else 'UP')

        else:

            candidates.append('DOWN' if dy > 0 else 'UP')

            candidates.append('RIGHT' if dx > 0 else 'LEFT')

        for d in ['UP', 'DOWN', 'LEFT', 'RIGHT']:

            if d not in candidates:

                candidates.append(d)

        best_dir = None

        best_score = -1

        for d in candidates:

            if d == OPPOSITE.get(snake.direction):

                continue

            nx, ny = (hx + DIRS[d][0], hy + DIRS[d][1])

            if nx < 0 or nx >= GRID_W or ny < 0 or (ny >= GRID_H):

                continue

            if game.grid[ny][nx] in (OBSTACLE, SNAKE1, SNAKE2):

                continue

            space = self._flood_fill(game.grid, nx, ny)

            toward = 1 if d == candidates[0] else 0

            score = space * 10 + toward * 5

            if score > best_score:

                best_score = score

                best_dir = d

        return best_dir if best_dir else snake.direction
