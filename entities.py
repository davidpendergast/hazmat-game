import pygame
import random
import math

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
        
    def center(self):
        r = self.get_rect()
        return (int(r.x + r.width/2), int(r.y + r.height/2))   
        
    def is_wall(self):
        return False  
        
    def is_actor(self):
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
        
class Enemy(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self.speed = 2
        self.current_dir = (0, 0)
        self.health = 50
        self._randint = random.randint(0,999)
    
    sprites = [images.BLUE_GUY, images.PURPLE_GUY, images.BROWN_GUY] 
     
    def sprite(self):
        return Enemy.sprites[self._randint % len(Enemy.sprites)] 
        
    def sprite_offset(self):
        return (-4, -40)
        
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
                
                
class Turret(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 24)
        self.color = (125,125,125)
        self.top_color = (175,175,175)
        self.barrel_color = (175,175,175)
        self.turret_angle = (0, 1)
    
    def sprite(self):
        return images.RED_TURRET
        
    def sprite_offset(self):
        return (-4, -40)
        
    def update(self, tick_counter, input_state, world):
        v1, v2 = self.turret_angle
        cos = math.cos(0.02)
        sin = math.sin(0.02)
        self.turret_angle = (cos*v1 + sin*v2, -sin*v1 + cos*v2)
        
        if random.random() < 0.05:
            self.shoot(world)
        
    def shoot(self, world):
        c = self.center()
        bullet = Bullet(c[0], c[1], self.turret_angle, 10, 10)
        world.add_entity(bullet)
        
    def get_rect(self):
        return self.rect
        
    def is_wall(self):
        return True
        
class Bullet(Entity):
    def __init__(self, x, y, direction, speed, damage):
        Entity.__init__(self, x, y, 4, 4)
        self.dir = direction
        self.speed = speed
        self.damage = damage
        self.spawn_time = None
        self.lifespan = 30
        
    def draw(self, screen, offset=(0,0)):
        center = self.center()
        pos = (center[0] + offset[0], center[1] + offset[1])
        pygame.draw.circle(screen, (255,255,255), pos, 2, 0)
        
    def update(self, tick_counter, input_state, world):
        if self.spawn_time == None:
            self.spawn_time = tick_counter
        elif tick_counter - self.spawn_time > self.lifespan:
            self.is_alive = False
            return
            
        self.x += self.speed * self.dir[0]
        self.y += self.speed * self.dir[1]
        self.rect.x = round(self.x) % 640
        self.rect.y = round(self.y) % 480
    
        is_enemy = lambda x: type(x) is Enemy
        colliding = world.get_entities_in_rect(self.rect, is_enemy)
        if len(colliding) > 0:
            colliding[0].health -= self.damage
            self.is_alive = False 
            
            
class Wall(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 32, 32)
    
    def sprite(self):
        return images.WHITE_WALL
        
    def sprite_offset(self):
        return (0, -32)
    
    def update(self, tick_counter, input_state, world):
        pass
    
    def get_rect(self):
        """
        The space that this entity physically occupies
        returns: pygame.Rect
        """
        return self.rect
        
    def is_wall(self):
        return True
        
class Ground(Entity):
    all_sprites = [images.STONE_GROUND, images.SAND_GROUND, 
            images.GRASS_GROUND, images.PURPLE_GROUND]
    def __init__(self, x, y, ground_type):
        Entity.__init__(self, x, y, 32, 32)
        self.ground_type = ground_type
    
    def sprite(self):
        return Ground.all_sprites[self.ground_type]
        
        
    
 

        
        
        
        
        

