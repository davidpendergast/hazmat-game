import pygame
import random

import global_state
import image_util

mult = 32

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


LIGHTMAP = None

RAINBOW = [0, 0, 0]

TICKS_PER_FRAME = 20    # default animation speed

ALL_ANIMATIONS = {}     # anim_id -> Animation

BIG_OL_IMG_CACHE = {}   # string -> [Surface, cache_time, last_accessed_time]


def wipe_caches():
    BIG_OL_IMG_CACHE.clear()


def refresh_caches(too_old_thresh_secs=10):
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


class Animation:
    def __init__(self, rects, anim_id="no_id", tpf=TICKS_PER_FRAME):
        self.rects = rects
        self.TPF = tpf
        self.anim_id = anim_id
        self._subanimations = [None] * len(rects)
        self._custom_sheet = None

    def num_frames(self):
        return len(self.rects)

    def single_frame(self, idx):
        """
        :returns a single-frame animation from a given index of this one.
        """
        idx = idx % self.num_frames()
        if self._subanimations[idx] is None:
            # id just for debugging, no global lookup
            anim_id = self.get_id() + "[" + str(idx) + "]"
            animation = Animation([self.rects[idx]], anim_id=anim_id, tpf=self.TPF)
            animation.set_custom_sheet(self.custom_sheet())
            self._subanimations[idx] = animation

        return self._subanimations[idx]

    def set_custom_sheet(self, sheet_name):
        self._custom_sheet = sheet_name

    def custom_sheet(self):
        return self._custom_sheet

    def width(self):
        return self.rects[0].width

    def height(self):
        return self.rects[0].height

    def size(self):
        return (self.width(), self.height())

    def get_id(self):
        return self.anim_id

    def ticks_per_frame(self):
        return self.TPF


def get_animation(anim_id):
    if anim_id not in ALL_ANIMATIONS:
        raise ValueError("No animation exists for id: " + str(anim_id))
    else:
        return ALL_ANIMATIONS[anim_id]


def create(anim_id, rects, tpf=TICKS_PER_FRAME):
    """
    Creates an animation and registers its id into ALL_ANIMATIONS
    """
    ALL_ANIMATIONS[anim_id] = Animation(rects, anim_id=anim_id, tpf=tpf)
    return ALL_ANIMATIONS[anim_id]


def r(x, y, w, h):
    return pygame.Rect(x * mult, y * mult, w * mult, h * mult)


def R(x, y, w, h):
    return pygame.Rect(x * 2, y * 2, w * 2, h * 2)  # game is drawn at 2x sprite resolution


