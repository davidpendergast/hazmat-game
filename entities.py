import pygame
import random
import math

import cool_math
import images

class Entity:
    def __init__(self, x, y, w, h):
        self.is_alive = True
        self.has_gravity = False
        self.is_grounded = True
        self.max_speed = (10, 20)
        self.x = x # floating point
        self.y = y # floating point
        self.vel = [0, 0]
        self.rect = pygame.Rect(x, y, w, h)
    
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
        
    def set_center_x(self, x):
        self.set_x(x - self.get_rect().width/2)
        
    def set_center_y(self, y):
        self.set_y(y - self.get_rect().height/2)
        
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
    gravity = 3
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
        if self.has_gravity:
            if not self.is_grounded:
                self.vel[1] += Actor.gravity
                self.vel[1] = min(self.vel[1], self.max_speed[1])        
            
        self.set_x(self.x + self.vel[0])
        self.set_y(self.y + self.vel[1])
        
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
        self.max_dmg_cooldown = 30 # frames of invincibility/inactivity
        self.current_dmg_cooldown = 0
        self.deflect_vector = None
     
    def sprite(self):
        return images.RED_GUY
        
    def sprite_offset(self):
        return (-4, -40)
        
    def update(self, tick_counter, input_state, world):
        speed = self.speed
        
        cur_cd = self.current_dmg_cooldown
        max_cd = self.max_dmg_cooldown
        if cur_cd > max_cd / 2:
            if self.deflect_vector is not None:
                speed = self.speed * 1.5 * (cur_cd - max_cd/2) / (max_cd/2)
                speed = -speed if self.deflect_vector[0] < 0 else speed
                self.vel[0] = speed
        else:    
            self.vel[0] = 0
            if input_state.is_held(pygame.K_a):
                self.vel[0] -= self.speed
            if input_state.is_held(pygame.K_d):
                self.vel[0] += self.speed  
            if input_state.is_held(pygame.K_w) and self.is_grounded:
                self.vel[1] = self.get_jump_speed()

        if self.current_dmg_cooldown > 0:
            self.current_dmg_cooldown -= 1
        
        self.apply_physics()
        
    def sprite_modifier(self):
        if self.current_dmg_cooldown > 0:
            return "white_ghosts"
        else:
            return "normal"
        
    def is_player(self):
        return True
        
    def deal_damage(self, damage, deflection_vector):
        if self.current_dmg_cooldown > 0:
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
        

