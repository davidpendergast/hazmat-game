import pygame

import copy
import collections

import entities
import global_state
import cool_math
import images
import text_stuff

class HUD:
    def __init__(self):
        self.selected_item_to_place = None
        self.selected_item_placeable = False
        self.items = [
            entities.Wall(0, 0), 
            entities.Wall(0,0,16,16,images.CHAIN_SMOL), 
            entities.Wall(0,0,16,16,images.WHITE_WALL_SMOL),
            entities.Terminal(0,0), 
            entities.Door(0,0,"test_door1","test_door2"),
            entities.Enemy(0,0),
            entities.LightEmittingDecoration(0,0,images.LIGHT_BULB, luminosity=255, light_radius=128),
            entities.Decoration(0,0,images.WIRE_VERTICAL),
            entities.Decoration(0,0,images.CHALKBOARD)
        ] 
        
        self.text_queue = collections.deque()
        self.show_text_time = -500
        
    def display_text(self, lines):
        """lines: string or list of strings to display"""
        if isinstance(lines, str):
            lines = [lines]
            
        self.text_queue.extend(lines)
        self.show_text_time = global_state.tick_counter
        
    def update(self, input_state, world):
        if self.is_showing_text(): # when text is showing, block all other user commands
            if input_state.was_pressed(pygame.K_k) and len(self.text_queue) > 0:
                # wait a little bit before nuking the text box
                if global_state.tick_counter - self.show_text_time > 15:
                    self.text_queue.popleft()
                    self.show_text_time = global_state.tick_counter
        else:
            self._handle_selecting_item(input_state)
            placed = self._handle_placing_item(input_state, world)
            removed = False
            if not placed:
                removed = self._handle_removing_item(input_state, world)
    
    def draw(self, screen, offset=(0, 0)):
        to_place = self.selected_item_to_place
        placeable = self.selected_item_placeable
        if to_place is not None and placeable is not None:
            mod = "green_ghosts" if placeable else "red_ghosts"    
            to_place.draw(screen, offset, modifier=mod)   
            
        if global_state.show_fps:
            basicfont = text_stuff.get_font("standard", 32)
            text = "FPS: " + str(global_state.current_fps)
            fps_text = basicfont.render(text, True, (255, 0, 0), (255, 255, 255))
            screen.blit(fps_text, (0, 0))
            
        if self.is_showing_text() and len(self.text_queue) > 0:
            text_string = self.text_queue[0]
            text_stuff.draw_text(screen, text_string, "standard", 32, 512)
        
    def _get_item_to_place(self, index):
        if index >= len(self.items):
            return None
        else:
            return self.items[index]
    
    KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
             pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0]
    
    def _handle_selecting_item(self, input_state):
        idx = None
        keys = HUD.KEYS
        for i in range(0, len(keys)):
            if input_state.was_pressed(keys[i]):
                idx = i
                break
        
        if idx is not None:
            item = self._get_item_to_place(idx)
            if self.selected_item_to_place == item:
                self._set_item_to_place(None)
            else:
                self._set_item_to_place(item)
    
    def _set_item_to_place(self, item):
        self.selected_item_to_place = item
        
    def _handle_placing_item(self, input_state, world):
        to_place = self.selected_item_to_place
        
        if to_place is not None:
            mouse = input_state.mouse_pos()
            if mouse is not None:
                in_world = world.to_world_pos(*mouse)
                w,h = to_place.get_rect().size
                w = 16 if w <= 16 else 32
                h = 16 if h <= 16 else 32
                c_xy = world.get_tile_at(*in_world, tilesize=(w,h))
                to_place.set_x(c_xy[0]-w/2)
                to_place.set_y(c_xy[1]-h/2)
        
        if to_place == None or world.player() == None or not input_state.mouse_in_window():
            self.selected_item_placeable = False
        else:
            loc = to_place.center()
            player_loc = world.player().center()
            dist = cool_math.dist(loc, player_loc)
            in_range = dist <= 120
            blocked_by = world.get_entities_in_rect(to_place.get_rect(), not_category="ground") 
            self.selected_item_placeable = in_range and len(blocked_by) == 0
            
            if input_state.mouse_was_pressed() and self.selected_item_placeable:
                world.add_entity(copy.deepcopy(to_place))
                self.selected_item_placeable = None
                self.selected_item_to_place = None 
                return True
                
        return False
    
    def _handle_removing_item(self, input_state, world):
        if self.selected_item_to_place == None:
            if input_state.mouse_in_window() and input_state.mouse_was_pressed():
                screen_pos = input_state.mouse_pos()
                world_pos = world.to_world_pos(*screen_pos)
                ents = world.get_entities_at_point(world_pos, not_category="ground")
                print("trying to del: ", ents)
                if len(ents) > 0:
                    return world.remove_entity(ents[0])
        return False
        
    def is_absorbing_inputs(self):
        freshly_closed = global_state.tick_counter - self.show_text_time < 2
        return self.is_showing_text() or freshly_closed
        
    def is_showing_text(self):
        return len(self.text_queue) > 0
        
    
        
    
            
            
            
        
    
        
    
        
        
