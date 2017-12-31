import pygame
import random
import math

import cool_math
import images

class Entity:
    def __init__(self, x, y, w, h):
        self.is_alive = True
        self.x = x # floating point
        self.y = y # floating point
        self.vel = [0, 0]
        self.rect = pygame.Rect(x, y, w, h)
        self.weight = 1
    
    def draw(self, screen, offset=(0,0), modifier=None):
        modifier = self.sprite_modifier() if modifier == None else modifier
        sprite = self.sprite()
        dest_rect = self.get_rect().move(*offset)
        if sprite != None:
            dest_rect.move_ip(*self.sprite_offset())
            images.draw_animated_sprite(screen, dest_rect, sprite, modifier)
        else:
            pygame.draw.rect(screen, images.rainbow, dest_rect, 0)
            
    def sprite_offset(self):
        return (0, 0)
        
    def sprite(self):
        return None
        
    def sprite_modifier(self):
        return "normal"
    
    def update(self, tick_counter, input_state, world):
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
        
    def set_xy(self, x, y):
        self.set_x(x)
        self.set_y(y)
        
    def set_center_x(self, x):
        self.set_x(x - self.get_rect().width/2)
        
    def set_center_y(self, y):
        self.set_y(y - self.get_rect().height/2)
        
    def set_center(self, x, y):
        self.set_center_x(x)
        self.set_center_y(y)
        
    def center(self):
        r = self.get_rect()
        return (int(r.x + r.width/2), int(r.y + r.height/2))   
        
    def is_wall(self):
        return False  
        
    def is_actor(self):
        return False
    
    def is_enemy(self):
        return False
        
    def is_player(self):
        return False
        
    def is_ground(self):
        return False
        
    def is_door(self):
        return False
        
    def is_interactable(self):
        return False
        
    def interact(self):
        pass
    
    def __repr__(self):
        pos = "(%s, %s)" % (self.rect.x, self.rect.y)
        return type(self).__name__ + pos
        
class Actor(Entity):
    gravity = 1.5
    def __init__(self, x, y, w, h):
        Entity.__init__(self, x, y, w, h)
        self.has_gravity = True
        self.is_grounded = False
        self.is_left_walled = False
        self.is_right_walled = False
        self.max_speed = (10, 20)
        self.jump_height = 64 + 32
        
        self.vel = [0, 0]
    
    def is_actor(self):
        return True
        
    def get_jump_speed(self):
        a = Actor.gravity
        return -math.sqrt(2*a*self.jump_height)
        
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
        
