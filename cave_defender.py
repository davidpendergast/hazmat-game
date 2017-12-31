import pygame

import random

import world
import images
import global_state as gs
import huds
import inputs
import cool_math


pygame.init()

pygame.display.set_caption("Cave", "Cave")
pygame.display.set_icon(images.get_window_icon())
screen = pygame.display.set_mode((gs.WIDTH, gs.HEIGHT), pygame.RESIZABLE)

still_running = True
clock = pygame.time.Clock()
FPS = 30

input_state = inputs.InputState()
world = world.World.gimme_a_sample_world()
hud = huds.HUD()

def stop_running(): 
    global still_running
    still_running = False

def draw(screen):
    screen_rect = (0, 0, gs.WIDTH, gs.HEIGHT)
    pygame.draw.rect(screen, (120,120,120), screen_rect, 0)
    world.draw_all(screen)
    hud.draw(screen, offset=cool_math.neg(world.get_camera()))
    
tick_counter = 0

def update():
    input_state.update(tick_counter)
    
    gs.update(input_state)
    world.update_all(tick_counter, input_state)
    hud.update(tick_counter, input_state, world)
    
    images.update(tick_counter)
    
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
            elif event.key == pygame.K_F2:
                pygame.image.save(screen, "screenshots/screenshot.png")
                print("saved screenshot: screenshot.png")
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
