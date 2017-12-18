import pygame
import entities

WIDTH = 640
HEIGHT = 480

show_debug_rects = False

def update(input_state):
    if input_state.was_pressed(pygame.K_r):
        global show_debug_rects
        show_debug_rects = not show_debug_rects