class Player(Actor):
    def __init__(self, x, y):
        Actor.__init__(self, x, y, 16, 48)
        self.speed = 5
        
        self.max_health = 50
        self.health = 50
        
        self.facing_right = True
        self.max_slide_speed = 1.5
        
        self.shoot_cooldown = 0
        self.shoot_max_cooldown = 15
        self.active_bullet = None # rect where bullet is
        
        self.interact_radius = 32
    
    def sprite(self):
        direction = self.facing_right
        if self._is_shooting():
            frm = (self.shoot_max_cooldown - self.shoot_cooldown) // 5 # lol
            anim = images.PLAYER_GUN if direction else images.PLAYER_GUN_LEFT
            return anim.single_frame(frm)
        elif self.is_grounded:
            if abs(self.vel[0]) > 1:
                return images.PLAYER_RUN if direction else images.PLAYER_RUN_LEFT
            else:
                return images.PLAYER_IDLE if direction else images.PLAYER_IDLE_LEFT
        elif self.is_left_walled or self.is_right_walled:
            return images.PLAYER_WALLSLIDE if direction else images.PLAYER_WALLSLIDE_LEFT
        else:
            return images.PLAYER_AIR if direction else images.PLAYER_AIR_LEFT
        
    def sprite_offset(self):
        spr = self.sprite()
        w = self.get_rect().width
        h = self.get_rect().height
        res = [(w - spr.width())/2, (h - spr.height())/2 - (64 - h)/2]
        if spr is images.PLAYER_WALLSLIDE:
            res[0] += 12 # needs changing if sprite is redrawn or player resized
        elif spr is images.PLAYER_WALLSLIDE_LEFT:
            res[0] -= 12
        return res
        
    def draw(self, screen, offset=(0,0), modifier=None):
        if self.active_bullet is not None:
            pygame.draw.rect(screen, (255,255,255), self.active_bullet.move(*offset), 0)
        Actor.draw(self, screen, offset, modifier)
        
    def _update_status_tags(self, world):
        self.is_grounded = world.is_touching_wall(self, (0, 1))
        self.is_left_walled = world.is_touching_wall(self, (-1, 0))
        self.is_right_walled = world.is_touching_wall(self, (1, 0))    
        if self.is_left_walled or self.vel[0] > 0:
            self.facing_right = True
        if self.is_right_walled or self.vel[0] < 0:
            self.facing_right = False
        
    def update(self, tick_counter, input_state, world):
        self._update_status_tags(world)
        self._handle_shooting()
        
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
            target_speed = keyboard_x * self.speed
            if self.is_grounded and self.vel[0] * target_speed < 0:
                # turn around instantly when grounded
                self.vel[0] = 0
            else:
                self.vel[0] = cool_math.tend_towards(target_speed, self.vel[0], 1, only_if_increasing=True)
        
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
            is_interactable = lambda x: x.is_interactable()
            box = self.get_rect().inflate((self.interact_radius,0))
            interactables = world.get_entities_in_rect(box, is_interactable)
            cntr = self.center()
            if len(interactables) > 0:
                interactables.sort(key=lambda x: cool_math.dist(cntr, x.center()))
                interactables[0].interact()
                print("interacted with: ", interactables[0])
                
        if self.is_left_walled or self.is_right_walled:
            if self.vel[1] > self.max_slide_speed:
                self.vel[1] = cool_math.tend_towards(self.max_slide_speed, self.vel[1], 2)

        self.apply_gravity()
        self.apply_physics()
        
    def _is_shooting(self):
        return self.shoot_cooldown > 0
        
    def _handle_shooting(self):
        if not self.is_grounded:
            self.shoot_cooldown = 0
        elif self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            if self.shoot_cooldown == 10: # loll cmon
                rect = self.get_rect()
                bullet_y = rect.y + rect.height - 26*2
                bullet_w = 300
                bullet_x = rect.x + rect.width if self.facing_right else rect.x - bullet_w
                self.active_bullet = pygame.Rect(bullet_x, bullet_y, bullet_w, 4)
                    
        if self.shoot_cooldown < 8 or self.shoot_cooldown > 10:
            self.active_bullet = None
        
    def sprite_modifier(self):
        return "normal"
        
    def is_player(self):
        return True
        
    def deal_damage(self, damage, deflection_vector):
        if self.current_dmg_cooldown > 0 or self.is_rolling():
            return
        else:
            self.health -= damage
            self.current_dmg_cooldown = self.max_dmg_cooldown
            self.deflect_vector = deflection_vector
        
class Enemy(Actor):
    def __init__(self, x, y):
        Actor.__init__(self, x, y, 24, 24)
        self.speed = 1.5 + random.random() / 2
        self.current_dir = (0, 0)
        self.health = 50
        self.max_health = 50
        self._randint = random.randint(0,999)
        self.radius = 140 # starts chasing player within this distance
        self.forget_radius = 300 # stops chasing at this distance
        self.is_chasing = False
    
    sprites = [images.BLUE_GUY, images.PURPLE_GUY, images.BROWN_GUY] 
     
    def sprite(self):
        return Enemy.sprites[self._randint % len(Enemy.sprites)] 
        
    def sprite_offset(self):
        return (-4, -40)
        
    def draw(self, screen, offset=(0,0), modifier=None):
        Entity.draw(self, screen, offset, modifier)
        if self.health < self.max_health:
            health_x = self.get_rect().x + offset[0]
            health_y = self.get_rect().y + self.sprite_offset()[1] - 6 + offset[1]
            health_width = self.get_rect().width
            health_rect = [health_x, health_y, health_width, 4]
            pygame.draw.rect(screen, (255, 50, 50), health_rect, 0)
            health_rect[2] = max(0,round(health_width * self.health / self.max_health))
            pygame.draw.rect(screen, (50, 255, 50), health_rect, 0)
        
    def update(self, tick_counter, input_state, world):
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
            if random.random() < 1/30:
                if random.random() < 0.25:
                    self.current_dir = (0, 0)
                else:
                    self.current_dir = cool_math.rand_direction()
        self.set_vel_x(self.current_dir[0] * self.speed)
        self.apply_physics()
        
    def touched_player(self, player, world):
        v = cool_math.sub(player.center(), self.center())
        v = cool_math.normalize(v)
        player.deal_damage(5, v)
        
    def is_actor(self):
        return True
        
    def is_enemy(self):
        return True   
        
