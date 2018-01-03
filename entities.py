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
        self.vel = [0, 0]
        self.rect = pygame.Rect(x, y, w, h)
        self.weight = 1
    
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
    
    def update(self, input_state, world):
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
        
    def set_xy(self, x, y):
        self.set_x(x)
        self.set_y(y)
        
    def set_center_x(self, x):
        self.set_x(x - self.get_rect().width/2)
        
    def set_center_y(self, y):
        self.set_y(y - self.get_rect().height/2)
        
    def set_center(self, x, y):
        self.set_center_x(x)
        self.set_center_y(y)
        
    def xy(self):
        r = self.get_rect()
        return (r.x, r.y)
        
    def center(self):
        r = self.get_rect()
        return (int(r.x + r.width/2), int(r.y + r.height/2))  
        
    def width(self):
        return self.get_rect().width
        
    def height(self):
        return self.get_rect().height
        
    def size(self):
        return (self.width(), self.height()) 
        
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
        
    def is_door(self):
        return False
        
    def is_interactable(self):
        return False
        
    def interact(self):
        pass
        
    def is_decoration(self):
        return False
        
    def is_light_source(self):
        return False
    
    def __repr__(self):
        pos = "(%s, %s)" % (self.rect.x, self.rect.y)
        return type(self).__name__ + pos
        
class Actor(Entity):
    gravity = 1.5
    def __init__(self, x, y, w, h):
        Entity.__init__(self, x, y, w, h)
        self.has_gravity = True
        self.is_grounded = False
        self.is_left_walled = False
        self.is_right_walled = False
        self.max_speed = (10, 20)
        self.jump_height = 64 + 32
        self.max_health = 50
        self.health = 50
        
        self.vel = [0, 0]
    
    def is_actor(self):
        return True
        
    def get_jump_speed(self):
        a = Actor.gravity
        return -math.sqrt(2*a*self.jump_height)
        
    def apply_physics(self):
        self.set_x(self.x + self.vel[0])
        self.set_y(self.y + self.vel[1])
    
    def apply_gravity(self):
        if self.has_gravity:
            if not self.is_grounded:
                self.vel[1] += Actor.gravity
                self.vel[1] = min(self.vel[1], self.max_speed[1]) 
        
    def set_vel_x(self, vx):
        self.vel[0] = vx
        
    def set_vel_y(self, vy):
        self.vel[1] = vy
        
    def deal_damage(self, damage, direction=None):
        self.health -= damage
        print(self, " was damaged by ", damage)
        