RED_GUY             = create("red_guy", [r(0, 0, 1, 2), r(1, 0, 1, 2)])
PURPLE_GUY          = create("purple_guy", [r(2, 0, 1, 2), r(3, 0, 1, 2)])
BLUE_GUY_UP         = create("blue_guy", [R(48 + i*16, 128, 16, 32) for i in range(0, 2)])
BLUE_GUY_DOWN       = create("blue_guy_down", [R(80 + i*16, 128, 16, 32) for i in range(0, 2)])
BLUE_GUY_MIDDLE     = create("blue_guy_middle", [R(112, 128, 16, 32)])
BROWN_GUY           = create("brown_guy", [r(10, 0, 1, 2), r(11, 0, 1, 2)])
WHITE_WALL          = create("white_wall", [r(7, 1, 1, 1)])
WHITE_WALL_SMOL     = create("white_wall_small", [R(88, 16, 8, 8)])
CHAIN_SMOL          = create("chain_small", [R(80, 16, 8, 8)])
SPAWNER_SKULL       = create("spawner_skull", [r(12, 0, 1, 1), r(12, 1, 1, 1)])
SPAWNER_SKULL_OPEN  = create("spawner_skull_open", [r(13, 0, 1, 2), r(14, 0, 1, 2)])
SPAWN_SPARKLES      = create("spawn_sparkles", [r(15, 0, 1, 2), r(16, 0, 1, 2)])
FIRE                = create("fire", [r(6, 2, 1, 2), r(7, 2, 1, 2)])
ENERGY_TANK         = create("energy_tank", [r(9, 2, 1, 2), r(10, 2, 1, 2)])
ROCK                = create("rock", [r(6, 2, 1, 2)])
DOOR_LOCKED         = create("door_locked", [R(0, 96, 16, 32)])
DOOR_UNLOCKED       = create("door_unlocked", [R(16, 96, 16, 32)])
DOOR_OPENING        = create("door_opening", [R(16 + 16*i, 96, 16, 32) for i in range(0, 5)], tpf=10)
DOOR_CLOSING        = image_util.reversify(DOOR_OPENING)
LADDER              = create("ladder", [R(64, 80, 16, 16)])
LIGHT_BULB          = create("light_bulb", [R(80, 88, 8, 8), R(88, 88, 8, 8)])
WIRE_VERTICAL       = create("wire_vertical", [R(80, 80, 8, 8)])
TERMINAL            = create("terminal", [R(96, 64, 16, 32)])
TERMINAL_SCREEN     = create("terminal_screen", [R(112, 64 + i*5, 10, 5) for i in range(0, 6)])
CHALKBOARD          = create("chalkboard", [R(96, 96, 32, 16)])
PUZZLE_TERMINAL     = create("puzzle_terminal", [R(128, 96, 16, 32)])
PUZZ_TERM_SCREEN    = create("puzzle_terminal_screen", [R(144, 96 + 9*i, 10, 9) for i in range(0, 3)])
DEATH_PUZZLE        = create("death_puzzle", [R(192, 128, 16, 32)])
DEATH_PUZZLE_SCREEN = create("death_puzzle_screen", [R(208, 128 + 9*i, 10, 9) for i in range(0, 3)])
BULLET_SPLASH       = create("bullet_splash", [R(160 + 8*i, 96, 8, 16) for i in range(0, 4)], tpf=3)
HEALTH_MACHINE      = create("health_machine", [R(208, 96, 16, 32)])
HEALTH_MACHINE_BAR  = create("health_machine_bar", [R(224, 112 + i*2, 4, 2) for i in range(0, 6)])
BLAST_DOOR_TOP      = create("blast_door_top", [R(240, 96, 32, 32)])
BLAST_DOOR_BOTTOM   = create("blast_door_bottom", [R(272, 96, 32, 32)])
BLAST_DOOR_BKGR     = create("blast_door_background", [R(304, 96, 32, 48)])
BREAKABLE_WALL      = create("breakable_wall", [R(128, 0, 16, 16)])
BREAKABLE_WALL_ANIM = create("breakable_wall_animation", [R(48 + i*20, 160, 20, 20) for i in range(0, 4)], tpf=4)
ACID_FULL           = create("acid_full", [R(128 + i*16, 144, 16, 16) for i in range(0, 4)])
ACID_TOP_HALF       = create("acid_top_half", [R(128 + i*16, 128, 16, 16) for i in range(0, 4)])

ACID_SLUG_U_L       = create("acid_slug_u_l", [R(224, 128 + i*8, 16, 8) for i in range(0, 2)])
ACID_SLUG_D_L       = create("acid_slug_d_l", [R(256, 128 + i*8, 16, 8) for i in range(0, 2)])
ACID_SLUG_L_L       = create("acid_slug_l_l", [R(240 + i*8, 128, 8, 16) for i in range(0, 2)])
ACID_SLUG_R_L       = create("acid_slug_r_l", [R(272 + i*8, 128, 8, 16) for i in range(0, 2)])
ACID_SLUG_U_R       = create("acid_slug_u_r", [R(224, 144 + i*8, 16, 8) for i in range(0, 2)])
ACID_SLUG_D_R       = create("acid_slug_d_r", [R(256, 144 + i*8, 16, 8) for i in range(0, 2)])
ACID_SLUG_L_R       = create("acid_slug_l_r", [R(240 + i*8, 144, 8, 16) for i in range(0, 2)])
ACID_SLUG_R_R       = create("acid_slug_r_r", [R(272 + i*8, 144, 8, 16) for i in range(0, 2)])


