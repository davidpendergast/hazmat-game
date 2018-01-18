import pygame
import logging

import file_stuff

_DIR = "res/sound/"

ALL_SOUNDS = {}  # filename -> Sound


def _put(name):
    ALL_SOUNDS[name] = None
    return name


CREEPY_LIL_NOISE    = _put("creepy.ogg")
ENERGY_PULSE        = _put("energy_pulse.wav")


def play(sound_name, loops=0, maxtime=0, fade_ms=0):
    if sound_name not in ALL_SOUNDS:
        raise ValueError("unrecognized sound: ", sound_name)
    else:
        sound = ALL_SOUNDS[sound_name]
        if sound is not None:
            sound.play(loops=loops, maxtime=maxtime, fade_ms=fade_ms)


def init_sounds():
    for filename in ALL_SOUNDS:
        filepath = _DIR + filename
        if not file_stuff.exists(filepath):
            print("sound file doesn't exist: ", filepath)
        else:
            try:
                ALL_SOUNDS[filename] = pygame.mixer.Sound(filepath)
            except Exception as ex:
                print("exception while loading sound: ", filepath)
                logging.error(ex)



