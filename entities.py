import pygame
import random
import math

import cool_math
import images
import global_state


class Entity:
    def __init__(self, x, y, w, h):
        self.is_alive = True
        self.x = x  # floating point
        self.y = y  # floating point
        self.vel = [0, 0]
        self.rect = pygame.Rect(x, y, w, h)
        self.weight = 1
        self.categories = set()
        self.ref_id = None  # used by the level loader to mark entity as 'special'

    def draw(self, screen, offset=(0, 0), modifier=None):
        modifier = self.sprite_modifier() if modifier is None else modifier
        sprite = self.sprite()
        dest_rect = self.get_rect().move(*offset)
        if sprite is not None:
            dest_rect.move_ip(*self.sprite_offset())
            images.draw_animated_sprite(screen, dest_rect, sprite, modifier)
        else:
            pygame.draw.rect(screen, images.RAINBOW, dest_rect, 0)

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

    def interact(self):
        pass

    def is_decoration(self):
        return self.is_("decoration")

    def is_light_source(self):
        return self.is_("light_source")

    def __repr__(self):
        pos = "(%s, %s)" % (self.rect.x, self.rect.y)
        return type(self).__name__ + pos


class Actor(Entity):
    gravity = 1.5

    def __init__(self, x, y, w, h):
        Entity.__init__(self, x, y, w, h)
        self.categories.update(["actor"])
        self.has_gravity = True
        self.is_grounded = False
        self.is_left_walled = False
        self.is_right_walled = False
        self.facing_right = True
        self.max_speed = (10, 20)
        self.jump_height = 64 + 32
        self.max_health = 50
        self.health = 50

        self.vel = [0, 0]

    def sprite_modifier(self):
        return "normal" if self.facing_right else "flipped"

    def get_jump_speed(self):
        a = Actor.gravity
        return -math.sqrt(2 * a * self.jump_height)

    def apply_physics(self):
        self.set_x(self.x + self.vel[0])
        self.set_y(self.y + self.vel[1])

    def apply_gravity(self):
        if self.has_gravity:
            if not self.is_grounded:
                self.vel[1] += Actor.gravity
                self.vel[1] = min(self.vel[1], self.max_speed[1])

    def set_vel_x(self, vx):
        self.vel[0] = vx

    def set_vel_y(self, vy):
        self.vel[1] = vy

    def _update_status_tags(self, world, input_state):
        self.is_grounded = world.is_touching_wall(self, (0, 1))
        self.is_left_walled = world.is_touching_wall(self, (-1, 0))
        self.is_right_walled = world.is_touching_wall(self, (1, 0))
        if self.vel[0] > 0 or (not self.is_grounded and self.is_left_walled):
            self.facing_right = True
        if self.vel[0] < 0 or (not self.is_grounded and self.is_right_walled):
            self.facing_right = False

    def deal_damage(self, damage, direction=None):
        self.health -= damage
        print(self, " was damaged by ", damage)


