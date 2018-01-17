import entities
import images

ALL_DECORATIONS = {}  # dec_id -> lambda(() -> Decoration)


def init_decorations():
    print("initializing decorations...")
    ALL_DECORATIONS["lightbulb"] = lambda: LightEmittingDecoration(0, 0, "lightbulb", images.LIGHT_BULB, luminosity=255, light_radius=128)
    ALL_DECORATIONS["wire_vert"] = lambda: Decoration(0, 0, "wire_vert", images.WIRE_VERTICAL)
    ALL_DECORATIONS["chalkboard"] = lambda: Decoration(0, 0, "chalkboard", images.CHALKBOARD)
    ALL_DECORATIONS["ground_stone"] = lambda: Ground(0, 0, "ground_stone", images.STONE_GROUND)
    ALL_DECORATIONS["ground_sand"] = lambda: Ground(0, 0, "ground_sand", images.SAND_GROUND)
    ALL_DECORATIONS["ground_grass"] = lambda: Ground(0, 0, "ground_grass", images.GRASS_GROUND)
    ALL_DECORATIONS["ground_purple"] = lambda: Ground(0, 0, "ground_purple", images.PURPLE_GROUND)
    ALL_DECORATIONS["ground_wall"] = lambda: Ground(0, 0, "ground_wall", images.WALL_GROUND)
    ALL_DECORATIONS["ground_dark"] = lambda: Ground(0, 0, "ground_dark", images.DARK_GROUND)


def get_decoration(dec_id):
    if dec_id not in ALL_DECORATIONS:
        raise ValueError("Unknown decoration id: " + str(dec_id))
    else:
        return ALL_DECORATIONS[dec_id]()


class Decoration(entities.Entity):
    """Just a noninteractive piece of art basically."""

    def __init__(self, x, y, dec_id, animation):
        entities.Entity.__init__(self, x, y, animation.width(), animation.height())
        self.animation = animation
        self.dec_id = dec_id
        self.categories.update(["decoration"])

    def get_dec_id(self):
        return self.dec_id

    def sprite(self):
        return self.animation

    def sprite_offset(self):
        return (0, 0)


class LightEmittingDecoration(Decoration):
    """A decoration that emits light. Should never move."""

    def __init__(self, x, y, dec_id, animation, luminosity, light_radius):
        Decoration.__init__(self, x, y, dec_id, animation)
        self._luminosity = luminosity  # brightness level from 0 to 255
        self.radius = light_radius  # radius in pixels
        self.categories.update(["light_source"])

    def light_profile(self):
        """returns: integers (x, y, luminosity, radius), or None if luminosity
            or radius is zero
        """
        if self._luminosity > 0 and self.radius > 0:
            pos = self.center()
            return (pos[0], pos[1], self._luminosity, self.radius)
        else:
            return None


class Ground(Decoration):

    def __init__(self, x, y, dec_id, animation):
        Decoration.__init__(self, x, y, dec_id, animation)
        self.categories.update(["ground"])


init_decorations()