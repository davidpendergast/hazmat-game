
_CONFIG_FILE = "res/configs.txt"

CONFIGS = {
    "level_dir": "levels/",
    "debug_mode": True,
    "light_blend_throttle": 0
}


STARTING_LEVEL_OVERRIDE = "platformer_test"  # "level_02"


FPS_THROTTLE = 1  # frames will only be drawn every X updates


WAIT_TICKS_AFTER_DEATH = 75


def get_light_blend_throttle_level():
    """
    returns float in [0, 1]. Higher number = more chunky lighting (helps reduce number of colors onscreen for gif recordings)
    """
    val = CONFIGS["light_blend_throttle"]
    if isinstance(val, (int, float)) and 0 <= val <= 1:
        return val
    else:
        print("ERROR\tinvalid config value \"light_blend_throttle\" = ", val)
        return 0


def is_debug():
    return CONFIGS["debug_mode"]


# TODO - load configs from file
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (75, 255, 75)
RED = (255, 75, 75)
BLUE = (120, 120, 200)