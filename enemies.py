import random
import math

import pygame

import actors
import cool_math
import global_state
import images
import entities


class Enemy(actors.Actor):
    def __init__(self, w, h):
        actors.Actor.__init__(self, w, h)
        self.categories.update(["enemy"])
        self.speed = 0.75 + random.random()/2
        self.current_dir = [0, 0]
        self.max_health = 4  # four hearts
        self.health = 4

    def sprite(self):
        return None

    def sprite_offset(self):
        spr = self.sprite()
        w = self.get_rect().width
        h = self.get_rect().height
        return [(w - spr.width()) / 2, (h - spr.height()) / 2 - (64 - h) / 2]

    def _update_status_tags(self, world, input_state):
        actors.Actor._update_status_tags(self, world, input_state)
        if self.vel[0] < 0:
            self.facing_right = False
        if self.vel[1] > 0:
            self.facing_right = True

    def draw(self, screen, offset=(0, 0), modifier=None):
        entities.Entity.draw(self, screen, offset=offset, modifier=modifier)
        if self.health < self.max_health and global_state.show_enemy_health:
            health_x = self.get_rect().x + offset[0]
            health_y = self.get_rect().y + self.sprite_offset()[1] - 6 + offset[1]
            health_width = self.get_rect().width
            health_rect = [health_x, health_y, health_width, 4]
            pygame.draw.rect(screen, (255, 50, 50), health_rect, 0)
            health_rect[2] = max(0, round(health_width * self.health / self.max_health))
            pygame.draw.rect(screen, (50, 255, 50), health_rect, 0)

    def update(self, input_state, world):
        actors.Actor.update(self, input_state, world)

        self.do_ai_behavior(input_state, world)

        self.update_vel()
        self.apply_gravity()
        self.apply_physics()

    def do_ai_behavior(self, input_state, world):
        self.vel[0] = self.current_dir[0] * self.speed
        self.vel[1] = self.current_dir[1] * self.speed

    def update_vel(self):
        new_vel_x = cool_math.tend_towards(self.current_dir[0] * self.speed, self.vel[0], 0.3)
        self.set_vel_x(new_vel_x)

        if not self.has_gravity:
            new_vel_y = cool_math.tend_towards(self.current_dir[1] * self.speed, self.vel[1], 0.3)
            self.set_vel_y(new_vel_y)

    def touched_player(self, player, world):
        v = cool_math.sub(player.center(), self.center())
        v = cool_math.normalize(v)
        player.deal_damage(1, source=self, direction=v)

    def get_hurtbox(self):
        return self.get_rect().copy()

    def deal_damage(self, damage, source=None, direction=None):
        actors.Actor.deal_damage(self, damage, source=source, direction=direction)

        if direction is not None:
            x_dir = 1 if direction[0] > 0 else -1
            y_dir = -0.75
            self.knock_back(3, (x_dir, y_dir))

    def set_direction(self, x, y):
        self.current_dir[0] = x
        self.current_dir[1] = y

    def with_dir(self, x, y):
        self.set_direction(x, y)
        return self


class DumbEnemy(Enemy):
    def __init__(self):
        Enemy.__init__(self, 16, 48)
        self._reverse_countdown = 0

    def sprite(self):
        return images.PURPLE_GUY

    def death_sprite(self, cause=None):
        return images.PURPLE_GUY_DYING

    def do_ai_behavior(self, input_state, world):
        dir_x = self.current_dir[0]
        if dir_x != 1 and dir_x != -1:
            dir_x = -1
            self.set_direction(dir_x, 0)

        if (dir_x < 0 and self.is_left_walled) or (dir_x > 0 and self.is_right_walled):
            self.set_direction(-dir_x, 0)
            self._reverse_countdown = 20

        if self._reverse_countdown <= 0:
            if len(world.get_entities_in_rect(self.get_rect(), category="reverse", limit=1)) > 0:
                self.set_direction(-dir_x, 0)
                self._reverse_countdown = 20
        else:
            self._reverse_countdown -= 1


