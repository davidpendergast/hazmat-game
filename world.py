import pygame
import random

import images
import entities
import global_state
import cool_math

draw_rects_debug = False

class World:
    def __init__(self):
        
        self.camera = (0, 0)
        self._player = None
        self.ground = []
        self.stuff = []
        
    def update_all(self, tick_counter, input_state):
        self._do_debug_stuff(input_state)
            
        for thing in self.stuff:
            thing.update(tick_counter, input_state, self)
        
        self.stuff = self._remove_dead(self.stuff)
        
        for e in self.stuff:
            if e.is_actor():
                self.uncollide(e)
                
        self._handle_placing_item(input_state)
        
        p = self.player()        
        if p is not None:
            self.recenter_camera(p.center())
      
    def recenter_camera(self, pos):
        x = round(pos[0] - global_state.WIDTH/2)
        y = round(pos[1] - global_state.HEIGHT/2)
        self.camera = (x, y)
        
    def _remove_dead(self, entity_list):
        still_alive = []
        for e in self.stuff:
            if e.is_alive:
                still_alive.append(e)
            else:
                self._prepare_to_remove(e)
        return still_alive
            
    def _prepare_to_remove(self, entity):
        entity.is_alive = False
        if entity.is_player():
            self._player = None
        
    def _do_debug_stuff(self, input_state):
        global draw_rects_debug
        if input_state.was_pressed(pygame.K_r):
            draw_rects_debug = not draw_rects_debug 
    
    def draw_all(self, screen):
        offset = cool_math.neg(self.camera)
        num_draw_calls = 0
        for g in self.ground:
            g.draw(screen, offset)
            num_draw_calls += 1
            
        self.stuff.sort(key=lambda x: x.get_rect().bottomleft[1])
        for thing in self.stuff:
            thing.draw(screen, offset)
            num_draw_calls += 1
            
        to_place = global_state.selected_item_to_place
        placeable = global_state.selected_item_placeable
        if to_place is not None and placeable is not None:
            mod = "green_ghosts" if placeable else "red_ghosts"    
            global_state.selected_item_to_place.draw(screen, offset, modifier=mod)   
            
        if draw_rects_debug:
            for thing in self.stuff:
                pygame.draw.rect(screen, images.rainbow, thing.get_rect().move(*offset), 2)
                if hasattr(thing, 'radius'):
                    center = cool_math.add(thing.center(), offset)
                    pygame.draw.circle(screen, images.rainbow, center, thing.radius, 2)
            basicfont = pygame.font.SysFont(None, 16)
            string_text = "draw calls: " + str(num_draw_calls)
            text = basicfont.render(string_text, True, (255, 0, 0), (255, 255, 255))
            screen.blit(text, (0, 0))
            
    def add_entity(self, entity):
        if entity.is_player():
            if self._player is not None:
                raise ValueError("There is already a player in this world.")
            self._player = entity
            
        if entity.is_ground():
            self.ground.append(entity)
        else:
            self.stuff.append(entity)
        
    def add_all_entities(self, entity_list):
        for x in entity_list:
            self.add_entity(x)
            
    def player(self):
        return self._player
        
    def get_entities_in_rect(self, rect, cond=None):
        # TODO - slowwww
        return [e for e in self.stuff if e.get_rect().colliderect(rect) and (cond == None or cond(e))]
        
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
                    
    def get_tile_at(self, x, y):
        """returns: coordinate of center of 32x32 'tile' that contains (x, y)"""
        x = x + self.camera[0]
        y = y + self.camera[1]
        cx = int(x / 32)*32 + 16
        cy = int(y / 32)*32 + 16
        return (cx, cy)
        
    def _handle_placing_item(self, input_state):
        to_place = global_state.selected_item_to_place
        if to_place == None or self.player() == None or not input_state.mouse_in_window():
            global_state.selected_item_placeable = None
        else:
            loc = to_place.center()
            player_loc = self.player().center()
            dist = cool_math.dist(loc, player_loc)
            in_range = dist <= 120
            unblocked = len(self.get_entities_in_rect(to_place.get_rect())) == 0
            global_state.selected_item_placeable = in_range and unblocked
            
            if input_state.mouse_was_pressed() and global_state.selected_item_placeable:
                self.add_entity(to_place)
                global_state.selected_item_placeable = None
                global_state.selected_item_to_place = None        
                    
    def gimme_a_sample_world():
        world = World()
        
        other_junk = [entities.Player(50, 50), entities.Turret(320-96+4, 96*2+4)]
        for i in range(0, 640, 32):
            other_junk.append(entities.Wall(i, 0))
            other_junk.append(entities.Wall(i, 480-32))
        for i in range(32, 480, 32):
            other_junk.append(entities.Wall(0, i))
            other_junk.append(entities.Wall(640-32, i))
            
        other_junk.append(entities.Spawner(320+4, 64+4, 60))
        
        ground = []    
        for x in range(0, 640, 32):
            for y in range(0, 480, 32):
                rx = random.random() * 640
                ry = random.random() * 480
                n = 0 if rx < x else 2
                n += 0 if ry < y else 1
                ground.append(entities.Ground(x, y, n))
        
        all_stuff = other_junk + ground
        world.add_all_entities(all_stuff)
        return world 
                    
        
    
        
