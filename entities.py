import pygame
import random

import cool_math
import image_cache
import images
import global_state
import puzzles


class Entity:
    def __init__(self, x, y, w, h):
        self.is_alive = True
        self.x = x  # floating point
        self.y = y  # floating point
        self.vel = [0, 0]
        self.rect = pygame.Rect(x, y, w, h)
        self.categories = set()
        self.light_radius = None
        self.ref_id = None      # used by the level loader to mark entity as 'special'
        self.factory_id = None  # used by the level loaded to mark entity as factory created

    def draw(self, screen, offset=(0, 0), modifier=None):
        modifier = self.sprite_modifier() if modifier is None else modifier
        sprite = self.sprite()
        dest_rect = self.get_rect().move(*offset)
        if sprite is not None:
            dest_rect.move_ip(*self.sprite_offset())
            images.draw_animated_sprite(screen, dest_rect, sprite, modifier)
        else:
            pygame.draw.rect(screen, images.RAINBOW, dest_rect, 0)

    def with_category(self, category):
        validate_category(category)
        self.categories.add(category)
        return self

    def set_factory_id(self, factory_id):
        self.factory_id = factory_id

    def get_factory_id(self):
        return self.factory_id

    def sprite_offset(self):
        return (0, 0)

    def sprite(self):
        """returns: animated_sprite"""
        return None

    def sprite_modifier(self):
        return "normal"

    def update(self, input_state, world):
        pass

    def get_rect(self):
        """
        The space that this entity physically occupies
        returns: pygame.Rect
        """
        return self.rect.copy()

    def set_x(self, x):
        self.x = x
        self.rect.x = round(x)

    def set_y(self, y):
        self.y = y
        self.rect.y = round(y)

    def set_w(self, w):
        self.rect.width = w

    def set_h(self, h):
        self.rect.height = h

    def set_xy(self, x, y):
        self.set_x(x)
        self.set_y(y)

    def set_center_x(self, x):
        self.set_x(x - self.get_rect().width / 2)

    def set_center_y(self, y):
        self.set_y(y - self.get_rect().height / 2)

    def set_center(self, x, y):
        self.set_center_x(x)
        self.set_center_y(y)

    def get_x(self):
        return self.get_rect().x

    def get_y(self):
        return self.get_rect().y

    def xy(self):
        r = self.get_rect()
        return (r.x, r.y)

    def center(self):
        r = self.get_rect()
        return (int(r.x + r.width / 2), int(r.y + r.height / 2))

    def width(self):
        return self.get_rect().width

    def height(self):
        return self.get_rect().height

    def size(self):
        return (self.width(), self.height())

    def get_ref_id(self):
        return self.ref_id

    def set_ref_id(self, ref_id):
        self.ref_id = ref_id

    def is_(self, category):
        validate_category(category)
        return category in self.categories

    def is_wall(self):
        return self.is_("wall")

    def is_actor(self):
        return self.is_("actor")

    def is_enemy(self):
        return self.is_("enemy")

    def is_player(self):
        return self.is_("player")

    def is_ground(self):
        return self.is_("ground")

    def is_door(self):
        return self.is_("door")

    def is_interactable(self):
        return self.is_("interactable")

    def can_interact(self):
        return False

    def interact_action_text(self, world):
        return "interact with entity"

    def interact_message(self, world):
        return "press [k] to " + self.interact_action_text(world)

    def interact(self, world):
        pass

    def is_decoration(self):
        return self.is_("decoration")

    def is_light_source(self):
        return self.is_("light_source")

    def with_light_level(self, radius):
        """
        Should only be called when building entity. Also, giving light to an entity
        that moves a lot will likely cause performance issues
        """
        self.light_radius = radius
        if radius is not None:
            self.categories.add("light_source")
        elif "light_source" in self.categories:
            self.categories.remove("light_source")

        return self

    def light_profile(self):
        """
        returns: integers (x, y, luminosity, radius), or None if luminosity
        or radius is zero
        """
        if self.light_radius is None or self.light_radius <= 0:
            return None
        else:
            pos = self.center()
            return (pos[0], pos[1], 255, self.light_radius)

    def __repr__(self):
        pos = "(%s, %s)" % (self.rect.x, self.rect.y)
        return type(self).__name__ + pos


