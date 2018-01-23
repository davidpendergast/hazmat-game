
_CONFIG_FILE = "res/configs.txt"

CONFIGS = {
    "level_dir": "levels/",
    "level_file_load": "default_level",
    "level_file_save": "default_level",
    "debug_mode": True
}


def is_debug():
    return CONFIGS["debug_mode"]


# TODO - load configs from file
