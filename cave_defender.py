import pygame

import random

from inputs import InputState
from entities import Player, Enemy
from world import World
import images
import global_state as gs


pygame.init()

pygame.display.set_caption("Cavve (ooh nice, a stylish typo)", "Cavve")
pygame.display.set_icon(images.get_window_icon())
screen = pygame.display.set_mode((gs.WIDTH, gs.HEIGHT), pygame.RESIZABLE)

still_running = True
clock = pygame.time.Clock()
FPS = 30

input_state = InputState()
world = World()

def stop_running(): 
    global still_running
    still_running = False

def draw(screen):
    screen_rect = (0, 0, gs.WIDTH, gs.HEIGHT)
    pygame.draw.rect(screen, (120,120,120), screen_rect, 0)
    world.draw_all(screen)
    
tick_counter = 0

def update():
    world.update_all(tick_counter, input_state)
    images.update(tick_counter)
    input_state.update(tick_counter)
    
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
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pass
            
    draw(screen)
    update()
    
    tick_counter += 1

    pygame.display.flip()
    clock.tick(FPS)
        
pygame.quit()
