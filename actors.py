import math

import pygame

import cool_math
import global_state
import images
import sounds
from entities import Entity, Overlay
import inputs


class Actor(Entity):
    gravity = 0.65

    def __init__(self, w, h):
        Entity.__init__(self, w, h)
        self.categories.update(["actor"])
        self.has_gravity = True
        self.is_grounded = False
        self.is_left_walled = False
        self.is_right_walled = False
        self.facing_right = True
        self.max_speed = (5, 10)
        self.jump_height = 64 + 32

        self.max_health = 8  # four hearts
        self.health = 8

        self.vel = [0, 0]

    def sprite_modifier(self):
        return "normal" if self.facing_right else "flipped"

    def death_sprite(self, cause=None):
        return None

    def get_jump_speed(self):
        a = Actor.gravity
        return -math.sqrt(2 * a * self.jump_height)

    def update(self, input_state, world):
        self._update_status_tags(world, input_state)

        if self.health <= 0:
            self.is_alive = False
            self.on_death(world)

    def on_death(self, world):
        death_spr = self.death_sprite()
        if death_spr is not None:
            death_overlay = Overlay(death_spr)
            death_overlay.set_center_x(self.center()[0])
            death_overlay.set_y(self.get_y() + self.height() - death_spr.height())
            death_overlay.with_lifespan(cycles=1)
            world.add_entity(death_overlay)

    def apply_physics(self):
        self.shift_x(self.vel[0])
        self.shift_y(self.vel[1])

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
        self.is_grounded = world.is_touching(self, "solid", (0, 1), cond=lambda x: x.blocks_movement(self))
        self.is_left_walled = world.is_touching(self, "wall", (-1, 0))
        self.is_right_walled = world.is_touching(self, "wall", (1, 0))

        if self.vel[0] > 0.75 or (not self.is_grounded and self.is_left_walled):
            self.facing_right = True

        if self.vel[0] < -0.75 or (not self.is_grounded and self.is_right_walled):
            self.facing_right = False

    def deal_damage(self, damage, source=None, direction=None):
        self.health -= damage

    def knock_back(self, speed, direction):
        vect = cool_math.set_length(direction, speed)
        self.set_vel_x(vect[0])
        self.set_vel_y(vect[1])


