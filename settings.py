
_CONFIG_FILE = "res/configs.txt"

CONFIGS = {
    "level_dir": "levels/",
    "debug_mode": True
}
#    "level_file_load": "default_level",
#    "level_file_save": "default_level",




def is_debug():
    return CONFIGS["debug_mode"]


# TODO - load configs from file
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (75, 255, 75)
RED = (255, 75, 75)
BLUE = (120, 120, 200)