import pygame
import random

import images
import entities
import global_state
import cool_math

CHUNK_SIZE = 8*32

class Chunk:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, CHUNK_SIZE, CHUNK_SIZE)
        self.entities = entities.EntityCollection()
        
    def get_rect(self):
        return self.rect
        
    def size(self):
        return self.rect.size()
    
    def draw_nonactors(self, screen, offset):
        for g in self.entities.get_all(category="ground"):
            g.draw(screen, offset)
            
        for e in self.entities.get_all(not_category=["ground","actor"]):
            e.draw(screen, offset)
        
    def draw_actors(self, screen, offset):
        # Actor sprites can overflow out of their rects on the left or above,
        # so they need to be drawn after everything else (to prevent issues at
        # chunk borders). TODO - fix this?     
        for e in self.entities.get_all(category="actor"):
            e.draw(screen, offset)
                    
    def draw_darkness(self, screen, offset):
        pass
    
    def draw_debug_stuff(self, screen, offset):
        if global_state.show_debug_rects:
            pygame.draw.rect(screen, (0,0,0), self.get_rect().move(*offset), 1)
            for thing in self.entities.get_all(not_category="ground"):
                pygame.draw.rect(screen, images.rainbow, thing.get_rect().move(*offset), 2)
                if hasattr(thing, 'radius'):
                    center = cool_math.add(thing.center(), offset)
                    pygame.draw.circle(screen, images.rainbow, center, thing.radius, 2)
        
    def __contains__(self, entity):
        return entity in self.entities

class World:
    def __init__(self):
        self.camera = (0, 0)
        self._player = None
        self.chunks = {} 
        
    def get_chunk_key_for_point(self, x, y):
        return (x -(x % CHUNK_SIZE), y - (y % CHUNK_SIZE))
        
    def get_chunk(self, x, y):
        key = self.get_chunk_key_for_point(x, y)
        if key in self.chunks:
            return self.chunks[key]
        else:
            return None
            
    def get_chunks_in_rect(self, rect):
        xy_min = self.get_chunk_key_for_point(rect[0], rect[1])
        xy_max = self.get_chunk_key_for_point(rect[0] + rect[2], rect[1] + rect[3])
        res = []
        for x in range(xy_min[0]-1, xy_max[0]+1):
            for y in range(xy_min[1]-1, xy_max[1]+1):
                if (x, y) in self.chunks:
                    res.append(self.chunks[(x, y)])
        return res
    
    def get_or_create_chunk(self, x, y):
        key = (int(x -(x % CHUNK_SIZE)), int(y - (y % CHUNK_SIZE)))
        if key not in self.chunks:
            self.chunks[key] = Chunk(key[0], key[1])
        return self.chunks[key]
        
    def update_all(self, tick_counter, input_state):
        for chunk in self.chunks.values():
            for entity in chunk.entities:
                entity.update(tick_counter, input_state, self)
        
        for chunk in self.chunks.values():
            dead = []
            moved_out = []
            for entity in chunk.entities:
                if not entity.is_alive:
                    dead.append(entity)
                elif not chunk.get_rect().collidepoint(entity.center()):
                    moved_out.append(entity)
            for entity in dead:
                print(entity, " has died.")
                self._prepare_to_remove(entity)
                chunk.entities.remove(entity)
            for entity in moved_out:
                chunk.entities.remove(entity)
                moving_to = self.get_or_create_chunk(*entity.center())
                moving_to.entities.add(entity)
        
        for chunk in self.chunks.values():
            for e in chunk.entities.get_all(category="actor"):
                self.uncollide(e)
        
        p = self.player()        
        if p is not None:
            for e in self.get_entities_in_rect(p.get_rect(), category="enemy"):
                e.touched_player(p, self)
                    
            self.recenter_camera(p.center())
      
    def recenter_camera(self, pos):
        x = round(pos[0] - global_state.WIDTH/2)
        y = round(pos[1] - global_state.HEIGHT/2)
        self.camera = (x, y)
        
    def get_camera(self):
        return self.camera
            
    def _prepare_to_remove(self, entity):
        entity.is_alive = False
        if entity.is_player():
            self._player = None
        if entity.is_wall():
            r = entity.get_rect().inflate(2, 2)
            for wall in self.get_entities_in_rect(r, category="wall"):
                wall.set_outline_dirty(True)
    
    def draw_all(self, screen):
        offset = cool_math.neg(self.camera)
        sortkey = lambda chunk: chunk.get_rect().x + chunk.get_rect().y
        chunks_to_draw = sorted(self.chunks.values(), key=sortkey) # TODO - onscreen only
        
        for chunk in chunks_to_draw:
            chunk.draw_nonactors(screen, offset)
            
        for chunk in chunks_to_draw:
            chunk.draw_actors(screen, offset)
            
        for chunk in chunks_to_draw:
            chunk.draw_darkness(screen, offset)
            chunk.draw_debug_stuff(screen, offset)
            
    def add_entity(self, entity):
        if entity.is_player():
            if self._player is not None:
                raise ValueError("There is already a player in this world.")
            self._player = entity
            
        chunk = self.get_or_create_chunk(*entity.xy())
        chunk.entities.add(entity) 
        
        if entity.is_wall():
            r = entity.get_rect().inflate(2, 2)
            for wall in self.get_entities_in_rect(r, category="wall"):
                wall.set_outline_dirty(True)
        
    def add_all_entities(self, entity_list):
        for x in entity_list:
            self.add_entity(x)
            
    def player(self):
        return self._player
        
    def get_entities_in_circle(self, center, radius, category=None, not_category=[], cond=None):
        rect = [center[0]-radius, center[1]-radius, radius*2, center[1]*2]
        in_circle = lambda x: cool_math.dist(x.center(), center) <= radius
        rect_search_cond = lambda x: in_circle(x) and (cond==None or cond(x))
        return self.get_entities_in_rect(
                rect, 
                category=category, 
                not_category=not_category, 
                cond=rect_search_cond)
        
    def get_entities_in_rect(self, rect, category=None, not_category=[], cond=None):
        res = []
        for chunk in self.get_chunks_in_rect(rect):
            to_add = chunk.entities.get_all(
                    category=category, 
                    not_category=not_category, 
                    rect=rect, 
                    cond=cond)
            res.extend(to_add)
        return res
        
    def get_entities_at_point(self, pt, cond=None):
        return self.get_entities_in_rect([pt[0], pt[1], 1, 1], cond=cond)
        
    def get_entities_with(self, cond):
        return self.get_chunks_in_rect(null, cond=cond)
        
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
        v_collides = self.get_entities_in_rect(v_rect, category="wall")
        
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
        h_collides = self.get_entities_in_rect(h_rect, category="wall")
                    
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
            
        other_junk.append(entities.Enemy(300,200))
        
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
                    
        
    
        
