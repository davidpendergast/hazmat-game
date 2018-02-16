import pygame
import random

import image_cache
import image_util
import images
import entities
import global_state
import cool_math
import settings

CHUNK_SIZE = 96

AMBIENT_DARKNESS = 200

DUMMY_CHUNK = None


class Chunk:
    def __init__(self, x, y):
        cs = CHUNK_SIZE
        self.rect = pygame.Rect(x, y, cs, cs)
        self.entities = entities.EntityCollection(name_for_debug="Chunk("+str(x)+", "+str(y)+") collection")

        dirs = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        self._neighbors = [(x + d[0] * cs, y + d[1] * cs) for d in dirs]

    def add(self, entity):
        self.entities.add(entity)
        if entity.is_ground() or entity.is_wall():
            self.mark_dirty()

    def remove(self, entity):
        self.entities.remove(entity)
        if entity.is_ground() or entity.is_wall():
            self.mark_dirty()

    def xy(self):
        rect = self.get_rect()
        return (rect.x, rect.y)

    def get_rect(self):
        return self.rect

    def center(self):
        r = self.get_rect()
        x = round(r.x + r.width / 2)
        y = round(r.y + r.height / 2)
        return (x, y)

    def size(self):
        return self.get_rect().size

    def _cache_key(self):
        return str(self.xy()) + "_walls_n_ground"

    def mark_dirty(self):
        """Must be called whenever something ~static~ changes"""
        image_cache.remove_cached_image(self._cache_key())

    def draw_nonactors(self, screen, offset):
        if len(self.entities.get_all(category=["ground", "wall"], limit=1)) > 0:
            key = self._cache_key()
            cache_img = image_cache.get_cached_image(key)
            if cache_img is None:
                cache_img = pygame.Surface(self.size(), flags=pygame.SRCALPHA)
                new_offset = cool_math.neg(self.xy())
                for g in self.entities.get_all(category="ground"):
                    g.draw(cache_img, new_offset)
                for e in self.entities.get_all(category="wall"):
                    e.draw(cache_img, new_offset)
                image_cache.put_cached_image(key, cache_img)

            screen_pos = cool_math.add(self.xy(), offset)
            screen.blit(cache_img, screen_pos)

        special_stuff = ["ground", "wall", "actor", "overlay", "zone", "reference", "spawner"]
        for e in self.entities.get_all(not_category=special_stuff):
            e.draw(screen, offset)

    def draw_actors(self, screen, offset):
        # Actor sprites can overflow out of their rects on the left or above,
        # so they need to be drawn after everything else (to prevent issues at
        # chunk borders).
        for e in self.entities.get_all(category="actor"):
            e.draw(screen, offset)

    def draw_overlays(self, screen, offset):
        # These bad boys go on top of everything
        for e in self.entities.get_all(category="overlay"):
            e.draw(screen, offset)

    def draw_darkness(self, world, screen, offset):
        sources = []
        max_range = settings.MAX_LIGHT_RADIUS

        rect = self.get_rect()
        r = [rect.x - max_range, rect.y - max_range,
             rect.width + max_range*2, rect.height + max_range*2]

        for chunk in world.get_chunks_in_rect(r, and_above_and_left=False):
            if chunk is not None:
                for decoration in chunk.entities.get_all(category="light_source"):
                    lp = decoration.light_profile()
                    if lp is not None:
                        sources.append(lp)

        img = image_util.get_darkness_overlay(rect, sources, AMBIENT_DARKNESS)
        screen.blit(img, cool_math.add(rect.topleft, offset))

    def draw_debug_stuff(self, screen, offset):
        if global_state.show_chunk_redraws:
            key = self._cache_key()
            if image_cache.get_cached_image(key) is not None and image_cache.time_since_cached(key) < 15:
                screen_pos = cool_math.add(offset, self.xy())
                rect = [screen_pos[0], screen_pos[1], self.size()[0], self.size()[1]]
                pygame.draw.rect(screen, (255, 90, 90), rect, 10)

        if global_state.show_debug_rects:
            pygame.draw.rect(screen, (0, 0, 0), self.get_rect().move(*offset), 1)
            for thing in self.entities.get_all(not_category="ground"):
                pygame.draw.rect(screen, images.RAINBOW, thing.get_rect().move(*offset), 2)
                if hasattr(thing, 'radius') and thing.radius > 2:
                    center = cool_math.add(thing.center(), offset)
                    pygame.draw.circle(screen, images.RAINBOW, center, thing.radius, 2)

            for zone in self.entities.get_all(category="zone"):
                zone.draw(screen, offset)

        if global_state.show_items_to_place:
            for thing in self.entities.get_all(category=["spawner", "reference"]):
                thing.draw(screen, offset)

    def __contains__(self, entity):
        return entity in self.entities


