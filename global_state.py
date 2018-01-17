import pygame
import time

WIDTH = 640
HEIGHT = 480

hud = None

tick_counter = 0

show_debug_rects = False
show_fps = True
show_no_darkness = False
show_items_to_place = False

current_fps = 0
last_timing = 0
last_tick_count = 0


def update(input_state):
    global tick_counter
    tick_counter += 1
    
    if input_state.was_pressed(pygame.K_r):
        global show_debug_rects
        show_debug_rects = not show_debug_rects
        
    global show_fps
    if input_state.was_pressed(pygame.K_f):
        show_fps = not show_fps   
    
    if show_fps:
        global last_timing, last_tick_count, current_fps
        cur_time = time.time()
        if cur_time - last_timing >= 1:
            current_fps = tick_counter - last_tick_count
            last_timing = cur_time
            last_tick_count = tick_counter
            
    if input_state.was_pressed(pygame.K_g):
        global show_no_darkness
        show_no_darkness = not show_no_darkness

    if input_state.was_pressed(pygame.K_i):
        global show_items_to_place
        show_items_to_place = not show_items_to_place
