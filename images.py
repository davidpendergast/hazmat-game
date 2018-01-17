import pygame
import random

import global_state

mult = 32

SHEETS = {
    "normal": None,
    "flipped": None,
    "green_ghosts": None,
    "red_ghosts": None,
    "white_ghosts": None,
}

LIGHTMAP = None

RAINBOW = [0, 0, 0]

TICKS_PER_FRAME = 20    # default animation speed

ALL_ANIMATIONS = {}     # anim_id -> Animation


CACHED_LIGHTMAPS = {}           # radius -> Surface
CACHED_DARKNESS_CHUNKS = {}     # light profile -> Surface


def wipe_caches():
    CACHED_LIGHTMAPS.clear()
    CACHED_DARKNESS_CHUNKS.clear()


class Animation:
    def __init__(self, rects, anim_id="no_id", tpf=TICKS_PER_FRAME):
        self.rects = rects
        self.TPF = tpf
        self.anim_id = anim_id
        self._subanimations = [None] * len(rects)

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
            self._subanimations[idx] = animation

        return self._subanimations[idx]

    def width(self):
        return self.rects[0].width

    def height(self):
        return self.rects[0].height

    def size(self):
        return (self.width(), self.height())

    def get_id(self):
        return self.anim_id


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


def reversify(animation):
    anim_id = animation.get_id() + "_reversed"
    return create(anim_id, list(reversed(animation.rects)), tpf=animation.TPF)


def r(x, y, w, h):
    return pygame.Rect(x * mult, y * mult, w * mult, h * mult)


def R(x, y, w, h):
    return pygame.Rect(x * 2, y * 2, w * 2, h * 2)  # game is drawn at 2x sprite resolution


RED_GUY             = create("red_guy", [r(0, 0, 1, 2), r(1, 0, 1, 2)])
PURPLE_GUY          = create("purple_guy", [r(2, 0, 1, 2), r(3, 0, 1, 2)])
BLUE_GUY            = create("blue_guy", [r(8, 0, 1, 2), r(9, 0, 1, 2)])
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
DOOR_OPENING        = create("door_opening", [R(16 + 16 * i, 96, 16, 32) for i in range(0, 5)], tpf=10)
DOOR_CLOSING        = reversify(DOOR_OPENING)
LADDER              = create("ladder", [R(64, 80, 16, 16)])
LIGHT_BULB          = create("light_bulb", [R(80, 88, 8, 8), R(88, 88, 8, 8)])
WIRE_VERTICAL       = create("wire_vertical", [R(80, 80, 8, 8)])
TERMINAL            = create("terminal", [R(96, 64, 16, 32)])
TERMINAL_SCREEN     = create("terminal_screen", [R(112, 64 + i * 5, 10, 5) for i in range(0, 6)])
CHALKBOARD          = create("chalkboard", [R(96, 96, 32, 16)])
PUZZLE_TERMINAL     = create("puzzle_terminal", [R(128, 96, 16, 32)])
PUZZ_TERM_SCREEN    = create("puzzle_terminal_screen", [R(144, 96 + 9*i, 10, 9) for i in range(0, 3)])

PLAYER_IDLE         = create("player_idle", [R(176, 32, 16, 32), R(192, 32, 16, 32)])
PLAYER_GUN          = create("player_gun", [R(208 + i * 32, 32, 24, 32) for i in range(0, 3)], tpf=10)
PLAYER_AIR          = create("player_air", [R(304, 32, 32, 32), R(336, 32, 32, 32)])
PLAYER_WALLSLIDE    = create("player_wallslide", [R(368, 32, 24, 32)])
PLAYER_RUN          = create("player_run", [R(272 + 32 * i, 0, 32, 32) for i in range(0, 7)], tpf=5)
PLAYER_LADDER       = create("player_ladder", [R(128, 64, 16, 32), R(144, 64, 16, 32), R(160, 64, 16, 32), R(144, 64, 16, 32)])
PLAYER_CROUCH       = create("player_crouch", [R(176 + i * 16, 64, 16, 32) for i in range(0, 2)])
PLAYER_CROUCH_WALK  = create("player_crouch_walk", [R(208 + i * 16, 64, 16, 32) for i in range(0, 6)], tpf=6)

STONE_GROUND        = create("ground_stone", [r(0, 2, 1, 1)])
SAND_GROUND         = create("ground_sand", [r(1, 2, 1, 1)])
GRASS_GROUND        = create("ground_grass", [r(2, 2, 1, 1)])
PURPLE_GROUND       = create("ground_purple", [r(3, 2, 1, 1)])

TEXT_BORDER_L       = create("tb_l", [R(0, 144, 16, 16)])
TEXT_BORDER_TL      = create("tb_tl", [R(0, 128, 16, 16)])
TEXT_BORDER_T       = create("tb_t", [R(16, 128, 16, 16)])
TEXT_BORDER_TR      = create("tb_tr", [R(32, 128, 16, 16)])
TEXT_BORDER_R       = create("tb_r", [R(32, 144, 16, 16)])
TEXT_BORDER_BR      = create("tb_br", [R(32, 160, 16, 16)])
TEXT_BORDER_B       = create("tb_b", [R(16, 160, 16, 16)])
TEXT_BORDER_BL      = create("tb_bl", [R(0, 160, 16, 16)])


