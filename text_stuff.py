import pygame

import global_state
import images


_FONT_NAMES = {
    "fancy": "res/Fipps-Regular.otf",
    "standard": "res/coders_crux.ttf"
}

_CACHED_FONTS = {}


def get_font(style, size):
    key = (style, size)
    if key not in _CACHED_FONTS:
        _CACHED_FONTS[key] = pygame.font.Font(_FONT_NAMES[style], size)
    return _CACHED_FONTS[key]


def wrap_text(text_string, rect_width, font):
    """returns: (rectangle, list of lines)"""
    box_w = rect_width
    box_x = int(global_state.WIDTH/2 - box_w/2) 
    lines = []
    
    words = text_string.split(" ")
    next_word = 0
    
    i = 1
    while i < (len(words) - next_word):
        candidate = " ".join(words[next_word:next_word+i+1])
        if font.size(candidate)[0] > box_w:
            lines.append(" ".join(words[next_word:next_word+i]))
            next_word = next_word + i
            i = 1
        else:
            i += 1
    if next_word < len(words)-1:
        lines.append(" ".join(words[next_word:]))             
    
    box_h = len(lines) * 32
    box_y = global_state.HEIGHT - box_h
    box = [box_x, box_y, box_w, box_h]
    return (box, lines)


def draw_text(screen, text_string, font_name, font_size, width):
    font = get_font(font_name, font_size)
    rect, lines = wrap_text(text_string, width, font)

    draw_pretty_bordered_rect(screen, rect, bottom=False)

    for i in range(0, len(lines)):
        line_img = font.render(lines[i], False, (255, 255, 255), (0, 0, 0))
        screen.blit(line_img, (rect[0], rect[1]+32*i))


def draw_pretty_bordered_rect(screen, rect, top=True, left=True, bottom=True, right=True):
    x1 = rect[0]
    x2 = rect[0] + rect[2]
    y1 = rect[1]
    y2 = rect[1] + rect[3]

    bord_w, bord_h = images.TEXT_BORDER_L.size()
    if top and left:
        images.draw_animated_sprite(screen, (x1 - bord_w, y1 - bord_h), images.TEXT_BORDER_TL)
    if top and right:
        images.draw_animated_sprite(screen, (x2, y1 - bord_h), images.TEXT_BORDER_TR)
    if bottom and left:
        images.draw_animated_sprite(screen, (x1 - bord_w, y2), images.TEXT_BORDER_BL)
    if bottom and right:
        images.draw_animated_sprite(screen, (x2, y2), images.TEXT_BORDER_BR)

    for x in range(x1, x2, bord_w):
        if x + bord_w > x2:
            x = x2 - bord_w  # prevent overdrawing of border
        if top:
            images.draw_animated_sprite(screen, (x, y1 - bord_h), images.TEXT_BORDER_T)
        if bottom:
            images.draw_animated_sprite(screen, (x, y2), images.TEXT_BORDER_B)
    for y in range(y1, y2, bord_h):
        if y + bord_h > y2:
            y = y2 - bord_h  # prevent overdrawing of border
        if left:
            images.draw_animated_sprite(screen, (x1 - bord_w, y), images.TEXT_BORDER_L)
        if right:
            images.draw_animated_sprite(screen, (x2, y), images.TEXT_BORDER_R)

    pygame.draw.rect(screen, (0, 0, 0), rect)
