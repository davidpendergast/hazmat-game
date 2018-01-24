import pygame

import text_stuff
import cool_math
import settings

import traceback
import random

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (75, 255, 75)
RED = (255, 75, 75)
BLUE = (120, 120, 200)

DRAW_SIZE = 600, 300

# exit statuses
FAILURE = 0
SUCCESS = 1
QUIT = 3
ERROR = 4

IN_PROGRESS = 2     # puzzle is being played
TITLE_START = 5     # title screen with "start" selected
TITLE_EXIT = 6      # title screen with "exit" selected


class Puzzle:
    def __init__(self, puzzle_id, title, instructions):
        self.puzzle_id = puzzle_id
        self.status = TITLE_START
        self.close_delay = 30
        self.title = title
        self.instructions = instructions

    def update(self, input_state):
        if self.is_closing():
            if self.close_delay > 0:
                self.close_delay -= 1

        elif self.status == TITLE_START:
            if input_state.was_pressed(pygame.K_k):
                self.set_status(IN_PROGRESS)
            elif input_state.was_pressed(pygame.K_d):
                self.set_status(TITLE_EXIT)
            elif input_state.was_pressed(pygame.K_ESCAPE):
                self.set_status(QUIT, close_delay=10)

        elif self.status == TITLE_EXIT:
            if input_state.was_pressed(pygame.K_k) or input_state.was_pressed(pygame.K_ESCAPE):
                self.set_status(QUIT, close_delay=10)
            elif input_state.was_pressed(pygame.K_a):
                self.set_status(TITLE_START)

        elif self.status == IN_PROGRESS:
            try:
                if settings.is_debug() and input_state.was_pressed(pygame.K_TAB):
                    self.set_status(SUCCESS)
                else:
                    self.update_puzzle(input_state)
            except:
                print("Exception thrown while updating puzzle: ", self.puzzle_id)
                traceback.print_exc()
                self.set_status(ERROR)

    def draw(self, screen, w, h):
        if self.status == TITLE_START or self.status == TITLE_EXIT:
            self.draw_title_screen(screen, w, h)
        elif self.status == FAILURE:
            self._draw_centered_text(screen, [0, 0, w, h], "FAILURE", 48, RED)
        elif self.status == SUCCESS:
            self._draw_centered_text(screen, [0, 0, w, h], "SUCCESS", 48, GREEN)
        elif self.status == ERROR:
            self._draw_centered_text(screen, [0, 0, w, h], "ERROR", 48, RED)
        elif self.status == QUIT:
            pass  # just a black screen for quitty-type exits
        elif self.status == IN_PROGRESS:
            try:
                self.draw_puzzle(screen, w, h)
            except:
                print("exception thrown while drawing puzzle: ", self.puzzle_id)
                traceback.print_exc()
                self.set_status(ERROR)

    def draw_title_screen(self, screen, screen_w, screen_h):
        title_height = int(screen_h / 4)
        title_rect = [0, 0, screen_w, title_height]
        instruction_height = int(screen_h / 2 + screen_h / 8)
        instruction_rect = [0, title_height, screen_w, instruction_height]
        options_rect = [0, int(0 + 7*screen_h/8), screen_w, int(screen_h/8)]

        title_img = text_stuff.get_text_image(self.title, "standard", title_height-10, WHITE, bg_color=BLACK)
        screen.blit(title_img, title_rect)

        instruction_line_height = int(title_height/2)
        instruction_font = text_stuff.get_font("standard", instruction_line_height)
        instruction_lines = text_stuff.wrap_text(self.instructions, instruction_rect[2], instruction_font)
        for i in range(0, len(instruction_lines)):
            line = instruction_lines[i]
            line_img = text_stuff.get_text_image(line, "standard", instruction_line_height, WHITE, bg_color=BLACK)
            screen.blit(line_img, (instruction_rect[0], instruction_rect[1] + i*instruction_line_height))

        options_height = int(2*title_height/3)
        start_color = BLUE if self.get_status() == TITLE_START else WHITE
        exit_color = (120, 120, 200) if self.get_status() != TITLE_START else WHITE
        r = options_rect
        options_left = [r[0], r[1], int(r[2]/2), r[3]]
        options_right = [int(r[0]+r[2]/2), r[1], int(r[2]/2), r[3]]
        self._draw_centered_text(screen, options_left, "start", options_height, start_color)
        self._draw_centered_text(screen, options_right, "exit", options_height, exit_color)

    def _draw_centered_text(self, screen, rect, text, text_size, text_color):
        text_img = text_stuff.get_text_image(text, "standard", text_size, text_color, bg_color=BLACK)
        text_rect = cool_math.recenter_rect_in([0, 0, text_img.get_width(), text_img.get_height()], rect)
        screen.blit(text_img, text_rect)

    def get_status(self):
        return self.status

    def set_status(self, status, close_delay=30):
        if self.is_closing():
            print("puzzle is already closing, get outta here")
            return
        else:
            self.status = status
            self.close_delay = close_delay

    def is_closing(self):
        return self.status not in [IN_PROGRESS, TITLE_EXIT, TITLE_START]

    def ready_to_close(self):
        return self.is_closing() and self.close_delay <= 0

    def size(self):
        """preferred size of puzzle. May not be respected during draw calls."""
        return DRAW_SIZE

    def draw_puzzle(self, screen, w, h):
        pass

    def update_puzzle(self, input_state):
        pass


