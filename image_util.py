import pygame
import random
import math

import cool_math
import image_cache
import settings


TICKS_PER_FRAME = 20    # default animation speed


def dye_sheet(sheet, color, base_color=(0, 0, 0), alpha=255):
    new_sheet = sheet.copy()
    size = new_sheet.get_size()
    for x in range(0, size[0]):
        for y in range(0, size[1]):
            c = sheet.get_at((x, y))
            if c[3] == 0:
                continue
            val = (0.2989 * c[0] + 0.5870 * c[1] + 0.1140 * c[2]) / 256
            r = int(base_color[0] + (color[0] - base_color[0]) * val)
            g = int(base_color[1] + (color[1] - base_color[1]) * val)
            b = int(base_color[2] + (color[2] - base_color[2]) * val)
            new_sheet.set_at((x, y), (r, g, b, alpha))
    return new_sheet


def get_lightmap(radius):
    cache_key = "lightmap_" + str(radius)
    cached_img = image_cache.get_cached_image(cache_key)

    if cached_img is None:
        size = (radius * 2 + 1, radius * 2 + 1)
        cached_img = pygame.transform.scale(image_cache.LIGHTMAP, size)
        image_cache.put_cached_image(cache_key, cached_img)

    return cached_img


def get_darkness_overlay(rect, sources, ambient_darkness):
    """
        rect: rectangle that determines size of result, and relative positions
            of light sources.

        sources: list of tuples (x, y, luminosity, radius). If unsorted, will
            become sorted as a side effect of calling this method.

        ambient_darkness: number from 0 to 1, with 1 being completely dark
    """
    # we gotta recompute light if something changes
    sources.sort()
    relative_sources = tuple([(lp[0] - rect[0], lp[1] - rect[1], lp[2], lp[3]) for lp in sources])
    cache_key = "darkness_overlay_" + str(relative_sources)

    cached_img = image_cache.get_cached_image(cache_key)
    if cached_img is None:
        cached_img = pygame.Surface((rect[2], rect[3]), flags=pygame.SRCALPHA)
        cached_img.fill((0, 0, 0, ambient_darkness))
        for src in relative_sources:
            sized_lightmap = get_lightmap(src[3])
            dest = (src[0] - src[3], src[1] - src[3])
            cached_img.blit(sized_lightmap, dest, special_flags=pygame.BLEND_RGBA_SUB)
            image_cache.put_cached_image(cache_key, cached_img)

    return cached_img


def _rand_scatter(x, y, max_dist):
    d = random.random()*max_dist
    angle = random.random() * 2 * 3.1415
    x_res = x + d*math.cos(angle)
    y_res = y + d*math.sin(angle)
    return (x_res, y_res)


def create_death_animation(base_animation, base_sheet, anim_id, num_frames, tpf):
    """Creates and caches a new sheet with , returns Animation"""
    w = base_animation.width()
    h = base_animation.height()
    new_surface = pygame.Surface((w*num_frames, h), pygame.SRCALPHA)

    # t goes from 0 to 1
    # f = lambda x, y, t: (x, y + t*(h-y))
    f = lambda _x, _y, _t: _rand_scatter(_x, _y, _t*10)

    base_rect = base_animation.rects[0]

    for i in range(0, num_frames):
        for x in range(0, w):
            for y in range(0, h):
                base_x = base_rect[0] + x
                base_y = base_rect[1] + y
                mapping = f(x, y, i / num_frames)
                mapped_x = int(mapping[0])
                mapped_y = int(mapping[1])
                if 0 <= mapped_x < w and 0 <= mapped_y < h:
                    color = base_sheet.get_at((base_x, base_y))
                    new_surface.set_at((i*w + mapped_x, mapped_y), color)

    sheet_id = anim_id + "_death"
    image_cache.add_sheet(sheet_id, new_surface)

    rects = [pygame.Rect(i*w, 0, w, h) for i in range(0, num_frames)]
    res = Animation(rects, anim_id, tpf=tpf)
    res.set_custom_sheet(sheet_id)
    return res


def create_lightmap(r, exp=0):
    lightmap = pygame.Surface((r*2, r*2), flags=pygame.SRCALPHA)

    throttle = settings.get_light_blend_throttle_level()
    num_rings = None if throttle == 0 else int(9 * (1-throttle)) + 1
    ring_alphas = [int(255*(1 - (i+0.5)/num_rings)) for i in range(0, num_rings)] if num_rings is not None else None

    ctr = (r, r)
    # going pixel by pixel is very slow, but only done once at launch
    lightmap.lock()  # helps performance supposedly
    for x in range(0, r*2):
        for y in range(0, r*2):
            pt = (x, y)
            rel_dist = cool_math.dist(ctr, pt) / r
            if rel_dist <= 1:

                for _ in range(0, exp):
                    rel_dist = math.sqrt(rel_dist)

                if num_rings is None:
                    alpha = int(255*(1 - rel_dist))
                else:
                    my_ring = min(num_rings-1, int(num_rings * rel_dist))
                    alpha = ring_alphas[my_ring]

                color = (255, 255, 255, alpha)
                lightmap.set_at(pt, color)
    lightmap.unlock()

    return lightmap


class Animation:
    def __init__(self, rects, anim_id="no_id", tpf=TICKS_PER_FRAME):
        self.rects = rects
        self.TPF = tpf
        self.anim_id = anim_id
        self._subanimations = [None] * len(rects)
        self._custom_sheet = None

    def num_frames(self):
        return len(self.rects)

    def single_frame(self, idx):
        """
        :returns a single-frame animation from a given index of this one.
        """
        idx = idx % self.num_frames()
        if self._subanimations[idx] is None:
            # id just for debugging, no global lookup
            anim_id = self.get_id() + "[" + str(idx) + "]"
            animation = Animation([self.rects[idx]], anim_id=anim_id, tpf=self.TPF)
            animation.set_custom_sheet(self.custom_sheet())
            self._subanimations[idx] = animation

        return self._subanimations[idx]

    def set_custom_sheet(self, sheet_name):
        self._custom_sheet = sheet_name

    def custom_sheet(self):
        return self._custom_sheet

    def width(self):
        return self.rects[0].width

    def height(self):
        return self.rects[0].height

    def size(self):
        return (self.width(), self.height())

    def get_id(self):
        return self.anim_id

    def ticks_per_frame(self):
        return self.TPF