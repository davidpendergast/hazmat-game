import pygame
import random

import global_state

mult = 32
sheets = {
    "normal":None,
    "green_ghosts":None,
    "red_ghosts":None,
    "white_ghosts":None,
}

lightmap = None
cached_lightmaps = {} # radius -> Surface

rainbow = [0,0,0]

TICKS_PER_FRAME = 10

class Animation:
    def __init__(self, rects, TPF=TICKS_PER_FRAME): 
        self.rects = rects
        self.TPF = TPF
        self._subanimations = [None] * len(rects)
        
    def num_frames(self):
        return len(self.rects)
        
    def single_frame(self, idx):
        idx = idx % self.num_frames()
        if self._subanimations[idx] == None:
            self._subanimations[idx] = Animation([self.rects[idx]], self.TPF)

        return self._subanimations[idx]
        
    def _reversify(self):
        return Animation(list(reversed(self.rects)), self.TPF)
        
    def width(self):
        return self.rects[0].width
        
    def height(self):
        return self.rects[0].height

def A(rects, TPF=TICKS_PER_FRAME):
    return Animation(rects, TPF=TPF)

def r(x,y,w,h):
    return pygame.Rect(x*mult,y*mult,w*mult,h*mult)
    
def R(x,y,w,h):
    return pygame.Rect(x*2,y*2,w*2,h*2)

RED_GUY     = A([r(0,0,1,2), r(1,0,1,2)])
PURPLE_GUY  = A([r(2,0,1,2), r(3,0,1,2)])
BLUE_GUY    = A([r(8,0,1,2), r(9,0,1,2)])
BROWN_GUY   = A([r(10,0,1,2), r(11,0,1,2)])
RED_TURRET  = A([r(4,0,1,2), r(5,0,1,2)])
WHITE_WALL  = A([r(7,1,1,1)])
WHITE_WALL_SMOL = A([R(88,16,8,8)])
CHAIN_SMOL = A([R(80,16,8,8)])
SPAWNER_SKULL = A([r(12,0,1,1), r(12,1,1,1)])
SPAWNER_SKULL_OPEN = A([r(13,0,1,2), r(14,0,1,2)])
SPAWN_SPARKLES = A([r(15,0,1,2), r(16,0,1,2)])
FIRE        = A([r(6,2,1,2), r(7,2,1,2)])
HEXAGON     = A([r(0,4,2,2), r(3,4,2,2)])
ENERGY_TANK = A([r(9,2,1,2), r(10,2,1,2)])
ROCK        = A([r(6,2,1,2)])
DOOR_LOCKED = A([R(0,96,16,32)])
DOOR_UNLOCKED = A([R(16,96,16,32)])
DOOR_OPENING = A([R(16+16*i,96,16,32) for i in range(0, 5)], TPF=5)
DOOR_CLOSING = DOOR_OPENING._reversify()
LADDER = A([R(64,80,16,16)])
LIGHT_BULB = A([R(80,88,8,8), R(88,88,8,8)])
WIRE_VERTICAL = A([R(80,80,8,8)])

PLAYER_IDLE     = A([R(176,32,16,32), R(192,32,16,32)])
PLAYER_IDLE_LEFT = A([R(176,64,16,32), R(192,64,16,32)])
PLAYER_GUN      = A([R(208+i*32,32,24,32) for i in range(0, 3)], TPF=5)
PLAYER_GUN_LEFT = A([R(208+i*32,64,24,32) for i in range(0, 3)], TPF=5)
PLAYER_AIR      = A([R(304,32,32,32), R(336,32,32,32)])
PLAYER_AIR_LEFT = A([R(304,64,32,32), R(336,64,32,32)])
PLAYER_WALLSLIDE = A([R(368,32,24,32)])
PLAYER_WALLSLIDE_LEFT = A([R(376,64,24,32)]) 
PLAYER_RUN      = A([R(400+32*i,32,32,32) for i in range(0, 6)], TPF=3)
PLAYER_RUN_LEFT = A([R(400+32*i,64,32,32) for i in range(0, 6)], TPF=3)
PLAYER_LADDER   = A([R(128,64,16,32), R(144,64,16,32),R(160,64,16,32),R(144,64,16,32)])

