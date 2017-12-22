import pygame
import random

mult = 32
sheets = {
    "normal":None,
    "green_ghosts":None,
    "red_ghosts":None,
    "white_ghosts":None
}

tick_cnt = 0
rainbow = [0,0,0]

TICKS_PER_FRAME = 10

def r(x,y,w,h):
    return pygame.Rect(x*mult,y*mult,w*mult,h*mult)

RED_GUY = [r(0,0,1,2), r(1,0,1,2)]
PURPLE_GUY = [r(2,0,1,2), r(3,0,1,2)]
BLUE_GUY = [r(8,0,1,2), r(9,0,1,2)]
BROWN_GUY = [r(10,0,1,2), r(11,0,1,2)]
RED_TURRET = [r(4,0,1,2), r(5,0,1,2)]
WHITE_WALL = [r(7,0,1,2)]
SPAWNER_SKULL = [r(12,0,1,1), r(12,1,1,1)]
SPAWNER_SKULL_OPEN = [r(13,0,1,2), r(14,0,1,2)]
SPAWN_SPARKLES = [r(15,0,1,2), r(16,0,1,2)]
FIRE = [r(6,2,1,2), r(7,2,1,2)]
HEXAGON = [r(0,4,2,2), r(3,4,2,2)]
ENERGY_TANK = [r(9,2,1,2), r(10,2,1,2)]
ROCK = [r(6,2,1,2)]

STONE_GROUND = [r(0,2,1,1)]
SAND_GROUND = [r(1,2,1,1)]
GRASS_GROUND = [r(2,2,1,1)]
PURPLE_GROUND = [r(3,2,1,1)]


def draw_animated_sprite(screen, dest_rect, sprite_rects, modifier="normal"):
    frame = (tick_cnt // TICKS_PER_FRAME ) % len(sprite_rects)
    draw_sprite(screen, dest_rect, sprite_rects[frame], modifier)

def draw_sprite(screen, dest_rect, source_rect, modifier="normal"):
    screen.blit(get_sheet(modifier), dest_rect, source_rect)
    
def get_sheet(modifier="normal"):
    if modifier not in sheets:
        raise ValueError("Unrecognized sprite modifier: "+str(modifier))
    else:
        return sheets[modifier]
    
def get_window_icon():
    res_surface = pygame.Surface((32, 32))
    draw_sprite(res_surface, [0,0,32,32], [0,32,32,32]) # uhh.. hack alert lol
    return res_surface
    
def reload_sheet():
    print ("Loading sprites...")
    global sheets
    actual_size = pygame.image.load("art_n_stuff.png")
    sprite_sheet = pygame.transform.scale2x(actual_size)
    sheets["normal"] = sprite_sheet
    sheets["green_ghosts"] = dye_sheet(sprite_sheet, (0,255,0), alpha=100)
    sheets["red_ghosts"]   = dye_sheet(sprite_sheet, (255,0,0), alpha=100)
    sheets["white_ghosts"]   = dye_sheet(sprite_sheet, (255,255,255), alpha=100)
    
    print ("done.")
    
def update(tick_counter):
    global tick_cnt, rainbow
    tick_cnt = tick_counter
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
            
    
reload_sheet()
    
    
    