class Player(Actor):
    def __init__(self, x, y):
        Actor.__init__(self, x, y, 16, 48)
        self.speed = 5
        
        self.facing_right = True
        self.max_slide_speed = 1.5
        
        self.shoot_cooldown = 0
        self.shoot_max_cooldown = 15
        self.active_bullet = None # rect where bullet is
        
        self.interact_radius = 32
    
    def sprite(self):
        direction = self.facing_right
        if self._is_shooting():
            frm = (self.shoot_max_cooldown - self.shoot_cooldown) // 5 # lol
            anim = images.PLAYER_GUN if direction else images.PLAYER_GUN_LEFT
            return anim.single_frame(frm)
        elif self.is_grounded:
            if abs(self.vel[0]) > 1:
                return images.PLAYER_RUN if direction else images.PLAYER_RUN_LEFT
            else:
                return images.PLAYER_IDLE if direction else images.PLAYER_IDLE_LEFT
        elif self.is_left_walled or self.is_right_walled:
            return images.PLAYER_WALLSLIDE if direction else images.PLAYER_WALLSLIDE_LEFT
        else:
            return images.PLAYER_AIR if direction else images.PLAYER_AIR_LEFT
        
    def sprite_offset(self):
        spr = self.sprite()
        w = self.get_rect().width
        h = self.get_rect().height
        res = [(w - spr.width())/2, (h - spr.height())/2 - (64 - h)/2]
        if spr is images.PLAYER_WALLSLIDE:
            res[0] += 12 # needs changing if sprite is redrawn or player resized
        elif spr is images.PLAYER_WALLSLIDE_LEFT:
            res[0] -= 12
        return res
        
    def draw(self, screen, offset=(0,0), modifier=None):
        if self.active_bullet is not None:
            pygame.draw.rect(screen, (255,255,255), self.active_bullet.move(*offset), 0)
        Actor.draw(self, screen, offset, modifier)
        
    def _update_status_tags(self, world):
        self.is_grounded = world.is_touching_wall(self, (0, 1))
        self.is_left_walled = world.is_touching_wall(self, (-1, 0))
        self.is_right_walled = world.is_touching_wall(self, (1, 0))    
        if self.is_left_walled or self.vel[0] > 0:
            self.facing_right = True
        if self.is_right_walled or self.vel[0] < 0:
            self.facing_right = False
        
    def update(self, input_state, world):
        self._update_status_tags(world)
        self._handle_shooting(world)
        
        keyboard_x = 0
        if input_state.is_held(pygame.K_a):
            keyboard_x -= 1
        if input_state.is_held(pygame.K_d):
            keyboard_x += 1
        
        keyboard_jump = input_state.was_pressed(pygame.K_w) and not self._is_shooting()
        keyboard_shoot = input_state.was_pressed(pygame.K_j) and not self._is_shooting()
        keyboard_interact = input_state.was_pressed(pygame.K_k)
        
        if keyboard_x == 0 or self._is_shooting():
            fric = 1
            if not self.is_grounded:
                fric = 0.25
            self.vel[0] = cool_math.tend_towards(0, self.vel[0], fric)
        else:    
            target_speed = keyboard_x * self.speed
            if self.is_grounded and self.vel[0] * target_speed < 0:
                # turn around instantly when grounded
                self.vel[0] = 0
            else:
                self.vel[0] = cool_math.tend_towards(target_speed, self.vel[0], 1, only_if_increasing=True)
        
        if keyboard_jump:
            if self.is_grounded:
                self.vel[1] = self.get_jump_speed()
            elif self.is_left_walled:
                self.vel[1] = self.get_jump_speed()
                self.vel[0] = self.speed
            elif self.is_right_walled:
                self.vel[1] = self.get_jump_speed()
                self.vel[0] = -self.speed
                
        if keyboard_shoot and not keyboard_jump and self.is_grounded:
            self.shoot_cooldown = self.shoot_max_cooldown
            
        if keyboard_interact and not self._is_shooting():
            box = self.get_rect().inflate((self.interact_radius,0))
            interactables = world.get_entities_in_rect(box, category="interactable")
            cntr = self.center()
            if len(interactables) > 0:
                interactables.sort(key=lambda x: cool_math.dist(cntr, x.center()))
                interactables[0].interact()
                print("interacted with: ", interactables[0])
                
        if self.is_left_walled or self.is_right_walled:
            if self.vel[1] > self.max_slide_speed:
                self.vel[1] = cool_math.tend_towards(self.max_slide_speed, self.vel[1], 2)

        self.apply_gravity()
        self.apply_physics()
        
    def _is_shooting(self):
        return self.shoot_cooldown > 0
        
    def _handle_shooting(self, world):
        if not self.is_grounded:
            self.shoot_cooldown = 0
        elif self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            if self.shoot_cooldown == 10: # loll cmon
                rect = self.get_rect()
                bullet_y = rect.y + rect.height - 26*2
                bullet_w = 300
                bullet_x = rect.x + rect.width if self.facing_right else rect.x - bullet_w
                self.active_bullet = pygame.Rect(bullet_x, bullet_y, bullet_w, 4)
                bullet_hitbox = self.active_bullet.inflate(0, 8)
                direction = (1, 0) if self.facing_right else (-1, 0)
                for e in world.get_entities_in_rect(bullet_hitbox, category="enemy"):
                    e.deal_damage(10, direction)
                    
        if self.shoot_cooldown < 8 or self.shoot_cooldown > 10:
            self.active_bullet = None
        
    def sprite_modifier(self):
        return "normal"
        
    def is_player(self):
        return True
        