class SmartEnemy(Enemy):
    """chases player"""

    def __init__(self, w, h):
        Enemy.__init__(self, w, h)
        self.radius = 140  # starts chasing player within this distance
        self.forget_radius = 300  # stops chasing at this distance
        self.is_chasing = False
        self.start_chasing_time = 0
        self.forget_time = 240

    def do_ai_behavior(self, input_state, world):
        p = world.player()
        if p is not None:
            dist = cool_math.dist(self.center(), p.center())
            if dist <= self.radius:
                self.start_chasing()  # it's ok to call this every frame
            elif dist > self.forget_radius:
                follow_time = global_state.tick_counter - self.start_chasing_time
                if follow_time >= self.forget_time:
                    self.is_chasing = False

        if self.is_chasing and p is not None:
            self.do_chase_behavior(world)
        else:
            self.do_non_chase_behavior(world)

    def do_chase_behavior(self, world):
        p = world.player()
        if p is None:
            return
        direction = cool_math.sub(p.center(), self.center())
        direction = cool_math.normalize(direction)
        self.set_direction(direction[0], direction[1])

    def do_non_chase_behavior(self, world):
        # change directions approx every 30 ticks
        if random.random() < 1 / 60:
            if random.random() < 0.25:
                self.set_direction(0, 0)
            else:
                rand_direct = cool_math.rand_direction()
                self.set_direction(rand_direct[0], rand_direct[1])

    def start_chasing(self):
        self.start_chasing_time = global_state.tick_counter
        self.is_chasing = True

    def deal_damage(self, damage, source=None, direction=None):
        Enemy.deal_damage(self, damage, source=source, direction=direction)
        self.start_chasing()


class Zombie(SmartEnemy):
    def __init__(self):
        SmartEnemy.__init__(self, 16, 48)
        self.health = 3

    def sprite(self):
        return images.BROWN_GUY

    def death_sprite(self, cause=None):
        return images.BROWN_GUY_DYING

    def on_death(self, world):
        Enemy.on_death(self, world)

        pos = self.center()

        flappy_left = FlappyEnemy()
        flappy_left.set_direction(-1, 0)
        flappy_left.set_center(pos[0], pos[1])
        world.add_entity(flappy_left)

        flappy_right = FlappyEnemy()
        flappy_right.set_center(pos[0], pos[1])
        flappy_right.set_direction(1, 0)
        world.add_entity(flappy_right)


class FlappyEnemy(Enemy):
    def __init__(self):
        Enemy.__init__(self, 16, 24)
        self.has_gravity = False
        self.speed = 1
        self.health = 1
        self.current_dir[0] = -1
        self.is_falling = False
        self.fall_timer = 0
        self.bob_offset = random.random() * 6.28

    def sprite(self):
        return images.FLAPPY_GUY

    def sprite_offset(self):
        spr = self.sprite()
        w = self.get_rect().width
        h = self.get_rect().height
        return [(w - spr.width()) / 2, (h - spr.height()) / 2]

    def death_sprite(self, cause=None):
        return images.FLAPPY_GUY_DYING

    def do_ai_behavior(self, input_state, world):
        if self.current_dir[0] <= 0 and self.is_left_walled:
            self.current_dir[0] = 1
        elif self.current_dir[1] >= 0 and self.is_right_walled:
            self.current_dir[0] = -1

        if self.is_falling:
            self.fall_timer += 1
            if self.is_grounded or self.fall_timer >= 45:
                self.is_falling = False
                self.fall_timer = 0
        else:
            val = math.cos(global_state.tick_counter / 60.0 + self.bob_offset)
            vel_y = -1 if val < -0.65 else 0 if val < 0.65 else 1
            self.vel[1] = cool_math.tend_towards(vel_y, self.vel[1], 0.1)

        self.has_gravity = self.is_falling

    def deal_damage(self, damage, source=None, direction=None):
        Enemy.deal_damage(self, damage, source=source, direction=direction)
        self.is_falling = True


class Skorg(SmartEnemy):
    def __init__(self):
        SmartEnemy.__init__(self, 48, 48)

    def sprite(self):
        return images.SKORG

    def death_sprite(self, cause=None):
        return images.SKORG_DYING