class Player(Actor):
    def __init__(self, x, y):
        self.full_height = 48
        self.crouch_height = 32
        Actor.__init__(self, x, y, 16, self.full_height)
        self.categories.update(["player"])
        self.speed = 5
        self.crouch_speed = 2.5

        self.max_slide_speed = 1.5

        self.shoot_cooldown = 0
        self.shoot_max_cooldown = 15
        self.active_bullet = None  # rect where bullet is

        self.interact_radius = 32
        self.is_crouching = False

    def sprite(self):
        if self._is_shooting():
            frm = (self.shoot_max_cooldown - self.shoot_cooldown) // 5  # lol
            anim = images.PLAYER_GUN
            return anim.single_frame(frm)
        elif self.is_grounded:
            if self.is_crouching:
                if abs(self.vel[0]) > 0.5:
                    return images.PLAYER_CROUCH_WALK
                else:
                    return images.PLAYER_CROUCH
            else:
                if abs(self.vel[0]) > 1:
                    return images.PLAYER_RUN
                else:
                    return images.PLAYER_IDLE
        elif self.is_left_walled or self.is_right_walled:
            return images.PLAYER_WALLSLIDE
        else:
            return images.PLAYER_AIR

    def sprite_offset(self):
        spr = self.sprite()
        w = self.get_rect().width
        h = self.get_rect().height
        res = [(w - spr.width()) / 2, (h - spr.height()) / 2 - (64 - h) / 2]
        if spr is images.PLAYER_WALLSLIDE:
            sign = 1 if self.facing_right else -1
            res[0] = res[0] + sign * 12
        if self.is_crouching:
            # res[1] -= 8
            pass

        return res

    def draw(self, screen, offset=(0, 0), modifier=None):
        if self.active_bullet is not None:
            bullet_pos = self.active_bullet.move(offset[0], offset[1])
            pygame.draw.rect(screen, (255, 255, 255), bullet_pos, 0)
        Actor.draw(self, screen, offset, modifier)

    def update(self, input_state, world):
        self._update_status_tags(world, input_state)

        h = self.height()
        expected_h = self.crouch_height if self.is_crouching else self.full_height
        if h != expected_h:
            y = self.xy()[1]
            self.set_h(expected_h)
            self.set_y(y + (h - expected_h))  # keep feet in same place

        self._handle_shooting(world)

        keyboard_x = 0
        if input_state.is_held(pygame.K_a):
            keyboard_x -= 1
        if input_state.is_held(pygame.K_d):
            keyboard_x += 1

        keyboard_jump = input_state.was_pressed(pygame.K_w) and not self._is_shooting()
        keyboard_shoot = input_state.was_pressed(pygame.K_j) and not self._is_shooting()
        keyboard_interact = input_state.was_pressed(pygame.K_k)

        if keyboard_x == 0 or self._is_shooting():
            fric = 1
            if not self.is_grounded:
                fric = 0.25
            self.vel[0] = cool_math.tend_towards(0, self.vel[0], fric)
        else:
            target_speed = self.speed if not self.is_crouching else self.crouch_speed
            target_speed *= keyboard_x
            if self.is_grounded and self.vel[0] * target_speed < 0:
                # turn around instantly when grounded
                self.vel[0] = 0
            else:
                self.vel[0] = cool_math.tend_towards(target_speed, self.vel[0], 1)

        if keyboard_jump:
            if self.is_grounded:
                self.vel[1] = self.get_jump_speed()
            elif self.is_left_walled:
                self.vel[1] = self.get_jump_speed()
                self.vel[0] = self.speed
            elif self.is_right_walled:
                self.vel[1] = self.get_jump_speed()
                self.vel[0] = -self.speed

        if keyboard_shoot and not keyboard_jump and self.is_grounded:
            self.shoot_cooldown = self.shoot_max_cooldown

        if keyboard_interact and not self._is_shooting():
            box = self.get_rect().inflate((self.interact_radius, 0))
            interactables = world.get_entities_in_rect(box, category="interactable")
            cntr = self.center()
            if len(interactables) > 0:
                interactables.sort(key=lambda x: cool_math.dist(cntr, x.center()))
                interactables[0].interact()

        if self.is_left_walled or self.is_right_walled:
            if self.vel[1] > self.max_slide_speed:
                self.vel[1] = cool_math.tend_towards(self.max_slide_speed, self.vel[1], 2)

        self.apply_gravity()
        self.apply_physics()

    def _update_status_tags(self, world, input_state):
        Actor._update_status_tags(self, world, input_state)

        was_crouching = self.is_crouching
        self.is_crouching = self.is_grounded and input_state.is_held(pygame.K_s)
        if was_crouching and self.is_grounded and not self.is_crouching:
            blocked_above = world.is_touching_wall(self, (0, -1))
            if blocked_above:
                self.is_crouching = True

    def _is_shooting(self):
        return self.shoot_cooldown > 0

    def _handle_shooting(self, world):
        if not self.is_grounded:
            self.shoot_cooldown = 0
        elif self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            if self.shoot_cooldown == 10:  # loll cmon
                rect = self.get_rect()
                bullet_y = rect.y + rect.height - 26 * 2
                bullet_w = 300
                bullet_x = rect.x + rect.width if self.facing_right else rect.x - bullet_w
                self.active_bullet = pygame.Rect(bullet_x, bullet_y, bullet_w, 4)
                bullet_hitbox = self.active_bullet.inflate(0, 8)
                direction = (1, 0) if self.facing_right else (-1, 0)
                for e in world.get_entities_in_rect(bullet_hitbox, category="enemy"):
                    e.deal_damage(10, direction)

        if self.shoot_cooldown < 8 or self.shoot_cooldown > 10:
            self.active_bullet = None