PLAYER_IDLE         = create("player_idle", [R(176, 32, 16, 32), R(192, 32, 16, 32)])
PLAYER_GUN          = create("player_gun", [R(208 + 32*i, 32, 24, 32) for i in range(0, 3)], tpf=10)
PLAYER_AIR          = create("player_air", [R(304, 32, 32, 32), R(336, 32, 32, 32)])
PLAYER_WALLSLIDE    = create("player_wallslide", [R(368, 32, 24, 32)])
PLAYER_RUN          = create("player_run", [R(272 + 32*i, 0, 32, 32) for i in range(0, 7)], tpf=5)
PLAYER_LADDER       = create("player_ladder", [R(128, 64, 16, 32), R(144, 64, 16, 32), R(160, 64, 16, 32), R(144, 64, 16, 32)])
PLAYER_CROUCH       = create("player_crouch", [R(176 + i*16, 64, 16, 32) for i in range(0, 2)])
PLAYER_CROUCH_WALK  = create("player_crouch_walk", [R(208 + i*16, 64, 16, 32) for i in range(0, 6)], tpf=6)
PLAYER_CROUCH_SHOOT = create("player_crouch_shoot", [R(304 + i*32, 64, 24, 32) for i in range(0, 3)], tpf=10)
PLAYER_STUNNED      = create("player_stunned", [R(400 + i*24, 32, 24, 32) for i in range(0, 2)], tpf=10)

STONE_GROUND        = create("ground_stone", [r(0, 2, 1, 1)])
SAND_GROUND         = create("ground_sand", [r(1, 2, 1, 1)])
GRASS_GROUND        = create("ground_grass", [r(2, 2, 1, 1)])
PURPLE_GROUND       = create("ground_purple", [r(3, 2, 1, 1)])
WALL_GROUND         = create("ground_wall", [r(0, 3, 1, 1)])
DARK_GROUND         = create("ground_dark", [r(1, 3, 1, 1)])

TEXT_BORDER_L       = create("tb_l", [R(0, 144, 16, 16)])
TEXT_BORDER_TL      = create("tb_tl", [R(0, 128, 16, 16)])
TEXT_BORDER_T       = create("tb_t", [R(16, 128, 16, 16)])
TEXT_BORDER_TR      = create("tb_tr", [R(32, 128, 16, 16)])
TEXT_BORDER_R       = create("tb_r", [R(32, 144, 16, 16)])
TEXT_BORDER_BR      = create("tb_br", [R(32, 160, 16, 16)])
TEXT_BORDER_B       = create("tb_b", [R(16, 160, 16, 16)])
TEXT_BORDER_BL      = create("tb_bl", [R(0, 160, 16, 16)])

HEART_FULL          = create("heart_full", [R(160, 112, 13, 13)])
HEART_HALF          = create("heart_half", [R(176, 112, 13, 13)])
HEART_EMPTY         = create("heart_empty", [R(192, 112, 13, 13)])


def _flip_rect(rect):
    sheet_w = get_sheet(modifier="flipped").get_width()
    x = sheet_w - rect[0] - rect[2]
    return [x, rect[1], rect[2], rect[3]]