class Enemy(Actor):
    def __init__(self, x, y):
        Actor.__init__(self, x, y, 16, 48)
        self.speed = 1.5 + random.random() / 2
        self.current_dir = (0, 0)
        self._randint = random.randint(0,999)
        self.radius = 140 # starts chasing player within this distance
        self.forget_radius = 300 # stops chasing at this distance
        self.is_chasing = False
    
    sprites = [images.BLUE_GUY, images.PURPLE_GUY, images.BROWN_GUY] 
     
    def sprite(self):
        return Enemy.sprites[self._randint % len(Enemy.sprites)] 
        
    def sprite_offset(self):
        spr = self.sprite()
        w = self.get_rect().width
        h = self.get_rect().height
        return [(w - spr.width())/2, (h - spr.height())/2 - (64 - h)/2]
        
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
        
    def update(self, input_state, world):
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
        self.apply_gravity()
        self.apply_physics()
        
    def touched_player(self, player, world):
        v = cool_math.sub(player.center(), self.center())
        v = cool_math.normalize(v)
        player.deal_damage(5, v)
        
    def is_actor(self):
        return True
        
    def is_enemy(self):
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
        
    def update(self, input_state, world):
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
    def __init__(self, x, y, w=32, h=32, sprite=images.WHITE_WALL):
        Entity.__init__(self, x, y, w, h)
        self._sprite = sprite
        self._cached_outline = None # surface
        self._outline_dirty = True
    
    def sprite(self):
        return self._sprite
        
    def sprite_offset(self):
        return (0, 0)
        
    def set_outline_dirty(self, is_dirty):
        self._outline_dirty = is_dirty
        
    def draw(self, screen, offset=(0,0), modifier=None):
        Entity.draw(self, screen, offset, modifier)
        if self._cached_outline != None:
            screen.blit(self._cached_outline, cool_math.add(self.xy(), offset))    
            
    def update(self, input_state, world):
        if self._outline_dirty:
            self.update_outlines(world)
            self._outline_dirty = False 
        
    def update_outlines(self, world):
        if self._cached_outline == None:
            self._cached_outline = pygame.Surface(self.size(), pygame.SRCALPHA, 32)
        else:
            self._cached_outline.fill((0,0,0,0), None, 0)
        rect = self.get_rect()
        is_wall = lambda x: x.is_wall()
        r = [0,0,2,2]
        for x in range(0, self.width(), 2):
            if len(world.get_entities_at_point((rect.x + x, rect.y - 1), is_wall)) == 0:
                r[0]=x
                r[1]=0
                pygame.draw.rect(self._cached_outline, (0,0,0), r, 0)
            if len(world.get_entities_at_point((rect.x + x, rect.y + rect.height), is_wall)) == 0:
                r[0]=x
                r[1]=rect.height - 2
                pygame.draw.rect(self._cached_outline, (0,0,0), r, 0)
        for y in range(0, self.height(), 2):
            if len(world.get_entities_at_point((rect.x - 1, rect.y + y), is_wall)) == 0:
                r[0]=0
                r[1]=y
                pygame.draw.rect(self._cached_outline, (0,0,0), r, 0)
            if len(world.get_entities_at_point((rect.x + rect.width, rect.y + y), is_wall)) == 0:
                r[0]=rect.width - 2
                r[1]=y
                pygame.draw.rect(self._cached_outline, (0,0,0), r, 0)
        
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
        
    def update(self, input_state, world):
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
        
        if len(world.get_entities_in_rect(spawned.get_rect()), not_category="ground") == 0:
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
        
class Door(Entity):
    def __init__(self, x, y, door_id, dest_id, locked=False):
        Entity.__init__(self, x, y, 32, 64) 
        self.door_id = door_id
        self.dest_id = dest_id
        self.locked = locked
        
        # Cooldown behavior:
        #   0: door is closed. 
        #   1: player is teleported to reciever door.
        #   >1: door is opening.
        #   <0: door is closing
        self.open_cooldown = 0
        self.open_max_cooldown = 20
        
    def sprite(self):
        if self.open_cooldown > 0:
            return images.DOOR_OPENING
        elif self.open_cooldown < 0:
            return images.DOOR_CLOSING
        else:
            if self.locked:
                return images.DOOR_LOCKED
            else:
                return images.DOOR_UNLOCKED
    
    def update(self, input_state, world):
        if self.open_cooldown == 1:
            player = world.player()
            dest_door = world.get_door(self.dest_id)
            if player != None and dest_door != None:
                player.set_center(*dest_door.center())
                dest_door.open_cooldown = -dest_door.open_max_cooldown
        
        if self.open_cooldown > 0:
            self.open_cooldown -= 1
        if self.open_cooldown < 0:
            self.open_cooldown += 1
            
    def is_interactable(self):
        # can't interact after it's already been interacted with
        return not self.locked and self.open_cooldown == 0
        
    def interact(self):
        if not self.locked:
            self.open_cooldown = self.open_max_cooldown
            
    def is_door(self):
        return True
                
        
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
    
    def update(self, input_state, world):
        if self.lifespan <= 0 or self.target is not None and not self.target.is_alive:
            self.is_alive = False
        else:
            self.lifespan -= 1
            if self.target is not None:
                pos = self.target.center()
                self.set_center_x(pos[0])
                self.set_center_y(pos[1])
                
