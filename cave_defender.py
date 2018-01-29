import pygame

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

pygame.mixer.pre_init(22050, 16, 1, 4096)
pygame.init()

pygame.display.set_caption("HATE")
pygame.display.set_icon(images.get_window_icon())
screen = pygame.display.set_mode((gs.WIDTH, gs.HEIGHT), pygame.DOUBLEBUF)

sounds.init_sounds()
# sounds.play_song(sounds.SONG_CREEPY, loops=-1)

still_running = True
clock = pygame.time.Clock()
FPS = 60

input_state = inputs.InputState()
active_world = world.World()
active_world.add_entity(actors.Player(0, 0))

gs.hud = huds.HUD()
gs.hud.set_active_menu(menus.MAIN_MENU)


def stop_running():
    global still_running
    still_running = False


def draw(screen):
    screen_rect = (0, 0, gs.WIDTH, gs.HEIGHT)
    pygame.draw.rect(screen, (120, 120, 120), screen_rect, 0)
    active_world.draw_all(screen)
    gs.hud.draw(screen, offset=cool_math.neg(active_world.get_camera()))


def update():
    global active_world, input_state

    input_state.update()

    gs.update(input_state)
    gs.hud.update(input_state, active_world)
    if not gs.hud.is_absorbing_inputs():
        active_world.update_all(input_state)

    if gs.queued_next_level_name is not None:
        level = levels.get_level(gs.queued_next_level_name)
        gs.level_save_dest = gs.queued_next_level_name
        pygame.display.set_caption("HATE (editing " + gs.queued_next_level_name + ".txt)")
        gs.queued_next_level_name = None

        player = actors.Player(0, 0)
        pos = level.get_player_start_pos()
        player.set_xy(pos[0], pos[1])

        active_world = world.World()  # start anew
        level.build(active_world)
        active_world.add_entity(player)

        images.wipe_caches()

    player_dead = active_world.time_since_player_death() > settings.WAIT_TICKS_AFTER_DEATH
    if player_dead and not gs.hud.is_absorbing_inputs():
        gs.hud.set_active_menu(menus.DEATH_MENU)

    images.update()

    if gs.exit_requested:
        stop_running()


def set_fullscreen(val):
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


    global screen
    screen = new_screen


while still_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            stop_running()
        elif event.type == pygame.VIDEORESIZE:
            gs.WIDTH = event.w
            gs.HEIGHT = event.h
            new_size = (gs.WIDTH, gs.HEIGHT)
            screen = pygame.display.set_mode(new_size, pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            input_state.set_key(event.key, True)
            if event.key == pygame.K_F1:
                images.reload_sheet()
            elif event.key == pygame.K_F2:
                pygame.image.save(screen, "screenshots/screenshot.png")
                print("INFO\tsaved screenshot: screenshot.png")
            elif event.key == pygame.K_F4:
                set_fullscreen(not gs.is_fullscreen)
            elif event.key == pygame.K_F5:
                filename = gs.level_save_dest
                if filename is not None:
                    print("INFO\tsaving world to: ", filename)
                    levels.save_to_level_file(active_world, filename)
                else:
                    print("ERROR\tgs.level_save_dest is None! Not saving.")
        elif event.type == pygame.KEYUP:
            input_state.set_key(event.key, False)
        elif event.type == pygame.MOUSEMOTION:
            input_state.set_mouse_pos(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            input_state.set_mouse_down(True)
        elif event.type == pygame.MOUSEBUTTONUP:
            input_state.set_mouse_down(False)

    if not pygame.mouse.get_focused():
        input_state.set_mouse_pos(None)

    update()
    draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

print("INFO\texit imminent")
pygame.quit()
