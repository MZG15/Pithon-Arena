import math

import socket

import threading

import time

from protocol import send_msg, recv_msg

from game import GameState, Bot, DEFAULT_SETTINGS, TIME_OPTIONS

HOST = '0.0.0.0'

PORT = 5555

clients = {}

challenges = {}

player_ids = {}

active_game = None

game_players = {}

spectators = set()

player_profiles = {}

lock = threading.Lock()

MATCH_COUNTDOWN_SECONDS = 5



def sanitize_color_idx(value):

    try:

        return int(value) % 8

    except Exception:

        return 0


def normalize_settings(settings):

    merged = DEFAULT_SETTINGS.copy()

    if isinstance(settings, dict):

        merged.update(settings)

    merged['sudden_death'] = bool(merged.get('sudden_death', True))

    merged['speed_boost'] = bool(merged.get('speed_boost', True))

    merged['bad_pies'] = bool(merged.get('bad_pies', True))

    try:

        time_limit = int(merged.get('time_limit', DEFAULT_SETTINGS['time_limit']))

    except (TypeError, ValueError):

        time_limit = DEFAULT_SETTINGS['time_limit']

    if time_limit not in TIME_OPTIONS:

        time_limit = DEFAULT_SETTINGS['time_limit']

    merged['time_limit'] = time_limit

    merged['music'] = str(merged.get('music', DEFAULT_SETTINGS.get('music', 'chiptune')))

    return merged



def broadcast_player_list():

    with lock:

        names = list(clients.keys())

        sockets = list(clients.values())

    msg = {'type': 'PLAYER_LIST', 'players': names}

    for sock in sockets:

        try:

            send_msg(sock, msg)

        except Exception:

            pass



def send_to(username, msg):

    with lock:

        sock = clients.get(username)

    if sock:

        try:

            send_msg(sock, msg)

        except Exception:

            pass



def broadcast_state(state, p1_name, p2_name):

    send_to(p1_name, state)

    if p2_name != '__BOT__':

        send_to(p2_name, state)

    with lock:

        spec_list = list(spectators)

    for name in spec_list:

        send_to(name, state)



def get_outgoing_challenge(username):

    return challenges.get(username)



def get_incoming_challenge(username):

    for challenger, info in challenges.items():

        if info.get('target') == username:

            return (challenger, info)

    return (None, None)



def has_pending_challenge(username):

    return get_outgoing_challenge(username) is not None or get_incoming_challenge(username)[0] is not None



def clear_challenges_for_user(username):

    notifications = []

    with lock:

        outgoing = challenges.pop(username, None)

        if outgoing:

            notifications.append((outgoing['target'], {'type': 'DECLINED', 'by': username}))

        incoming = [challenger for challenger, info in list(challenges.items()) if info.get('target') == username]

        for challenger in incoming:

            challenges.pop(challenger, None)

            notifications.append((challenger, {'type': 'DECLINED', 'by': username}))

    for target, msg in notifications:

        send_to(target, msg)



def player_in_active_match(username):

    return username in player_ids



def game_loop(game, p1_name, p2_name, bot_id=None):

    global active_game, game_players, player_ids

    tick_rate = 0.1

    bot = Bot(bot_id) if bot_id else None

    while True:

        with lock:

            started = game.started

            countdown_end_time = getattr(game, 'countdown_end_time', None)

        if started:

            break

        if countdown_end_time is not None and time.monotonic() >= countdown_end_time:

            with lock:

                game.started = True

            break

        time.sleep(0.05)

    while not game.game_over:

        time.sleep(tick_rate)

        try:

            with lock:

                if bot:

                    direction = bot.decide(game)

                    if direction:

                        game.set_direction(bot_id, direction)

                game.tick(tick_rate)

                state = game.get_state_msg()

            broadcast_state(state, p1_name, p2_name)

        except Exception as e:

            print(f'[!] Game loop error: {e}')

            import traceback

            traceback.print_exc()

            break

    with lock:

        winner_id = game.winner

        scores = {'p1': game.snake1.health, 'p2': game.snake2.health}

    if winner_id == 1:

        winner_name = p1_name

    elif winner_id == 2:

        winner_name = p2_name if p2_name != '__BOT__' else 'BOT'

    else:

        winner_name = None

    game_over_msg = {'type': 'GAME_OVER', 'winner': winner_name, 'scores': scores}

    broadcast_state(game_over_msg, p1_name, p2_name)

    print(f'[*] Game over. Winner: {winner_name}')

    with lock:

        active_game = None

        player_ids.pop(p1_name, None)

        if p2_name != '__BOT__':

            player_ids.pop(p2_name, None)

        game_players.clear()

        spectators.clear()

    broadcast_player_list()



