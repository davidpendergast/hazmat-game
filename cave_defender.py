import pygame

import random

from inputs import InputState
from entities import Player, Enemy
from world import World
import images


pygame.init()

WIDTH = 640
HEIGHT = 480

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

still_running = True
clock = pygame.time.Clock()
FPS = 30

input_state = InputState()
world = World()

def stop_running(): 
    global still_running
    still_running = False

def draw(screen):
    pygame.draw.rect(screen, (120,120,120), (0,0,WIDTH,HEIGHT), 0)
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
            WIDTH = event.w
            HEIGHT = event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
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