class Wall(Entity):
    def __init__(self, x, y, w=32, h=32, sprite=images.WHITE_WALL):
        Entity.__init__(self, x, y, w, h)
        self._sprite = sprite
        self._cached_outline = None  # surface
        self._outline_dirty = True
        self.categories.update(["wall"])

    def bullet_hit(self):
        pass

    def sprite(self):
        return self._sprite

    def sprite_offset(self):
        return (0, 0)

    def set_outline_dirty(self, is_dirty):
        self._outline_dirty = is_dirty

    def draw(self, screen, offset=(0, 0), modifier=None):
        Entity.draw(self, screen, offset, modifier)
        if self._cached_outline is not None:
            screen.blit(self._cached_outline, cool_math.add(self.xy(), offset))

    def update(self, input_state, world):
        if self._outline_dirty:
            self.update_outlines(world)
            self._outline_dirty = False

            for chunk in world.get_chunks_in_rect(self.get_rect(), and_above_and_left=False):
                chunk.mark_dirty()  # ehh this is kinda gross

    def update_outlines(self, world):
        if self._cached_outline is None:
            self._cached_outline = pygame.Surface(self.size(), flags=pygame.SRCALPHA)
        else:
            self._cached_outline.fill((0, 0, 0, 0), None, 0)
        rect = self.get_rect()
        r = [0, 0, 2, 2]
        for x in range(0, self.width(), 2):
            if len(world.get_entities_at_point((rect.x + x, rect.y - 1), category="wall")) == 0:
                r[0] = x
                r[1] = 0
                pygame.draw.rect(self._cached_outline, (0, 0, 0), r, 0)
            if len(world.get_entities_at_point((rect.x + x, rect.y + rect.height), category="wall")) == 0:
                r[0] = x
                r[1] = rect.height - 2
                pygame.draw.rect(self._cached_outline, (0, 0, 0), r, 0)
        for y in range(0, self.height(), 2):
            if len(world.get_entities_at_point((rect.x - 1, rect.y + y), category="wall")) == 0:
                r[0] = 0
                r[1] = y
                pygame.draw.rect(self._cached_outline, (0, 0, 0), r, 0)
            if len(world.get_entities_at_point((rect.x + rect.width, rect.y + y), category="wall")) == 0:
                r[0] = rect.width - 2
                r[1] = y
                pygame.draw.rect(self._cached_outline, (0, 0, 0), r, 0)


class BreakableWall(Wall):
    def __init__(self, x, y, sprite, break_animation=None):
        Wall.__init__(self, x, y, sprite=sprite)
        self.break_animation = break_animation
        self._was_hit = False

    def bullet_hit(self):
        self._was_hit = True

    def update(self, input_state, world):
        Wall.update(self, input_state, world)
        if self._was_hit:
            self.is_alive = False
            if self.break_animation is not None:
                explosion = Overlay(self.break_animation, 0, 0).with_lifespan(cycles=1)
                ctr = self.center()
                explosion.set_center(ctr[0], ctr[1])
                world.add_entity(explosion)
            # TODO - sound


class Door(Entity):
    def __init__(self, x, y, door_id, dest_id, locked=False):
        Entity.__init__(self, x, y, 32, 64)
        self.door_id = door_id
        self.dest_id = dest_id
        self.locked = locked
        self.categories.update(["door", "interactable"])

        # Cooldown behavior:
        #   0: door is closed. 
        #   1: player is teleported to reciever door.
        #   >1: door is opening.
        #   <0: door is closing
        self.open_cooldown = 0
        self.open_max_cooldown = 30

    def sprite(self):
        if self.open_cooldown != 0 and abs(self.open_cooldown) < self.open_max_cooldown:
            cd = self.open_cooldown if self.open_cooldown > 0 else self.open_max_cooldown + self.open_cooldown
            progress = cd / self.open_max_cooldown
            animation = images.DOOR_CLOSING
            frame = int(progress * animation.num_frames())
            return animation.single_frame(frame)
        else:
            if self.locked:
                return images.DOOR_LOCKED
            else:
                return images.DOOR_UNLOCKED

    def update(self, input_state, world):
        if self.open_cooldown == 1:
            player = world.player()
            dest_door = world.get_door(self.dest_id)
            if player is not None and dest_door is not None:
                player.set_center(*dest_door.center())
                dest_door.open_cooldown = -dest_door.open_max_cooldown

        if self.open_cooldown > 0:
            self.open_cooldown -= 1
        if self.open_cooldown < 0:
            self.open_cooldown += 1

    def can_interact(self):
        # can't interact after it's already been interacted with
        return self.open_cooldown == 0

    def interact(self, world):
        if not self.locked:
            self.open_cooldown = self.open_max_cooldown
        else:
            global_state.hud.display_text("It's locked.")

    def interact_action_text(self, world):
        return "enter door"