class Player(Actor):
    def __init__(self):
        self.full_height = 48
        self.crouch_height = 32
        Actor.__init__(self, 16, self.full_height)
        self.categories.update(["player"])
        self.speed = 4
        self.crouch_speed = 1.25
        self.max_slide_speed = 1

        self.move_accel = 0.5

        self.shoot_cooldown = 0
        self.shoot_max_cooldown = 30
        self.shoot_on_frame = 20
        self.active_bullet = None  # rect where bullet is

        self.interact_radius = 32
        self.is_crouching = False

        self.post_dmg_invincibility_max_cooldown = 45
        self.post_dmg_invincibility_cooldown = 0
        self.flying_uncontrollably = False
        self.flying_uncontrollably_time = 0
        self.flying_uncontrollably_max_time = 500  # just to be safe, i don't want to softlock the game

        self.hover_overhead_text = None

    def sprite(self):
        if self._is_shooting():
            anim = images.PLAYER_GUN if not self.is_crouching else images.PLAYER_CROUCH_SHOOT
            num_frms = images.PLAYER_GUN.num_frames()
            numerator = self.shoot_max_cooldown - self.shoot_cooldown
            denominator = self.shoot_max_cooldown / num_frms
            frm = int(numerator / denominator)
            return anim.single_frame(frm)
        elif self.is_grounded:
            if self.is_crouching:
                if abs(self.vel[0]) > 0.25:
                    return images.PLAYER_CROUCH_WALK
                else:
                    return images.PLAYER_CROUCH
            else:
                if abs(self.vel[0]) > 0.5:
                    return images.PLAYER_RUN
                else:
                    return images.PLAYER_IDLE
        elif self.is_left_walled or self.is_right_walled:
            return images.PLAYER_WALLSLIDE
        else:
            return images.PLAYER_AIR

    def death_sprite(self, cause=None):
        return images.PLAYER_DYING

    def sprite_modifier(self):
        return Actor.sprite_modifier(self)

    def sprite_offset(self):
        spr = self.sprite()
        w = self.get_rect().width
        h = self.get_rect().height
        res = [(w - spr.width()) / 2, (h - spr.height()) / 2 - (64 - h) / 2]
        if spr is images.PLAYER_WALLSLIDE:
            sign = 1 if self.facing_right else -1
            res[0] = res[0] + sign * 12

        return res

    def draw(self, screen, offset=(0, 0), modifier=None):
        if self.active_bullet is not None:
            bullet_pos = self.active_bullet.move(offset[0], offset[1])
            pygame.draw.rect(screen, (255, 255, 255), bullet_pos, 0)

        Actor.draw(self, screen, offset, modifier)

    def update(self, input_state, world):
        Actor.update(self, input_state, world)

        if self.post_dmg_invincibility_cooldown > 0:
            self.post_dmg_invincibility_cooldown -= 1

        if self.flying_uncontrollably:
            on_ground = self.is_grounded or self.is_left_walled or self.is_right_walled
            if on_ground and self.flying_uncontrollably_time > 15:
                self.flying_uncontrollably = False
            elif self.flying_uncontrollably_time > self.flying_uncontrollably_max_time:
                print("WARN\tPlayer was uncontrollable for max duration, had to break forcefully")
                self.flying_uncontrollably = False
            else:
                self.flying_uncontrollably_time += 1

        h = self.height()
        expected_h = self.crouch_height if self.is_crouching else self.full_height
        if h != expected_h:
            y = self.xy()[1]
            self.set_h(expected_h)
            self.set_y(y + (h - expected_h))  # keep feet in same place

        self._handle_shooting(world)

        keyboard_x = 0
        keyboard_jump = False
        keyboard_shoot = False
        keyboard_interact = False

        if self._has_control_of_character():
            if input_state.is_held(inputs.LEFT):
                keyboard_x -= 1
            if input_state.is_held(inputs.RIGHT):
                keyboard_x += 1

            keyboard_jump = input_state.was_pressed(inputs.JUMP) and not self._is_shooting()
            keyboard_shoot = input_state.was_pressed(inputs.SHOOT) and not self._is_shooting()
            keyboard_interact = input_state.was_pressed(inputs.INTERACT)

        if keyboard_x == 0:
            fric = 1
            if not self.is_grounded:
                fric = 0.125
            self.vel[0] = cool_math.tend_towards(0, self.vel[0], fric)
        else:
            target_speed = self.speed if not self.is_crouching else self.crouch_speed
            target_speed *= keyboard_x
            if self.is_grounded and self.vel[0] * target_speed < 0:
                # turn around instantly when grounded
                self.vel[0] = 0
            else:
                self.vel[0] = cool_math.tend_towards(target_speed, self.vel[0], self.move_accel)

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

        if self._has_control_of_character():
            box = self.get_rect().inflate((self.interact_radius, 0))
            interactables = world.get_entities_in_rect(box, category="interactable")
            cntr = self.center()
            if len(interactables) > 0:
                interactables.sort(key=lambda x: cool_math.dist(cntr, x.center()))
                if keyboard_interact:
                    interactables[0].interact(world)
                else:
                    # TODO - plop down "press k" Overlay
                    pass

        if self.is_left_walled or self.is_right_walled:
            if self.vel[1] > self.max_slide_speed:
                self.vel[1] = cool_math.tend_towards(self.max_slide_speed, self.vel[1], 1)

        self.apply_gravity()
        self.apply_physics()

    def _update_status_tags(self, world, input_state):
        Actor._update_status_tags(self, world, input_state)

        # if finishing shooting animation, maintain crouchedness
        if self._has_control_of_character() or self.shoot_cooldown > self.shoot_on_frame:
            will_be_crouching = self.is_grounded and input_state.is_held(inputs.CROUCH)
            if self.is_crouching and self.is_grounded and not will_be_crouching:
                crouch_height_diff = self.full_height - self.crouch_height
                blocked_above = world.is_touching(self, "wall", (0, -1), dist=crouch_height_diff)
                if blocked_above:
                    will_be_crouching = True
            self.is_crouching = will_be_crouching

    def deal_damage(self, damage, source=None, direction=None):
        if not self._is_invincible():
            Actor.deal_damage(self, damage, source=source, direction=direction)
            self.post_dmg_invincibility_cooldown = self.post_dmg_invincibility_max_cooldown

            if direction is not None:
                x_dir = 1 if direction[0] > 0 else -1
                y_dir = -0.75
                self.knock_back(7, (x_dir, y_dir))

                self.flying_uncontrollably = True
                self.flying_uncontrollably_time = 0

            sounds.play(sounds.PLAYER_DAMAGE)

        if self.health <= 0 and not global_state.allow_player_deaths:
            self.health = 1

    def _has_control_of_character(self):
        return not self.flying_uncontrollably and not self._is_shooting()

    def _is_invincible(self):
        return self.post_dmg_invincibility_cooldown > 0

    def _is_shooting(self):
        return self.shoot_cooldown > 0

    def _handle_shooting(self, world):
        if not self.is_grounded:
            self.shoot_cooldown = 0
        elif self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            if self.shoot_cooldown == self.shoot_on_frame:
                hit_entity = self._create_bullet(world)
                if hit_entity is not None:
                    if hit_entity.is_enemy():
                        direction = (1, 0) if self.facing_right else (-1, 0)
                        hit_entity.deal_damage(1, source=self, direction=direction)
                    elif hit_entity.is_wall():
                        hit_entity.bullet_hit()

                sounds.play(sounds.ENERGY_PULSE)

        if self.shoot_cooldown < self.shoot_on_frame - 4 or self.shoot_cooldown > self.shoot_on_frame:
            self.active_bullet = None

    def _create_bullet(self, world):
        rect = self.get_rect()
        crouching = 1 if self.is_crouching else 0
        bullet_y = rect.y + rect.height - 26*2 + 30*crouching
        bullet_w = int(global_state.WIDTH/2 + 64)
        bullet_x = rect.x + rect.width if self.facing_right else rect.x - bullet_w
        bullet_h = 4
        self.active_bullet = pygame.Rect(bullet_x, bullet_y, bullet_w, bullet_h)

        hitbox = self.active_bullet.inflate(0, 4)
        hitting_hurtbox = lambda x: hitbox.colliderect(x.get_hurtbox())
        colliders = world.get_entities_in_rect(hitbox, category="enemy", cond=hitting_hurtbox)
        colliders.extend(world.get_entities_in_rect(self.active_bullet, category="wall"))

        hit_entity = None
        if len(colliders) > 0:
            if self.facing_right:
                colliders.sort(key=lambda x: x.get_x())
                hit_entity = colliders[0]
                bullet_w = hit_entity.get_x() - bullet_x
                splash = Overlay(images.BULLET_SPLASH).with_lifespan(cycles=1)
                splash.set_x(bullet_x + bullet_w - splash.width())
            else:
                colliders.sort(key=lambda x: x.get_x() + x.width())
                hit_entity = colliders[-1]
                bullet_w = self.get_x() - (hit_entity.get_x() + hit_entity.width())
                bullet_x = hit_entity.get_x() + hit_entity.width()
                splash = Overlay(images.BULLET_SPLASH, modifier="flipped").with_lifespan(cycles=1)
                splash.set_x(bullet_x)

            splash.set_center_y(int(bullet_y + bullet_h / 2))
            world.add_entity(splash)
            self.active_bullet.x = bullet_x
            self.active_bullet.width = bullet_w

        return hit_entity