class DodgeEnemy(SmartEnemy):
    def __init__(self):
        SmartEnemy.__init__(self, 16, 48)
        self.is_up = True
        self.time_since_last_swap = 0

    def sprite(self):
        if self.is_up:
            return images.BLUE_GUY_UP
        else:
            return images.BLUE_GUY_DOWN

    def death_sprite(self, cause=None):
        return images.BLUE_GUY_DYING

    def update(self, input_state, world):
        Enemy.update(self, input_state, world)
        self.time_since_last_swap += 1

        # 0-30 = 0%, 31-150 = 1%-25%, 151+ = 25%
        swap_chance = min((max(0, self.time_since_last_swap-30) / 240), 1) * 0.25
        if random.random() < swap_chance:
            self.is_up = not self.is_up
            self.time_since_last_swap = 0

    def get_hurtbox(self):
        r = self.get_rect()
        if self.is_up:
            return [r[0], r[1], r[2], int(r[3]/2)]
        else:
            return [r[0], r[1]+int(r[3]/2), r[2], int(r[3]/2)]


class SpikyEnemy(Enemy):
    def __init__(self):
        Enemy.__init__(self, 32, 32)
        self.speed = 0.75
        self.health = 2
        self._reverse_countdown = 0
        self.is_top_walled = False
        self.has_gravity = False

    def sprite(self):
        return images.SPIKY_GUY

    def sprite_offset(self):
        return (0, 0)

    def death_sprite(self, cause=None):
        return images.SPIKY_GUY_DYING

    def _update_status_tags(self, world, input_state):
        Enemy._update_status_tags(self, world, input_state)
        up_sliver = cool_math.sliver_adjacent(self.get_rect(), (0, -1), 2)
        self.is_top_walled = len(world.get_entities_in_rect(up_sliver, category="wall", limit=1)) > 0

    def do_ai_behavior(self, input_state, world):
        if self._reverse_countdown > 0:
            self._reverse_countdown -= 1
        else:
            x_dir = self.current_dir[0]
            y_dir = self.current_dir[1]

            did_reverse = False
            if (x_dir < 0 and self.is_left_walled) or (x_dir > 0 and self.is_right_walled):
                x_dir = -x_dir
                did_reverse = True

            if (y_dir < 0 and self.is_top_walled) or (y_dir > 0 and self.is_grounded):
                y_dir = -y_dir
                did_reverse = True

            if not did_reverse and len(world.get_entities_in_rect(self.get_rect(), category="reverse", limit=1)) > 0:
                x_dir = -x_dir  # ideally one of these directions would be zero
                y_dir = -y_dir
                did_reverse = True

            if did_reverse:
                self._reverse_countdown = 20
                self.set_direction(x_dir, y_dir)

    def touched_player(self, player, world):
        v = cool_math.sub(player.center(), self.center())
        v = cool_math.normalize(v)
        player.deal_damage(10, source=self, direction=v)  # basically an insta-kill


