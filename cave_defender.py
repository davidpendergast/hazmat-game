import pygame

import random

from inputs import InputState
from entities import Player, Enemy
from world import World
import images
import global_state as gs


pygame.init()

pygame.display.set_caption("Cave", "Cave")
pygame.display.set_icon(images.get_window_icon())
screen = pygame.display.set_mode((gs.WIDTH, gs.HEIGHT), pygame.RESIZABLE)

still_running = True
clock = pygame.time.Clock()
FPS = 30

input_state = InputState()
world = World.gimme_a_sample_world()

def stop_running(): 
    global still_running
    still_running = False

def draw(screen):
    screen_rect = (0, 0, gs.WIDTH, gs.HEIGHT)
    pygame.draw.rect(screen, (120,120,120), screen_rect, 0)
    world.draw_all(screen)
    
tick_counter = 0

def update():
    input_state.update(tick_counter)
    world.update_all(tick_counter, input_state)
    
    images.update(tick_counter)
    if gs.selected_item_to_place is not None:
        mouse = input_state.mouse_pos()
        if mouse is not None:
            c_xy = world.get_tile_at(*mouse)
            gs.selected_item_to_place.set_center_x(c_xy[0])
            gs.selected_item_to_place.set_center_y(c_xy[1])
    
while still_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            stop_running()
        elif event.type == pygame.VIDEORESIZE:
            gs.WIDTH = event.w
            gs.HEIGHT = event.h
            new_size = (gs.WIDTH, gs.HEIGHT)
            screen = pygame.display.set_mode(new_size, pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            input_state.set_key(event.key, True)
            if event.key == pygame.K_RETURN:
                images.reload_sheet()
        elif event.type == pygame.KEYUP:
            input_state.set_key(event.key, False)
        elif event.type == pygame.MOUSEMOTION:
            input_state.set_mouse_pos(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            input_state.set_mouse_down(True)
        elif event.type == pygame.MOUSEBUTTONUP:
            input_state.set_mouse_down(False)
    
    if not pygame.mouse.get_focused():
        input_state.set_mouse_pos(None)
            
    update()
    draw(screen)
    
    tick_counter += 1

    pygame.display.flip()
    clock.tick(FPS)
        
pygame.quit()
