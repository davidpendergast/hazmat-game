import pygame

import image_cache
import world
import images
import global_state as gs
import huds
import inputs
import cool_math
import levels
import sounds
import actors
import menus
import settings


class Hate:
    def __init__(self):
        pygame.mixer.pre_init(22050, 16, 1, 4096)
        numpass, numfail = pygame.init()
        print("INFO\tpygame initialized: ", numfail, " module(s) failed to init.")

        pygame.display.set_caption("HATE")
        pygame.display.set_icon(images.get_window_icon())
        self.screen = pygame.display.set_mode((gs.WIDTH, gs.HEIGHT), pygame.DOUBLEBUF)

        print("display initted = ", pygame.display.get_init())

        sounds.init_sounds()
        # sounds.play_song(sounds.SONG_CREEPY, loops=-1)

        self.still_running = True
        self.clock = pygame.time.Clock()
        self.FPS = 60

        self.input_state = inputs.InputState()
        self.active_world = world.World()
        self.active_world.add_entity(actors.Player())

        gs.hud = huds.HUD()
        gs.hud.set_active_menu(menus.MAIN_MENU)

    def stop_running(self):
        self.still_running = False

    def draw(self):
        s = self.screen
        screen_rect = (0, 0, gs.WIDTH, gs.HEIGHT)
        pygame.draw.rect(s, (120, 120, 120), screen_rect, 0)
        self.active_world.draw_all(s)
        gs.hud.draw(s, offset=cool_math.neg(self.active_world.get_camera()))
        gs.draw_counter += 1

    def update(self):
        self.input_state.update()

        gs.update(self.input_state)
        gs.hud.update(self.input_state, self.active_world)
        if not gs.hud.is_absorbing_inputs():
            self.active_world.update_all(self.input_state)

        if gs.queued_next_level_name is not None:
            level = levels.get_level(gs.queued_next_level_name)
            gs.level_save_dest = gs.queued_next_level_name
            pygame.display.set_caption("HATE (editing " + gs.queued_next_level_name + ".txt)")
            gs.queued_next_level_name = None

            player = actors.Player()
            pos = level.get_player_start_pos()
            player.set_xy(pos[0], pos[1])

            self.active_world = world.World()  # start anew
            level.build(self.active_world)
            self.active_world.add_entity(player)

            image_cache.wipe_caches()

        player_dead = self.active_world.time_since_player_death() > settings.WAIT_TICKS_AFTER_DEATH
        if player_dead and not gs.hud.is_absorbing_inputs():
            gs.hud.set_active_menu(menus.DEATH_MENU)

        images.update()

        if gs.exit_requested:
            self.stop_running()

    def set_fullscreen(self, val):
        print("INFO\tsetting fullscreen to: ", val)
        gs.is_fullscreen = val

        if gs.is_fullscreen:
            # TODO - aparently resolution=(0, 0) raises an exception on certain hardware? need to investigate
            new_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
        else:
            pygame.display.quit()   # TODO - this is kinda janky, need to make sure this works on other systems
            pygame.display.init()
            pygame.display.set_caption("HATE")
            pygame.display.set_icon(images.get_window_icon())
            size = (gs.WIDTH, gs.HEIGHT)
            new_screen = pygame.display.set_mode(size, pygame.DOUBLEBUF)

        self.screen = new_screen

    def start(self):
        while self.still_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop_running()
                elif event.type == pygame.VIDEORESIZE:
                    gs.WIDTH = event.w
                    gs.HEIGHT = event.h
                    new_size = (gs.WIDTH, gs.HEIGHT)
                    self.screen = pygame.display.set_mode(new_size, pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    self.input_state.set_key(event.key, True)
                    if event.key == pygame.K_F1:
                        images.reload_sheet()
                    elif event.key == pygame.K_F2:
                        pygame.image.save(self.screen, "screenshots/screenshot.png")
                        print("INFO\tsaved screenshot: screenshot.png")
                    elif event.key == pygame.K_F4:
                        self.set_fullscreen(not gs.is_fullscreen)
                    elif event.key == pygame.K_F5:
                        filename = gs.level_save_dest
                        if filename is not None:
                            print("INFO\tsaving world to: ", filename)
                            levels.save_to_level_file(self.active_world, filename)
                        else:
                            print("ERROR\tgs.level_save_dest is None! Not saving.")
                elif event.type == pygame.KEYUP:
                    self.input_state.set_key(event.key, False)
                elif event.type == pygame.MOUSEMOTION:
                    self.input_state.set_mouse_pos(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.input_state.set_mouse_down(True)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.input_state.set_mouse_down(False)

            if not pygame.mouse.get_focused():
                self.input_state.set_mouse_pos(None)

            self.update()

            if gs.tick_counter % settings.FPS_THROTTLE == 0:
                self.draw()
                pygame.display.flip()

                self.clock.tick(self.FPS)

        print("INFO\texit imminent")
        pygame.quit()


if __name__ == "__main__":
    hate = Hate()
    hate.start()
