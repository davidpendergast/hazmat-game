import pygame
import random
import math

import images


def reversify(animation):
    anim_id = animation.get_id() + "_reversed"
    anim = images.create(anim_id, list(reversed(animation.rects)), tpf=animation.TPF)
    anim.set_custom_sheet(animation.custom_sheet())
    return anim


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

    cached_img = images.get_cached_image(cache_key)
    if cached_img is None:
        cached_img = pygame.Surface((rect[2], rect[3]), flags=pygame.SRCALPHA)
        cached_img.fill((0, 0, 0, ambient_darkness))
        for src in relative_sources:
            sized_lightmap = images.get_lightmap(src[3])
            dest = (src[0] - src[3], src[1] - src[3])
            cached_img.blit(sized_lightmap, dest, special_flags=pygame.BLEND_RGBA_SUB)
            images.put_cached_image(cache_key, cached_img)

    return cached_img


def _rand_scatter(x, y, max_dist):
    d = random.random()*max_dist
    angle = random.random() * 2 * 3.1415
    x_res = x + d*math.cos(angle)
    y_res = y + d*math.sin(angle)
    return (x_res, y_res)


def create_death_animation(base_animation, anim_id, num_frames, tpf):
    w = base_animation.width()
    h = base_animation.height()
    new_surface = pygame.Surface((w*num_frames, h), pygame.SRCALPHA)

    # t goes from 0 to 1
    # f = lambda x, y, t: (x, y + t*(h-y))
    f = lambda _x, _y, _t: _rand_scatter(_x, _y, _t*10)

    base_rect = base_animation.rects[0]
    base_sheet = images.SHEETS["normal"]  # ehh kinda unsafe but w/ever

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

    res = images.create(anim_id, [pygame.Rect(i*w, 0, w, h) for i in range(0, num_frames)], tpf=tpf)
    sheet_id = anim_id + "_death"
    res.set_custom_sheet(sheet_id)
    images.add_sheet(sheet_id, new_surface)
    return res

