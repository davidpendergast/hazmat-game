import pygame

from abc import ABC, abstractmethod
import inspect

import text_stuff
import global_state
import levels

from settings import WHITE, BLACK, GREEN, RED, BLUE

ALL_MENUS = {}      # menu_id -> Menu

MAIN_MENU = "main_menu"
DEATH_MENU = "death_menu"

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


class Menu(ABC):
    def __init__(self, menu_id):
        self.menu_id = menu_id

    def get_id(self):
        return self.menu_id

    @abstractmethod
    def draw(self, screen):
        pass

    @abstractmethod
    def update(self, input_state):
        pass

    def prepare_to_show(self, prev_menu=None):
        pass


class OptionSelectMenu(Menu, ABC):
    def __init__(self, menu_id, options):
        Menu.__init__(self, menu_id)
        self.options = options
        self.selected_idx = 0

    @abstractmethod
    def activate_option(self, opt_idx):
        pass

    def selected_index(self):
        return self.selected_idx

    def get_option(self, index):
        return self.options[index]

    def update(self, input_state):
        if input_state.was_pressed(pygame.K_s) or input_state.was_pressed(pygame.K_DOWN):
            self.selected_idx = (self.selected_idx + 1) % len(self.options)

        if input_state.was_pressed(pygame.K_w) or input_state.was_pressed(pygame.K_UP):
            self.selected_idx = (self.selected_idx - 1) % len(self.options)

        if input_state.was_pressed(pygame.K_k) or input_state.was_pressed(pygame.K_RETURN):
            self.activate_option(self.selected_idx)

    def draw_options(self, screen, rect_to_fill):
        r_x = rect_to_fill[0]
        r_y = rect_to_fill[1]
        r_w = rect_to_fill[2]
        r_h = rect_to_fill[3]
        opt_h = int(r_h / len(self.options))
        for i in range(0, len(self.options)):
            opt_color = WHITE if self.selected_idx != i else BLUE
            opt_text = self.options[i]
            opt_img = text_stuff.get_text_image(opt_text, text_stuff.FONT_STANDARD, opt_h, opt_color, bg_color=BLACK)
            opt_y = r_y + i * opt_h
            opt_x = int(r_x + r_w / 2 - opt_img.get_width() / 2)
            screen.blit(opt_img, (opt_x, opt_y))


class MainMenu(OptionSelectMenu):
    def __init__(self):
        self.opt_new_game = "new_game"
        self.opt_continue = "continue"
        self.opt_settings = "settings"
        self.opt_exit = "exit"
        options = [self.opt_new_game, self.opt_continue, self.opt_settings, self.opt_exit]
        OptionSelectMenu.__init__(self, MAIN_MENU, options)

    def draw(self, screen):
        screen.fill(BLACK)
        title_txt = "HATE"
        title_img = text_stuff.get_text_image(title_txt, text_stuff.FONT_SCARY, 128, WHITE, bg_color=BLACK)
        title_pos = (int(global_state.WIDTH/2 - title_img.get_width()/2), _BORDER_THICKNESS)
        screen.blit(title_img, title_pos)

        y = _BORDER_THICKNESS + title_img.get_height() + _BORDER_THICKNESS
        y_space_remaining = global_state.HEIGHT - y - _BORDER_THICKNESS
        option_rect = [0, y, global_state.WIDTH, y_space_remaining]

        self.draw_options(screen, option_rect)

    def activate_option(self, option_idx):
        option_name = self.get_option(option_idx)
        if option_name == self.opt_new_game:
            global_state.queued_next_level_name = levels.get_first_level_id()
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

    def prepare_to_show(self, prev_menu=None):
        self.selected_idx = 0


class DeathMenu(OptionSelectMenu):
    def __init__(self):
        self.opt_retry = "continue"
        self.opt_exit = "exit"
        options = [self.opt_retry, self.opt_exit]
        OptionSelectMenu.__init__(self, DEATH_MENU, options)

    def activate_option(self, option_idx):
        option_name = self.get_option(option_idx)
        if option_name == self.opt_retry:
            print("INFO\tretrying level")
        elif option_name == self.opt_exit:
            global_state.hud.set_active_menu(MAIN_MENU)

    def draw(self, screen):
        pass


print("\nINFO\tbuilding menus...")
g = globals().copy()
menu_stack = [Menu]
while len(menu_stack) > 0:
    menu = menu_stack.pop(-1)
    if inspect.isabstract(menu):
        for child_menu in menu.__subclasses__():
            menu_stack.append(child_menu)
    else:
        menu_instance = menu()
        inst_id = menu_instance.get_id()
        ALL_MENUS[inst_id] = menu_instance
        print("INFO\tbuilt menu: ", inst_id)