class StickyEnemy(Enemy):
    def __init__(self, clockwise=True):
        Enemy.__init__(self, 24, 24)
        self.clockwise = clockwise
        self.speed = 0.75
        self.health = 2
        self.set_direction(1, 0)
        self.is_top_walled = False
        self.just_snapped = False

    def sprite_offset(self):
        spr = self.sprite()
        sign = 1 if self.clockwise else 1
        orientation = self.get_orientation()
        x_offs = -orientation[0] * 4 * sign
        y_offs = -orientation[1] * 4 * sign
        return (int(self.width()/2 - spr.width()/2) + x_offs, int(self.height()/2 - spr.height()/2) + y_offs)

    _slug_sprites = (images.ACID_SLUG_U_L, images.ACID_SLUG_D_L, images.ACID_SLUG_L_L, images.ACID_SLUG_R_L,
                     images.ACID_SLUG_U_R, images.ACID_SLUG_D_R, images.ACID_SLUG_L_R, images.ACID_SLUG_R_R)

    def sprite(self):
        num = 4 if self.clockwise else 0
        orientation = self.get_orientation()
        if orientation[0] != 0:
            num += 2
            num += 1 if orientation[0] > 0 else 0
        else:
            num += 1 if orientation[1] > 0 else 0
        return StickyEnemy._slug_sprites[num]

    def sprite_modifier(self):
        return "normal"  # never flipped because of all the special case stuff

    def death_sprite(self, cause=None):
        orientation = self.get_orientation()
        if orientation[0] != 0:
            return images.SLUG_DYING_L if orientation[0] < 0 else images.SLUG_DYING_R
        else:
            return images.SLUG_DYING_U if orientation[1] < 0 else images.SLUG_DYING_D

    def deal_damage(self, damage, source=None, direction=None):
        if source is not None:
            if source.is_player():
                self.clockwise = not self.clockwise
                self.set_direction(0, 0)
            elif isinstance(source, entities.KillBlock):
                return  # unaffected by kill blocks
        Enemy.deal_damage(self, damage, source=source, direction=direction)

    def set_direction(self, x, y):
        if (x == 0 and (y == 1 or y == -1)) or (y == 0 and (x == 1 or x == -1)):
            self.current_dir[0] = x
            self.current_dir[1] = y
        else:
            self.current_dir[0] = 0
            self.current_dir[1] = 0

    def get_orientation(self):
        cd = self.current_dir
        if cd[0] == 0 and cd[1] == 0:
            return (0, 1)  # falls upside down, for cuteness
        else:
            if self.clockwise:
                return (cd[1], -cd[0])  # 90 degree rotation matrices
            else:
                return (-cd[1], cd[0])

    def _update_status_tags(self, world, input_state):
        Enemy._update_status_tags(self, world, input_state)
        up_sliver = cool_math.sliver_adjacent(self.get_rect(), (0, -1), 2)
        self.is_top_walled = len(world.get_entities_in_rect(up_sliver, category="wall", limit=1)) > 0

    def update(self, input_state, world):
        actors.Actor.update(self, input_state, world)

        self.do_ai_behavior(input_state, world)

        if self.has_gravity:
            self.apply_gravity()
            self.apply_physics()
        else:
            self.apply_physics()

            self._update_status_tags(world, input_state)
            post_left = self.is_left_walled
            post_right = self.is_right_walled
            post_up = self.is_top_walled
            post_down = self.is_grounded

            if not (post_left or post_right or post_down or post_up):
                # gotta wrap now
                rect = self.get_rect()
                search_rect = rect.inflate(self.speed + 4, self.speed + 4)
                walls_nearby = world.get_entities_in_rect(search_rect, category="wall")
                if len(walls_nearby) > 0:
                    rects_nearby = list(map(lambda x: x.get_rect(), walls_nearby))
                    snaps = map(lambda x: cool_math.corner_snap_rects(rect, x, outside=True), rects_nearby)
                    my_center = self.center()
                    best_snap = cool_math.closest_rect_by_center(my_center, snaps)

                    # snap onto surface, and update direction
                    self.set_xy(best_snap[0], best_snap[1])
                    cd = self.current_dir
                    if cd[0] == -1:
                        self.set_direction(0, -1 if self.clockwise else 1)
                    elif cd[0] == 1:
                        self.set_direction(0, 1 if self.clockwise else -1)
                    elif cd[1] == -1:
                        self.set_direction(1 if self.clockwise else -1, 0)
                    elif cd[1] == 1:
                        self.set_direction(-1 if self.clockwise else 1, 0)

                    self.set_x(self.get_x() + self.current_dir[0] * 4)  # move a bit onto the next edge
                    self.set_y(self.get_y() + self.current_dir[1] * 4)

    def do_ai_behavior(self, input_state, world):
        up = self.is_top_walled
        left = self.is_left_walled
        right = self.is_right_walled
        down = self.is_grounded

        if not (up or left or right or down):
            self.set_direction(0, 0)
            self.has_gravity = True
            return

        cd = self.current_dir

        if cd[0] == 0 and cd[1] == 0:
            self.has_gravity = True  # just in case, we don't want to float
            if down:
                self.set_direction(1 if self.clockwise else -1, 0)
                self.has_gravity = False
            return

        self.has_gravity = False

        if cd[0] == -1:
            if left:
                self.set_direction(0, 1 if self.clockwise else -1)
        elif cd[0] == 1:
            if right:
                self.set_direction(0, -1 if self.clockwise else 1)
        elif cd[1] == -1:
            if up:
                self.set_direction(-1 if self.clockwise else 1, 0)
        elif cd[1] == 1:
            if down:
                self.set_direction(1 if self.clockwise else -1, 0)

        if not self.has_gravity:
            self.vel[0] = self.current_dir[0] * self.speed
            self.vel[1] = self.current_dir[1] * self.speed
