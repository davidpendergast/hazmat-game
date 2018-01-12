LEVELS_DIR = "levels/"
WALLS_HEADER = "##  WALLS  ##"
DECOR_HEADER = "##  DECORATIONS  ##"
GROUND_HEADER = "##  GROUND  ##"
REF_HEADER = "##  REFERENCES  ##"


class Level:
    def __init__(self, name):
        self.name = name

    def build(self, world):
        pass


def save_to_level_file(world, filename):
    with open(LEVELS_DIR + filename, "w") as file:

        walls = []
        decorations = []
        ground = []
        references = []

        for e in world.get_entities_with(not_category="actor"):
            if e.get_ref_id() is not None:
                references.append(e)
            if e.is_("wall"):
                walls.append(e)
            elif e.is_("ground"):
                ground.append(e)
            elif e.is_("decoration"):
                decorations.append(e)
            else:
                print("discarding entity: ", e)

        lines = list()
        lines.append(REF_HEADER)
        for ref in references:
            lines.append("{}, {}, {}".format(ref.get_ref_id(), ref.get_x(), ref.get_y()))
        lines.append("")

        lines.append(DECOR_HEADER)
        for dec in decorations:
            lines.append("{}, {}, {}".format(dec.get_dec_id(), dec.get_x(), dec.get_y()))
        lines.append("")

        lines.append(WALLS_HEADER)
        for wall in walls:
            r = wall.get_rect()
            lines.append("wall, {}, {}, {}, {}".format(r[0], r[1], r[2], r[3]))
        lines.append("")

        lines.append(GROUND_HEADER)
        for gr in ground:
            lines.append("{}, {}, {}".format(gr.get_dec_id(), gr.get_x(), gr.get_y()))
        lines.append("")

        for l in lines:
            file.write(l + "\n")