def _flip_rect(rect):
    sheet_w = get_sheet(modifier="flipped").get_width()
    x = sheet_w - rect[0] - rect[2]
    return [x, rect[1], rect[2], rect[3]]


def draw_animated_sprite(screen, dest_rect, animation, modifier="normal"):
    """animation: either an Animation or a Rect"""
    if type(animation) is Animation:
        frame = (global_state.tick_counter // animation.TPF) % len(animation.rects)
        draw_sprite(screen, dest_rect, animation.rects[frame], modifier)
    else:
        draw_sprite(screen, dest_rect, animation, modifier)


def draw_sprite(screen, dest_rect, source_rect, modifier="normal"):
    if modifier == "flipped":
        source_rect = _flip_rect(source_rect)
    screen.blit(get_sheet(modifier), dest_rect, source_rect)


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
    if radius not in CACHED_LIGHTMAPS:
        num_lightmaps = len(CACHED_LIGHTMAPS) + 1
        print("computing lightmap of radius: ", radius, " (", num_lightmaps, " total)")
        size = (radius * 2 + 1, radius * 2 + 1)
        CACHED_LIGHTMAPS[radius] = pygame.transform.scale(LIGHTMAP, size)
    return CACHED_LIGHTMAPS[radius]


def reload_sheet():
    print("Loading sprites...")
    global SHEETS, LIGHTMAP
    actual_size = pygame.image.load("res/art_n_stuff.png")
    sprite_sheet = pygame.transform.scale2x(actual_size)
    SHEETS["normal"] = sprite_sheet
    SHEETS["green_ghosts"] = dye_sheet(sprite_sheet, (0, 255, 0), alpha=100)
    SHEETS["red_ghosts"] = dye_sheet(sprite_sheet, (255, 0, 0), alpha=100)
    SHEETS["white_ghosts"] = dye_sheet(sprite_sheet, (255, 255, 255), alpha=100)
    SHEETS["flipped"] = pygame.transform.flip(sprite_sheet, True, False)

    raw_lightmap = pygame.image.load("res/lightmap.jpg")
    w, h = raw_lightmap.get_size()
    LIGHTMAP = pygame.Surface((w, h), flags=pygame.SRCALPHA)

    # going pixel by pixel is very slow, but only done once at launch
    # TODO - just get a png that already has proper alpha
    LIGHTMAP.lock()  # helps performance supposedly
    for x in range(0, w):
        for y in range(0, h):
            color = raw_lightmap.get_at((x, y))
            with_alpha = (255, 255, 255, color[0])
            LIGHTMAP.set_at((x, y), with_alpha)
    LIGHTMAP.unlock()

    print("done.")


def update():
    global RAINBOW
    i = random.randint(0, 2)
    RAINBOW[i] = (RAINBOW[i] + 5) % 256


def dye_sheet(sheet, color, base_color=(0, 0, 0), alpha=255):
    new_sheet = sheet.copy()
    size = new_sheet.get_size()
    for x in range(0, size[0]):
        for y in range(0, size[1]):
            c = sheet.get_at((x, y))
            if c[3] == 0:
                continue
            val = (0.2989 * c[0] + 0.5870 * c[1] + 0.1140 * c[2]) / 256
            r = int(base_color[0] + (color[0] - base_color[0]) * val)
            g = int(base_color[1] + (color[1] - base_color[1]) * val)
            b = int(base_color[2] + (color[2] - base_color[2]) * val)
            new_sheet.set_at((x, y), (r, g, b, alpha))
    return new_sheet


def get_darkness_overlay(rect, sources, ambient_darkness):
    """
        rect: rectangle that determines size of result, and relative positions 
            of light sources. 
        
        sources: list of tuples (x, y, luminosity, radius). If unsorted, will 
            become sorted as a side effect of calling this method.
             
        ambient_darkness: number from 0 to 1, with 1 being completely dark
    """
    # we gotta recompute light if something changes
    # TODO - put limit on number of cached light images
    sources.sort()
    key = tuple([(lp[0] - rect[0], lp[1] - rect[1], lp[2], lp[3]) for lp in sources])
    if key not in CACHED_DARKNESS_CHUNKS or CACHED_DARKNESS_CHUNKS[key] is None:

        if len(CACHED_DARKNESS_CHUNKS) > 1000:
            print("Warning: there are LOTS of darkness overlays in memory...")

        res = pygame.Surface((rect[2], rect[3]), flags=pygame.SRCALPHA)
        res.fill((0, 0, 0, ambient_darkness))
        for src in key:
            sized_lightmap = get_lightmap(src[3])
            dest = (src[0] - src[3], src[1] - src[3])
            res.blit(sized_lightmap, dest, special_flags=pygame.BLEND_RGBA_SUB)
        CACHED_DARKNESS_CHUNKS[key] = res
    return CACHED_DARKNESS_CHUNKS[key]


reload_sheet()