class Terminal(Entity):
    def __init__(self, x, y, message="It's a computer terminal"):
        Entity.__init__(self, x, y, 32, 64)
        self.categories.update(["terminal", "interactable"])
        self.message = message

    def update(self, input_state, world):
        pass

    def sprite(self):
        return images.TERMINAL

    def sprite_offset(self):
        return (0, 0)

    def screen_sprite(self):
        return images.TERMINAL_SCREEN

    def draw(self, screen, offset=(0, 0), modifier=None):
        Entity.draw(self, screen, offset=offset, modifier=modifier)

        modifier = self.sprite_modifier() if modifier is None else modifier
        screen_sprite = self.screen_sprite()
        dest_rect = self.get_rect().move(*offset)
        dest_rect.move_ip(3 * 2, 9 * 2)  # shift into screen area of sprite
        dest_rect.move_ip(*self.sprite_offset())
        images.draw_animated_sprite(screen, dest_rect, screen_sprite, modifier)

    def can_interact(self):
        return True

    def set_message(self, message):
        """
        :param message: string or list of strings
        """
        self.message = message

    def interact(self, world):
        global_state.hud.display_text(self.message)

    def interact_action_text(self, world):
        return "read terminal"


class PuzzleTerminal(Terminal):
    def __init__(self, x, y, puzzle_giver):
        Terminal.__init__(self, x, y)
        self.categories.update(["puzzle_terminal"])
        self.active_callback = None
        self.on_success = None  # no-arg lambda
        self.puzzle_creator = puzzle_giver
        self.has_been_completed = False

    def update(self, input_state, world):
        if self.active_callback is not None:
            if self.active_callback[0] == puzzles.SUCCESS:
                self.has_been_completed = True
                if self.on_success is not None:
                    self.on_success()
            self._handle_result(self.active_callback[0], world)
            self.active_callback = None

    def _handle_result(self, puzzle_result, world):
        pass

    def set_on_success(self, on_success):
        self.on_success = on_success

    def sprite(self):
        return images.PUZZLE_TERMINAL

    def screen_sprite(self):
        return images.PUZZ_TERM_SCREEN

    def interact(self, world):
        if self.is_complete():
            global_state.hud.display_text("This puzzle has already been completed.")
        else:
            puzzle = self.puzzle_creator()
            self.active_callback = global_state.hud.set_puzzle(puzzle)

    def is_complete(self):
        return self.has_been_completed

    def interact_action_text(self, world):
        return "attempt puzzle"


class DeathPuzzleTerminal(PuzzleTerminal):
    def __init__(self, x, y, puzzle_giver):
        PuzzleTerminal.__init__(self, x, y, puzzle_giver)

    def sprite(self):
        return images.DEATH_PUZZLE

    def screen_sprite(self):
        return images.DEATH_PUZZLE_SCREEN

    def _handle_result(self, puzzle_result, world):
        if puzzle_result == puzzles.FAILURE:
            player = world.player()
            if player is not None:
                player.deal_damage(1, source=self)


class HealthMachine(Entity):
    def __init__(self, x, y, num_hearts=3):
        Entity.__init__(self, x, y, 32, 64)
        self.categories.update(["interactable", "health_machine"])
        self.hearts_left = max(0, min(4, num_hearts))  # gotta be between zero and four hearts

    def sprite(self):
        return images.HEALTH_MACHINE

    def draw(self, screen, offset=(0, 0), modifier="normal"):
        Entity.draw(self, screen, offset, modifier=modifier)
        bar_1_pos = (self.get_x() + offset[0] + 6*2, self.get_y() + offset[1] + 24*2)
        for i in range(0, self.hearts_left):
            dest = (bar_1_pos[0], bar_1_pos[1] - i*4)
            images.draw_animated_sprite(screen, dest, images.HEALTH_MACHINE_BAR, modifier=modifier)

    def interact(self, world):
        if self.hearts_left <= 0:
            global_state.hud.display_text("It's empty.")
        else:
            player = world.player()
            if player is not None:
                if player.health >= player.max_health:
                    global_state.hud.display_text("Health is full.")
                else:
                    if player.health % 2 == 1:
                        # heals half a heart for free, even if machine is empty
                        player.health += 1
                    elif self.hearts_left > 0:
                        player.health += 2
                        self.hearts_left -= 1
                    else:
                        global_state.hud.display_text("Machine is empty.")

    def interact_action_text(self, world):
        return "use healing machine"


