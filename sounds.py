from typing import Dict, List, Tuple

try:

    import numpy as np

except ModuleNotFoundError:

    np = None

try:

    import pygame

except ModuleNotFoundError as e:

    raise ModuleNotFoundError('pygame is required for sounds.py. Install it with: pip install pygame') from e



class SoundManager:



    def __init__(self, sample_rate: int=44100, volume: float=0.35):

        self.sample_rate = sample_rate

        self.master_volume = max(0.0, min(1.0, volume))

        self.enabled = False

        self.effects: Dict[str, pygame.mixer.Sound] = {}

        self.music_loops: Dict[str, pygame.mixer.Sound] = {}

        self._music_channel = None

        self._effect_channel = None

        self.current_track = None

        if np is None:

            raise RuntimeError('numpy is required for procedural audio')

        try:

            if not pygame.mixer.get_init():

                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)

            self._music_channel = pygame.mixer.Channel(0)

            self._effect_channel = pygame.mixer.Channel(1)

            self._build_sounds()

            self.enabled = True

        except Exception as exc:

            raise RuntimeError(f'Audio initialization failed: {exc}') from exc



    def play(self, name: str):

        if not self.enabled:

            return

        sound = self.effects.get(name)

        if sound is not None:

            self._effect_channel.play(sound)



    def play_music(self, track: str='chiptune'):

        if not self.enabled or track == 'off':

            self.stop_music()

            return

        sound = self.music_loops.get(track)

        if sound is None:

            return

        self.current_track = track

        self._music_channel.play(sound, loops=-1)



    def stop_music(self):

        if self._music_channel is not None:

            self._music_channel.stop()

        self.current_track = None



    def _build_sounds(self):

        self.effects = {'pie': self._make_sound(self._coin_up(880, 0.07, 1320, 0.06), 0.45), 'pie_gold': self._make_sound(self._coin_up(950, 0.08, 1650, 0.12, sparkle=True), 0.55), 'pie_bad': self._make_sound(self._down_beep(720, 0.1, 220, 0.18), 0.45), 'boost': self._make_sound(self._rise_sweep(420, 1100, 0.22), 0.45), 'death': self._make_sound(self._noise_burst(0.28, start_freq=180, end_freq=40), 0.5), 'game_over': self._make_sound(self._game_over_phrase(), 0.55), 'sudden_death': self._make_sound(self._alarm_phrase(), 0.5), 'countdown': self._make_sound(self._countdown_phrase(), 0.5), 'count_5': self._make_sound(self._count_number_tone(659.25), 0.52), 'count_4': self._make_sound(self._count_number_tone(587.33), 0.52), 'count_3': self._make_sound(self._count_number_tone(523.25), 0.52), 'count_2': self._make_sound(self._count_number_tone(493.88), 0.52), 'count_1': self._make_sound(self._count_number_tone(440.0), 0.56), 'count_go': self._make_sound(self._count_go_phrase(), 0.56)}

        self.music_loops = {'chiptune': self._make_sound(self._track_chiptune(), 0.3), 'electronic': self._make_sound(self._track_electronic(), 0.25), 'lofi': self._make_sound(self._track_lofi(), 0.28)}



    def _make_sound(self, mono_wave: np.ndarray, volume: float) -> pygame.mixer.Sound:

        wave = np.clip(mono_wave * self.master_volume * volume, -1.0, 1.0)

        stereo = np.column_stack((wave, wave))

        audio = np.asarray(stereo * 32767, dtype=np.int16)

        return pygame.sndarray.make_sound(audio)



    def _envelope(self, n: int, attack: float=0.01, decay: float=0.05, sustain: float=0.75, release: float=0.08) -> np.ndarray:

        a = max(1, int(n * attack))

        d = max(1, int(n * decay))

        r = max(1, int(n * release))

        s = max(0, n - a - d - r)

        env = np.empty(0, dtype=np.float32)

        env = np.concatenate((env, np.linspace(0.0, 1.0, a, endpoint=False, dtype=np.float32)))

        env = np.concatenate((env, np.linspace(1.0, sustain, d, endpoint=False, dtype=np.float32)))

        if s > 0:

            env = np.concatenate((env, np.full(s, sustain, dtype=np.float32)))

        env = np.concatenate((env, np.linspace(sustain, 0.0, r, endpoint=True, dtype=np.float32)))

        if len(env) < n:

            env = np.pad(env, (0, n - len(env)))

        return env[:n]



    def _tone(self, freq: float, duration: float, wave: str='sine', attack: float=0.01, decay: float=0.06, sustain: float=0.75, release: float=0.08) -> np.ndarray:

        n = max(1, int(self.sample_rate * duration))

        t = np.arange(n, dtype=np.float32) / self.sample_rate

        if wave == 'square':

            base = np.sign(np.sin(2 * np.pi * freq * t))

        elif wave == 'triangle':

            base = 2.0 * np.abs(2.0 * (freq * t - np.floor(freq * t + 0.5))) - 1.0

        elif wave == 'saw':

            base = 2.0 * (freq * t - np.floor(0.5 + freq * t))

        else:

            base = np.sin(2 * np.pi * freq * t)

        return base * self._envelope(n, attack, decay, sustain, release)



    def _silence(self, duration: float) -> np.ndarray:

        return np.zeros(max(1, int(self.sample_rate * duration)), dtype=np.float32)



    def _concat(self, parts: List[np.ndarray]) -> np.ndarray:

        if not parts:

            return np.zeros(1, dtype=np.float32)

        return np.concatenate(parts).astype(np.float32)



    def _coin_up(self, f1: float, d1: float, f2: float, d2: float, sparkle: bool=False) -> np.ndarray:

        parts = [self._tone(f1, d1, wave='square', release=0.03), self._tone(f2, d2, wave='square', release=0.05)]

        if sparkle:

            parts.append(0.35 * self._tone(f2 * 1.5, 0.1, wave='triangle', release=0.06))

        return self._concat(parts)



    def _down_beep(self, f1: float, d1: float, f2: float, d2: float) -> np.ndarray:

        return self._concat([self._tone(f1, d1, wave='triangle', sustain=0.6), self._tone(f2, d2, wave='triangle', sustain=0.5, release=0.12)])



    def _rise_sweep(self, start_freq: float, end_freq: float, duration: float) -> np.ndarray:

        n = max(1, int(self.sample_rate * duration))

        freqs = np.linspace(start_freq, end_freq, n, dtype=np.float32)

        phase = 2 * np.pi * np.cumsum(freqs) / self.sample_rate

        wave = np.sin(phase) + 0.35 * np.sign(np.sin(phase * 0.5))

        return (wave * 0.7 * self._envelope(n, 0.01, 0.1, 0.8, 0.15)).astype(np.float32)



    def _noise_burst(self, duration: float, start_freq: float=200.0, end_freq: float=50.0) -> np.ndarray:

        n = max(1, int(self.sample_rate * duration))

        rng = np.random.default_rng()

        noise = rng.uniform(-1.0, 1.0, n).astype(np.float32)

        freqs = np.linspace(start_freq, end_freq, n, dtype=np.float32)

        phase = 2 * np.pi * np.cumsum(freqs) / self.sample_rate

        tone = np.sin(phase)

        wave = 0.65 * noise + 0.35 * tone

        env = np.linspace(1.0, 0.0, n, dtype=np.float32) ** 1.8

        return wave * env



    def _game_over_phrase(self) -> np.ndarray:

        notes = [(660, 0.1), (494, 0.12), (392, 0.18), (262, 0.35)]

        parts: List[np.ndarray] = []

        for i, (freq, dur) in enumerate(notes):

            parts.append(self._tone(freq, dur, wave='square', sustain=0.65, release=0.1))

            if i < len(notes) - 1:

                parts.append(self._silence(0.02))

        return self._concat(parts)



    def _alarm_phrase(self) -> np.ndarray:

        parts: List[np.ndarray] = []

        for _ in range(3):

            parts.append(self._tone(880, 0.09, wave='square', sustain=0.7, release=0.03))

            parts.append(self._tone(660, 0.09, wave='square', sustain=0.7, release=0.03))

            parts.append(self._silence(0.03))

        return self._concat(parts)



    def _countdown_phrase(self) -> np.ndarray:

        parts = [self._tone(523.25, 0.1, wave='square', release=0.04), self._silence(0.06), self._tone(523.25, 0.1, wave='square', release=0.04), self._silence(0.06), self._tone(784.0, 0.18, wave='square', release=0.08)]

        return self._concat(parts)



    def _count_number_tone(self, freq: float) -> np.ndarray:

        return self._concat([0.7 * self._tone(freq, 0.14, wave='triangle', sustain=0.68, release=0.04), 0.35 * self._tone(freq * 2.0, 0.08, wave='sine', attack=0.005, sustain=0.45, release=0.05), self._silence(0.02)])



    def _count_go_phrase(self) -> np.ndarray:

        return self._concat([self._tone(659.25, 0.09, wave='square', release=0.04), self._silence(0.02), self._tone(783.99, 0.11, wave='square', release=0.05), self._silence(0.02), self._tone(1046.5, 0.16, wave='square', release=0.08)])



    def _note(self, midi_note: int) -> float:

        return 440.0 * 2.0 ** ((midi_note - 69) / 12.0)



    def _sequence(self, events: List[Tuple[int, float]], beat: float, wave: str='square', gap: float=0.02, sustain: float=0.72) -> np.ndarray:

        parts: List[np.ndarray] = []

        for note, beats in events:

            duration = beats * beat

            if note < 0:

                parts.append(self._silence(duration))

            else:

                parts.append(self._tone(self._note(note), max(0.04, duration - gap), wave=wave, sustain=sustain, release=min(0.08, duration * 0.35)))

                if gap > 0:

                    parts.append(self._silence(min(gap, duration * 0.3)))

        return self._concat(parts)



    def _mix(self, *tracks: np.ndarray) -> np.ndarray:

        length = max((len(t) for t in tracks))

        out = np.zeros(length, dtype=np.float32)

        for t in tracks:

            out[:len(t)] += t.astype(np.float32)

        peak = max(1e-06, float(np.max(np.abs(out))))

        if peak > 1.0:

            out = out / peak

        return out



    def _track_chiptune(self) -> np.ndarray:

        beat = 0.22

        lead = self._sequence([(72, 1), (76, 1), (79, 1), (76, 1), (74, 1), (76, 1), (81, 2), (79, 1), (76, 1), (72, 2), (-1, 1)], beat, wave='square', gap=0.015, sustain=0.65)

        bass = self._sequence([(48, 2), (55, 2), (43, 2), (50, 2), (48, 2), (55, 2), (43, 2), (50, 2)], beat, wave='triangle', gap=0.01, sustain=0.78)

        return self._mix(0.55 * lead, 0.35 * bass)



    def _track_electronic(self) -> np.ndarray:

        beat = 0.2

        arp = self._sequence([(60, 0.5), (67, 0.5), (72, 0.5), (67, 0.5), (62, 0.5), (69, 0.5), (74, 0.5), (69, 0.5), (59, 0.5), (66, 0.5), (71, 0.5), (66, 0.5), (55, 0.5), (62, 0.5), (67, 0.5), (62, 0.5)], beat, wave='saw', gap=0.005, sustain=0.82)

        bass = self._sequence([(36, 2), (-1, 2), (38, 2), (-1, 2), (35, 2), (-1, 2), (31, 2), (-1, 2)], beat, wave='triangle', gap=0.0, sustain=0.92)

        pulse = self._sequence([(84, 0.25), (-1, 0.75), (84, 0.25), (-1, 0.75), (84, 0.25), (-1, 0.75), (84, 0.25), (-1, 0.75), (86, 0.25), (-1, 0.75), (86, 0.25), (-1, 0.75), (86, 0.25), (-1, 0.75), (86, 0.25), (-1, 0.75)], beat, wave='square', gap=0.0, sustain=0.4)

        return self._mix(0.42 * arp, 0.35 * bass, 0.18 * pulse)



    def _track_lofi(self) -> np.ndarray:

        beat = 0.28

        chords = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]

        chord_parts: List[np.ndarray] = []

        for chord in chords:

            voices = [self._tone(self._note(n), beat * 4, wave='sine', attack=0.02, decay=0.12, sustain=0.55, release=0.18) for n in chord]

            chord_parts.append(0.5 * self._mix(*voices))

        pad = self._concat(chord_parts)

        melody = self._sequence([(72, 1), (74, 1), (76, 2), (71, 1), (72, 1), (74, 2), (69, 1), (71, 1), (72, 2), (67, 1), (69, 1), (71, 2)], beat, wave='triangle', gap=0.02, sustain=0.72)

        n = len(pad)

        rng = np.random.default_rng(7)

        noise = rng.normal(0.0, 0.06, n).astype(np.float32)

        wobble = 0.85 + 0.15 * np.sin(2 * np.pi * np.arange(n, dtype=np.float32) / self.sample_rate * 0.33)

        hiss = noise * wobble

        return self._mix(0.55 * pad, 0.28 * melody, 0.08 * hiss)
