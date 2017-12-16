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
        self.rect = pygame.Rect(x, y, w, h)
        pass
    
    def draw(self, screen, offset=(0,0)):
        sprite = self.sprite()
        dest_rect = self.get_rect().move(*offset)
        if sprite != None:
            dest_rect.move_ip(*self.sprite_offset())
            images.draw_animated_sprite(screen, dest_rect, sprite)
        else:
            pygame.draw.rect(screen, images.rainbow, dest_rect, 0)
            
    def sprite_offset(self):
        return (0, 0)
        
    def sprite(self):
        return None
    
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
        
class Player(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self.speed = 5
     
    def sprite(self):
        return images.RED_GUY
        
    def sprite_offset(self):
        return (-4, -40)
        
    def update(self, tick_counter, input_state, world):
        v = [0, 0]
        if input_state.is_held(pygame.K_a):
            v[0] -= 1
        if input_state.is_held(pygame.K_s):
            v[1] += 1
        if input_state.is_held(pygame.K_d):
            v[0] += 1  
        if input_state.is_held(pygame.K_w):
            v[1] -= 1
        if abs(v[0] + v[1]) == 2:
            v[0] *= 0.7071 # 1 over sqrt(2)
            v[1] *= 0.7071
        self.x += self.speed * v[0]
        self.y += self.speed * v[1]
        self.rect.x = round(self.x)
        self.rect.y = round(self.y)
        
    def is_actor(self): 
        return True
        
    def is_player(self):
        return False
        
class Enemy(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self.speed = 2
        self.current_dir = (0, 0)
        self.health = 50
        self.max_health = 50
        self._randint = random.randint(0,999)
    
    sprites = [images.BLUE_GUY, images.PURPLE_GUY, images.BROWN_GUY] 
     
    def sprite(self):
        return Enemy.sprites[self._randint % len(Enemy.sprites)] 
        
    def sprite_offset(self):
        return (-4, -40)
        
    def draw(self, screen, offset=(0,0)):
        Entity.draw(self, screen, offset)
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
            
        # change directions approx every 30 ticks
        if random.random() < 1/30:
            if random.random() < 0.25:
                self.current_dir = (0, 0)
            else:
                rads = random.random() * 2 * math.pi
                self.current_dir = (math.cos(rads), math.sin(rads))
        
        self.x += self.speed * self.current_dir[0]
        self.y += self.speed * self.current_dir[1]
        self.rect.x = round(self.x)
        self.rect.y = round(self.y)
        
    def is_actor(self):
        return True
        
    def is_enemy(self):
        return True
                
                
class Turret(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        
        self.radius = 32*4
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
        r = [c[0] - self.radius, c[1] - self.radius, self.radius*2, self.radius*2]
        is_shootable = lambda x: x.is_enemy() and self.in_range(x)
        enemies = world.get_entities_in_rect(r, is_shootable)
        if len(enemies) > 0:
            return min(enemies, key=lambda x: x.health)
        else:
            return None
        
    def in_range(self, entity):
        return cool_math.dist(entity.center(), self.center()) < self.radius
        
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
        
    def draw(self, screen, offset=(0,0)):
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
        

