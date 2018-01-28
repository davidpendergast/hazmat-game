import pygame
import time

HEIGHT = 16*32
WIDTH = round(HEIGHT * 15/9)

hud = None

tick_counter = 0

show_debug_rects = False
show_chunk_redraws = False
show_fps = False
show_no_darkness = False
show_items_to_place = False

current_fps = 0
last_timing = 0
last_tick_count = 0

is_fullscreen = False

level_save_dest = None          # TODO - move to LevelManager
queued_next_level_name = None

show_enemy_health = False

exit_requested = False



def update(input_state):
    global tick_counter
    tick_counter += 1
    _handle_debug_toggles(input_state)


def _handle_debug_toggles(input_state):
    if input_state.was_pressed(pygame.K_r):
        global show_debug_rects
        show_debug_rects = not show_debug_rects
        global show_chunk_redraws
        show_chunk_redraws = not show_chunk_redraws

    global show_fps
    if input_state.was_pressed(pygame.K_f):
        show_fps = not show_fps

    if show_fps:
        global last_timing, last_tick_count, current_fps
        cur_time = time.time()
        if cur_time - last_timing >= 1:
            current_fps = round((tick_counter - last_tick_count) / (cur_time - last_timing))
            last_timing = cur_time
            last_tick_count = tick_counter

    if input_state.was_pressed(pygame.K_g):
        global show_no_darkness
        show_no_darkness = not show_no_darkness

    if input_state.was_pressed(pygame.K_i):
        global show_items_to_place
        show_items_to_place = not show_items_to_place

