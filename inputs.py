class InputState:
    def __init__(self):
        self.held_keys = {} # keycode -> time pressed
        self.current_time = 0
    
    def set_key(self, key, held):
        if held and key not in self.held_keys:
                self.held_keys[key] = self.current_time
        elif not held and key in self.held_keys:
            del self.held_keys[key]
    
    def is_held(self, key):
        return key in self.held_keys
    
    def time_held(self, key):
        if not key in self.held_keys:
            return -1
        else:
            return self.current_time - self.held_keys[key]
            
    def was_pressed(self, key):
        return self.time_held(key) == 0
    
    def all_held_keys(self):
        return self.held_keys.keys()
        
    def update(self, tick_counter):
        self.current_time = tick_counter
        
        
        
                