class Enemy(Actor):
    def __init__(self, x, y):
        Actor.__init__(self, x, y, 16, 48)
        self.categories.update(["enemy"])
        self.speed = 1.5 + random.random() / 2
        self.current_dir = (0, 0)
        self._randint = random.randint(0, 999)
        self.radius = 140  # starts chasing player within this distance
        self.forget_radius = 300  # stops chasing at this distance
        self.is_chasing = False

    sprites = [images.BLUE_GUY, images.PURPLE_GUY, images.BROWN_GUY]

    def sprite(self):
        return Enemy.sprites[self._randint % len(Enemy.sprites)]

    def sprite_offset(self):
        spr = self.sprite()
        w = self.get_rect().width
        h = self.get_rect().height
        return [(w - spr.width()) / 2, (h - spr.height()) / 2 - (64 - h) / 2]

    def draw(self, screen, offset=(0, 0), modifier=None):
        Entity.draw(self, screen, offset, modifier)
        if self.health < self.max_health:
            health_x = self.get_rect().x + offset[0]
            health_y = self.get_rect().y + self.sprite_offset()[1] - 6 + offset[1]
            health_width = self.get_rect().width
            health_rect = [health_x, health_y, health_width, 4]
            pygame.draw.rect(screen, (255, 50, 50), health_rect, 0)
            health_rect[2] = max(0, round(health_width * self.health / self.max_health))
            pygame.draw.rect(screen, (50, 255, 50), health_rect, 0)

    def update(self, input_state, world):
        self._update_status_tags(world, input_state)

        if self.health <= 0:
            self.is_alive = False
            return

        p = world.player()
        if p is not None:
            dist = cool_math.dist(self.center(), p.center())
            if dist <= self.radius:
                self.is_chasing = True
            elif dist > self.forget_radius:
                self.is_chasing = False

        if self.is_chasing and p is not None:
            direction = cool_math.sub(p.center(), self.center())
            direction = cool_math.normalize(direction)
            self.current_dir = direction
        else:
            # change directions approx every 30 ticks
            if random.random() < 1 / 30:
                if random.random() < 0.25:
                    self.current_dir = (0, 0)
                else:
                    self.current_dir = cool_math.rand_direction()
        self.set_vel_x(self.current_dir[0] * self.speed)
        self.apply_gravity()
        self.apply_physics()

    def touched_player(self, player, world):
        v = cool_math.sub(player.center(), self.center())
        v = cool_math.normalize(v)
        player.deal_damage(5, v)


class Wall(Entity):
    def __init__(self, x, y, w=32, h=32, sprite=images.WHITE_WALL):
        Entity.__init__(self, x, y, w, h)
        self._sprite = sprite
        self._cached_outline = None  # surface
        self._outline_dirty = True
        self.categories.update(["wall"])

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