class Bullet(Entity):
    def __init__(self, x, y, target, speed, damage):
        Entity.__init__(self, x, y, 4, 4)
        self.start = (x, y)
        self.target = target
        self.speed = speed
        self.damage = damage
        self.hit_target = False
        
    def draw(self, screen, offset=(0,0), modifier=None):
        center = self.center()
        pos = (center[0] + offset[0], center[1] + offset[1])
        pygame.draw.circle(screen, (200, 100, 100), pos, 4, 0)
        
    def update(self, tick_counter, input_state, world):
        if not self.target.is_alive:
            self.is_alive = False
            
        c = self.center()
        t = self.target.center()
        if cool_math.dist(c, t) <= self.speed:
            self.target.health -= self.damage
            fire = Overlay(images.FIRE, 40, 0, 0, target=self.target)
            world.add_entity(fire)
            self.is_alive = False
        else:
            v = cool_math.sub(t, c)
            v = cool_math.set_length(v, self.speed)
            self.x += v[0]
            self.y += v[1]
            self.rect.x = round(self.x) % 640
            self.rect.y = round(self.y) % 480
            
class RopeBullet(Bullet):
    def __init__(self, x, y, direction, speed):
        Entity.__init__(self, x, y, 4, 4)
        self.direction = direction
        self.speed = speed
    
    def draw(self, screen, offset=(0,0), modifier=None):
        center = self.center()
        pos = (center[0] + offset[0], center[1] + offset[1])
        pygame.draw.circle(screen, (200, 100, 100), pos, 4, 0)
        
    def update(self, tick_counter, input_state, world):
        is_wall = lambda x: x.is_wall()
        colliding_with = world.get_entities_in_rect(self.get_rect(), is_wall)
        
        if len(colliding_with) > 0:
            colliding_with.sort(key=lambda x: cool_math.dist(self.center(), x.center()))
            wall_hit = colliding_with[0]
            player = world.player()
            if player != None:
                player.rope = Rope(wall_hit.center(), player.center())
            self.is_alive = False
        else:
            self.set_x(self.x + self.direction[0]*self.speed)
            self.set_y(self.y + self.direction[1]*self.speed)
                
               
class Wall(Entity):
    def __init__(self, x, y, w=32, h=32, sprite=images.WHITE_WALL):
        Entity.__init__(self, x, y, w, h)
        self.draw_outline = [True] * 4 # [left, top, right, bottom]
        self._sprite = sprite
    
    def sprite(self):
        return self._sprite
        
    def sprite_offset(self):
        return (0, 0)
    
    def update(self, tick_counter, input_state, world):
        pass
        
    def draw(self, screen, offset=(0,0), modifier=None):
        Entity.draw(self, screen, offset, modifier)
        r = self.get_rect()
        lt = (r.x + offset[0], r.y + offset[1])
        rb = (r.x + r.width + offset[0], r.y + r.height + offset[1])
        rt = (r.x + r.width + offset[0], r.y + offset[1])
        lb = (r.x + offset[0], r.y + r.height + offset[1])
        
        color = (0, 0, 0)
        if self.draw_outline[0]: # left 
            pygame.draw.rect(screen, color, [lt[0], lt[1], 2, r.height], 0)
        if self.draw_outline[1]: # top
            pygame.draw.rect(screen, color, [lt[0], lt[1], r.width, 2], 0)
        if self.draw_outline[2]: # right
            pygame.draw.rect(screen, color, [rt[0]-1, rt[1], 2, r.height], 0)
        if self.draw_outline[3]: # bottom
            pygame.draw.rect(screen, color, [lb[0], lb[1]-1, r.width, 2], 0)
        
    def update_outlines(self, world):
        is_wall = lambda x: x.is_wall()
        r = self.get_rect()
        rects = [
            cool_math.sliver_left(r),
            cool_math.sliver_above(r),
            cool_math.sliver_right(r),
            cool_math.sliver_below(r)
        ]
        for i in range(0, 4):
            self.draw_outline[i] = len(world.get_entities_in_rect(rects[i], is_wall)) == 0
        
    def is_wall(self):
        return True
        
class Spawner(Entity):
    def __init__(self, x, y, radius):
        Entity.__init__(self, x, y, 24, 24)
        self.radius = radius
        self.spawn_cooldown = 40
        self.current_cooldown = 0
        
    def is_wall(self):
        return True
        
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
        
    def update(self, tick_counter, input_state, world):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
        else:
            if random.random() < 1/30:
                self.do_spawn(world)
                
    def create_spawned(self):
        return Enemy(0,0)
        
    def do_spawn(self, world):
        c = self.center()
        r = random.random() * self.radius
        angle = random.random() * 2 * math.pi
        rand_x = round(r*math.cos(angle) + c[0])
        rand_y = round(r*math.sin(angle) + c[1])
        spawned = self.create_spawned()
        spawned.set_center_x(rand_x)
        spawned.set_center_y(rand_y)
        
        if len(world.get_entities_in_rect(spawned.get_rect())) == 0:
            world.add_entity(spawned)
            sparkles = Overlay(images.SPAWN_SPARKLES, 40, rand_x, rand_y, target=spawned)
            world.add_entity(sparkles)
        
        self.current_cooldown = self.spawn_cooldown
        
