import pygame
import text_stuff

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

    def update(self, input_state):
        if input_state.was_pressed(pygame.K_ESCAPE):
            self.set_status(QUIT)

    def draw(self, screen, rect):
        pass

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status

    def size(self):
        return DRAW_SIZE


class DummyPuzzle(Puzzle):
    def __init__(self):
        Puzzle.__init__(self, "dummy_puzzle")

    def draw(self, screen, rect):
        text = "press A to complete puzzle"
        font = text_stuff.get_font("standard", 32)
        color = (255, 255, 255)
        bg_color = (0, 0, 0)
        text_img = font.render(text, False, color, bg_color)
        screen.blit(text_img, (rect[0], rect[1]), [0, 0, rect[2], rect[3]])

    def update(self, input_state):
        Puzzle.update(self, input_state)
        if self.get_status() == IN_PROGRESS:
            if input_state.was_pressed(pygame.K_a):
                self.set_status(SUCCESS)