class Spawner(Entity):
    def __init__(self, x, y, radius):
        Entity.__init__(self, x, y, 24, 24)
        self.radius = radius
        self.spawn_cooldown = 40
        self.current_cooldown = 0
        self.categories.update(["wall"])

    def sprite(self):
        if self.current_cooldown > 0:
            return images.SPAWNER_SKULL_OPEN
        else:
            return images.SPAWNER_SKULL

    def sprite_offset(self):
        if self.current_cooldown > 0:
            return (-4, -40)
        else:
            return (-4, -4)

    def update(self, input_state, world):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
        else:
            if random.random() < 1 / 30:
                self.do_spawn(world)

    def create_spawned(self):
        return Enemy(0, 0)

    def do_spawn(self, world):
        c = self.center()
        r = random.random() * self.radius
        angle = random.random() * 2 * math.pi
        rand_x = round(r * math.cos(angle) + c[0])
        rand_y = round(r * math.sin(angle) + c[1])
        spawned = self.create_spawned()
        spawned.set_center_x(rand_x)
        spawned.set_center_y(rand_y)

        if len(world.get_entities_in_rect(spawned.get_rect(), not_category="ground")) == 0:
            world.add_entity(spawned)
            sparkles = Overlay(images.SPAWN_SPARKLES, 40, rand_x, rand_y, target=spawned)
            world.add_entity(sparkles)

        self.current_cooldown = self.spawn_cooldown


class EnergyTank(Entity):
    def __init__(self, x, y, health):
        Entity.__init__(self, x, y, 24, 24)
        self.max_health = health
        self.health = health
        self.categories.update(["wall"])

    def sprite(self):
        return images.ENERGY_TANK

    def sprite_offset(self):
        return (-4, -40)


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
        self.open_max_cooldown = 20

    def sprite(self):
        if self.open_cooldown > 0:
            return images.DOOR_OPENING
        elif self.open_cooldown < 0:
            return images.DOOR_CLOSING
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

    def interact(self):
        if not self.locked:
            self.open_cooldown = self.open_max_cooldown
        else:
            global_state.hud.display_text("It's locked.")


class Terminal(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 32, 64)
        self.categories.update(["terminal", "interactable"])

    def update(self, input_state, world):
        pass

    def sprite(self):
        return images.TERMINAL

    def sprite_offset(self):
        return (0, 0)

    def draw(self, screen, offset=(0, 0), modifier=None):
        Entity.draw(self, screen, offset=offset, modifier=modifier)

        modifier = self.sprite_modifier() if modifier is None else modifier
        screen_sprite = images.TERMINAL_SCREEN
        dest_rect = self.get_rect().move(*offset)
        dest_rect.move_ip(3 * 2, 9 * 2)  # shift into screen area of sprite
        dest_rect.move_ip(*self.sprite_offset())
        images.draw_animated_sprite(screen, dest_rect, screen_sprite, modifier)

    def can_interact(self):
        return True

    def interact(self):
        print("interacted with terminal")
        global_state.hud.display_text("It's a computer terminal.")


class Overlay(Entity):
    def __init__(self, animation, lifespan, x, y, target=None):
        Entity.__init__(self, x, y, 32, 32)
        self.target = target
        self.animation = animation
        self.lifespan = lifespan

    def sprite(self):
        return self.animation

    def sprite_offset(self):
        return (0, -32)

    def update(self, input_state, world):
        if self.lifespan <= 0 or self.target is not None and not self.target.is_alive:
            self.is_alive = False
        else:
            self.lifespan -= 1
            if self.target is not None:
                pos = self.target.center()
                self.set_center_x(pos[0])
                self.set_center_y(pos[1])


class Decoration(Entity):
    """Just a noninteractive piece of art basically."""

    def __init__(self, x, y, dec_id, animation):
        Entity.__init__(self, x, y, animation.width(), animation.height())
        self.animation = animation
        self.dec_id = dec_id
        self.categories.update(["decoration"])

    def get_dec_id(self):
        return self.dec_id

    def sprite(self):
        return self.animation

    def sprite_offset(self):
        return (0, 0)


