import pygame

import math
import copy
import collections

import entities
import global_state
import cool_math
import images
import settings
import text_stuff
import puzzles
import menus
import entity_factory
import inputs


LEVEL_TITLE_SIZE = 128


class HUD:
    def __init__(self):
        self.selected_item_to_place = None
        self.selected_item_placeable = False

        self.hotkey_active_idx = None
        self.hotkey_item_page_idx = 0
        self.hotkey_items_draw_lookup = {}  # fac_id -> entity
        self.hotkey_items = [None] * 20
        self._update_hotkey_items()

        self.text_queue = collections.deque()
        self.text_queue_color = settings.WHITE
        self.text_queue_blocking = False
        self.show_text_time = -500

        self.active_puzzle = None
        self.puzzle_state_callback = None
        self.puzzle_surface = None
        self.active_player = None

        self.level_title_card = None  # (title, subtitle)
        self.level_title_card_countdown = -1
        self.level_title_card_max_countdown = 50

        self.active_menu = None

    def set_active_menu(self, menu_id):
        print("INFO\tswitching to menu: ", menu_id)
        if menu_id is None:
            self.active_menu = None
        else:
            menu = menus.get_menu(menu_id)
            menu.prepare_to_show(self.active_menu)
            self.active_menu = menu

    def display_text(self, lines, color=settings.WHITE, blocking=True):
        """
        lines: string or list of strings to display
        color: color of text
        blocking: if true, world will freeze until player has finished reading
        """
        if isinstance(lines, str):
            lines = [lines]

        if not blocking and len(lines) > 1:
            raise ValueError("cannot have non-blocking text that's more than one page")

        self.text_queue.clear()

        self.text_queue.extend(lines)
        self.text_queue_blocking = blocking
        self.text_queue_color = color
        self.show_text_time = global_state.tick_counter

    def stop_displaying_text(self):
        self.text_queue.clear()

    def set_level_title_card(self, level_name, level_subtitle):
        self.level_title_card = (level_name, level_subtitle)
        self.level_title_card_countdown = self.level_title_card_max_countdown

    def is_showing_title_card(self):
        return self.level_title_card_countdown > 0 and self.level_title_card is not None

    def update(self, input_state, world):

        if self.active_menu is not None:
            self.active_menu.update(input_state)
            return

        self.active_player = world.player()

        if global_state.show_items_to_place:
            if input_state.was_pressed(pygame.K_TAB):
                inc = 1 if not input_state.is_held(pygame.K_LSHIFT) else -1
                self.hotkey_item_page_idx += inc
                self._update_hotkey_items()

        if self.is_showing_title_card():
            self.level_title_card_countdown -= 1

        elif self.active_puzzle is not None:
            # if puzzle is active block everything else
            if self.active_puzzle.ready_to_close():
                self.puzzle_state_callback[0] = self.active_puzzle.get_status()
                self.active_puzzle = None
                self.puzzle_state_callback = None
            else:
                self.active_puzzle.update(input_state)

        elif self.is_showing_text():
            # if text is showing, block everything else
            if input_state.was_pressed(inputs.INTERACT) and len(self.text_queue) > 0:
                # wait a little bit before nuking the text box
                if global_state.tick_counter - self.show_text_time > 15:
                    self.text_queue.popleft()
                    self.show_text_time = global_state.tick_counter
        else:
            self._handle_selecting_item(input_state)
            placed = self._handle_placing_item(input_state, world)
            if not placed:
                self._handle_removing_item(input_state, world)

    def _update_hotkey_items(self):
        all_ids = entity_factory.ALL_IDS_SORTED
        num_slots = len(self.hotkey_items)
        num_pages = max(1, math.ceil(len(all_ids) / num_slots))
        self.hotkey_item_page_idx = self.hotkey_item_page_idx % num_pages
        start_idx = self.hotkey_item_page_idx * num_slots

        for i in range(0, num_slots):
            item_idx = start_idx + i
            if item_idx < len(all_ids):
                item_id = all_ids[item_idx]
                self.hotkey_items[i] = item_id
                if item_id not in self.hotkey_items_draw_lookup:
                    item_instance = entity_factory.build(item_id)
                    if item_instance.is_("spawner"):
                        item_instance = item_instance.create_entity()
                    self.hotkey_items_draw_lookup[item_id] = item_instance
            else:
                self.hotkey_items[i] = None

    def draw(self, screen, offset=(0, 0)):
        if self.active_menu is not None:
            self.active_menu.draw(screen)

        elif self.is_showing_title_card():
            self._draw_title_card(screen)

        else:
            if self.active_player is not None:
                cur_health = max(0, self.active_player.health)
                max_health = max(0, self.active_player.max_health)
                self._draw_hearts(screen, (0, 0), cur_health/2, int(max_health/2))

            if self.active_puzzle is not None:
                puzzle_rect = self._get_puzzle_rect()
                text_stuff.draw_pretty_bordered_rect(screen, puzzle_rect)
                self.puzzle_surface.fill(settings.BLACK)
                draw_w = self.puzzle_surface.get_width()
                draw_h = self.puzzle_surface.get_height()
                self.active_puzzle.draw(self.puzzle_surface, draw_w, draw_h)
                screen.blit(self.puzzle_surface, (puzzle_rect[0], puzzle_rect[1]))
            else:
                to_place = self.selected_item_to_place
                placeable = self.selected_item_placeable
                if to_place is not None and placeable is not None:
                    mod = "green_ghosts" if placeable else "red_ghosts"

                    # wanna draw the thing the spawner creates
                    to_draw = self.hotkey_items_draw_lookup[self.hotkey_items[self.hotkey_active_idx]]
                    if to_place.is_("spawner"):
                        offs = cool_math.sub(to_place.xy(), to_draw.xy())
                        offs = cool_math.add(offs, offset)
                        to_draw.draw(screen, offs, modifier=mod)

                    to_place.draw(screen, offset, modifier=mod)

                if global_state.show_items_to_place:
                    self._draw_placeable_items(screen)

                if self.is_showing_text() and len(self.text_queue) > 0:
                    text_string = self.text_queue[0]
                    text_stuff.draw_text(screen, text_string, "standard", 32, 512, color=self.text_queue_color)

        self.draw_debug_stuff(screen)

    def draw_debug_stuff(self, screen):
        debug_y = 0

        if global_state.show_fps:
            text = "FPS: " + str(global_state.current_fps)
            fps_text = text_stuff.get_text_image(text, "standard", 32, settings.WHITE, bg_color=None)
            x = global_state.WIDTH - fps_text.get_width()
            screen.blit(fps_text, (x, debug_y))
            debug_y += fps_text.get_height()

        if global_state.is_profiling:
            text = "profiling..."
            profiling_text = text_stuff.get_text_image(text, "standard", 32, settings.WHITE, bg_color=None)
            x = global_state.WIDTH - profiling_text.get_width()
            screen.blit(profiling_text, (x, debug_y))
            debug_y =+ profiling_text.get_height()

    def _draw_title_card(self, screen):
        white = (255, 255, 255)
        black = (0, 0, 0)
        screen.fill(black)
        title = self.level_title_card[0]
        border = 32
        title_h = LEVEL_TITLE_SIZE
        title_font = text_stuff.get_font("standard", title_h)
        title_lines = text_stuff.wrap_text(title, global_state.WIDTH - border*2, title_font)
        title_y = int(global_state.HEIGHT / 4)
        for i in range(0, len(title_lines)):
            line = title_lines[i]
            img = text_stuff.get_text_image(line, "standard", title_h, white, bg_color=black)
            screen.blit(img, (border, title_y + title_h*i))

        subtitle = self.level_title_card[1]
        if subtitle is not None:
            subtitle_h = int(title_h * 2 / 3)
            subtitle_img = text_stuff.get_text_image(subtitle, "standard", subtitle_h, white, bg_color=black)
            subtitle_y = title_y + title_h*len(title_lines) + 16
            screen.blit(subtitle_img, (border, subtitle_y))

    def _draw_hearts(self, screen, pos, full, total):
        heart_w = images.HEART_FULL.width()
        for i in range(0, total):
            dest_x = pos[0] + i*heart_w
            dest = (dest_x, pos[1])
            sprite = images.HEART_FULL
            if (i+1) > full:
                sprite = images.HEART_EMPTY if i >= full else images.HEART_HALF
            images.draw_animated_sprite(screen, dest, sprite)

    def _draw_placeable_items(self, screen):
        w = global_state.WIDTH
        h = 128
        y1 = global_state.HEIGHT - h
        y2 = int(y1 + h / 2)
        columns = 10

        pygame.draw.rect(screen, (0, 0, 0), [0, y1, w, h], 2)
        pygame.draw.line(screen, (0, 0, 0), (0, y2), (w, y2), 2)

        for i in range(0, columns):
            x = int((i+0.5) * w / columns)
            pygame.draw.line(screen, (0, 0, 0), (int(i*w/columns), y1), (int(i*w/columns), y1+h), 2)
            if i < len(self.hotkey_items) and self.hotkey_items[i] is not None:
                item = self.hotkey_items_draw_lookup[self.hotkey_items[i]]
                pos = item.center()
                item.draw(screen, cool_math.sub((x, int(y1 + h/4)), pos))
            i2 = i + columns
            if i2 < len(self.hotkey_items) and self.hotkey_items[i2] is not None:
                item = self.hotkey_items_draw_lookup[self.hotkey_items[i2]]
                pos = item.center()
                item.draw(screen, cool_math.sub((x, int(y2 + h/4)), pos))

    def set_puzzle(self, puzzle):
        """
        Displays a puzzle to the player. Cannot be called if there is already an active puzzle.
        :param puzzle: Puzzle
        :return: a single-element list whose value will eventually be set to the puzzle's exit status.
        """
        if self.active_puzzle is not None:
            raise ValueError("There is already an active puzzle.")
        else:
            self.active_puzzle = puzzle
            self.puzzle_state_callback = [puzzles.IN_PROGRESS]
            if self.puzzle_surface is None or self.puzzle_surface.get_size() != puzzle.size():
                print("INFO\tregenning puzzle surface to size=", puzzle.size())
                self.puzzle_surface = pygame.Surface(puzzle.size())
            return self.puzzle_state_callback

    def _get_item_to_place(self, index, alt):
        if alt:
            index += int(len(self.hotkey_items) / 2)
        factory_id = self.hotkey_items[index]
        if factory_id is not None:
            return entity_factory.build(factory_id)
        else:
            return None

    KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
            pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0]

    def _handle_selecting_item(self, input_state):
        idx = None
        keys = HUD.KEYS
        for i in range(0, len(keys)):
            if input_state.was_pressed(keys[i]):
                idx = i
                break

        if idx is not None:
            alt = input_state.is_held(pygame.K_LSHIFT) or input_state.is_held(pygame.K_RSHIFT)
            item = self._get_item_to_place(idx, alt)
            if item is None or self.hotkey_active_idx == idx:
                self._set_item_to_place(None, None)
            else:
                self._set_item_to_place(item, idx)

    def _set_item_to_place(self, item, index):
        self.selected_item_to_place = item
        self.hotkey_active_idx = index

    def _handle_placing_item(self, input_state, world):
        to_place = self.selected_item_to_place

        if to_place is not None:
            mouse = input_state.mouse_pos()
            if mouse is not None:
                in_world = world.to_world_pos(*mouse)
                w, h = to_place.get_rect().size
                w = 16 if w <= 16 else 32
                h = 16 if h <= 16 else 32
                c_xy = world.get_tile_at(*in_world, tilesize=(w, h))
                to_place.set_x(c_xy[0] - w / 2)
                to_place.set_y(c_xy[1] - h / 2)

        if to_place is None or world.player() is None or not input_state.mouse_in_window():
            self.selected_item_placeable = False
        else:
            if to_place.is_ground():
                blocked_by = world.get_entities_in_rect(to_place.get_rect(), category="ground")
            else:
                blocked_by = world.get_entities_in_rect(to_place.get_rect(), not_category="ground")
            self.selected_item_placeable = len(blocked_by) == 0

            if input_state.mouse_was_pressed() and self.selected_item_placeable:
                new_entity = copy.deepcopy(to_place)
                if isinstance(new_entity, entities.ReferenceEntity):
                    ref_id = input("Enter reference id: ")
                    new_entity.set_ref_id(ref_id)
                world.add_entity(new_entity)
                # keep holding original object
                return True

        return False

    def _handle_removing_item(self, input_state, world):
        if self.selected_item_to_place is None:
            if input_state.mouse_in_window() and input_state.mouse_was_pressed():
                screen_pos = input_state.mouse_pos()
                world_pos = world.to_world_pos(*screen_pos)

                rm_ground = input_state.is_held(pygame.K_LSHIFT) or input_state.is_held(pygame.K_RSHIFT)
                if rm_ground:
                    ents = world.get_entities_at_point(world_pos, category="ground")
                else:
                    ents = world.get_entities_at_point(world_pos, not_category="ground")

                if len(ents) > 0:
                    return world.remove_entity(ents[0])

        return False

    def is_absorbing_inputs(self):
        absorbing = global_state.tick_counter - self.show_text_time < 2
        absorbing = absorbing or (self.is_showing_text() and self.text_queue_blocking)
        absorbing = absorbing or self.active_puzzle is not None
        absorbing = absorbing or self.is_showing_title_card()
        absorbing = absorbing or self.active_menu is not None

        return absorbing

    def is_showing_text(self):
        return len(self.text_queue) > 0

    def _get_puzzle_rect(self):
        if self.active_puzzle is None:
            return None
        else:
            screen_rect = [0, 0, global_state.WIDTH, global_state.HEIGHT]
            puzzle_size = self.active_puzzle.size()
            puzzle_rect = [0, 0, puzzle_size[0], puzzle_size[1]]

            return cool_math.recenter_rect_in(puzzle_rect, screen_rect)
