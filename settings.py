
_CONFIG_FILE = "res/configs.txt"

CONFIGS = {
    "level_dir": "levels/",
    "debug_mode": True
}


STARTING_LEVEL_OVERRIDE = None  # "level_02"


FPS_THROTTLE = 1  # frames will only be drawn every X updates


WAIT_TICKS_AFTER_DEATH = 75


def is_debug():
    return CONFIGS["debug_mode"]


# TODO - load configs from file
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (75, 255, 75)
RED = (255, 75, 75)
BLUE = (120, 120, 200)