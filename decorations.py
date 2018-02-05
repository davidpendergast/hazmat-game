import entities
import images


class Decoration(entities.Entity):
    """Just a noninteractive piece of art basically."""

    def __init__(self, dec_id, animation):
        entities.Entity.__init__(self, animation.width(), animation.height())
        self.animation = animation
        self.dec_id = dec_id
        self.categories.update(["decoration"])

    def get_dec_id(self):
        return self.dec_id

    def sprite(self):
        return self.animation

    def sprite_offset(self):
        return (0, 0)


class Ground(Decoration):

    def __init__(self, dec_id, animation):
        Decoration.__init__(self, dec_id, animation)
        self.categories.update(["ground"])

