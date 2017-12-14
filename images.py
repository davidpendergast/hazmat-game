import pygame
import random

mult = 32
sprite_sheet = None
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

STONE_GROUND = [r(0,2,1,1)]
SAND_GROUND = [r(1,2,1,1)]
GRASS_GROUND = [r(2,2,1,1)]
PURPLE_GROUND = [r(3,2,1,1)]


def draw_animated_sprite(screen, dest_rect, sprite_rects, offset=0):
    frame = (tick_cnt // TICKS_PER_FRAME + offset) % len(sprite_rects)
    draw_sprite(screen, dest_rect, sprite_rects[frame])

def draw_sprite(screen, dest_rect, source_rect):
    screen.blit(sprite_sheet, dest_rect, source_rect)
    
def get_window_icon():
    res_surface = pygame.Surface((32, 32))
    draw_sprite(res_surface, [0,0,32,32], [0,32,32,32]) # uhh.. hack alert lol
    return res_surface
    
def reload_sheet():
    print ("Loading sprites...")
    global sprite_sheet
    actual_size = pygame.image.load("art_n_stuff.png")
    sprite_sheet = pygame.transform.scale2x(actual_size)
    print ("done.")
    
def update(tick_counter):
    global tick_cnt, rainbow
    tick_cnt = tick_counter
    i = random.randint(0,2)
    rainbow[i] = (rainbow[i] + 5) % 256
    
reload_sheet()
    
    
    