def start_game(p1_name, p2_name, bot_id=None, settings=None):

    global active_game, game_players, player_ids

    clean_settings = normalize_settings(settings)

    game = GameState(settings=clean_settings)

    is_bot_game = p2_name == '__BOT__'

    game.countdown_seconds = MATCH_COUNTDOWN_SECONDS

    game.countdown_end_time = time.monotonic() + MATCH_COUNTDOWN_SECONDS

    with lock:

        p1_color_idx = player_profiles.get(p1_name, 0)

        p2_color_idx = 1 if is_bot_game else player_profiles.get(p2_name, 0)

        game.p1_color_idx = sanitize_color_idx(p1_color_idx)

        game.p2_color_idx = sanitize_color_idx(p2_color_idx)

        active_game = game

        game_players[1] = p1_name

        game_players[2] = p2_name

        player_ids[p1_name] = 1

        if not is_bot_game:

            player_ids[p2_name] = 2

    opponent_display = 'BOT' if is_bot_game else p2_name

    send_to(p1_name, game.get_start_msg(your_id=1, opponent=opponent_display, settings=clean_settings, countdown_seconds=MATCH_COUNTDOWN_SECONDS, p1_color_idx=game.p1_color_idx, p2_color_idx=game.p2_color_idx))

    if not is_bot_game:

        send_to(p2_name, game.get_start_msg(your_id=2, opponent=p1_name, settings=clean_settings, countdown_seconds=MATCH_COUNTDOWN_SECONDS, p1_color_idx=game.p1_color_idx, p2_color_idx=game.p2_color_idx))

    initial_state = game.get_state_msg()

    broadcast_state(initial_state, p1_name, p2_name)

    thread = threading.Thread(target=game_loop, args=(game, p1_name, p2_name), kwargs={'bot_id': bot_id}, daemon=True)

    thread.start()

    print(f'[*] Game loop started with {MATCH_COUNTDOWN_SECONDS}s countdown: {p1_name} vs {opponent_display}')



