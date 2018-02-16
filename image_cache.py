import global_state

LIGHTMAP = None


def set_lightmap(lightmap):
    global LIGHTMAP
    LIGHTMAP = lightmap


def get_lightmap():
    return LIGHTMAP


BIG_OL_IMG_CACHE = {}   # string -> [Surface, cache_time, last_accessed_time]


def wipe_caches():
    BIG_OL_IMG_CACHE.clear()


def refresh_caches(too_old_thresh_secs=2):
    thresh_ticks = too_old_thresh_secs * 60
    cur_time = global_state.tick_counter
    to_remove = list()
    for x in BIG_OL_IMG_CACHE:
        if cur_time - BIG_OL_IMG_CACHE[x][2] >= thresh_ticks:
            to_remove.append(x)
    if len(to_remove) > 0:
        remaining = len(BIG_OL_IMG_CACHE)-len(to_remove)
        print("INFO:\tremoving ", len(to_remove), " image(s) from cache... ", remaining, " remain.")
    for x in to_remove:
        del BIG_OL_IMG_CACHE[x]


def get_cached_image(key):
    if key in BIG_OL_IMG_CACHE:
        datablob = BIG_OL_IMG_CACHE[key]
        datablob[2] = global_state.tick_counter
        return datablob[0]
    else:
        return None


def remove_cached_image(key):
    if key in BIG_OL_IMG_CACHE:
        del BIG_OL_IMG_CACHE[key]


def put_cached_image(key, image):
    data_blob = [image, global_state.tick_counter, global_state.tick_counter]
    BIG_OL_IMG_CACHE[key] = data_blob


def time_since_last_access(key):
    if key not in BIG_OL_IMG_CACHE:
        return None
    else:
        data_blob = BIG_OL_IMG_CACHE[key]
        return global_state.tick_counter - data_blob[2]


def time_since_cached(key):
    if key not in BIG_OL_IMG_CACHE:
        return None
    else:
        data_blob = BIG_OL_IMG_CACHE[key]
        return global_state.tick_counter - data_blob[1]


SHEETS = {
    "normal": None,
    "flipped": None,
    "green_ghosts": None,
    "red_ghosts": None,
    "white_ghosts": None,
}


def add_sheet(name, surface):
    print("INFO\tadding new sheet: ", name)
    SHEETS[name] = surface


def get_sheet(name):
    return SHEETS[name]