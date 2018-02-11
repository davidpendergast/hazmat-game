import pygame

import cProfile
import pstats

import cave_defender
import global_state


class Profiler:
    def __init__(self):
        self.is_running = False
        self.pr = cProfile.Profile(builtins=False)

    def toggle(self):
        self.is_running = not self.is_running
        global_state.is_profiling = self.is_running

        if not self.is_running:
            self.pr.disable()

            sortby = 'cumulative'
            ps = pstats.Stats(self.pr)
            ps.strip_dirs()
            ps.sort_stats(sortby)
            ps.print_stats(35)

        else:
            print("INFO\tstarted profiling...")
            self.pr.clear()
            self.pr.enable()


if __name__ == "__main__":
    profiler = Profiler()

    hate = cave_defender.Hate()
    hate.set_custom_command(pygame.K_F3, profiler.toggle, "toggle profiling")
    hate.start()