def handle_client(conn, addr):

    global active_game

    print(f'[+] New connection from {addr}')

    username = None

    try:

        while True:

            msg = recv_msg(conn)

            if msg is None or msg.get('type') != 'JOIN':

                conn.close()

                return

            attempted = msg['username'].strip()

            color_idx = sanitize_color_idx(msg.get('color_idx', 0))

            if not attempted:

                try:

                    send_msg(conn, {'type': 'JOIN_FAIL', 'reason': 'Username cannot be empty'})

                except Exception:

                    pass

                continue

            with lock:

                taken = attempted in clients

                if not taken:

                    clients[attempted] = conn

                    player_profiles[attempted] = color_idx

                    username = attempted

            if taken:

                try:

                    send_msg(conn, {'type': 'JOIN_FAIL', 'reason': 'Username already taken - pick another'})

                except Exception:

                    return

                continue

            break

        send_msg(conn, {'type': 'JOIN_OK'})

        print(f'[+] {username} joined')

        broadcast_player_list()

        while True:

            msg = recv_msg(conn)

            if msg is None:

                break

            mtype = msg.get('type')

            if mtype == 'REQUEST_PLAYER_LIST':

                broadcast_player_list()

            elif mtype == 'PROFILE_UPDATE':

                with lock:

                    player_profiles[username] = sanitize_color_idx(msg.get('color_idx', 0))

            elif mtype == 'CHALLENGE':

                target = msg.get('target')

                settings = normalize_settings(msg.get('settings'))

                error = None

                notify_target = None

                with lock:

                    if active_game is not None:

                        error = 'A match is already in progress'

                    elif target == username:

                        error = 'You cannot challenge yourself'

                    elif target not in clients:

                        error = 'Player not found'

                    elif player_in_active_match(username) or player_in_active_match(target):

                        error = 'One of the players is already in a match'

                    elif has_pending_challenge(username):

                        error = 'Resolve your pending challenge first'

                    elif has_pending_challenge(target):

                        error = 'That player has a pending challenge'

                    else:

                        challenges[username] = {'target': target, 'settings': settings}

                        notify_target = {'type': 'CHALLENGED', 'by': username, 'settings': settings}

                if error:

                    send_msg(conn, {'type': 'ERROR', 'reason': error})

                elif notify_target:

                    send_msg(conn, {'type': 'CHALLENGE_SENT', 'to': target, 'settings': settings})

                    send_to(target, notify_target)

            elif mtype == 'ACCEPT':

                challenger = None

                challenge_info = None

                error = None

                with lock:

                    if active_game is not None:

                        error = 'A match is already in progress'

                    elif get_outgoing_challenge(username) is not None:

                        error = 'Wait for a reply to the challenge you sent'

                    else:

                        challenger, challenge_info = get_incoming_challenge(username)

                        if challenger is None:

                            error = 'No pending challenge'

                        elif player_in_active_match(challenger) or player_in_active_match(username):

                            error = 'One of the players is already in a match'

                        else:

                            challenges.pop(challenger, None)

                if error:

                    send_msg(conn, {'type': 'ERROR', 'reason': error})

                else:

                    start_game(challenger, username, settings=challenge_info.get('settings'))

            elif mtype == 'DECLINE':

                challenger = None

                error = None

                with lock:

                    if get_outgoing_challenge(username) is not None:

                        error = 'Wait for a reply to the challenge you sent'

                    else:

                        challenger, _ = get_incoming_challenge(username)

                        if challenger is None:

                            error = 'No pending challenge'

                        else:

                            challenges.pop(challenger, None)

                if error:

                    send_msg(conn, {'type': 'ERROR', 'reason': error})

                else:

                    send_to(challenger, {'type': 'DECLINED', 'by': username})

            elif mtype == 'PLAY_BOT':

                with lock:

                    blocked = active_game is not None or has_pending_challenge(username) or player_in_active_match(username)

                if blocked:

                    send_msg(conn, {'type': 'ERROR', 'reason': 'You cannot start a bot match right now'})

                else:

                    print(f'[*] {username} starting game vs bot')

                    bot_settings = normalize_settings(msg.get('settings'))

                    start_game(username, '__BOT__', bot_id=2, settings=bot_settings)

            elif mtype == 'READY':

                pass

            elif mtype == 'INPUT':

                direction = msg.get('direction')

                with lock:

                    pid = player_ids.get(username)

                    game = active_game

                if pid and game:

                    with lock:

                        game.set_direction(pid, direction)

            elif mtype == 'CHAT':

                text = msg.get('text', '')

                chat_msg = {'type': 'CHAT', 'from': username, 'text': text}

                with lock:

                    all_sockets = list(clients.values())

                for sock in all_sockets:

                    try:

                        send_msg(sock, chat_msg)

                    except Exception:

                        pass

            elif mtype == 'WATCH':

                with lock:

                    game_running = active_game is not None

                    can_watch = username not in player_ids

                if not game_running:

                    send_msg(conn, {'type': 'ERROR', 'reason': 'No game in progress'})

                elif not can_watch:

                    send_msg(conn, {'type': 'ERROR', 'reason': 'Players in the match cannot spectate'})

                else:

                    with lock:

                        spectators.add(username)

                        game = active_game

                        p1 = game_players.get(1, 'P1')

                        p2 = game_players.get(2, 'P2')

                        if not game.started:

                            remaining = max(0, int(math.ceil(game.countdown_end_time - time.monotonic())))

                        else:

                            remaining = 0

                    send_msg(conn, game.get_start_msg(your_id=0, opponent='', settings=game.settings, countdown_seconds=remaining, p1_color_idx=getattr(game, 'p1_color_idx', 0), p2_color_idx=getattr(game, 'p2_color_idx', 1)))

                    send_msg(conn, {'type': 'WATCH_OK', 'p1': p1, 'p2': p2})

                    try:

                        send_msg(conn, game.get_state_msg())

                    except Exception:

                        pass

                    print(f'[~] {username} is now spectating')

    except Exception as e:

        print(f'[!] Error with {username or addr}: {e}')

    finally:

        if username:

            clear_challenges_for_user(username)

            with lock:

                clients.pop(username, None)

                player_profiles.pop(username, None)

                player_ids.pop(username, None)

                spectators.discard(username)

            print(f'[-] {username} disconnected')

            broadcast_player_list()

        conn.close()



def main():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))

    server.listen()

    print(f'[*] Server listening on port {PORT}')

    while True:

        conn, addr = server.accept()

        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)

        thread.start()

if __name__ == '__main__':

    main()