class World:
    def __init__(self):
        self.camera = (0, 0)
        self._player = None
        self.chunks = {}

        # counts up as player is missing (used to pause a bit before restarting level after deaths)
        self._missing_player_counter = 0

    def get_chunk_key_for_point(self, x, y):
        return (x - (x % CHUNK_SIZE), y - (y % CHUNK_SIZE))

    def get_chunk(self, x, y):
        key = self.get_chunk_key_for_point(x, y)
        if key in self.chunks:
            return self.chunks[key]
        else:
            return None

    def get_chunk_from_key(self, key):
        if key in self.chunks:
            return self.chunks[key]
        else:
            return None

    def get_chunk_keys_in_rect(self, rect, and_above_and_left=True):
        xy_min = self.get_chunk_key_for_point(rect[0], rect[1])
        xy_max = self.get_chunk_key_for_point(rect[0] + rect[2], rect[1] + rect[3])
        xy_min = (int(xy_min[0] / CHUNK_SIZE), int(xy_min[1] / CHUNK_SIZE))
        xy_max = (int(xy_max[0] / CHUNK_SIZE), int(xy_max[1] / CHUNK_SIZE))

        res = []
        extra = 1 if and_above_and_left else 0

        for x in range(xy_min[0] - extra, xy_max[0] + 1):
            for y in range(xy_min[1] - extra, xy_max[1] + 1):
                res.append((x * CHUNK_SIZE, y * CHUNK_SIZE))

        return res

    def get_chunks_in_rect(self, rect, and_above_and_left=True):
        keys = self.get_chunk_keys_in_rect(rect, and_above_and_left=and_above_and_left)
        res = []
        for key in keys:
            if key in self.chunks:
                res.append(self.chunks[key])
        return res

    def get_or_create_chunk(self, x, y, and_add_to_dict=True):
        key = self.get_chunk_key_for_point(x, y)
        if key not in self.chunks:
            new_chunk = Chunk(key[0], key[1])
            if and_add_to_dict:
                self.chunks[key] = new_chunk
            return new_chunk
        else:
            return self.chunks[key]

    def get_chunks_to_update(self):
        return [c for c in self.chunks.values()]

    def update_all(self, input_state):
        updating_chunks = self.get_chunks_to_update()
        for chunk in updating_chunks:
            for entity in chunk.entities:
                entity.update(input_state, self)

        new_chunks = {}
        for chunk in updating_chunks:
            dead = []
            moved_out = []
            for entity in chunk.entities:
                if not entity.is_alive:
                    dead.append(entity)
                elif not chunk.get_rect().collidepoint(entity.xy()):
                    moved_out.append(entity)
            for entity in dead:
                self.remove_entity(entity, chunk=chunk)
            for entity in moved_out:
                chunk.remove(entity)

                key = self.get_chunk_key_for_point(*entity.xy())
                moving_to = self.get_chunk_from_key(key)
                if moving_to is None:
                    if key in new_chunks:
                        # in case two entities move into a new chunk on the same frame
                        moving_to = new_chunks[key]
                    else:
                        moving_to = self.get_or_create_chunk(
                            key[0], key[1],
                            and_add_to_dict=False)
                        new_chunks[key] = moving_to
                moving_to.add(entity)
        self.chunks.update(new_chunks)
        updating_chunks.extend(new_chunks.values())

        for chunk in updating_chunks:
            for e in chunk.entities.get_all(category="actor"):
                self.uncollide(e)

        p = self.player()
        if p is not None:
            for e in self.get_entities_in_rect(p.get_rect(), category="enemy"):
                e.touched_player(p, self)

            self.recenter_camera(p.center())

        if p is None:
            self._missing_player_counter += 1
        else:
            self._missing_player_counter = 0

    def recenter_camera(self, pos):
        x = round(pos[0] - global_state.WIDTH / 2)
        y = round(pos[1] - global_state.HEIGHT / 2)
        self.camera = (x, y)

    def get_camera(self):
        return self.camera

    def time_since_player_death(self):
        return self._missing_player_counter

    def _prepare_to_remove(self, entity):
        entity.is_alive = False
        if entity.is_player():
            self._player = None
        if entity.is_wall():
            r = entity.get_rect().inflate(2, 2)
            for wall in self.get_entities_in_rect(r, category="wall"):
                wall.set_outline_dirty(True)
            for chunk in self.get_chunks_in_rect(r, and_above_and_left=False):
                chunk.mark_dirty()

    def draw_all(self, screen):
        screen_rect = [
            self.camera[0], self.camera[1],
            global_state.WIDTH, global_state.HEIGHT
        ]
        chunks_to_draw = self.get_chunks_in_rect(screen_rect)

        def sortkey(c):
            return -c.get_rect().x - c.get_rect().y

        chunks_to_draw.sort(key=sortkey)

        offset = cool_math.neg(self.camera)

        for chunk in chunks_to_draw:
            chunk.draw_nonactors(screen, offset)

        for chunk in chunks_to_draw:
            chunk.draw_actors(screen, offset)

        for chunk in chunks_to_draw:
            chunk.draw_overlays(screen, offset)

        onscreen_keys = self.get_chunk_keys_in_rect(
            screen_rect,
            and_above_and_left=False)

        # global DUMMY_CHUNK
        # if DUMMY_CHUNK is None:
        #    DUMMY_CHUNK = Chunk(0, 0)

        for key in onscreen_keys:
            chunk = self.get_chunk_from_key(key)
            if chunk is not None:
                if not global_state.show_no_darkness:
                    chunk.draw_darkness(self, screen, offset)
                chunk.draw_debug_stuff(screen, offset)
            # else:
            #    pass  # no need for this if background is black
                # if not global_state.show_no_darkness:
                #    DUMMY_CHUNK.rect.x = key[0]
                #    DUMMY_CHUNK.rect.y = key[1]
                #    DUMMY_CHUNK.draw_darkness(self, screen, offset)

    def add_entity(self, entity):
        if entity.is_player():
            if self._player is not None:
                raise ValueError("There is already a player in this world.")
            self._player = entity

        chunk = self.get_or_create_chunk(*entity.xy())
        chunk.add(entity)

        if entity.is_wall() or entity.is_ground():
            r = entity.get_rect().inflate(2, 2)
            for wall in self.get_entities_in_rect(r, category="wall"):
                wall.set_outline_dirty(True)
            for chunk in self.get_chunks_in_rect(r, and_above_and_left=False):
                chunk.mark_dirty()

    def add_all_entities(self, entity_list):
        for x in entity_list:
            self.add_entity(x)

    def remove_entity(self, entity, chunk=None):
        if chunk is None:
            chunk = self.get_chunk(*entity.xy())
            if chunk is None:
                return False
        if entity in chunk.entities:
            self._prepare_to_remove(entity)
            chunk.remove(entity)
            return True
        else:
            return False

    def player(self):
        return self._player

    def get_entities_in_circle(self, center, radius, category=None, not_category=None, cond=None):
        rect = [center[0] - radius, center[1] - radius, radius * 2, center[1] * 2]

        def in_circle(x):
            return cool_math.dist(x.center(), center) <= radius

        return self.get_entities_in_rect(
            rect,
            category=category,
            not_category=not_category,
            cond=lambda x: in_circle(x) and (cond is None or cond(x)))

    def get_entities_in_rect(self, rect, category=None, not_category=None, cond=None, limit=None):
        res = []
        for chunk in self.get_chunks_in_rect(rect):
            to_add = chunk.entities.get_all(
                category=category,
                not_category=not_category,
                rect=rect,
                cond=cond,
                limit=limit)
            res.extend(to_add)
        return res

    def get_entities_at_point(self, pt, category=None, not_category=None, cond=None, limit=None):
        return self.get_entities_in_rect(
            [pt[0], pt[1], 1, 1],
            category=category,
            not_category=not_category,
            cond=cond,
            limit=limit)

    def get_entities_with(self, category=None, not_category=None, cond=None, limit=None):
        res = []
        for chunk in self.chunks.values():
            res.extend(chunk.entities.get_all(
                category=category,
                not_category=not_category,
                cond=cond,
                limit=limit))
        return res

    def get_door(self, door_id):
        matches = self.get_entities_with(cond=lambda x: x.is_door() and x.door_id == door_id, limit=1)
        if len(matches) == 0:
            return None
        else:
            return matches[0]

    def uncollide(self, entity):
        initial_rect = entity.get_rect()
        shifted = self._uncollide_helper(entity)
        if shifted[1] != initial_rect.y:
            entity.set_vel_y(0)
        if shifted[0] != initial_rect.x:
            entity.set_vel_x(0)

        entity.set_x(shifted[0])
        entity.set_y(shifted[1])

    def _uncollide_helper(self, entity):
        """
        returns: (x, y) coordinates that rect can be shifted to so that
        it doesn't collide with wall entities in the world. If no 'good'
        positions can be found, returns the rect's original coordinates.
        """
        rect = entity.get_rect().copy()
        res_y = rect.y
        res_x = rect.x

        v_rect = rect.inflate(-10, 0)
        v_collides = self.get_entities_in_rect(v_rect, category="solid", cond=lambda x: x.blocks_movement(entity))

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
        h_rect = rect.inflate(0, -10)
        h_collides = self.get_entities_in_rect(h_rect, category="solid", cond=lambda x: x.is_("wall"))  # ehh

        for w in h_collides:
            w_rect = w.get_rect()
            if w_rect.colliderect(h_rect):
                left_shift_x = w_rect.x - rect.width
                right_shift_x = w_rect.x + w_rect.width
                if abs(left_shift_x - rect.x) < abs(right_shift_x - rect.x):
                    res_x = left_shift_x
                else:
                    res_x = right_shift_x
        return (res_x, res_y)

    def is_touching(self, actor, category, direction, cond=None, dist=1):
        rect = actor.get_rect()
        detector_rect = cool_math.sliver_adjacent(rect, direction, thickness=dist)
        detected = self.get_entities_in_rect(detector_rect, category=category, cond=cond, limit=1)
        return len(detected) > 0

    def to_world_pos(self, screen_x, screen_y):
        x = screen_x + self.camera[0]
        y = screen_y + self.camera[1]
        return (x, y)

    def get_tile_at(self, x, y, tilesize=(32, 32)):
        """returns: coordinate of center of 'tile' that contains (x, y)"""
        cx = int(abs(x) / tilesize[0]) * tilesize[0] + tilesize[0] / 2
        cx = cx if x >= 0 else -cx
        cy = int(abs(y) / tilesize[1]) * tilesize[1] + tilesize[1] / 2
        cy = cy if y >= 0 else -cy
        return (cx, cy)
