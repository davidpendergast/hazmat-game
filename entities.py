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
    
    def __repr__(self):
        pos = "(%s, %s)" % (self.rect.x, self.rect.y)
        return type(self).__name__ + pos
        
class Actor(Entity):
    gravity = 1.5
    def __init__(self, x, y, w, h):
        Entity.__init__(self, x, y, w, h)
        self.has_gravity = True
        self.is_grounded = False
        self.max_speed = (10, 20)
        self.jump_height = 64 + 16
        
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
        Actor.__init__(self, x, y, 24, 24)
        self.speed = 5
        self.has_gravity = True
        
        self.max_health = 50
        self.health = 50
        
        self.rope = None
        self.is_launching_from_rope = False
        
    def is_rolling(self):
        return self.roll_duration > 0
     
    def sprite(self):
        return images.RED_GUY
        
    def sprite_offset(self):
        return (-4, -40)
        
    def draw(self, screen, offset=(0,0), modifier=None):
        if self.rope is not None:
            self.rope.draw(screen, offset, modifier)
        Actor.draw(self, screen, offset, modifier)
        
    def _update_status_tags(self, world):
        self.is_grounded = world.is_grounded(self)
        if self.is_grounded:
            self.is_launching_from_rope = False
        
    def update(self, tick_counter, input_state, world):
        self._update_status_tags(world)
        
        keyboard_x = 0
        if input_state.is_held(pygame.K_a):
            keyboard_x -= 1
        if input_state.is_held(pygame.K_d):
            keyboard_x += 1
            
        keyboard_jump = input_state.is_held(pygame.K_w) and self.is_grounded
        
        if keyboard_x == 0:
            fric = 1
            # reduce friction in air when swinging on rope, or when player has 
            # just finished swinging without hitting the ground yet.
            if not self.is_grounded and (self.rope != None or self.is_launching_from_rope):
                fric = 0.05
            # friction
            self.vel[0] = cool_math.tend_towards(0, self.vel[0], fric)
        else:    
            target_speed = keyboard_x * self.speed
            if self.is_grounded and self.vel[0] * target_speed < 0:
                # turn around instantly when grounded
                self.vel[0] = 0
            else:
                self.vel[0] = cool_math.tend_towards(target_speed, self.vel[0], 1, only_if_increasing=True)
            
        if self.is_grounded and keyboard_jump:
            self.vel[1] = self.get_jump_speed()

        self.apply_gravity()
        self._update_position(world)
        self._update_rope(tick_counter, input_state, world)
    
    def _update_position(self, world):
        if self.rope == None:
            # no rope, easy
            self.apply_physics()
        else:
            # oh boy
            start_xy = (self.x, self.y)
            new_xy = (self.x + self.vel[0], self.y + self.vel[1])
            new_rect = pygame.Rect(new_xy[0], new_xy[1], self.rect.width, self.rect.height)
            uncollided = world.uncollide_rect(new_rect)
            uncollided_center = (uncollided[0]+new_rect.width/2, uncollided[1]+new_rect.height/2)
            horz_change = uncollided[0] != new_rect.x
            vert_change = uncollided[1] != new_rect.y
            rope_pivot = self.rope.get_point(0)
            rope_r = self.rope.max_length
            
            if cool_math.dist(uncollided_center, rope_pivot) <= rope_r:
                # we good, ignore rope
                self.set_x(uncollided[0] if horz_change else new_xy[0])
                self.set_y(uncollided[1] if vert_change else new_xy[1])
            elif rope_r == 0:
                pass
            else:
                # rope is overstretched
                rope_v = cool_math.sub(uncollided_center, rope_pivot)
                rope_v = cool_math.set_length(rope_v, rope_r)
                new_center = cool_math.add(rope_pivot, rope_v)
                
                rope_dir = cool_math.normalize(rope_v)
                correction = cool_math.sub(new_center, uncollided_center)
                rope_component = cool_math.component(self.vel, rope_dir)
                
                if cool_math.same_direction(self.vel, rope_dir):
                    # nuking velocity in the direction of the rope
                    new_vel = cool_math.sub(self.vel, rope_component)
                    # fudge in some conservation of energy
                    y_correction = correction[1]
                    if y_correction < 0:
                        # add speed if moving down, else reduce speed
                        mult = 1 if new_vel[1] < 0 else -1
                        new_vel = cool_math.extend(new_vel, mult*y_correction / 5)
                    self.vel[0] = new_vel[0]
                    self.vel[1] = new_vel[1]
                    
                self.set_center(*new_center)
            
    def _update_rope(self, tick_counter, input_state, world):
        if input_state.mouse_was_pressed():
            if self.rope is not None:
                self.rope = None
                if not self.is_grounded:
                    self.is_launching_from_rope = True
            else:
                pos = world.to_world_pos(input_state.mouse_pos())
                self.rope = Rope(pos, self.center())
            
        if self.rope is not None:
            self.rope.set_point(-1, self.center())
            self.rope.update(tick_counter, input_state, world)
            p = self.rope.get_point(-1)
            self.set_center_x(p[0])
            self.set_center_y(p[1])
        
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
                
class Turret(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        
        self.radius = 32*2
        self.cooldown = 30
        self.current_cooldown = 0
        
        self.damage = 5;
    
    def sprite(self):
        return images.RED_TURRET
        
    def sprite_offset(self):
        return (-4, -40)
        
    def update(self, tick_counter, input_state, world):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
        else:
            target = self.choose_target(world)
            if target != None:
                self.shoot(world, target)
                self.current_cooldown = self.cooldown
        
    def choose_target(self, world):
        c = self.center()
        is_shootable = lambda x: x.is_enemy()
        enemies = world.get_entities_in_circle(c, self.radius, is_shootable)
        if len(enemies) > 0:
            return min(enemies, key=lambda x: x.health)
        else:
            return None
        
    def shoot(self, world, target):
        c = self.center()
        bullet = Bullet(c[0], c[1], target, 10, 10)
        world.add_entity(bullet)
        
    def get_rect(self):
        return self.rect
        
    def is_wall(self):
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
                  
class Wall(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 32, 32)
    
    def sprite(self):
        return images.WHITE_WALL
        
    def sprite_offset(self):
        return (0, -32)
    
    def update(self, tick_counter, input_state, world):
        pass
        
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
        