class LevelEndDoor(Entity):
    def __init__(self, x, y, dest_level_id):
        Entity.__init__(self, x, y, 64, 96)
        self.categories.update(["interactable", "level_door"])
        self.dest_level_id = dest_level_id
        self.is_locked = True
        self.is_open = False
        self.max_opening_cooldown = 60
        self.opening_cooldown = -1

    def update(self, input_state, world):
        if not self.is_locked and self.opening_cooldown > 0:
            self.opening_cooldown -= 1
        if not self.is_locked and self.opening_cooldown <= 0:
            self.is_open = True
            # TODO - play sound

    def draw(self, screen, offset=(0, 0), modifier="normal"):
        x = self.get_x() + offset[0]
        top_sprite = images.BLAST_DOOR_TOP
        bot_sprite = images.BLAST_DOOR_BOTTOM
        top_y_closed = self.get_y() + offset[1]
        bot_y_closed = self.get_y() + offset[1] + self.height() - top_sprite.height()
        if self.is_locked or self.opening_cooldown == self.max_opening_cooldown:
            images.draw_animated_sprite(screen, (x, top_y_closed), top_sprite, modifier=modifier)
            images.draw_animated_sprite(screen, (x, bot_y_closed), bot_sprite, modifier=modifier)
        elif self.is_open or self.opening_cooldown <= 0:
            images.draw_animated_sprite(screen, self.get_rect().move(offset[0], offset[1]), images.BLAST_DOOR_BKGR)
        else:
            # door is opening
            images.draw_animated_sprite(screen, self.get_rect().move(offset[0], offset[1]), images.BLAST_DOOR_BKGR)
            progress = 1 - self.opening_cooldown / self.max_opening_cooldown
            top_cut_off = int(progress * top_sprite.height())
            bot_cut_off = int(progress * bot_sprite.height())
            top_subset = [0, top_cut_off, top_sprite.width(), top_sprite.height() - top_cut_off]
            bot_subset = [0, 0, bot_sprite.width(), bot_sprite.height() - bot_cut_off]
            top_pos = (x, top_y_closed)
            bot_pos = (x, bot_y_closed + bot_cut_off)
            images.draw_animated_sprite(screen, top_pos, top_sprite, modifier=modifier, src_subset=top_subset)
            images.draw_animated_sprite(screen, bot_pos, bot_sprite, modifier=modifier, src_subset=bot_subset)

    def can_interact(self):
        return True

    def interact(self, world):
        print("interacted with door")
        if self.is_open:
            print("Going to next level")
            global_state.queued_next_level_name = self.dest_level_id
        elif self.is_locked:
            all_puzzles = world.get_entities_with(category="puzzle_terminal")
            incomplete = len([x for x in all_puzzles if not x.is_complete()])
            if incomplete > 0:
                if incomplete == 1:
                    msg = "There is one puzzle remaining. Finish it to unlock the door."
                else:
                    msg = "There are " + str(incomplete) + " puzzles remaining. Finish them to unlock the door."
                global_state.hud.display_text(msg)
            else:
                self.is_locked = False
                self.opening_cooldown = self.max_opening_cooldown
                # TODO - play sound
        else:
            # door is opening
            pass

    def interact_action_text(self, world):
        if self.is_locked:
            return "unlock door"
        else:
            return "enter door"


class Overlay(Entity):
    def __init__(self, animation, x, y, modifier="normal"):
        Entity.__init__(self, x, y, animation.width(), animation.height())
        self._modifier = modifier
        self.categories.update(["overlay"])
        self.animation = animation
        self._tick_limit = -1
        self._create_time = global_state.tick_counter
        self._target = None

    def sprite_modifier(self):
        return self._modifier

    def with_lifespan(self, cycles=-1, ticks=-1):
        """
        Sets lifespan of overlay. Exactly one of cycles or ticks should
        be nonnegative, or else behavior is unspecified. Restarts animation.

        """
        self._create_time = global_state.tick_counter
        if cycles >= 0:
            tpf = self.animation.ticks_per_frame()
            num_frames = self.animation.num_frames()
            self._tick_limit = tpf * num_frames * cycles
        else:
            self._tick_limit = ticks
        return self

    def with_target(self, target):
        self._target = target
        return self

    def sprite(self):
        current_tick = global_state.tick_counter
        spawn_tick = self._create_time
        lifetime = current_tick - spawn_tick
        tpf = self.animation.ticks_per_frame()
        cur_frame = lifetime % (tpf * self.animation.num_frames())
        cur_frame = int(cur_frame / tpf)
        return self.animation.single_frame(cur_frame)

    def update(self, input_state, world):
        if self._target is not None and not self._target.is_alive:
            self.is_alive = False
        elif self._tick_limit >= 0:
            current_tick = global_state.tick_counter
            spawn_tick = self._create_time
            lifetime = current_tick - spawn_tick
            if lifetime >= self._tick_limit:
                self.is_alive = False
        elif self._target is not None:
            pos = self._target.center()
            self.set_center(pos[0], pos[1])