class LightEmittingDecoration(Decoration):
    """A decoration that emits light. Should never move."""

    def __init__(self, x, y, dec_id, animation, luminosity, light_radius):
        Decoration.__init__(self, x, y, dec_id, animation)
        self._luminosity = luminosity  # brightness level from 0 to 255
        self.radius = light_radius  # radius in pixels
        self.categories.update(["light_source"])

    def light_profile(self):
        """returns: integers (x, y, luminosity, radius), or None if luminosity 
            or radius is zero
        """
        if self._luminosity > 0 and self.radius > 0:
            pos = self.center()
            return (pos[0], pos[1], self._luminosity, self.radius)
        else:
            return None


class Ladder(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 32)

    def sprite_offset(self):
        return (-4, 0)

    def sprite(self):
        return images.LADDER


class Ground(Decoration):
    all_sprites = [images.STONE_GROUND, images.SAND_GROUND,
                   images.GRASS_GROUND, images.PURPLE_GROUND]

    def __init__(self, x, y, ground_type):
        sprite = Ground.all_sprites[ground_type]
        Decoration.__init__(self, x, y, sprite.get_id(), sprite)
        self.categories.update(["ground"])


def _safe_remove(item, collection, print_err=False):
    try:
        collection.remove(item)
    except ValueError:
        if print_err:
            print("cannot remove ", item, ", probably because it's not in the collection")


class EntityCollection:
    def __init__(self, entities=()):
        self.all_stuff = []
        self.category_tests = {}    # category_name -> lambda(entity->bool)
        self.categories = {}        # category_name -> set of entities
        self.add_category("actor", lambda x: x.is_actor())
        self.add_category("enemy", lambda x: x.is_enemy())
        self.add_category("player", lambda x: x.is_player())
        self.add_category("ground", lambda x: x.is_ground())
        self.add_category("door", lambda x: x.is_door())
        self.add_category("interactable", lambda x: x.is_interactable())
        self.add_category("wall", lambda x: x.is_wall())
        self.add_category("decoration", lambda x: x.is_decoration())
        self.add_category("light_source", lambda x: x.is_light_source())

        for e in entities:
            self.add(e)

    def add_category(self, name, test):
        if name in self.categories:
            print("Warning: Attempted to add category twice: ", name)
        else:
            self.category_tests[name] = test
            self.categories[name] = set()

    def add(self, entity):
        self.all_stuff.append(entity)
        cats = self._get_categories(entity)
        for catkey in cats:
            self.categories[catkey].add(entity)

    def remove(self, entity):
        _safe_remove(entity, self.all_stuff, True)
        cats = self._get_categories(entity)
        for catkey in cats:
            _safe_remove(entity, self.categories[catkey])

    def get_all(self, category=None, not_category=None, rect=None, cond=None):
        """
            category: Single category or a list of categories from which the 
                results must belong. If null, all categories are allowed.
            
            not_category: Single category or a list of categories from which
                the results may not belong. Overpowers the category parameter.
            
            rect: if given, all returned entities must intersect this rect.
            
            cond: boolean lambda. if given, entities must satisfy the condition.   
                      
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
                for x in self.categories[cat]:
                    to_test.add(x)

        for e in to_test:
            accept = True
            for not_cat in not_category:
                if self.category_tests[not_cat](e):
                    accept = False
                    break
            accept = accept and (rect is None or e.get_rect().colliderect(rect))
            accept = accept and (cond is None or cond(e))
            if accept:
                res_set.add(e)

        return list(res_set)

    def all_categories(self):
        return self.categories.keys()

    def _get_categories(self, entity):
        return [x for x in self.categories if self.category_tests[x](entity)]

    def __contains__(self, key):
        return key in self.all_stuff  # TODO ehh

    def __len__(self):
        return len(self.all_stuff)

    def __iter__(self):
        return iter(self.all_stuff)
