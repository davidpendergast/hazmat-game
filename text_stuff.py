import pygame


_FONT_NAMES = {
    "fancy":"res/Fipps-Regular.otf",
    "standard":"res/coders_crux.ttf"
}

_CACHED_FONTS = {}

def get_font(style, size):
    key = (style, size)
    if not key in _CACHED_FONTS:
        _CACHED_FONTS[key] = pygame.font.Font(_FONT_NAMES[style], size)
    return _CACHED_FONTS[key]
        
    
