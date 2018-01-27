import pygame

import text_stuff
import global_state

from settings import WHITE, BLACK, GREEN, RED, BLUE

ALL_MENUS = {}      # menu_id -> Menu

MAIN_MENU = "main_menu"

_BORDER_THICKNESS = 32


def get_menu(menu_id):
    if menu_id not in ALL_MENUS:
        raise ValueError("Unrecognized menu id: ", menu_id)
    else:
        return ALL_MENUS[menu_id]


def _create(menu):
    menu_id = menu.get_id()
    ALL_MENUS[menu_id] = menu
    return menu_id


class Menu:
    def __init__(self, menu_id):
        self.menu_id = menu_id

    def get_id(self):
        return self.menu_id

    def draw(self, screen):
        pass

    def update(self, input_state):
        pass

    def prepare_to_show(self, prev_menu):
        pass


class MainMenu(Menu):
    def __init__(self):
        Menu.__init__(self, MAIN_MENU)
        self.opt_new_game = "new_game"
        self.opt_continue = "continue"
        self.opt_settings = "settings"
        self.opt_exit = "exit"
        self.options = [self.opt_new_game, self.opt_continue, self.opt_settings, self.opt_exit]
        self.selected_idx = 0

    def draw(self, screen):
        screen.fill(BLACK)
        title_txt = "HATE"
        title_img = text_stuff.get_text_image(title_txt, text_stuff.FONT_SCARY, 128, WHITE, bg_color=BLACK)
        title_pos = (int(global_state.WIDTH/2 - title_img.get_width()/2), _BORDER_THICKNESS)
        screen.blit(title_img, title_pos)

        y = _BORDER_THICKNESS + title_img.get_height() + _BORDER_THICKNESS
        y_space_remaining = global_state.HEIGHT - y - _BORDER_THICKNESS
        opt_h = int(y_space_remaining / len(self.options))
        for i in range(0, len(self.options)):
            opt_color = WHITE if self.selected_idx != i else BLUE
            opt_text = self.options[i]
            opt_img = text_stuff.get_text_image(opt_text, text_stuff.FONT_STANDARD, opt_h, opt_color, bg_color=BLACK)
            opt_y = y + i*opt_h
            opt_x = int(global_state.WIDTH/2 - opt_img.get_width()/2)
            screen.blit(opt_img, (opt_x, opt_y))

    def update(self, input_state):
        if input_state.was_pressed(pygame.K_s) or input_state.was_pressed(pygame.K_DOWN):
            self.selected_idx = (self.selected_idx + 1) % len(self.options)

        if input_state.was_pressed(pygame.K_w) or input_state.was_pressed(pygame.K_UP):
            self.selected_idx = (self.selected_idx - 1) % len(self.options)

        if input_state.was_pressed(pygame.K_k) or input_state.was_pressed(pygame.K_RETURN):
            self._activated(self.options[self.selected_idx])

    def _activated(self, option_name):
        if option_name == self.opt_new_game:
            global_state.queued_next_level_name = "level_01"
            global_state.hud.set_active_menu(None)
            print("starting game...")
        elif option_name == self.opt_continue:
            print("not ready yet...")
            # TODO - continue
        elif option_name == self.opt_settings:
            print("not ready yet...")
            # TODO - settings
        elif option_name == self.opt_exit:
            print("INFO\texiting from main menu...")
            global_state.exit_requested = True


print("INFO\tBuilding menus...")
g = globals().copy()
for menu in Menu.__subclasses__():
    m = menu()
    ALL_MENUS[m.get_id()] = m
    print("INFO\tBuilt: ", m.get_id())


