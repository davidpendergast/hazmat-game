import pygame

import copy

import entities
import global_state
import cool_math
import images

class HUD:
    def __init__(self):
        self.selected_item_to_place = None
        self.selected_item_placeable = False
        self.items = [
            entities.Wall(0, 0), 
            entities.Wall(0,0,16,16,images.CHAIN_SMOL), 
            entities.Wall(0,0,16,16,images.WHITE_WALL_SMOL),
            entities.Ladder(0,0), 
            entities.Door(0,0,"test_door1", "test_door2"),
            entities.Enemy(0,0)
        ] 
        
    def update(self, tick_counter, input_state, world):
        self._handle_selecting_item(input_state)
        self._handle_placing_item(input_state, world)
    
    def draw(self, screen, offset=(0, 0)):
        to_place = self.selected_item_to_place
        placeable = self.selected_item_placeable
        if to_place is not None and placeable is not None:
            mod = "green_ghosts" if placeable else "red_ghosts"    
            to_place.draw(screen, offset, modifier=mod)   
        
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
                w,h = to_place.get_rect().size
                if w <= 16:
                    w = 16
                elif w <= 32:
                    w = 32
                if h <= 16:
                    h = 16
                elif h <= 32:
                    h = 32
                c_xy = world.get_tile_at(*mouse, tilesize=(w,h))
                to_place.set_center_x(c_xy[0])
                to_place.set_center_y(c_xy[1])
        
        if to_place == None or world.player() == None or not input_state.mouse_in_window():
            self.selected_item_placeable = None
        else:
            loc = to_place.center()
            player_loc = world.player().center()
            dist = cool_math.dist(loc, player_loc)
            in_range = dist <= 120
            unblocked = len(world.get_entities_in_rect(to_place.get_rect())) == 0
            self.selected_item_placeable = in_range and unblocked
            
            if input_state.mouse_was_pressed() and self.selected_item_placeable:
                world.add_entity(copy.deepcopy(to_place))
                self.selected_item_placeable = None
                self.selected_item_to_place = None 
        