class Decoration(Entity):
    """Just a noninteractive piece of art basically."""
    
    def __init__(self, x, y, animation):
        Entity.__init__(self, x, y, animation.width(), animation.height())
        self.animation = animation
        
    def sprite(self):
        return self.animation
        
    def sprite_offset(self):
        return (0, 0)
        
    def is_decoration(self):
        return True
            
class LightEmittingDecoration(Decoration):
    """A decoration that emits light. Should never move."""
    
    def __init__(self, x, y, animation, luminosity, light_radius):
        Decoration.__init__(self, x, y, animation)
        self._luminosity = luminosity   # brightness level from 0 to 255
        self.radius = light_radius      # radius in pixels
    
    def light_profile(self):
        """returns: integers (x, y, luminosity, radius), or None if luminosity 
            or radius is zero
        """
        if self._luminosity > 0 and self.radius > 0:
            pos = self.center()
            return (pos[0], pos[1], self._luminosity, self.radius)
        else:
            return None
    
    def is_light_source(self):
        return True
                
class Ladder(Entity):
    def __init__(self, x, y):
        Entity.__init__(self, x, y, 24, 32)
        
    def sprite_offset(self):
        return (-4, 0)
        
    def sprite(self):
        return images.LADDER

class Ground(Decoration):
    all_sprites = [images.STONE_GROUND, images.SAND_GROUND, 
            images.GRASS_GROUND, images.PURPLE_GROUND]
            
    def __init__(self, x, y, ground_type):
        Decoration.__init__(self, x, y, Ground.all_sprites[ground_type])
        
    def is_ground(self):
        return True
        
class EntityCollection:
    def __init__(self, entities=[]):
        self.all_stuff = []
        self.categories = { # category -> (test, entities)
            "actor":        (lambda x: x.is_actor(), set()),
            "enemy":        (lambda x: x.is_enemy(), set()),
            "player":       (lambda x: x.is_player(), set()),
            "ground":       (lambda x: x.is_ground(), set()),
            "door":         (lambda x: x.is_door(), set()),
            "interactable": (lambda x: x.is_interactable(), set()),
            "wall":         (lambda x: x.is_wall(), set()),
            "decoration":   (lambda x: x.is_decoration(), set()),
            "light_source": (lambda x: x.is_light_source(), set())
        }
        
        for e in entities:
            self.add(e)
        
    def add(self, entity):
        self.all_stuff.append(entity)
        cats = self._get_categories(entity)
        for catkey in cats:
            self.categories[catkey][1].add(entity)
        
    def remove(self, entity):
        EntityCollection._safe_remove(entity, self.all_stuff, True)
        cats = self._get_categories(entity)
        for catkey in cats:
            EntityCollection._safe_remove(entity, self.categories[catkey][1]) 
                
    def get_all(self, category=None, not_category=[], rect=None, cond=None):
        """
            category: Single category or a list of categories from which the 
                results must belong. If null, all categories are allowed.
            
            not_category: Single category or a list of categories from which
                the results may not belong. Overpowers the category parameter.
            
            rect: if given, all returned entities must intersect this rect.
            
            cond: boolean lambda. if given, entities must satisfy the condition.   
                      
        """
        res_set = set()
        
        # listify single elements
        if isinstance(not_category, str):
            not_category = [not_category]
        
        if category != None and isinstance(category, str):
            category = [category]
        
        to_test = None
        if category == None:
            to_test = self.all_stuff
        else:
            to_test = set()
            for cat in category:
                for x in self.categories[cat][1]:
                    to_test.add(x)
            
        for e in to_test:
            accept = True
            for not_cat in not_category:
                if self.categories[not_cat][0](e):
                    accept = False
                    break
            accept = accept and (rect==None or e.get_rect().colliderect(rect))
            accept = accept and (cond==None or cond(e))
            if accept:
                res_set.add(e)
        
        return list(res_set)    
        
    def all_categories(self):
        return self.categories.keys()     
            
    def _safe_remove(item, collection, print_err=False):
        try:
            collection.remove(item)
        except:
            if print_err:
                print("cannot remove ", item,", probably because it's not in the collection")
           
    def _get_categories(self, entity):
        return [x for x in self.categories if self.categories[x][0](entity)]       
        
    def __contains__(self, key):
        return key in self.all_stuff # TODO ehh
        
    def __len__(self):
        return len(self.all_stuff)
        
    def __iter__(self):
        return iter(self.all_stuff)
        
        