class KillBlock(Entity):
    def __init__(self, x, y, sprite, hitbox=None):
        Entity.__init__(self, x, y, sprite.width(), sprite.height())
        self._sprite = sprite
        self._hitbox = hitbox
        self.categories.update(["instakill"])

    def sprite(self):
        return self._sprite

    def update(self, input_state, world):
        actors_touching = world.get_entities_in_rect(self.hitbox(), category="actor")
        for actor in actors_touching:
            actor.deal_damage(9999, source=self)  # TODO - 9999 is probably ok?

    def hitbox(self):
        if self._hitbox is None:
            return self.get_rect()
        else:
            hb = self._hitbox
            return [self.get_x() + hb[0], self.get_y() + hb[1], hb[2], hb[3]]


class ReferenceEntity(Entity):
    def __init__(self, x, y, ref_id=None):
        Entity.__init__(self, x, y, 32, 32)
        self.categories.update(["reference"])
        self.set_ref_id(ref_id)

    def get_ref_id(self):
        if Entity.get_ref_id(self) is None:
            self.set_ref_id("ref_" + str(random.randint(0, 9999)))
        return Entity.get_ref_id(self)

    def draw(self, screen, offset=(0, 0), modifier=None):
        pygame.draw.rect(screen, (100, 100, 255), self.get_rect().move(*offset), 2)


class SpawnerEntity(Entity):
    """
    Creates a single entity and adds it to world at the first opportunity. Used for saving/loading
    entities that are destroyable (enemies, breakable blocks, etc.)
    """
    def __init__(self, x, y, create_entity):
        Entity.__init__(self, x, y, 32, 32)
        self.categories.update(["spawner"])
        self.create_entity = create_entity
        self.did_spawn = False

    def update(self, input_state, world):
        if not self.did_spawn:
            self.did_spawn = True
            my_entity = self.create_entity()

            if my_entity.is_("spawner"):
                raise ValueError("spawners can't spawn other spawners")

            my_entity.set_xy(self.get_x(), self.get_y())
            my_entity.set_ref_id("spawned_no_save_pls")
            world.add_entity(my_entity)

    def draw(self, screen, offset=(0, 0), modifier=None):
        rect = self.get_rect()
        rect.move_ip(offset[0], offset[1])
        pygame.draw.rect(screen, (100, 255, 100), rect, 2)


class Zone(Entity):
    """Invisible area that performs some effect when actors enter"""
    def __init__(self, x, y, w, h):
        Entity.__init__(self, x, y, w, h)
        self.categories.update(["zone"])
        self.debug_color = (125, 255, 125)
        self.actors_inside = {}

    def sprite(self):
        return None

    def draw(self, screen, offset=(0, 0), modifier=None):
        key = "zone_debug_overlay:" + str(self.size()) + "_" + str(self.debug_color)
        cached_img = image_cache.get_cached_image(key)
        if cached_img is None:
            cached_img = pygame.Surface(self.size(), pygame.SRCALPHA)
            cached_img.set_alpha(128)
            cached_img.fill(self.debug_color)
            image_cache.put_cached_image(key, cached_img)
        dest = (self.get_x() + offset[0], self.get_y() + offset[1])
        screen.blit(cached_img, dest)

    def update(self, input_state, world):
        current_actors = set(world.get_entities_in_rect(self.get_rect(), category="actor"))
        actors_last_frame = self.actors_inside

        for actor in current_actors:
            if actor not in actors_last_frame:
                self.actor_entered(actor, world)
            else:
                self.actor_remains(actor, world)
        for actor in actors_last_frame:
            if actor not in current_actors:
                self.actor_left(actor, world)

        self.actors_inside = current_actors

    def actor_entered(self, actor, world):
        print("actor entered zone: ", actor)

    def actor_left(self, actor, world):
        print("actor left zone: ", actor)

    def actor_remains(self, actor, world):
        pass


