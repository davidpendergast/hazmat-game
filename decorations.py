import entities
import images


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

    def __init__(self, x, y, dec_id, animation, light_radius):
        Decoration.__init__(self, x, y, dec_id, animation)
        self.radius = light_radius      # radius in pixels
        self.categories.update(["light_source"])

    def light_profile(self):
        """returns: integers (x, y, luminosity, radius), or None if luminosity
            or radius is zero
        """
        pos = self.center()
        return (pos[0], pos[1], 255, self.radius)


class Ground(Decoration):

    def __init__(self, x, y, dec_id, animation):
        Decoration.__init__(self, x, y, dec_id, animation)
        self.categories.update(["ground"])

