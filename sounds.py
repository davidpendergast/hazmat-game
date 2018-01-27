import pygame
import traceback

import file_stuff

_DIR = "res/sound/"

ALL_SOUNDS = {}  # filename -> Sound


def _put(name):
    ALL_SOUNDS[name] = None
    return name


CREEPY_LIL_NOISE    = _put("creepy.ogg")
ENERGY_PULSE        = _put("energy_pulse.wav")
PLAYER_DAMAGE       = _put("player_damage.wav")

SONG_CREEPY         = "creepy_song.wav"


def play(sound_name, loops=0, maxtime=0, fade_ms=0):
    if sound_name not in ALL_SOUNDS:
        raise ValueError("unrecognized sound: ", sound_name)
    else:
        sound = ALL_SOUNDS[sound_name]
        if sound is not None:
            sound.play(loops=loops, maxtime=maxtime, fade_ms=fade_ms)


def play_song(filename, loops=-1, start=0):
    filepath = _DIR + filename
    try:
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play(loops=loops, start=start)
    except:
        print("exception while playing song: ", filepath)
        traceback.print_exc()


def init_sounds():
    for filename in ALL_SOUNDS:
        filepath = _DIR + filename
        if not file_stuff.exists(filepath):
            print("sound file doesn't exist: ", filepath)
        else:
            try:
                ALL_SOUNDS[filename] = pygame.mixer.Sound(filepath)
            except:
                print("exception while loading sound: ", filepath)
                traceback.print_exc()



