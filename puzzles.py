import pygame
import text_stuff
import cool_math
import traceback

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
                self.update_puzzle(input_state)
            except:
                print("Exception thrown while updating puzzle: ", self.puzzle_id)
                traceback.print_exc()
                self.set_status(ERROR)

    def draw(self, screen, rect):
        if self.status == TITLE_START or self.status == TITLE_EXIT:
            self.draw_title_screen(screen, rect)
        elif self.status == FAILURE:
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
            except:
                print("exception thrown while drawing puzzle: ", self.puzzle_id)
                traceback.print_exc()
                self.set_status(ERROR)

    def draw_title_screen(self, screen, rect):
        title_height = int(rect[3] / 4)
        title_rect = [rect[0], rect[1], rect[2], title_height]
        instruction_height = int(rect[3] / 2 + rect[3] / 8)
        instruction_rect = [rect[0], rect[1] + title_height, rect[2], instruction_height]
        options_rect = [rect[0], int(rect[1] + 7*rect[3]/8), rect[2], int(rect[3]/8)]

        title_font = text_stuff.get_font("standard", title_height - 10)
        title_img = title_font.render(self.title, False, (255, 255, 255), (0, 0, 0))
        screen.blit(title_img, title_rect)

        instruction_line_height = int(title_height/2)
        instruction_font = text_stuff.get_font("standard", instruction_line_height)
        box, instruction_lines = text_stuff.wrap_text(self.instructions, instruction_rect[2], instruction_font)
        for i in range(0, len(instruction_lines)):
            line = instruction_lines[i]
            line_img = instruction_font.render(line, False, (255, 255, 255), (0, 0, 0))
            screen.blit(line_img, (instruction_rect[0], instruction_rect[1] + i*instruction_line_height))

        options_height = int(2*title_height/3)
        start_color = (120, 120, 200) if self.get_status() == TITLE_START else (255, 255, 255)
        exit_color = (120, 120, 200) if self.get_status() != TITLE_START else (255, 255, 255)
        r = options_rect
        options_left = [r[0], r[1], int(r[2]/2), r[3]]
        options_right = [int(r[0]+r[2]/2), r[1], int(r[2]/2), r[3]]
        self._draw_centered_text(screen, options_left, "start", options_height, start_color)
        self._draw_centered_text(screen, options_right, "exit", options_height, exit_color)

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
        return self.status not in [IN_PROGRESS, TITLE_EXIT, TITLE_START]

    def ready_to_close(self):
        return self.is_closing() and self.close_delay <= 0

    def size(self):
        return DRAW_SIZE

    def draw_puzzle(self, screen, rect):
        pass

    def update_puzzle(self, input_state):
        pass


class DummyPuzzle(Puzzle):
    def __init__(self):
        instructions = ("This isn't a real puzzle. It's only here for testing. " +
                        "This isn't a real puzzle. It's only here for testing. " +
                        "This isn't a real puzzle. It's only here for testing.")
        Puzzle.__init__(self, "dummy_puzzle", "Dummy Puzzle", instructions)

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



