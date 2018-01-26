import random

import pygame

import actors
import cool_math
import global_state
import images
import entities


class Enemy(actors.Actor):
    def __init__(self, x, y, w, h):
        actors.Actor.__init__(self, x, y, w, h)
        self.categories.update(["enemy"])
        self.speed = 0.75 + random.random()/2
        self.current_dir = (0, 0)
        self.max_health = 4  # four hearts
        self.health = 4

    def sprite(self):
        return None

    def sprite_offset(self):
        spr = self.sprite()
        w = self.get_rect().width
        h = self.get_rect().height
        return [(w - spr.width()) / 2, (h - spr.height()) / 2 - (64 - h) / 2]

    def draw(self, screen, offset=(0, 0), modifier=None):
        entities.Entity.draw(self, screen, offset, modifier)
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

        self.do_ai_behavior(input_state, world)

        self.apply_gravity()
        self.apply_physics()

    def do_ai_behavior(self, input_state, world):
        pass

    def touched_player(self, player, world):
        v = cool_math.sub(player.center(), self.center())
        v = cool_math.normalize(v)
        player.deal_damage(1, direction=v)

    def get_hurtbox(self):
        return self.get_rect()


class DumbEnemy(Enemy):
    def __init__(self, x, y):
        Enemy.__init__(self, x, y, 16, 48)

    def sprite(self):
        return images.PURPLE_GUY

    def do_ai_behavior(self, input_state, world):
        # change directions approx every second
        if random.random() < 1 / 60:
            if random.random() < 0.25:
                self.current_dir = (0, 0)
            else:
                self.current_dir = cool_math.rand_direction()
        new_vel = cool_math.tend_towards(self.current_dir[0] * self.speed, self.vel[0], 0.3)
        self.set_vel_x(new_vel)


class SmartEnemy(Enemy):
    """chases player"""

    def __init__(self, x, y):
        Enemy.__init__(self, x, y, 16, 48)
        self.radius = 140  # starts chasing player within this distance
        self.forget_radius = 300  # stops chasing at this distance
        self.is_chasing = False
        self.start_chasing_time = 0
        self.forget_time = 240

    def sprite(self):
        return images.BROWN_GUY

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
            direction = cool_math.sub(p.center(), self.center())
            direction = cool_math.normalize(direction)
            self.current_dir = direction
        else:
            # change directions approx every 30 ticks
            if random.random() < 1 / 60:
                if random.random() < 0.25:
                    self.current_dir = (0, 0)
                else:
                    self.current_dir = cool_math.rand_direction()
        new_vel = cool_math.tend_towards(self.current_dir[0] * self.speed, self.vel[0], 0.3)
        self.set_vel_x(new_vel)

    def start_chasing(self):
        self.start_chasing_time = global_state.tick_counter
        self.is_chasing = True

    def deal_damage(self, damage, direction=None):
        actors.Actor.deal_damage(self, damage, direction=direction)
        self.start_chasing()


class DodgeEnemy(SmartEnemy):
    def __init__(self, x, y):
        SmartEnemy.__init__(self, x, y)
        self.is_up = True
        self.time_since_last_swap = 0

    def sprite(self):
        if self.is_up:
            return images.BLUE_GUY_UP
        else:
            return images.BLUE_GUY_DOWN

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