def _safe_remove(item, collection, print_err=False):
    try:
        collection.remove(item)
    except ValueError:
        if print_err:
            print("cannot remove ", item, ", probably because it's not in the collection")


class EntityCollection:
    VOLATILE_CATEGORIES = {"actor", "enemy", "player", "overlay"}

    def __init__(self, entities=(), name_for_debug="unnamed collection"):
        self.all_stuff = []
        self.category_tests = {}    # category_name -> lambda(entity->bool)
        self.categories = {}        # category_name -> set of entities
        self.name_for_debug = name_for_debug

        for e in entities:
            self.add(e)

    def _add_category(self, name, test):
        validate_category(name)
        if name in self.categories:
            print("Warning: ", self.name_for_debug, " attempted to add category twice: ", name)
        else:
            # print(self.name_for_debug, " adding category: ", name)
            self.category_tests[name] = test
            self.categories[name] = set()

    def has_category(self, cat_name):
        validate_category(cat_name)
        return cat_name in self.categories

    def add(self, entity):
        self.all_stuff.append(entity)

        e_cats = entity.categories
        for category in e_cats:
            if not self.has_category(category):
                self._add_category(category, lambda x: x.is_(category))
            self.categories[category].add(entity)

    def remove(self, entity):
        _safe_remove(entity, self.all_stuff, True)
        e_cats = entity.categories
        for catkey in e_cats:
            if self.has_category(catkey):
                _safe_remove(entity, self.categories[catkey])
                if catkey not in EntityCollection.VOLATILE_CATEGORIES and len(self.categories[catkey]) == 0:
                    self._remove_category(catkey)
            else:
                raise ValueError("entity has a category that collection is missing? cat=" + str(catkey))

    def _remove_category(self, catkey):
        validate_category(catkey)
        # print(self.name_for_debug, " removing category: ", catkey)
        if catkey in self.categories:
            del self.categories[catkey]
        if catkey in self.category_tests:
            del self.category_tests[catkey]

    def get_all(self, category=None, not_category=None, rect=None, cond=None):
        """
            category: Single category or a list of categories from which the 
                results must belong to at least one. If None, all categories
                are allowed.
            
            not_category: Single category or a list of categories from which
                the results may not belong. Overpowers the category parameter.
            
            rect: if given, all returned entities must intersect this rect.
            
            cond: boolean lambda. if given, results must satisfy the condition.
                      
        """
        res_set = set()

        if not_category is None:
            not_category = []

        # listify single elements
        if isinstance(not_category, str):
            not_category = [not_category]

        if category is not None and isinstance(category, str):
            category = [category]

        if category is None:
            to_test = self.all_stuff
        else:
            to_test = set()
            for cat in category:
                validate_category(cat)
                if self.has_category(cat):
                    for x in self.categories[cat]:
                        to_test.add(x)

        for e in to_test:
            accept = True
            for not_cat in not_category:
                validate_category(not_cat)
                if e.is_(not_cat):
                    accept = False
            accept = accept and (rect is None or e.get_rect().colliderect(rect))
            accept = accept and (cond is None or cond(e))
            if accept:
                res_set.add(e)

        return list(res_set)

    def all_categories(self):
        return self.categories.keys()

    def __contains__(self, key):
        return key in self.all_stuff  # TODO ehh

    def __len__(self):
        return len(self.all_stuff)

    def __iter__(self):
        return iter(self.all_stuff)

    def get_debug_string(self):
        lines = ["EntityCollection: " + self.name_for_debug,
                 "\tsize = " + str(len(self)) + ", categories = " + str(self.categories.keys()),
                 "\tall_stuff: " + str(self.all_stuff)]
        for category in self.categories:
            lines.append("\t" + category + ": " + str([x for x in self.categories[category]]))
        return "\n".join(lines)


_INVALIDS = set()
_VALID_CATEGORIES = {"ground", "actor", "enemy", "decoration", "terminal", "puzzle_terminal",
                     "health_machine", "wall", "overlay", "player", "interactable", "light_source",
                     "level_door", "door", "zone", "instakill", "spawner", "reference"}


def validate_category(category):
    if category not in _VALID_CATEGORIES and category not in _INVALIDS:
        print("WARN\tinvalid category: ", category)
        _INVALIDS.add(category)