class EnergyTank(Entity):
    def __init__(self, x, y, health):
        Entity.__init__(self, x, y, 24, 24)
        self.max_health = health
        self.health = health
        
    def is_wall(self):
        return True
        
    def sprite(self):
        return images.ENERGY_TANK
        
    def sprite_offset(self):
        return (-4, -40)

class Rope():
    def __init__(self, p1, p2, max_length=-1):
        """Create a new rope object.
            p1: anchor point
            p2: most flexible point"""
        self._points = [p1, p2]
        self.max_length = max_length
        if max_length < 0:
            self.max_length = cool_math.dist(p1, p2)
        
    def length(self, end_idx=None):
        if end_idx == None or end_idx == -1:
            end_idx = len(self._points) - 1
        elif end_idx == 0:
            return 0
            
        res = 0
        pts = self._points
        
        for i in range(0, end_idx):
            res += cool_math.dist(pts[i], pts[i+1])
        return res
         
    def draw(self, screen, offset=(0,0), modifier=None):
        # color = (255,0,0) if self.length() > self.max_length else (0,0,0)
        color = (0, 0, 0)
        pygame.draw.lines(screen, color, False, self.all_points(offset), 2)
    
    def all_points(self, offset=(0, 0)):
        if offset == (0, 0):
            return self._points
        else:
            return [cool_math.add(x, offset) for x in self._points]
         
    def num_points(self):
        return len(self._points)     
            
    def get_point(self, idx):
        return self._points[idx % self.num_points()]
        
    def set_point(self, idx, point):
        self._points[idx % self.num_points()] = point
        
    def add_point(self, point):
        self._points.append(point)
    
    def update(self, tick_counter, input_state, world):
        return
        length = self.length()
        while length > self.max_length:
            seg = (self.get_point(-1), self.get_point(-2))
            seg_length = cool_math.dist(seg[0], seg[1])
            remaining_length = length - seg_length
            if remaining_length > self.max_length:
                del self._points[-1]
            else:
                seg_length_new = self.max_length - remaining_length
                v = cool_math.sub(seg[0], seg[1])
                v = cool_math.set_length(v, seg_length_new)
                new_last_point = cool_math.add(seg[1], v)
                self.set_point(-1, new_last_point)
                return
            length = self.length()
            
    def get_allowable_positions(self, idx=None):
        """returns: (x,y,radius)"""
        if idx == None:
            idx = -1
        idx = idx % self.num_points()
        length = self.length(idx-1)
        print("get_allowable length=",length)
        radius = max(0, self.max_length - length)
        print("get_allowable radius=",radius)
        pt = self.get_point(idx)
        return (pt[0], pt[1], radius)
            
    def get_slack(self):
        return max(0, self.max_length - self.length())
        
class Door(Entity):
    def __init__(self, x, y, door_id, dest_id, locked=False):
        Entity.__init__(self, x, y, 32, 64) 
        self.door_id = door_id
        self.dest_id = dest_id
        self.locked = locked
        
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
    
    def update(self, tick_counter, input_state, world):
        if self.open_cooldown == 1:
            player = world.player()
            dest_door = world.get_door(self.dest_id)
            if player != None and dest_door != None:
                player.set_center(*dest_door.center())
                dest_door.open_cooldown = -dest_door.open_max_cooldown
        
        if self.open_cooldown > 0:
            self.open_cooldown -= 1
        if self.open_cooldown < 0:
            self.open_cooldown += 1
            
    def is_interactable(self):
        # can't interact after it's already been interacted with
        return not self.locked and self.open_cooldown == 0
        
    def interact(self):
        if not self.locked:
            self.open_cooldown = self.open_max_cooldown
            
    def is_door(self):
        return True
                
        
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
    
    def update(self, tick_counter, input_state, world):
        if self.lifespan <= 0 or self.target is not None and not self.target.is_alive:
            self.is_alive = False
        else:
            self.lifespan -= 1
            if self.target is not None:
                pos = self.target.center()
                self.set_center_x(pos[0])
                self.set_center_y(pos[1])

class Ground(Entity):
    all_sprites = [images.STONE_GROUND, images.SAND_GROUND, 
            images.GRASS_GROUND, images.PURPLE_GROUND]
    def __init__(self, x, y, ground_type):
        Entity.__init__(self, x, y, 32, 32)
        self.ground_type = ground_type
    
    def sprite(self):
        return Ground.all_sprites[self.ground_type]
        
    def is_ground(self):
        return True
        

