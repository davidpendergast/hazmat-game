import pygame
import text_stuff
import cool_math
import logging

DRAW_SIZE = 320, 240

# puzzle statuses
FAILURE = 0
SUCCESS = 1
IN_PROGRESS = 2
QUIT = 3
ERROR = 4


class Puzzle:
    def __init__(self, puzzle_id):
        self.puzzle_id = puzzle_id
        self.status = IN_PROGRESS
        self.close_delay = 30

    def update(self, input_state):
        if self.is_closing():
            if self.close_delay > 0:
                self.close_delay -= 1
        else:
            if input_state.was_pressed(pygame.K_ESCAPE):
                self.set_status(QUIT, close_delay=10)
            else:
                try:
                    self.update_puzzle(input_state)
                except Exception as e:
                    print("Exception thrown while updating puzzle: ", self.puzzle_id)
                    logging.exception(e)
                    self.set_status(ERROR)

    def draw(self, screen, rect):
        if self.status == FAILURE:
            self._draw_centered_text(screen, rect, "FAILURE", 48, (255, 75, 75))
        elif self.status == SUCCESS:
            self._draw_centered_text(screen, rect, "SUCCESS", 48, (75, 255, 75))
        elif self.status == ERROR:
            self._draw_centered_text(screen, rect, "ERROR", 48, (255, 75, 75))
        elif self.status == QUIT:
            pass  # just a black screen for quitty-type exits
        elif self.status == IN_PROGRESS:
            try:
                self.draw_puzzle(screen, rect)
            except Exception as e:
                print("Exception thrown while drawing puzzle: ", self.puzzle_id)
                logging.exception(e)
                self.set_status(ERROR)

    def _draw_centered_text(self, screen, rect, text, text_size, text_color):
        font = text_stuff.get_font("standard", text_size)
        text_img = font.render(text, False, text_color, (0, 0, 0))
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
        return self.status != IN_PROGRESS

    def ready_to_close(self):
        return self.status != IN_PROGRESS and self.close_delay <= 0

    def size(self):
        return DRAW_SIZE

    def draw_puzzle(self, screen, rect):
        pass

    def update_puzzle(self, input_state):
        pass

class DummyPuzzle(Puzzle):
    def __init__(self):
        Puzzle.__init__(self, "dummy_puzzle")

    def draw_puzzle(self, screen, rect):
        text = "press A to complete puzzle"
        font = text_stuff.get_font("standard", 32)
        color = (255, 255, 255)
        bg_color = (0, 0, 0)
        text_img = font.render(text, False, color, bg_color)
        screen.blit(text_img, (rect[0], rect[1]), [0, 0, rect[2], rect[3]])

    def update_puzzle(self, input_state):
        if input_state.was_pressed(pygame.K_a):
            self.set_status(SUCCESS)
        elif input_state.was_pressed(pygame.K_b):
            self.set_status(FAILURE)
        elif input_state.was_pressed(pygame.K_e):
            raise ValueError("eww you pressed E")