class DummyPuzzle(Puzzle):
    def __init__(self):
        instructions = ("This isn't a real puzzle. It's only here for testing. " +
                        "This isn't a real puzzle. It's only here for testing. " +
                        "This isn't a real puzzle. It's only here for testing.")
        Puzzle.__init__(self, "dummy_puzzle", "Dummy Puzzle", instructions)

    def draw_puzzle(self, screen, w, h):
        text = "press A to complete puzzle"
        color = (255, 255, 255)
        bg_color = (0, 0, 0)
        text_img = text_stuff.get_text_image(text, "standard", 32, color, bg_color=bg_color)
        screen.blit(text_img, (0, 0))

    def update_puzzle(self, input_state):
        if input_state.was_pressed(pygame.K_a):
            self.set_status(SUCCESS)
        elif input_state.was_pressed(pygame.K_b):
            self.set_status(FAILURE)
        elif input_state.was_pressed(pygame.K_e):
            raise ValueError("eww you pressed E")


class SnakePuzzle(Puzzle):
    def __init__(self, difficulty):
        self.num_to_collect = (difficulty + 1) * 5
        self.grid_w = 30
        self.grid_h = 20
        self.ticks_per_move = 20
        instructions = ("Collect " + str(self.num_to_collect) + " without hitting a wall or yourself. " +
                        "Use movement keys to change direction.")
        Puzzle.__init__(self, "snake_puzzle", "Snake", instructions)
        self.snake = [(15, 15), (15, 16)]
        self.apple = (15, 4)
        self.last_moved_count = 0
        self.move_dir = (0, -1)
        self.grow = False

    def _grid_rect(self, screen_w, screen_h, x, y):
        board_w = int(self.grid_w * screen_h / self.grid_h)
        board_x = int(screen_w/2 - board_w/2)
        rx = board_x + int(board_w * x / self.grid_w)
        ry = int(screen_h * y / self.grid_h)
        rw = int(board_w / self.grid_w)
        rh = int(screen_h / self.grid_h)
        return pygame.Rect(rx, ry, rw, rh)

    def draw_puzzle(self, screen, w, h):
        for x in range(0, self.grid_w):
            for y in range(0, self.grid_h):
                if x == 0 or x == self.grid_w - 1 or y == 0 or y == self.grid_h - 1:
                    pygame.draw.rect(screen, WHITE, self._grid_rect(w, h, x, y), 0)
                elif (x, y) in self.snake:
                    pygame.draw.rect(screen, WHITE, self._grid_rect(w, h, x, y), 0)
                elif (x, y) == self.apple:
                    pygame.draw.rect(screen, BLUE, self._grid_rect(w, h, x, y), 0)

    def update_puzzle(self, input_state):
        if self.apple is None:
            pos = (1 + int(random.random() * (self.grid_w-2)), 1 + int(random.random() * (self.grid_h-2)))
            if pos not in self.snake:
                self.apple = pos

        if self.snake[0] == self.apple:
            self.num_to_collect -= 1
            self.apple = None
            self.grow = True
            self.ticks_per_move = max(self.ticks_per_move-1, 5)

        if self.num_to_collect <= 0:
            self.set_status(SUCCESS)

        input_x = 0
        if input_state.was_pressed(pygame.K_a):
            input_x -= 1
        if input_state.was_pressed(pygame.K_d):
            input_x += 1
        input_y = 0
        if input_x == 0 and input_state.was_pressed(pygame.K_w):
            input_y -= 1
        if input_x == 0 and input_state.was_pressed(pygame.K_s):
            input_y += 1

        if (input_x, input_y) != (0, 0):
            self.move_dir = (input_x, input_y)

        self.last_moved_count += 1
        if self.last_moved_count >= self.ticks_per_move:
            self.last_moved_count = 0
            head = self.snake[0]
            new_head = (head[0]+self.move_dir[0], head[1]+self.move_dir[1])
            if new_head == self.snake[1]:
                # disallow insta turnaround deaths
                new_head = (head[0] - self.move_dir[0], head[1] - self.move_dir[1])
            if new_head in self.snake or new_head[0] <= 0 or new_head[1] <= 0 or \
                    new_head[0] >= self.grid_w - 1 or new_head[1] >= self.grid_h - 1:
                self.set_status(FAILURE)
            else:
                self.snake.insert(0, new_head)
                if not self.grow:
                    self.snake.pop(-1)
                else:
                    self.grow = False