STONE_GROUND = A([r(0,2,1,1)])
SAND_GROUND = A([r(1,2,1,1)])
GRASS_GROUND = A([r(2,2,1,1)])
PURPLE_GROUND = A([r(3,2,1,1)])

def draw_animated_sprite(screen, dest_rect, animation, modifier="normal"):
    """animation: either an Animation or a Rect"""
    if type(animation) is Animation:
        frame = (global_state.tick_counter // animation.TPF) % len(animation.rects)
        draw_sprite(screen, dest_rect, animation.rects[frame], modifier)
    else:
        draw_sprite(screen, dest_rect, animation, modifier)

def draw_sprite(screen, dest_rect, source_rect, modifier="normal"):
    screen.blit(get_sheet(modifier), dest_rect, source_rect)
    
def get_sheet(modifier="normal"):
    if modifier not in sheets:
        raise ValueError("Unrecognized sprite modifier: "+str(modifier))
    else:
        return sheets[modifier]
    
def get_window_icon():
    res_surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    draw_sprite(res_surface, [0,0,32,32], [0,32,32,32]) # uhh.. hack alert lol
    return res_surface
    
def get_lightmap(radius):
    if not radius in cached_lightmaps:
        num_lightmaps = len(cached_lightmaps) + 1
        print ("computing lightmap of radius: ", radius, " (",num_lightmaps," total)")
        size = (radius*2 + 1, radius*2 + 1)
        cached_lightmaps[radius] = pygame.transform.scale(lightmap, size)
    return cached_lightmaps[radius]
    
def reload_sheet():
    print ("Loading sprites...")
    global sheets, light_diffusion
    actual_size = pygame.image.load("art_n_stuff.png")
    sprite_sheet = pygame.transform.scale2x(actual_size)
    sheets["normal"] = sprite_sheet
    sheets["green_ghosts"] = dye_sheet(sprite_sheet, (0,255,0), alpha=100)
    sheets["red_ghosts"]   = dye_sheet(sprite_sheet, (255,0,0), alpha=100)
    sheets["white_ghosts"]   = dye_sheet(sprite_sheet, (255,255,255), alpha=100)
    
    light_diffusion = pygame.image.load("lightmap.jpg")
    
    print ("done.")
    
def wipe_caches():
    cached_lightmaps.clear()
    
def update():
    global rainbow
    i = random.randint(0,2)
    rainbow[i] = (rainbow[i] + 5) % 256
    
def dye_sheet(sheet, color, base_color = (0, 0, 0), alpha=255):
    new_sheet = sheet.copy()
    size = new_sheet.get_size()
    for x in range(0, size[0]):
        for y in range(0, size[1]):
            c = sheet.get_at((x, y))
            if c[3] == 0:
                continue
            val = (0.2989*c[0] + 0.5870*c[1] + 0.1140*c[2]) / 256
            r = int(base_color[0] + (color[0] - base_color[0])*val)
            g = int(base_color[1] + (color[1] - base_color[1])*val)
            b = int(base_color[2] + (color[2] - base_color[2])*val)
            new_sheet.set_at((x, y), (r, g, b, alpha))
    return new_sheet
    
CACHED_DARKNESS_CHUNKS = {}    
    
def get_darkness_overlay(rect, sources, ambient_darkness):
    """
        rect: Rect
        sources: list of (x, y, radius, luminosity)
        ambient_level: number from 0 to 1, with 1 being completely dark
    """
    key = (rect.x, rect.y)
    if key not in CACHED_DARKNESS_CHUNKS or CACHED_DARKNESS_CHUNKS[key] == None:
        res = Surface(rect.width, rect.height)
        res.fill((255,255,255,int(255)*ambient_darkness))
        for src in sources:
            pygame.draw.circle(res, (255,255,255,0), (src[0], src[1]), src[2], 0)
        CACHED_DARKNESS_CHUNKS[key] = res
    return CACHED_DARKNESS_CHUNKS[key]
                
    
reload_sheet()
    
    
    