def draw_animated_sprite(screen, dest, animation, modifier="normal", src_subset=None):
    """animation: either an Animation or a Rect"""
    if type(animation) is Animation:
        frame = (global_state.tick_counter // animation.TPF) % len(animation.rects)
        src_rect = animation.rects[frame]
        custom_sheet = animation.custom_sheet()
        if custom_sheet is not None:
            modifier = custom_sheet  # kinda hacky, whatever
    else:
        src_rect = animation
    if src_subset is not None:
        if src_subset[0] >= src_rect[2] or src_subset[1] >= src_rect[3]:
            print("WARN\tsrc_subset is out of range: src_subset=", src_subset, "src_rect=", src_rect)
            return
        else:
            x = src_rect[0] + src_subset[0]
            y = src_rect[1] + src_subset[1]
            w = src_subset[2] if src_subset[0] + src_subset[2] <= src_rect[2] else src_rect[2] - src_subset[0]
            h = src_subset[3] if src_subset[1] + src_subset[3] <= src_rect[3] else src_rect[3] - src_subset[1]
            src_rect = [x, y, w, h]
    draw_sprite(screen, dest, src_rect, modifier=modifier)


def draw_sprite(screen, dest, source_rect, modifier="normal"):
    if modifier == "flipped":
        source_rect = _flip_rect(source_rect)

    screen.blit(get_sheet(modifier), dest, source_rect)


def get_sheet(modifier="normal"):
    if modifier not in SHEETS:
        raise ValueError("Unrecognized sprite modifier: " + str(modifier))
    else:
        return SHEETS[modifier]


def get_window_icon():
    res_surface = pygame.Surface((32, 32), flags=pygame.SRCALPHA)
    draw_sprite(res_surface, (0, 0), [0, 32, 32, 32])  # uhh.. hack alert lol
    return res_surface


def get_lightmap(radius):
    cache_key = "lightmap_" + str(radius)
    cached_img = get_cached_image(cache_key)

    if cached_img is None:
        size = (radius * 2 + 1, radius * 2 + 1)
        cached_img = pygame.transform.scale(LIGHTMAP, size)
        put_cached_image(cache_key, cached_img)

    return cached_img


def reload_sheet():
    print("INFO\tloading sprite sheets...")
    global SHEETS, LIGHTMAP
    actual_size = pygame.image.load("res/art_n_stuff.png")
    sprite_sheet = pygame.transform.scale2x(actual_size)
    SHEETS["normal"] = sprite_sheet
    SHEETS["green_ghosts"] = image_util.dye_sheet(sprite_sheet, (0, 255, 0), alpha=100)
    SHEETS["red_ghosts"] = image_util.dye_sheet(sprite_sheet, (255, 0, 0), alpha=100)
    SHEETS["white_ghosts"] = image_util.dye_sheet(sprite_sheet, (255, 255, 255), alpha=100)
    SHEETS["flipped"] = pygame.transform.flip(sprite_sheet, True, False)

    # raw_lightmap = pygame.image.load("res/lightmap.jpg")

    LIGHTMAP = image_util.create_lightmap(100)  # raw_lightmap)

    wipe_caches()

    print("INFO\tfinished loading sheets")


def update():
    global RAINBOW
    i = random.randint(0, 2)
    RAINBOW[i] = (RAINBOW[i] + 5) % 256

    refresh_secs = 10
    if global_state.tick_counter % (60 * refresh_secs) == 0:
        refresh_caches(too_old_thresh_secs=refresh_secs)


reload_sheet()

# death animations can't be made until sheets are loaded
# also, these guys don't get reloaded when sheets are reloaded, probably ok though
print("INFO\tcreating death animations...")
PURPLE_GUY_DYING    = image_util.create_death_animation(PURPLE_GUY, "purple_guy_dying", 4, 6)
PLAYER_DYING        = image_util.create_death_animation(PLAYER_IDLE, "player_dying", 4, 6)
RED_GUY_DYING       = image_util.create_death_animation(RED_GUY, "red_guy_dying", 4, 6)
BLUE_GUY_DYING      = image_util.create_death_animation(BLUE_GUY_UP, "blue_guy_dying", 4, 6)
BROWN_GUY_DYING     = image_util.create_death_animation(BROWN_GUY, "brown_guy_dying", 4, 6)
SLUG_DYING_U        = image_util.create_death_animation(ACID_SLUG_U_L, "acid_slug_dying_u", 4, 6)
SLUG_DYING_R        = image_util.create_death_animation(ACID_SLUG_R_L, "acid_slug_dying_r", 4, 6)
SLUG_DYING_D        = image_util.create_death_animation(ACID_SLUG_D_L, "acid_slug_dying_d", 4, 6)
SLUG_DYING_L        = image_util.create_death_animation(ACID_SLUG_L_L, "acid_slug_dying_l", 4, 6)
print("INFO\tdone creating death animations")
