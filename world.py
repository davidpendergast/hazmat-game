import pygame

import images
import entities
import random

draw_rects_debug = False

class World:
    def __init__(self):
        self.player = entities.Player(50, 50)
        self.enemies = [entities.Enemy(random.randint(0,640), random.randint(0,480)) for _ in range(0, 10)]
        other_junk = [entities.Turret(300,200)]
        for i in range(0, 640, 32):
            other_junk.append(entities.Wall(i, 0))
            other_junk.append(entities.Wall(i, 480-32))
        for i in range(32, 480, 32):
            other_junk.append(entities.Wall(0, i))
            other_junk.append(entities.Wall(640-32, i))
        
        self.ground = []    
        for x in range(0, 640, 32):
            for y in range(0, 480, 32):
                rx = random.random() * 640
                ry = random.random() * 480
                n = 0 if rx < x else 2
                n += 0 if ry < y else 1
                self.ground.append(entities.Ground(x, y, n))
                
        self.stuff = [self.player] + self.enemies + other_junk
        self.camera = (0, 0)
        
    def update_all(self, tick_counter, input_state):
        self._do_debug_stuff(input_state)
            
        still_alive = []
        for thing in self.stuff:
            thing.update(tick_counter, input_state, self)
            if thing.is_alive:
                still_alive.append(thing)
                
        self.stuff = still_alive
        
        for e in self.stuff:
            if e.is_actor():
                self.uncollide(e)
            
        
    def _do_debug_stuff(self, input_state):
        global draw_rects_debug
        draw_rects_debug = input_state.is_held(pygame.K_r)
    
    def draw_all(self, screen):
        for g in self.ground:
            g.draw(screen, self.camera)
            
        self.stuff.sort(key=lambda x: x.get_rect().bottomleft[1])
        for thing in self.stuff:
            thing.draw(screen, self.camera)
            
        if draw_rects_debug:
            for thing in self.stuff:
                pygame.draw.rect(screen, images.rainbow, thing.get_rect().move(*self.camera), 2)
            
    def add_entity(self, entity):
        self.stuff.append(entity)
        
    def get_entities_in_rect(self, rect, cond=None):
        # TODO - slowwww
        return [e for e in self.stuff if rect.colliderect(e.get_rect()) and (cond == None or cond(e))]
        
    def uncollide(self, entity):
        e_rect = entity.get_rect()
        v_rect = e_rect.inflate(-10, 0)
        h_rect = e_rect.inflate(0,-10)
        is_wall = lambda e: e.is_wall()
        v_collides = self.get_entities_in_rect(v_rect, is_wall)
        h_collides = self.get_entities_in_rect(h_rect, is_wall)
        
        for w in h_collides:
            w_rect = w.get_rect()
            if w_rect.colliderect(h_rect):
                left_shift_x = w_rect.x - e_rect.width
                right_shift_x = w_rect.x + w_rect.width
                if abs(left_shift_x-e_rect.x) < abs(right_shift_x-e_rect.x):
                    entity.set_x(left_shift_x)
                else:
                    entity.set_x(right_shift_x)
                    
        for w in v_collides:
            w_rect = w.get_rect()
            if w_rect.colliderect(v_rect):
                up_shift_y = w_rect.y - e_rect.height
                down_shift_y = w_rect.y + w_rect.height
                if abs(up_shift_y - e_rect.y) < abs(down_shift_y - e_rect.y):
                    entity.set_y(up_shift_y)
                else:
                    entity.set_y(down_shift_y)
               
                    
                    
        
    
        
