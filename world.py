import pygame
import random

import images
import entities
import global_state
import cool_math

class World:
    def __init__(self):
        self.camera = (0, 0)
        self._player = None
        self.ground = []
        self.stuff = []
        self._outlines_dirty = False
        
    def update_all(self, tick_counter, input_state):
        for thing in self.stuff:
            thing.update(tick_counter, input_state, self)
        
        self.stuff = self._remove_dead(self.stuff)
        
        if self._outlines_dirty:
            for e in self.stuff:
                if e.is_wall():
                    e.update_outlines(self)
            self._outlines_dirty = False
        
        for e in self.stuff:
            if e.is_actor():
                self.uncollide(e)
        
        p = self.player()        
        if p is not None:
            is_enemy = lambda x: x.is_enemy()
            for e in self.get_entities_in_rect(p.get_rect(), is_enemy):
                e.touched_player(p, self)
                    
            self.recenter_camera(p.center())
      
    def recenter_camera(self, pos):
        x = round(pos[0] - global_state.WIDTH/2)
        y = round(pos[1] - global_state.HEIGHT/2)
        self.camera = (x, y)
        
    def get_camera(self):
        return self.camera
        
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
        if entity.is_wall():
            self._outlines_dirty = True
    
    def draw_all(self, screen):
        offset = cool_math.neg(self.camera)
        num_draw_calls = 0
        for g in self.ground:
            g.draw(screen, offset)
            num_draw_calls += 1
            
        self.stuff.sort(key=lambda x: x.get_rect().bottomleft[1])
        for thing in self.stuff:
            if not thing.is_actor():
                thing.draw(screen, offset)
                num_draw_calls += 1
        
        for thing in self.stuff:  # TODO cmon
            if thing.is_actor():
                thing.draw(screen, offset)
                num_draw_calls += 1
            
        if global_state.show_debug_rects:
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
            
        if entity.is_wall():
            self._outlines_dirty = True
            
        
    def add_all_entities(self, entity_list):
        for x in entity_list:
            self.add_entity(x)
            
    def player(self):
        return self._player
        
    def get_entities_in_circle(self, center, radius, cond=None):
        rect = [center[0]-radius, center[1]-radius, radius*2, center[1]*2]
        in_circle = lambda x: cool_math.dist(x.center(), center) <= radius
        rect_search_cond = lambda x: in_circle(x) and (cond==None or cond(x))
        return self.get_entities_in_rect(rect, cond=rect_search_cond)
        
    def get_entities_in_rect(self, rect, cond=None):
        # TODO - slowwww
        return [e for e in self.stuff if e.get_rect().colliderect(rect) and (cond == None or cond(e))]
        
    def get_entities_at_point(self, pt, cond=None):
        return self.get_entities_in_rect([pt[0], pt[1], 1, 1], cond)
        
    def get_entities_with(self, cond):
        # TODO - also sloooowww
        return [e for e in self.stuff if cond(e)]
        
    def get_door(self, door_id):
        is_my_door = lambda x: x.is_door() and x.door_id == door_id
        matches = self.get_entities_with(is_my_door)
        if len(matches) == 0:
            return None
        elif len(matches) > 0:
            print("Multiple doors in world with id=", door_id)
            random.shuffle(matches)
        return matches[0]
        
    def uncollide(self, entity):
        initial_rect = entity.get_rect()
        shifted = self.uncollide_rect(entity.get_rect())
        if shifted[1] != initial_rect.y:
            entity.set_vel_y(0)
        if shifted[0] != initial_rect.x:
            entity.set_vel_x(0)
        
        entity.set_x(shifted[0])
        entity.set_y(shifted[1])
                
    def uncollide_rect(self, rect):
        """returns: (x, y) coordinates that rect can be shifted to so that
            it doesn't collide with wall entities in the world. If no 'good'
            positions can be found, returns the rect's original coordinates."""
        rect = rect.copy()
        res_y = rect.y
        res_x = rect.x
        
        v_rect = rect.inflate(-10, 0)
        is_wall = lambda e: e.is_wall()
        v_collides = self.get_entities_in_rect(v_rect, is_wall)
        
        for w in v_collides:
            w_rect = w.get_rect()
            if w_rect.colliderect(v_rect):
                up_shift_y = w_rect.y - rect.height
                down_shift_y = w_rect.y + w_rect.height
                if abs(up_shift_y - rect.y) < abs(down_shift_y - rect.y):
                    res_y = up_shift_y
                else:
                    res_y = down_shift_y
                
        rect.y = res_y
        h_rect = rect.inflate(0,-10)
        h_collides = self.get_entities_in_rect(h_rect, is_wall)
                    
        for w in h_collides:
            w_rect = w.get_rect()
            if w_rect.colliderect(h_rect):
                left_shift_x = w_rect.x - rect.width
                right_shift_x = w_rect.x + w_rect.width
                if abs(left_shift_x-rect.x) < abs(right_shift_x-rect.x):
                    res_x = left_shift_x
                else:
                    res_x = right_shift_x
        return (res_x, res_y)
        
    def is_touching_wall(self, actor, direction):
        rect = actor.get_rect()
        detector_rect = cool_math.sliver_adjacent(rect, direction)
        is_wall = lambda x: x.is_wall()
        detected = self.get_entities_in_rect(detector_rect, cond=is_wall)
        return len(detected) > 0
                    
    def get_tile_at(self, screen_x, screen_y, tilesize=(32,32)):
        """returns: coordinate of center of 'tile' that contains (x, y)"""
        x = screen_x + self.camera[0]
        y = screen_y + self.camera[1]
        cx = int(x / tilesize[0])*tilesize[0] + tilesize[0]/2
        cy = int(y / tilesize[1])*tilesize[1] + tilesize[1]/2
        return (cx, cy)       
        
    def to_world_pos(self, screen_pos):
        x = screen_pos[0] + self.camera[0]
        y = screen_pos[1] + self.camera[1]
        return (x, y)
                    
    def gimme_a_sample_world():
        world = World()
        
        other_junk = [entities.Player(50, 50)]
        for i in range(0, 640, 32):
            other_junk.append(entities.Wall(i, 0))
            other_junk.append(entities.Wall(i, 480-32))
        for i in range(32, 480, 32):
            other_junk.append(entities.Wall(0, i))
            other_junk.append(entities.Wall(640-32, i))
        
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
                    
        
    
        
